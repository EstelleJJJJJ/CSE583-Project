# Data snapshot

Built on 2026-11-05 with `python -m parkmatch.snapshot`. Only the files below
ship with the package; the raw downloads are not committed.

## Sources

- NPS API (https://developer.nps.gov/, a free key from
  https://www.nps.gov/subjects/developer/get-started.htm): endpoints `parks`,
  `campgrounds`, `visitorcenters`, `amenities/parksplaces` and `feespasses`,
  fetched with `limit=1000`.
- NPS Visitor Use Statistics Data Package, 2025, `Main_Data.csv`, NPS DataStore
  reference 2317666, DOI 10.57830/2317666, public domain:
  https://irma.nps.gov/DataStore/DownloadFile/756959?Reference=2317666
  Statistics used: TRV (recreation visits) and TOS (total overnight stays).

## Files

- `parks.csv`: 475 rows
- `campgrounds.csv`: 665 rows
- `visitor_centers.csv`: 714 rows
- `amenities.csv`: 9,359 rows
- `visitation_annual.csv`: 16,146 rows
- `visitation_monthly.csv`: 4,752 rows

`visitation_monthly.csv` averages each month over 2021 to 2025.

## Unit code aliases

IRMA unit codes are matched to API park codes by lowercasing. These codes differ
and are mapped by hand; units that share a park code are summed:

- `SEQU` -> `seki`
- `KICA` -> `seki`
- `ROLA` -> `noca`
- `LACH` -> `noca`
- `JEFM` -> `thje`
- `NCPE` -> `nace`
- `OBRI` -> `obed`
- `PERL` -> `valr`
- `PRPA` -> `whho`

IRMA codes with no API counterpart are kept under their lowercased code and
do not join to any park. API units with no visitation series keep NaN visits.

## Rebuild

```
export NPS_API_KEY=...
python -m parkmatch.snapshot --download --download-visitation \
    --raw-dir data/raw --visitation data/raw/Main_Data.csv
```
