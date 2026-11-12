# Data files

These two files ship with the package, so nobody needs an API key to use it. They were built
on 2026-11-05.

| File | Source | Rows |
|---|---|---|
| `parks.csv` | NPS API: `parks`, `campgrounds`, `amenities/parksplaces`, `feespasses` | 475 parks |
| `visits.csv` | NPS Visitor Use Statistics, recreation visits (`TRV`) added up by year, 2016 to 2025 | 3,795 park-years |

The visitor statistics come from the "NPS Visitor Use Statistics Data Package, 2025"
(NPS DataStore, doi:10.57830/2317666). Nine of its park codes are different from the API codes
and are matched by hand in `scripts/build_data.py`.

## How to rebuild them

Get a free API key at https://www.nps.gov/subjects/developer/get-started.htm, then from the
repository root:

```
mkdir -p data/raw
for endpoint in parks campgrounds amenities/parksplaces feespasses; do
  curl "https://developer.nps.gov/api/v1/$endpoint?limit=1000&api_key=YOUR_KEY" \
       -o "data/raw/$(echo $endpoint | tr / _).json"
done
curl -L "https://irma.nps.gov/DataStore/DownloadFile/756959?Reference=2317666" -o data/raw/Main_Data.csv
python scripts/build_data.py
```

`data/raw/` is in `.gitignore`, so the raw downloads (about 90 MB) stay out of the repository.
