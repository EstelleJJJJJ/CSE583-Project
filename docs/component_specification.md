# Component specification

We kept the design small. Two components are built (the data manager and the matcher), two
are planned (the map and the web page), and there's one helper script for refreshing the
data.

## Software components

### 1. Data manager (`src/parkmatch/data.py`)

- **What it does:** Loads the two CSV files that ship with the package and joins them into
  one table with one row per park.
- **Inputs:** `build_park_table(year)` takes the year of visits to add (`int`, default 2025).
  `load_parks()` and `load_visits()` take nothing.
- **Outputs:** pandas DataFrames. `build_park_table()` returns 475 rows: the park columns
  plus `visits` (a float, NaN when a park has no visitor statistics).
- **Uses:** no other component.
- **Side effects:** none. It only reads files.

### 2. Matcher (`src/parkmatch/matcher.py`)

- **What it does:** Filters, scores, compares and looks up parks in the table from the data
  manager.
- **Inputs and outputs:**

| Function | Inputs | Output |
|---|---|---|
| `find_parks` | the table; `states`, `activities`, `amenities` (lists of strings); `max_fee` (float); `needs_campground` (bool) | DataFrame of matching parks with `match_score` (0 to 1) and `match_reasons` (str), best first |
| `explain_match` | one row of the table and the same choices | one sentence (str) |
| `compare_parks` | the table and a list of park codes | DataFrame with one column per park |
| `search_parks` | the table and some text | DataFrame of parks whose name contains the text |
| `park_summary` | the table and one park code | dict with name, states, description, fee, campgrounds, visits, link |

- **How the score works:** states, fee and campground are filters, so a park passes or not.
  A park with an unknown fee doesn't pass a fee filter. Activities and facilities are
  scored: `match_score` is the share of the requested ones the park has, so a park with 2 of
  3 gets 0.67. Parks with a score of 0 are left out, and ties are sorted by visits.
- **Uses:** the data manager's table, which is passed in as an argument.
- **Side effects:** none.

### 3. Map (planned, after the technology review)

- **What it does:** Shows a set of parks as markers on an interactive map, with a popup for
  each, and returns the same parks as a plain table for people who can't use the map.
- **Inputs:** a DataFrame from `find_parks` or the data manager, with `latitude` and
  `longitude`.
- **Outputs:** a map object from the library we choose (we are comparing folium, Plotly and
  pydeck on November 17) and a DataFrame.
- **Uses:** the matcher's results.
- **Side effects:** none.

### 4. Web page (planned)

- **What it does:** A simple page, probably made with Streamlit, where people pick filters
  from lists and see the results, a park summary, a comparison and the map.
- **Inputs:** the user's choices from the page.
- **Outputs:** tables, a map and park summaries on the page.
- **Uses:** the data manager once when it starts, and the matcher and map for every search.
- **Side effects:** none. Nothing is saved.

### Helper: data build script (`scripts/build_data.py`)

Only used when we refresh the data. It reads the raw downloads in `data/raw/`, puts the API
files together into `parks.csv`, adds up the monthly visits into `visits.csv`, and writes
both into `src/parkmatch/data/`. The download steps are in `src/parkmatch/data/README.md`.

## Interactions to accomplish a use case

UC1, finding parks that match what someone likes:

1. The web page (for now, a Python session) calls `build_park_table()`.
2. The data manager reads `parks.csv` and `visits.csv`, joins them on `park_code`, and returns the table.
3. The user's choices go to `find_parks(table, states=..., activities=..., amenities=..., max_fee=..., needs_campground=...)`.
4. The matcher filters the table, scores each park, calls `explain_match` for each one, and sorts the result.
5. The web page shows the result. When the user picks a park, it calls `park_summary` (UC2). When they pick a few, it calls `compare_parks` (UC3). The map shows the same result (UC4).

## Preliminary plan

| Priority | Task | When |
|---|---|---|
| 1 | Use cases from the user stories | done |
| 2 | Functional and component specifications | done |
| 3 | Data files, data manager and matcher, with tests | done |
| 4 | Continuous integration (ruff and pytest on GitHub Actions) | done |
| 5 | Technology review: compare map libraries | November 17 |
| 6 | Map component and its tests | after the review |
| 7 | Web page | by December 1 |
| 8 | Clean up the docs and the README | by December 8 |
| 9 | Final presentation | December 16 |
