"""Walk through the main parkmatch functions on the bundled data.

Run it from anywhere once the package is installed::

    python examples/find_parks_example.py

It prints three searches with their match reasons, a side-by-side comparison,
one park summary and one monthly visitation profile. Nothing here touches the
network.
"""

import pandas as pd

import parkmatch

SHOW = ["park_code", "full_name", "match_score", "match_reasons"]


def main() -> None:
    """Run the example searches and print the results."""
    pd.set_option("display.width", 160)
    pd.set_option("display.max_colwidth", 90)

    table = parkmatch.build_park_table()
    print(f"{len(table)} park units in the snapshot\n")

    print("1. Washington units with hiking and camping, entrance fee at most $35")
    hits = parkmatch.find_parks(table, states=["WA"], activities=["Hiking", "Camping"], max_fee=35)
    print(hits[SHOW].head(8).to_string(index=False), "\n")

    print("2. Anywhere: stargazing programs, a Night Sky topic and a campground, quietest first")
    hits = parkmatch.find_parks(
        table, activities=["Stargazing"], topics=["Night Sky"], needs_campground=True
    )
    hits = hits.sort_values(["match_score", "recreation_visits_2025"], ascending=[False, True])
    print(hits[SHOW + ["recreation_visits_2025"]].head(8).to_string(index=False), "\n")

    print("3. California units with an accessible restroom and wheelchair access")
    hits = parkmatch.find_parks(
        table, states=["CA"], amenities=["Restroom - Accessible", "Wheelchair Accessible"]
    )
    print(f"{len(hits)} units; {int((hits['match_score'] == 1).sum())} have both")
    print(hits[SHOW].head(5).to_string(index=False), "\n")

    print("4. Three Washington parks side by side")
    print(parkmatch.compare_parks(table, ["olym", "mora", "noca"]).to_string(), "\n")

    print("5. One park in detail")
    summary = parkmatch.park_summary(table, "olym")
    for key in (
        "full_name",
        "designation",
        "states",
        "fee_text",
        "campground_count",
        "visitor_center_count",
        "recreation_visits",
        "visits_year",
        "busiest_month",
        "quietest_month",
        "url",
    ):
        print(f"  {key}: {summary[key]}")
    print(f"  activities: {', '.join(summary['activities'][:8])}, ...\n")

    print("6. Mount Rainier by month (mean recreation visits, 2021 to 2025)")
    profile = parkmatch.load_monthly_profile()
    mora = profile[profile["park_code"] == "mora"].copy()
    mora["share_of_year"] = (mora["share_of_year"] * 100).round(1)
    print(mora.to_string(index=False))


if __name__ == "__main__":
    main()
