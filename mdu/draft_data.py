"""
this is where calculations are performed on the 17Lands public data sets and
aggregate calculations are returned.

In general, one loads a DraftData object for a certain set with a specified
filter, then asks for pandas DataFrame with certain metrics, grouped by
certain attributes. By default, grouping is by card name.

```
pandas.options.display.max_rows = 1000
ddo = DraftData('BLB', filter={'rank': 'mythic'})
df = ddo.df(['gpwr', 'ata', 'deq_base', 'deq']) # see notebooks/deq.ipynb for info on DEq
df
```

Dask is used to distribute computation among manageable chunks so that 
entire files do not need to be read into memory. 

Aggregate dataframes containing raw counts are cached in the local file system
for performance.
"""

import functools
import datetime

import dask.dataframe as dd
import numpy
import pandas

from mdu.cache_17l import data_file_path
import mdu.filter
import mdu.cache
from mdu.get_dytpes import get_dtypes
from mdu.extensions import game_counts_extensions

SUPPORTED_GROUPBYS = {
    "draft": [
        "name",
        "rank",
        "pack_number",
        "pick_number",
        "user_n_games_bucket",
        "user_game_win_rate_bucket",
        "player_cohort",
        "draft_date",
        "draft_week",
    ],
    "game": [
        "name",
        "build_index",
        "match_number",
        "game_number",
        "rank",
        "opp_rank",
        "main_colors",
        "splash_colors",
        "on_play",
        "num_mulligans",
        "opp_num_mulligans",
        "opp_colors",
        "user_n_games_bucket",
        "user_game_win_rate_bucket",
        "player_cohort",
        "draft_date",
        "draft_week",
    ],
    "card": ["color_identity_str", "rarity", "type", "cmc"],
}


def cache_key(ddo, *args, **kwargs):
    set_code = ddo.set_code
    filter_spec = ddo.filter_str
    arg_str = str(args) + str(kwargs)

    hash_num = hash(set_code + filter_spec + arg_str)
    return hex(hash_num)[3:]


def player_cohort(row):
    if row["user_n_games_bucket"] < 100:
        return "All"
    if row["user_game_win_rate_bucket"] < 0.49:
        return "Bottom"
    if row["user_game_win_rate_bucket"] > 0.57:
        return "Top"
    return "Middle"


def week_from_date(date_str):
    date = datetime.date.fromisoformat(date_str)
    return (date - datetime.timedelta(days=date.weekday())).isoformat()


def extend_shared_columns(df: dd.DataFrame):
    df["player_cohort"] = df.apply(player_cohort, axis=1, meta=pandas.Series(dtype="object"))
    df["draft_date"] = df["draft_time"].apply(
        lambda t: str(t[0:10]), meta=pandas.Series(dtype="object")
    )
    df["draft_week"] = df["draft_date"].apply(week_from_date, meta=pandas.Series(dtype="object"))


def extend_draft_columns(draft_df: dd.DataFrame) -> None:
    extend_shared_columns(draft_df)
    draft_df["event_matches"] = draft_df["event_match_wins"] + draft_df["event_match_losses"]
    draft_df["name"] = draft_df["pick"]


def extend_game_columns(game_df: dd.DataFrame) -> None:
    extend_shared_columns(game_df)


def picked_counts(draft_view: dd.DataFrame, groupbys=None):
    if not groupbys:
        groupbys = ["name"]

    df = (
        draft_view.groupby(groupbys)[["event_matches", "event_match_wins", "pick_number"]]
        .agg({"event_matches": "sum", "event_match_wins": "sum", "pick_number": ["sum", "count"]})
        .compute()
    )
    df["num_picked"] = df[("pick_number", "count")]
    df["num_matches"] = df[("event_matches", "sum")]
    df["sum_pick_num"] = df[("pick_number", "sum")] + df["num_picked"]
    df["num_match_wins"] = df[("event_match_wins", "sum")]

    df = df[["num_picked", "sum_pick_num", "num_matches", "num_match_wins"]].sort_index()
    df.columns = [
        "num_picked",
        "sum_pick_num",
        "num_matches",
        "num_match_wins",
    ]  # remove multiindex

    return df


class DraftData:
    def __init__(self, set_code: str, filter_spec: dict = None):
        self.set_code = set_code.upper()

        self._filter = mdu.filter.from_spec(filter_spec)
        self.filter_str = str(filter_spec)  # todo: standardize representation for sensible hashing

        draft_path = data_file_path(set_code, "draft")
        self._draft_df = dd.read_csv(draft_path, dtype=get_dtypes(draft_path))

        game_path = data_file_path(set_code, "game")
        self._game_df = dd.read_csv(game_path, dtype=get_dtypes(game_path))

        self._card_df = pandas.read_csv(data_file_path(set_code, "card"))
        self._dv = None
        self._gv = None

    @property
    def card_names(self):
        """
        The card file is generated from the draft data file, so this is exactly the
        list of card names used in the datasets
        """
        return list(self._card_df["name"].values)

    @property
    def draft_view(self):
        if self._dv is None:
            dv = self._draft_df.copy()
            extend_draft_columns(dv)
            if self._filter is not None:
                dv = dv.loc[self._filter]
            self._dv = dv
        return self._dv

    @property
    def game_view(self):
        if self._gv is None:
            gv = self._game_df.copy()
            extend_game_columns(gv)
            if self._filter is not None:
                gv = gv.loc[self._filter]
            self._gv = gv
        return self._gv

    def game_rates(self, game_counts: pandas.DataFrame):
        """
        in_pool_gwr             := num_win_in_pool / num_in_pool
        gpwr                    := num_wins_in_deck / num_in_deck
        gp_pct                  := num_games_in_deck / num_games_in_pool
        ohwr                    := <num_wins_oh> / num_oh
        gdwr                    := <num_wins_drawn> / num_drawn
        gihwr                   := <num_wins_gih> / num_gih
        gnswr                   := <num_wins_gns> / num_gns
        iwd                     := gihwr - gnswr
        ihd                     := gihwr - gpwr
        mull_rate               := mull_in_deck / num_in_deck
        turns_per_game          := turns_in_deck / num_in_deck
        """
        pass

    def game_counts(
        self, groupbys: list | None = None, read_cache: bool = True, write_cache: bool = True
    ) -> pandas.DataFrame:
        method_name = "game_counts"
        calc_method = self._game_counts

        return self.fetch_or_get(
            method_name,
            calc_method,
            read_cache=read_cache,
            write_cache=write_cache,
            groupbys=groupbys,
        )

    def fetch_or_get(
        self, method_name: str, calc_method, read_cache: bool, write_cache: bool, **kwargs
    ):
        if read_cache:
            key = cache_key(self, method_name, **kwargs)
            if mdu.cache.cache_exists(self.set_code, key):
                return mdu.cache.read_cache(self.set_code, key)
        result = calc_method(**kwargs)
        if write_cache:
            mdu.cache.write_cache(self.set_code, key, result)
        return result

    def _game_counts(
        self, groupbys: list | None = None, custom_extensions: list | tuple = ()
    ) -> pandas.DataFrame:
        """
        A data frame of counts easily aggregated from the 'game' file.
        Card-attribute groupbys can be applied after this stage to be filtered
        through a rates aggregator.
        """
        if not groupbys:
            groupbys = ["name"]

        extensions = game_counts_extensions + tuple(custom_extensions)

        game_view = self.game_view
        names = self.card_names
        nonname_groupbys = [c for c in groupbys if c != "name"]

        prefixes = [
            "deck",
            "sideboard",
            "opening_hand",
            "drawn",
            "tutored",
        ]

        prefix_names = {prefix: [f"{prefix}_{name}" for name in names] for prefix in prefixes}

        df_components = [game_view]
        for ext in extensions:
            df = ext["calc"](game_view, prefix_names)
            ext_names = [f"{ext['prefix']}_{name}" for name in names]
            prefix_names[ext["prefix"]] = ext_names
            df.columns = ext_names
            df_components.extend(df)

        concat_df = dd.concat(df_components, axis=1)

        all_count_df = concat_df[
            functools.reduce(lambda curr, prev: prev + curr, prefix_names.values())
        ]
        win_count_df = all_count_df.where(df["won"], other=0)

        all_df = dd.concat([all_count_df, concat_df[nonname_groupbys]], axis=1)
        win_df = dd.concat([win_count_df, concat_df[nonname_groupbys]], axis=1)

        if nonname_groupbys:
            games_result = all_df.groupby(nonname_groupbys).sum().compute()
            win_result = win_df.groupby(nonname_groupbys).sum().compute()
        else:
            games_sum = all_df.sum().compute()
            games_result = pandas.DataFrame(
                numpy.expand_dims(games_sum.values, 0), columns=games_sum.index
            )
            win_sum = win_df.sum().compute()
            win_result = pandas.DataFrame(
                numpy.expand_dims(win_sum.values, 0), columns=win_sum.index
            )

        count_cols = {}
        for prefix in prefixes:
            for outcome, df in {"all": games_result, "win": win_result}.items():
                count_df = df[prefix_names[prefix]]
                count_df.columns = names
                melt_df = pandas.melt(count_df, var_name="name", ignore_index=False)
                count_cols[f"{prefix}_{outcome}"] = melt_df["value"].reset_index(drop=True)
        # grab the indexes from the last one, they are all the same
        index_df = melt_df.reset_index().drop("value", axis="columns")

        by_name_df = pandas.DataFrame(count_cols, dtype=numpy.int64)
        by_name_df.index = pandas.MultiIndex.from_frame(index_df)

        if "name" in groupbys:
            if len(groupbys) == 1:
                by_name_df.index = by_name_df.index.droplevel()
            return by_name_df

        return by_name_df.groupby(groupbys).sum()
