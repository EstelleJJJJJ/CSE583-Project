"""ParkMatch: find U.S. National Park System sites that fit what you like.

Example::

    import parkmatch

    table = parkmatch.build_park_table()
    parkmatch.find_parks(table, states=["WA"], activities=["Hiking", "Camping"], max_fee=35)
"""

from parkmatch.data import build_park_table, load_parks, load_visits, split_list
from parkmatch.matcher import compare_parks, explain_match, find_parks, park_summary, search_parks

__version__ = "0.1.0"

__all__ = [
    "build_park_table",
    "compare_parks",
    "explain_match",
    "find_parks",
    "load_parks",
    "load_visits",
    "park_summary",
    "search_parks",
    "split_list",
]
