# ParkMatch

ParkMatch helps people choose which U.S. National Park System site to visit. You say what
you care about (a state, activities, themes such as geology or Civil War history, a
maximum entrance fee, facilities such as accessible restrooms, whether you need a
campground, how busy a park is) and it returns the matching sites with a plain sentence
saying why each one is there. It also looks up one park, compares two or three side by
side, and shows how visits spread over the year. The data comes from the National Park
Service: the NPS API for park facts and the NPS Visitor Use Statistics for monthly visits
since 1979.

This is our group project for CSE 583, Software Development for Data Scientists
(University of Washington, Autumn 2026). ParkMatch is a working name; the repository may be
renamed once the team settles on one.

## Who it is for

People planning a trip who know what they like and not much about the 475 units of the
park system: first-time visitors, families, campers, photographers, history and geology
fans, people with accessibility needs. They use travel websites and map apps and do not
write Python. For now the package is for anyone who can run `pip install` and a few lines
of pandas; a web page on top of it is planned for later in the quarter.

## What is here and what is coming

Done so far (the `parkmatch` package):

- `nps_api`: downloads whole NPS API tables with a key.
- `snapshot`: turns the raw downloads and the visitor statistics CSV into six small tables
  that ship inside the package.
- `data`: loads those tables and joins them into one row per park.
- `matcher`: `find_parks`, `explain_match`, `compare_parks`, `search_parks` and
  `park_summary`.
- Tests for all of it, an example script, and continuous integration (ruff and pytest).

Planned: an interactive map with a plain-table alternative (our technology review on
November 17 picks the library), a Streamlit app, and monthly temperatures from Open-Meteo.
The design documents are in [design/](design/) (user stories and use cases) and
[docs/](docs/) (functional and component specifications).

## Data

Two sources, both public:

- The [NPS API](https://www.nps.gov/subjects/developer/api-documentation.htm): the
  `parks`, `campgrounds`, `visitorcenters`, `amenities/parksplaces` and `feespasses`
  endpoints. A free key comes from
  [nps.gov/subjects/developer/get-started.htm](https://www.nps.gov/subjects/developer/get-started.htm).
- The NPS Visitor Use Statistics Data Package, 2025 (`Main_Data.csv`, NPS DataStore
  reference 2317666, [doi:10.57830/2317666](https://doi.org/10.57830/2317666)): recreation
  visits per unit and month, 1979 to 2025.

A snapshot downloaded on 2026-11-05 ships inside the package (about 1.7 MB), so the
examples and tests run offline and nobody needs a key to try it. Where the data is silent
the tables say so: a park whose fee is unknown has `NaN`, not 0, and a unit with no
visitation record has `NaN` visits. [src/parkmatch/data/SNAPSHOT.md](src/parkmatch/data/SNAPSHOT.md)
lists the sources, row counts and the unit code aliases.

To rebuild the snapshot with your own key:

```
export NPS_API_KEY=your-key
python -m parkmatch.snapshot --download --download-visitation \
    --raw-dir data/raw --visitation data/raw/Main_Data.csv
```

## Install

Python 3.11 or newer.

```
git clone https://github.com/EstelleJJJJJ/CSE583-Project.git
cd CSE583-Project
pip install -e ".[dev]"
pytest
```

## Quick example

```python
import parkmatch

table = parkmatch.build_park_table()
hits = parkmatch.find_parks(table, states=["WA"], activities=["Hiking", "Camping"], max_fee=35)
print(
    hits[["park_code", "full_name", "match_score", "match_reasons"]].head(3).to_string(index=False)
)

summary = parkmatch.park_summary(table, "olym")
print(
    summary["recreation_visits"],
    summary["visits_year"],
    summary["busiest_month"],
    summary["fee_text"],
)
```

Output:

```
park_code                    full_name  match_score                                              match_reasons
     olym        Olympic National Park          1.0 In WA; offers Hiking and Camping; lowest entrance fee $15.
     mora  Mount Rainier National Park          1.0 In WA; offers Hiking and Camping; lowest entrance fee $15.
     noca North Cascades National Park          1.0           In WA; offers Hiking and Camping; free entrance.
3584187 2025 August lowest entrance fee $15
```

`python examples/find_parks_example.py` runs a longer tour: three searches, a comparison
of Olympic, Mount Rainier and North Cascades, one park summary and a monthly profile.
Activity, topic and amenity names are the NPS's own; `parkmatch.list_values(table, "activities")`
shows the spelling and how common each one is.

## Project layout

```
design/          user stories and use cases (from the November 3 lecture)
docs/            functional and component specifications
src/parkmatch/   the package, with the data snapshot in src/parkmatch/data/
tests/           pytest tests (no network)
examples/        find_parks_example.py
.github/workflows/ci.yml   ruff and pytest on Python 3.11 and 3.13
```

## Contributors

| Name | GitHub | So far |
|---|---|---|
| Yucheng Jiang | @EstelleJJJJJ | repository setup, user story template |
| Peiyan Xie | @peiyax | the 30 user stories |
| Zitong Ren | @ari11a | package folder setup |
| Yuxia Liang | @zl1212-ship-it | use cases, specifications, data layer, matcher, tests, CI |

We will keep this table current as tasks are assigned.

## License

MIT, see [LICENSE](LICENSE).
