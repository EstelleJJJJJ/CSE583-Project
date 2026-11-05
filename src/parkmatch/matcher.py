"""Filter, score, explain, compare and look up parks (component C4).

All functions take a park table as their first argument. The table normally
comes from :func:`parkmatch.build_park_table`; :func:`parkmatch.load_parks`
also works for the functions that need only the park columns.

Matching on activities, topics and amenities uses the NPS names exactly as
they appear in the data (case does not matter). Use
:func:`parkmatch.list_values` to see the spelling and how common each value is.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import pandas as pd

from parkmatch.data import split_multi

VISITS_PREFIX = "recreation_visits_"
FEE_UNKNOWN_TEXT = "fee information not available"

# Attributes shown by compare_parks, in this order, when the table has them.
COMPARE_ATTRIBUTES = (
    "full_name",
    "designation",
    "states",
    "entrance_fee_min",
    "fee_per_vehicle",
    "fee_per_person",
    "campground_count",
    "rv_campground_count",
    "visitor_center_count",
    "busiest_month",
    "quietest_month",
    "url",
)
# Amenities shown as yes/no rows by compare_parks when the table has an amenities column.
COMPARE_AMENITIES = (
    "Restroom - Accessible",
    "Wheelchair Accessible",
    "Water - Drinking/Potable",
    "Pets Allowed",
    "Public Transit",
)


def _clean_list(values: Iterable[str] | str | None) -> list[str]:
    """Return the requested values as a de-duplicated list of stripped strings."""
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    cleaned: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text.lower() not in {c.lower() for c in cleaned}:
            cleaned.append(text)
    return cleaned


def _park_states(value: object) -> set[str]:
    """Return the set of state codes in a comma-separated ``states`` value."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return set()
    return {part.strip().upper() for part in str(value).split(",") if part.strip()}


def _present(row: pd.Series, column: str, requested: list[str]) -> list[str]:
    """Return the requested values that appear in the row's ``|``-joined column."""
    have = {v.lower() for v in split_multi(row.get(column))}
    return [value for value in requested if value.lower() in have]


def _join_words(items: Sequence[str]) -> str:
    """Join words as ``A``, ``A and B`` or ``A, B and C``."""
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _visits_column(year: int) -> str:
    return f"{VISITS_PREFIX}{year}"


def _is_missing(value: object) -> bool:
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _fee_text(fee: object) -> str:
    """Describe a park's lowest entrance fee in a few words."""
    if _is_missing(fee):
        return FEE_UNKNOWN_TEXT
    fee = float(fee)
    if fee == 0:
        return "free entrance"
    return (
        f"lowest entrance fee ${fee:,.0f}"
        if fee.is_integer()
        else f"lowest entrance fee ${fee:,.2f}"
    )


def _latest_visits(row: pd.Series) -> tuple[int | None, float | None]:
    """Return (year, visits) for the latest ``recreation_visits_<year>`` value present."""
    latest: tuple[int | None, float | None] = (None, None)
    for column in row.index:
        if not str(column).startswith(VISITS_PREFIX):
            continue
        try:
            year = int(str(column)[len(VISITS_PREFIX) :])
        except ValueError:
            continue
        value = row[column]
        if _is_missing(value):
            continue
        if latest[0] is None or year > latest[0]:
            latest = (year, float(value))
    return latest


def explain_match(
    row: pd.Series,
    states: Iterable[str] | None = None,
    activities: Iterable[str] | None = None,
    topics: Iterable[str] | None = None,
    max_fee: float | None = None,
    amenities: Iterable[str] | None = None,
    needs_campground: bool = False,
    max_visits: float | None = None,
    min_visits: float | None = None,
    year: int = 2025,
) -> str:
    """Write one plain sentence saying why a park matched the request.

    The sentence only talks about the criteria that were asked for: which
    requested states, activities, topics and amenities the park has (and
    which requested ones it does not list), the fee when a fee limit was
    given, the campground count when a campground was required, and the
    visit count when a visit range was given.

    Args:
        row: One row of a park table, for example from ``DataFrame.iterrows``.
        states: State codes that were requested.
        activities: Activity names that were requested.
        topics: Topic names that were requested.
        max_fee: The fee limit that was requested, if any.
        amenities: Amenity names that were requested.
        needs_campground: Whether a campground was required.
        max_visits: Upper visit bound that was requested, if any.
        min_visits: Lower visit bound that was requested, if any.
        year: Year of the visit count to mention.

    Returns:
        A sentence such as ``"In WA; offers Hiking and Camping; lowest entrance fee $15."``,
        or ``"No criteria given."`` when nothing was requested.
    """
    parts: list[str] = []

    wanted_states = _clean_list(states)
    if wanted_states:
        here = sorted(_park_states(row.get("states")) & {s.upper() for s in wanted_states})
        parts.append("in " + _join_words(here) if here else "not in the requested states")

    for column, requested, verb in (
        ("activities", _clean_list(activities), "offers"),
        ("topics", _clean_list(topics), "covers"),
        ("amenities", _clean_list(amenities), "has"),
    ):
        if not requested:
            continue
        found = _present(row, column, requested)
        missing = [value for value in requested if value not in found]
        if found:
            parts.append(f"{verb} {_join_words(found)}")
        if missing:
            parts.append(f"does not list {_join_words(missing)}")

    if max_fee is not None:
        parts.append(_fee_text(row.get("entrance_fee_min")))

    if needs_campground:
        count = row.get("campground_count")
        count = 0 if _is_missing(count) else int(count)
        parts.append(f"{count} campground" + ("" if count == 1 else "s"))

    if max_visits is not None or min_visits is not None:
        visits = row.get(_visits_column(year))
        if _is_missing(visits):
            parts.append(f"no visitation record for {year}")
        else:
            parts.append(f"{float(visits):,.0f} recreation visits in {year}")

    if not parts:
        return "No criteria given."
    sentence = "; ".join(parts)
    return sentence[0].upper() + sentence[1:] + "."


def find_parks(
    parks: pd.DataFrame,
    states: Iterable[str] | None = None,
    activities: Iterable[str] | None = None,
    topics: Iterable[str] | None = None,
    max_fee: float | None = None,
    amenities: Iterable[str] | None = None,
    needs_campground: bool = False,
    max_visits: float | None = None,
    min_visits: float | None = None,
    year: int = 2025,
    include_unknown_fee: bool = False,
) -> pd.DataFrame:
    """Return the parks that match a request, ranked by how well they match.

    States, the fee limit, the campground requirement and the visit range are
    hard filters. Activities, topics and amenities are soft criteria: every
    requested name counts as one criterion, ``match_score`` is the share of
    those criteria the park satisfies, and parks with a score of 0 are
    dropped. A park that lists all requested activities therefore ranks above
    one that lists only some of them. Without soft criteria every surviving
    park gets a score of 1.

    A park whose fee is unknown (NaN) is dropped by a fee limit unless
    ``include_unknown_fee`` is True. A park with no visitation record is
    dropped by a visit bound, since we cannot tell how busy it is.

    Args:
        parks: Park table, normally from :func:`parkmatch.build_park_table`.
        states: Two-letter state codes; a park matches when it lies in any of them.
        activities: Activity names, for example ``["Hiking", "Camping"]``.
        topics: Topic names, for example ``["Night Sky", "Geology"]``.
        max_fee: Keep parks whose ``entrance_fee_min`` is at most this many dollars.
        amenities: Amenity names, for example ``["Restroom - Accessible"]``.
        needs_campground: Keep only parks with at least one campground.
        max_visits: Keep parks with at most this many recreation visits in ``year``.
        min_visits: Keep parks with at least this many recreation visits in ``year``.
        year: Year of the ``recreation_visits_<year>`` column used for the visit
            bounds and for sorting.
        include_unknown_fee: Also keep parks with an unknown fee when ``max_fee`` is set.

    Returns:
        A copy of the matching rows with two extra columns, ``match_score``
        (float in [0, 1]) and ``match_reasons`` (str), sorted by score, then
        by visits in ``year`` (most visited first), then by name.

    Raises:
        KeyError: If a visit bound is given and the table has no
            ``recreation_visits_<year>`` column for ``year``.
    """
    wanted_states = _clean_list(states)
    wanted_activities = _clean_list(activities)
    wanted_topics = _clean_list(topics)
    wanted_amenities = _clean_list(amenities)
    visits_column = _visits_column(year)

    keep = pd.Series(True, index=parks.index)
    if wanted_states:
        wanted = {s.upper() for s in wanted_states}
        keep &= parks["states"].map(lambda value: bool(_park_states(value) & wanted))
    if max_fee is not None:
        fee = parks["entrance_fee_min"]
        fee_ok = fee <= max_fee
        if include_unknown_fee:
            fee_ok = fee_ok | fee.isna()
        keep &= fee_ok.fillna(False).astype(bool)
    if needs_campground:
        keep &= parks["campground_count"].fillna(0) > 0
    if max_visits is not None or min_visits is not None:
        if visits_column not in parks.columns:
            raise KeyError(
                f"The table has no '{visits_column}' column. build_park_table() adds one "
                "per year in parkmatch.data.VISIT_YEARS."
            )
        visits = parks[visits_column]
        if min_visits is not None:
            keep &= (visits >= min_visits).fillna(False).astype(bool)
        if max_visits is not None:
            keep &= (visits <= max_visits).fillna(False).astype(bool)

    result = parks.loc[keep].copy()

    requested = [
        ("activities", wanted_activities),
        ("topics", wanted_topics),
        ("amenities", wanted_amenities),
    ]
    n_criteria = sum(len(values) for _, values in requested)
    if n_criteria:
        scores = []
        for _, row in result.iterrows():
            hits = sum(len(_present(row, column, values)) for column, values in requested)
            scores.append(hits / n_criteria)
        result["match_score"] = scores
        result = result.loc[result["match_score"] > 0].copy()
    else:
        result["match_score"] = 1.0

    result["match_reasons"] = [
        explain_match(
            row,
            states=wanted_states,
            activities=wanted_activities,
            topics=wanted_topics,
            max_fee=max_fee,
            amenities=wanted_amenities,
            needs_campground=needs_campground,
            max_visits=max_visits,
            min_visits=min_visits,
            year=year,
        )
        for _, row in result.iterrows()
    ]

    order = ["match_score"]
    ascending = [False]
    if visits_column in result.columns:
        order.append(visits_column)
        ascending.append(False)
    if "full_name" in result.columns:
        order.append("full_name")
        ascending.append(True)
    result = result.sort_values(order, ascending=ascending, na_position="last", kind="mergesort")
    return result.reset_index(drop=True)


def _find_row(parks: pd.DataFrame, code: str) -> pd.Series:
    """Return the row for a park code, ignoring case and surrounding spaces."""
    wanted = str(code).strip().lower()
    matches = parks.loc[parks["park_code"].str.lower() == wanted]
    if matches.empty:
        raise ValueError(f"Unknown park code '{code}'. Try parkmatch.search_parks() to find it.")
    return matches.iloc[0]


def compare_parks(parks: pd.DataFrame, codes: Sequence[str]) -> pd.DataFrame:
    """Put two or more parks side by side, attributes as rows and parks as columns.

    Args:
        parks: Park table, normally from :func:`parkmatch.build_park_table`.
        codes: Two or more park codes, for example ``["olym", "mora", "noca"]``.

    Returns:
        DataFrame whose columns are the park codes (in the order given) and
        whose index holds the attribute names: name, designation, states,
        fees, campground and visitor center counts, every
        ``recreation_visits_<year>`` column present, busiest and quietest
        month, the nps.gov link, the number of listed activities, and a
        yes/no row for each amenity in ``COMPARE_AMENITIES``. Attributes
        missing from ``parks`` are skipped.

    Raises:
        ValueError: If fewer than two codes are given or a code is unknown.
    """
    codes = [str(code).strip().lower() for code in codes]
    if len(codes) < 2:
        raise ValueError("compare_parks needs at least two park codes.")
    rows = [_find_row(parks, code) for code in codes]

    attributes = [name for name in COMPARE_ATTRIBUTES if name in parks.columns]
    visit_columns = sorted(c for c in parks.columns if str(c).startswith(VISITS_PREFIX))
    insert_at = (
        attributes.index("busiest_month") if "busiest_month" in attributes else len(attributes)
    )
    attributes[insert_at:insert_at] = visit_columns

    columns = {code: row[attributes].to_dict() for code, row in zip(codes, rows)}
    for code, row in zip(codes, rows):
        if "activities" in parks.columns:
            columns[code]["activity_count"] = len(split_multi(row.get("activities")))
        if "amenities" in parks.columns:
            have = {a.lower() for a in split_multi(row.get("amenities"))}
            for amenity in COMPARE_AMENITIES:
                columns[code][f"amenity: {amenity}"] = "yes" if amenity.lower() in have else "no"
    comparison = pd.DataFrame(columns)
    comparison.index.name = "attribute"
    return comparison


def search_parks(parks: pd.DataFrame, text: str) -> pd.DataFrame:
    """Find parks whose name or park code contains a piece of text.

    The match is case-insensitive and looks at ``full_name``, ``name`` and
    ``park_code``. Blank text gives an empty result.

    Args:
        parks: Park table with at least a ``full_name`` or ``name`` column.
        text: Part of a park name or a park code, for example ``"rainier"``.

    Returns:
        The matching rows, sorted by full name, with a fresh index.
    """
    needle = str(text or "").strip().lower()
    columns = [c for c in ("full_name", "name", "park_code") if c in parks.columns]
    if not needle or not columns:
        return parks.iloc[0:0].copy()
    haystack = parks[columns[0]].fillna("").astype(str)
    for column in columns[1:]:
        haystack = haystack + " " + parks[column].fillna("").astype(str)
    hits = parks.loc[haystack.str.lower().str.contains(needle, regex=False)].copy()
    sort_by = "full_name" if "full_name" in hits.columns else columns[0]
    return hits.sort_values(sort_by).reset_index(drop=True)


def park_summary(parks: pd.DataFrame, code: str) -> dict:
    """Collect what we know about one park in a plain dict.

    Values that are unknown in the table (NaN) come back as None, and the fee
    line says ``"fee information not available"`` when the API lists no
    entrance fee rows for the park.

    Args:
        parks: Park table, normally from :func:`parkmatch.build_park_table`.
        code: Park code such as ``"olym"`` (case does not matter).

    Returns:
        Dict with the keys park_code, full_name, designation, states (list),
        description, url, image_url, image_alt, activities (list), topics
        (list), entrance_fee_min, fee_per_vehicle, fee_per_person, fee_text,
        campground_count, visitor_center_count, recreation_visits,
        visits_year, busiest_month and quietest_month. Count and visitation
        keys are None when the table does not have the matching column.

    Raises:
        ValueError: If the code is not in the table.
    """
    row = _find_row(parks, code)

    def value(column: str) -> object:
        item = row.get(column)
        if item is None or _is_missing(item):
            return None
        if hasattr(item, "item"):
            item = item.item()
        return item

    def count(column: str) -> int | None:
        item = value(column)
        return None if item is None else int(item)

    visits_year, visits = _latest_visits(row)
    return {
        "park_code": value("park_code"),
        "full_name": value("full_name"),
        "designation": value("designation"),
        "states": sorted(_park_states(row.get("states"))),
        "description": value("description"),
        "url": value("url"),
        "image_url": value("image_url"),
        "image_alt": value("image_alt"),
        "activities": split_multi(row.get("activities")),
        "topics": split_multi(row.get("topics")),
        "entrance_fee_min": value("entrance_fee_min"),
        "fee_per_vehicle": value("fee_per_vehicle"),
        "fee_per_person": value("fee_per_person"),
        "fee_text": _fee_text(row.get("entrance_fee_min")),
        "campground_count": count("campground_count"),
        "visitor_center_count": count("visitor_center_count"),
        "recreation_visits": None if visits is None else int(visits),
        "visits_year": visits_year,
        "busiest_month": value("busiest_month"),
        "quietest_month": value("quietest_month"),
    }
