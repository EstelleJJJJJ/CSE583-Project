"""ParkMatch: find, compare and look up U.S. National Park System sites.

The package bundles a snapshot of National Park Service data (park facts from
the NPS API and visitation from the NPS Visitor Use Statistics) and offers a
few pandas-based functions on top of it::

    import parkmatch

    table = parkmatch.build_park_table()
    hits = parkmatch.find_parks(table, states=["WA"], activities=["Hiking", "Camping"], max_fee=35)
    hits[["park_code", "full_name", "match_score", "match_reasons"]]
    parkmatch.compare_parks(table, ["olym", "mora", "noca"])
    parkmatch.park_summary(table, "olym")
    parkmatch.search_parks(table, "rainier")

See ``parkmatch/data/SNAPSHOT.md`` for where the data came from and how to
rebuild it.
"""

from parkmatch.data import (
    build_park_table,
    list_values,
    load_amenities,
    load_campgrounds,
    load_monthly_profile,
    load_parks,
    load_visitation,
    load_visitor_centers,
    split_multi,
)
from parkmatch.matcher import (
    compare_parks,
    explain_match,
    find_parks,
    park_summary,
    search_parks,
)
from parkmatch.nps_api import RateLimitError, download_raw, fetch_all
from parkmatch.snapshot import build_snapshot

__version__ = "0.1.0"

__all__ = [
    "RateLimitError",
    "__version__",
    "build_park_table",
    "build_snapshot",
    "compare_parks",
    "download_raw",
    "explain_match",
    "fetch_all",
    "find_parks",
    "list_values",
    "load_amenities",
    "load_campgrounds",
    "load_monthly_profile",
    "load_parks",
    "load_visitation",
    "load_visitor_centers",
    "park_summary",
    "search_parks",
    "split_multi",
]
