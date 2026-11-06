"""Build the two data files that ship with the parkmatch package.

This script is only for refreshing the data. It reads files downloaded by hand
into data/raw/ (see src/parkmatch/data/README.md for the download commands) and
writes two CSV files into src/parkmatch/data/:

- parks.csv: one row per park, from the NPS API.
- visits.csv: recreation visits per park and year, from the NPS Visitor Use
  Statistics.

Run it from the repository root::

    python scripts/build_data.py
"""

import json
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("src/parkmatch/data")
FIRST_YEAR = 2016

# Visitor statistics codes that are different from the API park codes.
# Units that point to the same park are added together.
ALIASES = {
    "SEQU": "seki",  # Sequoia, listed with Kings Canyon as one park in the API
    "KICA": "seki",  # Kings Canyon
    "ROLA": "noca",  # Ross Lake NRA, part of the North Cascades page in the API
    "LACH": "noca",  # Lake Chelan NRA, same
    "JEFM": "thje",  # Thomas Jefferson Memorial
    "NCPE": "nace",  # National Capital Parks-East
    "OBRI": "obed",  # Obed Wild and Scenic River
    "PERL": "valr",  # Pearl Harbor National Memorial
    "PRPA": "whho",  # President's Park
}

# Fee rows for a regular visitor. Group, school and tour bus rates are left out.
FEE_TITLES = ("Entrance - Private Vehicle", "Entrance - Per Person", "Entrance - Motorcycle")


def read_records(name: str) -> list:
    """Return the list of records in one raw NPS API file."""
    with open(RAW / name, encoding="utf-8") as file:
        return json.load(file)["data"]


def entrance_fee(park: dict, fee_free: bool) -> float:
    """Return the lowest regular entrance fee, 0 for a fee-free park, or NaN if unknown."""
    costs = [
        float(fee["cost"])
        for fee in park.get("entranceFees", [])
        if fee.get("title") in FEE_TITLES and fee.get("cost") and float(fee["cost"]) > 0
    ]
    if costs:
        return min(costs)
    return 0.0 if fee_free else float("nan")


def build_parks() -> pd.DataFrame:
    """Put the API files together into one row per park."""
    fee_free = {r["parkCode"]: r["isFeeFreePark"] is True for r in read_records("feespasses.json")}
    campgrounds = pd.Series([c["parkCode"] for c in read_records("campgrounds.json")])
    campground_counts = campgrounds.value_counts()

    amenities = {}
    for item in read_records("amenities_parksplaces.json"):
        for amenity in item:  # each item is a list with one amenity in it
            for park in amenity["parks"]:
                amenities.setdefault(park["parkCode"], set()).add(amenity["name"])

    rows = []
    for park in read_records("parks.json"):
        code = park["parkCode"]
        images = park.get("images") or [{}]
        rows.append(
            {
                "park_code": code,
                "full_name": park["fullName"],
                "designation": park["designation"],
                "states": park["states"],
                "latitude": float(park["latitude"]),
                "longitude": float(park["longitude"]),
                "url": park["url"],
                "description": " ".join(park["description"].split()),
                "image_url": images[0].get("url", ""),
                "activities": "|".join(dict.fromkeys(a["name"] for a in park["activities"])),
                "topics": "|".join(dict.fromkeys(t["name"] for t in park["topics"])),
                "amenities": "|".join(sorted(amenities.get(code, []))),
                "campgrounds": int(campground_counts.get(code, 0)),
                "entrance_fee": entrance_fee(park, fee_free.get(code, False)),
            }
        )
    return pd.DataFrame(rows).sort_values("park_code")


def build_visits() -> pd.DataFrame:
    """Add up monthly recreation visits into one row per park and year."""
    stats = pd.read_csv(RAW / "Main_Data.csv")
    visits = stats[(stats["Statistic"] == "TRV") & (stats["Year"] >= FIRST_YEAR)].copy()
    visits["park_code"] = visits["UnitCode"].map(lambda code: ALIASES.get(code, code.lower()))
    yearly = visits.groupby(["park_code", "Year"], as_index=False)["Value"].sum()
    return yearly.rename(columns={"Year": "year", "Value": "visits"})


def main() -> None:
    """Build both files and print how many rows each one has."""
    parks = build_parks()
    visits = build_visits()
    visits = visits[visits["park_code"].isin(parks["park_code"])]
    OUT.mkdir(parents=True, exist_ok=True)
    parks.to_csv(OUT / "parks.csv", index=False)
    visits.to_csv(OUT / "visits.csv", index=False)
    print(f"parks.csv: {len(parks)} rows, visits.csv: {len(visits)} rows")


if __name__ == "__main__":
    main()
