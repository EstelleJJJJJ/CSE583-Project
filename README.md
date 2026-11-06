# ParkMatch

ParkMatch helps people pick which U.S. National Park System sites to visit. You choose what
matters to you (states, activities, facilities, a highest entrance fee, whether you need a
campground) and it lists the parks that fit, with a short reason for each one. You can also
look up one park and compare a few side by side.

This is our group project for CSE 583, Software Development for Data Scientists (University of
Washington, Autumn 2026). ParkMatch is a working name for now.

## Who it is for

People planning a trip who don't know the park system well, such as first-time visitors,
families, campers and people who need accessible facilities. They use websites and map apps,
not Python. For now the package is used from Python; a map and a web page are planned.

## Data

We join two public sources from the National Park Service on the park code:

- The [NPS API](https://www.nps.gov/subjects/developer/api-documentation.htm): park details,
  activities, facilities, campgrounds and fees, one row per park.
- The NPS Visitor Use Statistics ([doi:10.57830/2317666](https://doi.org/10.57830/2317666)):
  recreation visits per park and month, which we add up by year.

A copy of both, downloaded on 2026-11-05, ships with the package, so you don't need an API key.
[src/parkmatch/data/README.md](src/parkmatch/data/README.md) explains how to refresh it.

## Install

Python 3.11 or newer.

```
git clone https://github.com/EstelleJJJJJ/CSE583-Project.git
cd CSE583-Project
pip install -e ".[dev]"
pytest
```

## Example

```python
import parkmatch

table = parkmatch.build_park_table()
hits = parkmatch.find_parks(table, states=["WA"], activities=["Hiking", "Camping"], max_fee=35)
print(hits[["full_name", "match_score", "match_reasons"]].head(3).to_string(index=False))
```

```
                   full_name  match_score                             match_reasons
       Olympic National Park          1.0 Has Hiking and Camping; entrance fee $15.
 Mount Rainier National Park          1.0 Has Hiking and Camping; entrance fee $15.
North Cascades National Park          1.0    Has Hiking and Camping; free entrance.
```

There's a longer example in [examples/find_parks_example.py](examples/find_parks_example.py).

## What's in the repository

```
design/          user stories and use cases
docs/            functional and component specifications
src/parkmatch/   the package: data.py (loads and joins the data), matcher.py (search and compare)
tests/           tests, run with pytest
examples/        an example script
scripts/         build_data.py, only used to refresh the data
```

GitHub Actions runs `ruff check .` and `pytest` on every push and pull request.

## Contributors

| Name | GitHub | So far |
|---|---|---|
| Yucheng Jiang | @EstelleJJJJJ | repository setup, user story template |
| Peiyan Xie | @peiyax | the 30 user stories |
| Zitong Ren | @ari11a | package folder setup |
| Yuxia Liang | @zl1212-ship-it | use cases, specifications, data and matcher code, tests, CI |

We'll update this table as we split up the rest of the work.

## License

MIT, see [LICENSE](LICENSE).
