"""
this is where calculations are performed on the 17Lands public data sets and
aggregate calculations are returned.

Aggregate dataframes containing raw counts are cached in the local file system
for performance.
"""

import functools
import re
from typing import Callable

import polars as pl

from mdu.cache_17l import data_file_path
from mdu.get_schema import schema
import mdu.cache
import mdu.filter
import mdu.manifest
from mdu.columns import ColumnDefinition
from mdu.enums import View, ColName, ColType


def cache_key(args) -> str:
    """
    cache arguments by __str__ (based on the current value of a mutable, so be careful)
    """
    return hex(hash(str(args)))[3:]


def col_df(
    df: pl.LazyFrame,
    col: str,
    col_def_map: dict[str, ColumnDefinition],
    is_view: bool,
):
    cdef = col_def_map[col]
    if not cdef.dependencies:
        return df.select(cdef.expr)

    root_col_exprs = []
    col_dfs = []
    for dep in cdef.dependencies:
        dep_def = col_def_map[dep]
        if dep_def.dependencies is None or is_view and len(dep_def.views):
            root_col_exprs.append(dep_def.expr)
        else:
            col_dfs.append(col_df(df, dep, col_def_map, is_view))

    if root_col_exprs:
        col_dfs.append(df.select(root_col_exprs))

    dep_df = pl.concat(col_dfs, how="horizontal")
    return dep_df.select(cdef.expr)


def fetch_or_cache(
    calc_fn: Callable,
    set_code: str,
    args: list,
    read_cache: bool = True,
    write_cache: bool = True,
):
    key = cache_key(args)

    if read_cache:
        if mdu.cache.cache_exists(set_code, key):
            return mdu.cache.read_cache(set_code, key)

    df = calc_fn(*args)

    if write_cache:
        mdu.cache.write_cache(set_code, key, df)

    return df


def base_agg_df(
    set_code: str,
    m: mdu.manifest.Manifest,
    use_streaming: bool = False,
) -> pl.DataFrame:
    """
    This is where the heavy lifting happens. There are two distinct kinds of aggregations, "pick_sum"
    and "name_sum". First, select the query plan for the derived required columns under m.view_cols
    for a base view (DRAFT or GAME). Then for pick_sum columns, simply sum with the given groupbys.

    For name_sum columns, groupby the nonname groupbys, then unpivot to card names. If card name
    (or any card attrs) are not groupbys, do an additional groupby step. Then collect and join
    the aggregated data frames.

    Note that all aggregations are sums. Any proper expectation (e.g. weight averages, variance)
    can be calculated using this paradigm. For e.g. max, you will either need to implement new
    logic or use the trick of doing nth rt(x ^ n) for large enough n to approximate.

    TODO: cache the individual column aggregations instead of the join for cache efficiency
    """
    join_dfs = []
    groupbys = m.base_view_groupbys

    is_name_gb = ColName.NAME in groupbys
    nonname_gb = tuple(gb for gb in groupbys if gb != ColName.NAME)

    for view, cols_for_view in m.view_cols.items():
        if view == View.CARD:
            continue
        df_path = data_file_path(set_code, view)
        base_view_df = pl.scan_csv(df_path, schema=schema(df_path))
        col_dfs = [col_df(base_view_df, col, m.col_def_map, is_view=True) for col in cols_for_view]
        base_df_prefilter = pl.concat(col_dfs, how="horizontal")

        if m.dd_filter is not None:
            base_df = base_df_prefilter.filter(m.dd_filter.expr)
        else:
            base_df = base_df_prefilter

        pick_sum_cols = tuple(
            c for c in cols_for_view if m.col_def_map[c].col_type == ColType.PICK_SUM
        )
        if pick_sum_cols:
            name_col_tuple = (pl.col(ColName.PICK).alias(ColName.NAME),) if is_name_gb else ()

            pick_df = base_df.select(nonname_gb + name_col_tuple + pick_sum_cols)
            join_dfs.append(pick_df.group_by(groupbys).sum().collect(streaming=use_streaming))

        name_sum_cols = tuple(
            c for c in cols_for_view if m.col_def_map[c].col_type == ColType.NAME_SUM
        )
        for col in name_sum_cols:
            cdef = m.col_def_map[col]
            pattern = f"^{cdef.name}_"
            name_map = functools.partial(lambda patt, name: re.split(patt, name)[1], pattern)

            expr = pl.col(f"^{cdef.name}_.*$").name.map(name_map)
            pre_agg_df = base_df.select((expr,) + nonname_gb)

            if nonname_gb:
                agg_df = pre_agg_df.group_by(nonname_gb).sum()
            else:
                agg_df = pre_agg_df.sum()

            index = nonname_gb if nonname_gb else None
            unpivoted = agg_df.unpivot(
                index=index, value_name=m.col_def_map[col].name, variable_name=ColName.NAME
            )

            if not is_name_gb:
                df = unpivoted.group_by(nonname_gb).sum().collect(streaming=use_streaming)
            else:
                df = unpivoted.collect(streaming=use_streaming)

            join_dfs.append(df)

    return functools.reduce(
        lambda prev, curr: prev.join(curr, on=groupbys, how="outer", coalesce=True), join_dfs
    )


def metrics(
    set_code: str,
    columns: list[str] | None = None,
    groupbys: list[str] | None = None,
    filter_spec: dict | None = None,
    extensions: list[ColumnDefinition] | None = None,
    use_streaming: bool = False,
    read_cache: bool = True,
    write_cache: bool = True,
) -> pl.DataFrame:
    m = mdu.manifest.create(columns, groupbys, filter_spec, extensions)

    agg_df = fetch_or_cache(
        base_agg_df,
        set_code,
        [set_code, m, use_streaming],
        read_cache=read_cache,
        write_cache=write_cache,
    )

    return agg_df
