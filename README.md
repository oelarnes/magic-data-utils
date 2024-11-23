# 🪄 spells ✨

**spells** is a python package that tutors up customizable, optimized analysis of the public data sets provided by [17Lands](https://www.17lands.com/) and exiles the annoying, fiddly, and slow parts of your workflow. Spells exposes one first-class function, `summon`, which summons a Polars DataFrame to the battlefield.

```python
>>>import spells
>>>spells.summon('BLB')
shape: (276, 14)
┌─────────────────────────┬───────┬──────────┬──────────┬───┬────────┬──────────┬─────────┬──────────┐
│ name                    ┆ color ┆ rarity   ┆ num_seen ┆ … ┆ num_oh ┆ oh_wr    ┆ num_gih ┆ gih_wr   │
│ ---                     ┆ ---   ┆ ---      ┆ ---      ┆   ┆ ---    ┆ ---      ┆ ---     ┆ ---      │
│ str                     ┆ str   ┆ str      ┆ i64      ┆   ┆ i64    ┆ f64      ┆ i64     ┆ f64      │
╞═════════════════════════╪═══════╪══════════╪══════════╪═══╪════════╪══════════╪═════════╪══════════╡
│ Agate Assault           ┆ R     ┆ common   ┆ 245811   ┆ … ┆ 30659  ┆ 0.529632 ┆ 72959   ┆ 0.541688 │
│ Agate-Blade Assassin    ┆ B     ┆ common   ┆ 289813   ┆ … ┆ 31099  ┆ 0.560886 ┆ 68698   ┆ 0.548939 │
│ Alania's Pathmaker      ┆ R     ┆ common   ┆ 315760   ┆ … ┆ 22774  ┆ 0.52819  ┆ 54702   ┆ 0.537439 │
│ Alania, Divergent Storm ┆ RU    ┆ rare     ┆ 37408    ┆ … ┆ 2133   ┆ 0.473043 ┆ 5843    ┆ 0.491528 │
│ Artist's Talent         ┆ R     ┆ rare     ┆ 44725    ┆ … ┆ 995    ┆ 0.433166 ┆ 2528    ┆ 0.455696 │
│ …                       ┆ …     ┆ …        ┆ …        ┆ … ┆ …      ┆ …        ┆ …       ┆ …        │
│ Wick, the Whorled Mind  ┆ B     ┆ rare     ┆ 27641    ┆ … ┆ 4648   ┆ 0.517857 ┆ 11640   ┆ 0.547938 │
│ Wildfire Howl           ┆ R     ┆ uncommon ┆ 121015   ┆ … ┆ 4370   ┆ 0.514416 ┆ 11029   ┆ 0.529422 │
│ Wishing Well            ┆ U     ┆ rare     ┆ 52946    ┆ … ┆ 584    ┆ 0.491438 ┆ 1622    ┆ 0.563502 │
│ Ygra, Eater of All      ┆ BG    ┆ mythic   ┆ 6513     ┆ … ┆ 3862   ┆ 0.620145 ┆ 9926    ┆ 0.62976  │
│ Zoraline, Cosmos Caller ┆ BW    ┆ rare     ┆ 17689    ┆ … ┆ 6381   ┆ 0.604294 ┆ 15242   ┆ 0.622753 │
└─────────────────────────┴───────┴──────────┴──────────┴───┴────────┴──────────┴─────────┴──────────┘
```

Coverting to pandas DataFrame is as simple as invoking the chained call `summon(...).to_pandas()`.

Spells is not affiliated with 17Lands. Please review the Usage Guidelines for 17lands data before using Spells, and consider supporting their patreon. Spells is free and open-source; please consider contributing and feel free to make use of the source code under the terms of the MIT license.

## spells

- Uses [Polars](https://docs.pola.rs/) for high-performance, multi-threaded, chunked aggregations of large datasets
- Uses Polars to power an expressive query language for specifying custom extensions and optimizing complex queries
- Supports calculating the standard aggregations and measures out of the box with no arguments (ALSA, GIH WR, etc)
- Caches aggregate DataFrames in the local file system automatically for instantaneous reproduction of previous analysis
- Manages grouping and filtering by built-in and custom columns at the row level
- Provides over 50 explicitly specified, enumerated, documented custom column definitions
- Supports "Deck Color Data" aggregations out of the box.
- Provides a CLI tool `spells [add|refresh|remove|clear_local] [SET]` to download and manage external files
- Downloads and manages public datasets from 17Lands
- Downloads and models booster configuration and card data from [MTGJSON](https://mtgjson.com/)
- Is fully typed, linted, and statically analyzed for support of advanced IDE features
- Provides optional enums for all base columns and built-in extensions, as well as for custom extension parameters
- Uses Polars expressions to support second-stage aggregations like z-scores out of the box with one call to summon
- Is lightweight: Polars is the only dependency

## summon

`summon` takes four optional arguments, allowing a fully declarative specification of your desired analysis. Basic functionality not provided by this api can often be managed by simple chained calls using the polars API, e.g. sorting and post-agg filtering.
  - `columns` specifies the desired output columns
    ```python
    >>spells.summon('BLB', columns=["gp_wr", "ata"])
    shape: (276, 3)
    ┌─────────────────────────┬──────────┬──────────┐
    │ name                    ┆ gp_wr    ┆ ata      │
    │ ---                     ┆ ---      ┆ ---      │
    │ str                     ┆ f64      ┆ f64      │
    ╞═════════════════════════╪══════════╪══════════╡
    │ Agate Assault           ┆ 0.538239 ┆ 6.162573 │
    │ Agate-Blade Assassin    ┆ 0.546623 ┆ 7.904145 │
    │ Alania's Pathmaker      ┆ 0.538747 ┆ 8.886676 │
    │ Alania, Divergent Storm ┆ 0.489466 ┆ 5.601287 │
    │ Artist's Talent         ┆ 0.466227 ┆ 7.515328 │
    │ …                       ┆ …        ┆ …        │
    │ Wick, the Whorled Mind  ┆ 0.525859 ┆ 3.618172 │
    │ Wildfire Howl           ┆ 0.513218 ┆ 8.632178 │
    │ Wishing Well            ┆ 0.533792 ┆ 8.56727  │
    │ Ygra, Eater of All      ┆ 0.570971 ┆ 1.559604 │
    │ Zoraline, Cosmos Caller ┆ 0.570701 ┆ 2.182625 │
    └─────────────────────────┴──────────┴──────────┘
    ```
  - `group_by` specifies the grouping by one or more columns. By default, group by card names, but optionally group by any of a large set of fundamental and derived columns, including card attributes and your own custom extension.
    ```python
    >>>spells.summon('BLB', columns=["num_won", "num_games", "game_wr"], group_by=["main_colors"], filter_spec={"num_colors": 2})
    shape: (10, 4)
    ┌─────────────┬─────────┬───────────┬──────────┐
    │ main_colors ┆ num_won ┆ num_games ┆ game_wr  │
    │ ---         ┆ ---     ┆ ---       ┆ ---      │
    │ str         ┆ u32     ┆ u32       ┆ f64      │
    ╞═════════════╪═════════╪═══════════╪══════════╡
    │ BG          ┆ 85022   ┆ 152863    ┆ 0.556197 │
    │ BR          ┆ 45900   ┆ 81966     ┆ 0.559988 │
    │ RG          ┆ 34641   ┆ 64428     ┆ 0.53767  │
    │ UB          ┆ 30922   ┆ 57698     ┆ 0.535928 │
    │ UG          ┆ 59879   ┆ 109145    ┆ 0.548619 │
    │ UR          ┆ 19638   ┆ 38679     ┆ 0.507717 │
    │ WB          ┆ 59480   ┆ 107443    ┆ 0.553596 │
    │ WG          ┆ 76134   ┆ 136832    ┆ 0.556405 │
    │ WR          ┆ 49712   ┆ 91224     ┆ 0.544944 │
    │ WU          ┆ 16483   ┆ 31450     ┆ 0.524102 │
    └─────────────┴─────────┴───────────┴──────────┘
    ```
  - `filter_spec` specifies a row-level filter for the dataset, using an intuitive custom query formulation
    ```python
    >>>from spells.enums import ColName
    >>>spells.summon('BLB', columns=["game_wr"], group_by=["player_cohort"], filter_spec={'lhs': 'num_mulligans', 'op': '>', 'rhs': 0})
    shape: (4, 2)
    ┌───────────────┬──────────┐
    │ player_cohort ┆ game_wr  │
    │ ---           ┆ ---      │
    │ str           ┆ f64      │
    ╞═══════════════╪══════════╡
    │ Bottom        ┆ 0.33233  │
    │ Middle        ┆ 0.405346 │
    │ Other         ┆ 0.406151 │
    │ Top           ┆ 0.475763 │
    └───────────────┴──────────┘
    ```
  - `extensions` allows for the specification of arbitrarily complex derived columns and aggregations, including custom columns built on top of custom columns.
    ```python
    >>>import polars as pl
    >>>from spells.columns import ColumnDefinition
    >>>from spells.enums import ColType, View, ColName
    >>>ext = ColumnDefinition(
    ...     name='deq_base',
    ...     col_type=ColType.AGG,
    ...     expr=(pl.col('gp_wr') - pl.col('gp_wr_mean') + (14 - pl.col('ata')).pow(2) * 0.03 / (14 ** 2)) * pl.col('pct_gp'),
    ...     dependencies=['gp_wr', 'gp_wr_mean', 'ata', 'pct_gp']
    ...)
    >>>spells.summon('BLB', columns=['deq_base'], filter_spec={'player_cohort': 'Top'}, extensions=[ext])
    ...     .filter(pl.col('deq_base').is_finite())
    ...     .sort('deq_base', descending=True)
    ...     .head(10)
    shape: (10, 2)
    ┌───────────────────────────┬──────────┐
    │ name                      ┆ deq_base │
    │ ---                       ┆ ---      │
    │ str                       ┆ f64      │
    ╞═══════════════════════════╪══════════╡
    │ Sword of Fire and Ice     ┆ 0.055695 │
    │ Valley Questcaller        ┆ 0.052849 │
    │ Maha, Its Feathers Night  ┆ 0.048736 │
    │ Season of Loss            ┆ 0.048111 │
    │ Fecund Greenshell         ┆ 0.045668 │
    │ Beza, the Bounding Spring ┆ 0.041635 │
    │ Season of Gathering       ┆ 0.041418 │
    │ Warren Warleader          ┆ 0.040377 │
    │ Ygra, Eater of All        ┆ 0.040024 │
    │ Valley Mightcaller        ┆ 0.039758 │
    └───────────────────────────┴──────────┘
    ```
    
    Note the use of chained calls to the Polars DataFrame api to perform manipulations on the result of `summon`.
    
## Installation

Spells is available on PyPI as *spells-mtg*, and can be installed using pip or any package manager:

`pip install spells-mtg`

Spells is still in development and could benefit from many new features and improvements. As such, you might rather clone this repository and install locally. It is set up to use pdm, but it's just a regular old python package and you can install with your normal workflow.

If you are new to Python, I recommend using a package manager like poetry, pdm or uv to create a virtual environment and manage your project.

## Performance

Spells provides several features out of the box to optimize performance to the degree possible given its generality.

### Query Optimization

Firstly, it is built on top of Polars, a modern, well-supported DataFrame engine that enables declarative query plans and lazy evaluation, allowing for automatic performance optimization in the execution of the query plan. Spells selects only the necessary columns for your analysis, at the lowest depth possible per column, and uses "concat" rather than "with" throughout to ensure the best performance and flexibility for optimization. 

By default, Polars loads the entire selection into memory before aggregation for optimal time performance. For query plans that are too memory-intensive, Spells exposes the Polars parameter `streaming`, which performs aggregations in chunks based on available system resources. `polars.Config` exposes settings for further tweaking your execution plan. Spells and Polars do not support distributed computation.

### Local Caching

Additionally, by default, Spells caches the results of expensive aggregations in the local file system as parquet files, which by default are found under the `data/local` path from the execution directory, which can be configured using the environment variable `SPELLS_PROJECT_DIR`. Query plans which request the same set of first-stage aggregations (sums over base rows) will attempt to locate the aggregate data in the cache before calculating. This guarantees that a repeated call to `summon` returns instantaneously.

When refreshing a given set's data files from 17Lands using the provided functions, the cache for that set is automatically cleared. Additionally `summon` has named arguments `read_cache` and `write_cache`, and the project exposes `spells.cache.clear_cache(set_code: str)` for further control.

# Documentation
In order to give a valid specification for more complex queries, it's important to understand a bit about what Spells is doing under the hood.

## Basic Concepts
Let's briefly review the structure of the underlying data. Spells supports aggregations on two of the three large data sets provided by 17Lands, which
are identified as "views" within Spells. First there is *draft*, which is the source for information about draft picks. The row model is single draft picks with pack and pool context. Unlike *game*, there are two different paradigms for aggregating over card names. 

First, one can group by the value of the "pick" column and sum numerical column values. This is how ATA is calculated. In Spells, we tag columns to be summed in this way as *pick_sum* columns. For example, "taken_at" is equivalent to "pick_number", but whereas the latter is available for grouping, "taken_at" is summed over groups. 

Second, certain columns are pivoted horizontally within the raw data and suffixed with card names, for example "pack_card_Savor". In Spells we tag such columns as *name_sum*, and group by non-name columns and sum before unpivoting. The columns are identified by their prefix only and Spells handles the mapping. 

A standard way to aggregate information in non-*name_sum* columns over names is to multiply that column over the pivoted column. For example, to calculate the *name_sum* column "last_seen", used in ALSA, we multiply "pack_card" by a modified version of "pick_number".

In the *game* file, the row model represents games, and primarily uses *name_sum* aggregations for the familiar columns, such as "num_gih", from which win rates are derived. For groupings that do not use card names or card attributes (to recreate the "deck color data" page, for example), one can also specify *game_sum* columns which aggregate simply over rows.

## Aggregate View

Once aggregation columns, filters and groupings are determined at the row level for each of the required base views, Spells asks Polars to sum over groups and unpivot as needed to produce the "base aggregate view", which fixes the row model (pre-card attributes) to the provided base groupings. This base aggregate view is cached by default to the local file system, keyed by the *manifest*, which is a function of the specification provided by the user.

Next, card attributes are calculated and joined to the base aggregate view by name, and an additional grouping is performed if requested by the user to produce the *aggregate view*.

A final extension and selection stage is applied to the aggregate view, which is where weighted averages like GIH WR are calculated. Polars expression language enables aggregations to be represented as expressions and broadcast back to the row level, enabling Spells to support arbitrary chains of aggregation and extension at the aggregate view level. For example, one could calculate the mean of a metric over groups by archetype, regress a metric by a function of that mean, then calculate the mean of that regressed metric, all expressed declaratively as column expressions and simply specified by name in the `summon` api call.

So that's it, that's what Spells does from a high level. `summon` will hand off a Polars DataFrame which can be cast to pandas, sorted, filtered, used to be generate plots or whatever you like. If a task can be handled as easily via a chained call or outside library, it should stay that way, but if you have a request for features specific to the structure of limited data that could be handled in a general way, please reach out! In particular I am interested in scientific workflows like maximum likelihood estimation, but I haven't yet considered how to build it into Spells.

# Roadmap to 1.0

- [ ] Implement GNS and name-mapped column exprs
- [ ] Organize and analyze daily downloads from 17Lands (not a scraper!)
- [ ] Helper functions to generate second-order analysis by card name
- [ ] Support min and max aggregations over base views
- [ ] Helper functions for common plotting paradigms
- [ ] Example notebooks
- [ ] Enhanced profiling
- [ ] Optimized caching strategy
- [ ] Testing of streaming mode
- [ ] Scientific workflows: regression, MLE, etc


