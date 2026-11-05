"""Load the bundled snapshot tables and join them into one park table (component C3).

The package ships six small CSV files in ``parkmatch/data`` that
:mod:`parkmatch.snapshot` builds from the NPS API and the NPS Visitor Use
Statistics. The ``load_*`` functions read them with pandas.
:func:`build_park_table` joins them into one row per park unit, which is the
table the matcher functions expect.

Multi-valued fields (activities, topics, amenities) are stored as one string
joined with ``|``; :func:`split_multi` turns such a string back into a list.
Unknown values stay NaN: a park with no fee rows in the API has
``entrance_fee_min`` NaN, not 0, and a unit with no visitation record has NaN
visits.
"""

from __future__ import annotations

import calendar
from collections.abc import Iterable
from importlib.resources import as_file, files

import pandas as pd

MULTI_SEP = "|"
# Years that get a recreation_visits_<year> column in build_park_table().
VISIT_YEARS = (2021, 2022, 2023, 2024, 2025)


def _read_table(name: str, **kwargs) -> pd.DataFrame:
    """Read one bundled CSV file by name."""
    resource = files("parkmatch") / "data" / name
    with as_file(resource) as path:
        return pd.read_csv(path, **kwargs)


def load_parks() -> pd.DataFrame:
    """Load the park table, one row per NPS unit.

    Returns:
        DataFrame with columns park_code, full_name, name, designation, states,
        latitude, longitude, description, url, activities, topics,
        entrance_fee_min, fee_per_vehicle, fee_per_person, fee_free, image_url,
        image_alt and weather_info. ``fee_free`` is True, False or NaN;
        ``entrance_fee_min`` is NaN only when the fee is unknown.
    """
    return _read_table("parks.csv", dtype={"park_code": str, "states": str})


def load_campgrounds() -> pd.DataFrame:
    """Load the campground table, one row per campground.

    Returns:
        DataFrame with columns park_code, name, latitude, longitude, total_sites,
        reservable_sites, rv_allowed, potable_water, toilets, dump_station,
        wheelchair_access and url.
    """
    return _read_table("campgrounds.csv", dtype={"park_code": str})


def load_visitor_centers() -> pd.DataFrame:
    """Load the visitor center table, one row per visitor center.

    Returns:
        DataFrame with columns park_code, name, latitude, longitude and url.
    """
    return _read_table("visitor_centers.csv", dtype={"park_code": str})


def load_amenities() -> pd.DataFrame:
    """Load the park-amenity links as a long table.

    Returns:
        DataFrame with columns amenity and park_code, one row per link.
    """
    return _read_table("amenities.csv", dtype={"park_code": str, "amenity": str})


def load_visitation() -> pd.DataFrame:
    """Load annual visitation, one row per reporting unit and year.

    ``park_code`` is the unit code after alias mapping (for example SEQU and
    KICA both map to ``seki``), so a park can have more than one row per year.
    Sum over ``park_code`` and ``year`` to get park totals.

    Returns:
        DataFrame with columns park_code, unit_code, year, recreation_visits
        and overnight_stays.
    """
    return _read_table("visitation_annual.csv", dtype={"park_code": str, "unit_code": str})


def load_monthly_profile() -> pd.DataFrame:
    """Load the 12-month visitation profile per park.

    Returns:
        DataFrame with columns park_code, month (1-12), mean_recreation_visits
        (mean over the snapshot's profile years) and share_of_year (that month's
        mean divided by the yearly total of the means).
    """
    return _read_table("visitation_monthly.csv", dtype={"park_code": str})


def split_multi(value: object) -> list[str]:
    """Split a ``|``-joined string into a list of values.

    Args:
        value: The joined string. NaN, None and empty strings give an empty list.

    Returns:
        The non-empty parts, stripped of surrounding spaces, in their original order.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    text = str(value)
    return [part.strip() for part in text.split(MULTI_SEP) if part.strip()]


def list_values(parks: pd.DataFrame, column: str) -> pd.Series:
    """Count how many parks list each value of a ``|``-joined column.

    Useful for seeing the exact spelling of activities, topics or amenities
    before passing them to :func:`parkmatch.find_parks`.

    Args:
        parks: A park table with the requested column.
        column: Name of a ``|``-joined column such as ``activities``.

    Returns:
        Series indexed by value, sorted from most to least common.
    """
    exploded = parks[column].map(split_multi).explode().dropna()
    return exploded.value_counts()


def month_name(month: object) -> object:
    """Return the English month name for a month number, or NaN when unknown.

    Args:
        month: Month number from 1 to 12, as int or float. NaN gives NaN.

    Returns:
        A month name such as ``"July"``, or NaN.
    """
    if month is None or pd.isna(month):
        return float("nan")
    return calendar.month_name[int(month)]


def build_park_table(visit_years: Iterable[int] = VISIT_YEARS) -> pd.DataFrame:
    """Join the bundled tables into one row per park unit.

    The result holds every column of :func:`load_parks` plus:

    * ``campground_count``, ``rv_campground_count``, ``has_campground`` and
      ``visitor_center_count`` from the campground and visitor center tables
      (0 and False when none are listed);
    * ``amenities``, the park's amenity names joined with ``|`` (NaN when the
      API lists none);
    * ``recreation_visits_<year>`` for each year in ``visit_years``, summed
      over the reporting units mapped to the park (NaN when no record exists);
    * ``busiest_month`` and ``quietest_month`` as month names taken from the
      monthly profile (NaN when the park has no profile).

    Args:
        visit_years: Years that get a ``recreation_visits_<year>`` column.

    Returns:
        DataFrame with one row per park, in the order of the park table.
    """
    table = load_parks().copy()
    campgrounds = load_campgrounds()
    centers = load_visitor_centers()
    amenities = load_amenities()
    visitation = load_visitation()
    profile = load_monthly_profile()

    codes = table["park_code"]
    campground_counts = campgrounds.groupby("park_code").size()
    table["campground_count"] = codes.map(campground_counts).fillna(0).astype(int)
    rv_counts = campgrounds.loc[campgrounds["rv_allowed"].astype(bool)].groupby("park_code").size()
    table["rv_campground_count"] = codes.map(rv_counts).fillna(0).astype(int)
    table["has_campground"] = table["campground_count"] > 0
    center_counts = centers.groupby("park_code").size()
    table["visitor_center_count"] = codes.map(center_counts).fillna(0).astype(int)

    joined = amenities.groupby("park_code")["amenity"].agg(lambda s: MULTI_SEP.join(sorted(set(s))))
    table["amenities"] = codes.map(joined)

    annual = visitation.groupby(["park_code", "year"])["recreation_visits"].sum().unstack("year")
    for year in visit_years:
        column = f"recreation_visits_{year}"
        if year in annual.columns:
            table[column] = codes.map(annual[year]).astype(float)
        else:
            table[column] = float("nan")

    # Parks whose profile years had zero visits have NaN shares and no busiest month.
    ranked = profile.dropna(subset=["share_of_year"]).sort_values(
        ["park_code", "mean_recreation_visits", "month"]
    )
    busiest = ranked.groupby("park_code")["month"].last()
    quietest = ranked.groupby("park_code")["month"].first()
    table["busiest_month"] = codes.map(busiest).map(month_name)
    table["quietest_month"] = codes.map(quietest).map(month_name)
    return table
