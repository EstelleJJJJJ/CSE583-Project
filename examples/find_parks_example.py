"""A short tour of parkmatch using the data that ships with the package.

Run it from the repository root after installing the package::

    python examples/find_parks_example.py
"""

import pandas as pd

import parkmatch

COLUMNS = ["park_code", "full_name", "match_score", "match_reasons"]


def main() -> None:
    """Run a few searches and print the results."""
    pd.set_option("display.width", 160)
    pd.set_option("display.max_colwidth", 80)
    table = parkmatch.build_park_table(year=2025)

    print("Washington parks with hiking and camping, entrance fee $35 or less:")
    hits = parkmatch.find_parks(
        table, states=["WA"], activities=["Hiking", "Camping"], max_fee=35, needs_campground=True
    )
    print(hits[COLUMNS].head(5).to_string(index=False), "\n")

    print("California parks with an accessible restroom and wheelchair access:")
    hits = parkmatch.find_parks(
        table, states=["CA"], amenities=["Restroom - Accessible", "Wheelchair Accessible"]
    )
    print(hits[COLUMNS].head(5).to_string(index=False), "\n")

    print("Three parks side by side:")
    print(parkmatch.compare_parks(table, ["olym", "mora", "noca"]).to_string(), "\n")

    print("Searching for 'rainier' and looking up the result:")
    code = parkmatch.search_parks(table, "rainier")["park_code"].iloc[0]
    summary = parkmatch.park_summary(table, code)
    for key in ["name", "states", "fee", "campgrounds", "visits", "url"]:
        print(f"  {key}: {summary[key]}")


if __name__ == "__main__":
    main()
