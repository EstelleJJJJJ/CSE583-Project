"""Find, compare and look up parks.

All functions take the table from park_matching.build_park_table(). Activity and
amenity names must be spelled the way the NPS data spells them, for example
"Hiking" or "Restroom - Accessible".
"""

import pandas as pd

from park_matching.data import split_list

COMPARE_COLUMNS = [
    "full_name",
    "designation",
    "states",
    "entrance_fee",
    "campgrounds",
    "visits",
    "url",
]


def fee_text(fee: float) -> str:
    """Describe an entrance fee in a few words.

    Args:
        fee: Fee in dollars, 0 for free, NaN for unknown.

    Returns:
        A short phrase such as "entrance fee $15".
    """
    if pd.isna(fee):
        return "entrance fee unknown"
    if fee == 0:
        return "free entrance"
    return f"entrance fee ${fee:g}"


def _join(words: list[str]) -> str:
    """Join words as "A", "A and B" or "A, B and C"."""
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]


def _features(row: pd.Series) -> set[str]:
    """Return the activities and amenities one park has."""
    return set(split_list(row["activities"])) | set(split_list(row["amenities"]))


def explain_match(
    row, activities=None, amenities=None, max_fee=None, needs_campground=False
) -> str:
    """Write one sentence that says why a park matched.

    Args:
        row: One row of the park table.
        activities: Activities the user asked for.
        amenities: Amenities the user asked for.
        max_fee: The fee limit, if the user set one.
        needs_campground: Whether the user asked for a campground.

    Returns:
        A sentence such as "Has Hiking and Camping; entrance fee $15."
    """
    wanted = list(activities or []) + list(amenities or [])
    have = _features(row)
    found = [name for name in wanted if name in have]
    missing = [name for name in wanted if name not in have]

    parts = []
    if found:
        parts.append("has " + _join(found))
    if missing:
        parts.append("missing " + _join(missing))
    if max_fee is not None:
        parts.append(fee_text(row["entrance_fee"]))
    if needs_campground:
        count = int(row["campgrounds"])
        parts.append(f"{count} campground" + ("" if count == 1 else "s"))
    if not parts:
        return "Matches the filters."
    sentence = "; ".join(parts)
    return sentence[0].upper() + sentence[1:] + "."


def find_parks(
    table, states=None, activities=None, amenities=None, max_fee=None, needs_campground=False
) -> pd.DataFrame:
    """Return the parks that fit what the user asked for, best matches first.

    States, max_fee and needs_campground are filters: a park either passes or
    not. Activities and amenities are scored: match_score is the share of them
    the park has, and parks with none of them are left out. Parks with the
    same score are sorted by visits, most visited first.

    Args:
        table: The park table from build_park_table().
        states: Two-letter state codes, for example ["WA", "OR"].
        activities: Activity names, for example ["Hiking", "Camping"].
        amenities: Amenity names, for example ["Restroom - Accessible"].
        max_fee: Highest entrance fee in dollars. Parks with an unknown fee are left out.
        needs_campground: Keep only parks with at least one campground.

    Returns:
        The matching rows with two extra columns, match_score and match_reasons.
    """
    keep = pd.Series(True, index=table.index)
    if states:
        wanted_states = {state.upper() for state in states}
        keep &= table["states"].map(lambda value: bool(wanted_states & set(str(value).split(","))))
    if max_fee is not None:
        keep &= table["entrance_fee"] <= max_fee  # unknown (NaN) fees fail this test
    if needs_campground:
        keep &= table["campgrounds"] > 0
    result = table[keep].copy()

    wanted = list(activities or []) + list(amenities or [])
    if wanted:
        result["match_score"] = [
            sum(name in _features(row) for name in wanted) / len(wanted)
            for _, row in result.iterrows()
        ]
        result = result[result["match_score"] > 0].copy()
    else:
        result["match_score"] = 1.0

    result["match_reasons"] = [
        explain_match(row, activities, amenities, max_fee, needs_campground)
        for _, row in result.iterrows()
    ]
    sort_by = ["match_score", "visits"] if "visits" in result.columns else ["match_score"]
    result = result.sort_values(sort_by, ascending=False, na_position="last")
    return result.reset_index(drop=True)


def compare_parks(table, codes) -> pd.DataFrame:
    """Show two or more parks side by side, one column per park.

    Args:
        table: The park table from build_park_table().
        codes: Park codes, for example ["olym", "mora"].

    Returns:
        A DataFrame with the parks as columns and their details as rows.

    Raises:
        ValueError: If a park code is not in the table.
    """
    unknown = [code for code in codes if code not in set(table["park_code"])]
    if unknown:
        raise ValueError(f"Unknown park code: {', '.join(unknown)}")
    columns = [column for column in COMPARE_COLUMNS if column in table.columns]
    return table.set_index("park_code").loc[list(codes), columns].T


def search_parks(table, text: str) -> pd.DataFrame:
    """Find parks whose name contains some text, ignoring upper and lower case.

    Args:
        table: The park table from build_park_table().
        text: Part of a park name, for example "rainier".

    Returns:
        The matching rows, sorted by name.
    """
    hits = table[table["full_name"].str.contains(text, case=False, regex=False)]
    return hits.sort_values("full_name").reset_index(drop=True)


def park_summary(table, code: str) -> dict:
    """Collect the main facts about one park.

    Args:
        table: The park table from build_park_table().
        code: The park code, for example "olym".

    Returns:
        A dictionary with name, designation, states, description, url,
        image_url, activities (a list), fee (a short phrase), campgrounds and
        visits. Unknown values are None.

    Raises:
        ValueError: If the park code is not in the table.
    """
    rows = table[table["park_code"] == code]
    if rows.empty:
        raise ValueError(f"Unknown park code: {code}. Try search_parks() to find it.")
    row = rows.iloc[0]

    def known(value):
        return None if pd.isna(value) else value

    visits = known(row.get("visits"))
    return {
        "name": row["full_name"],
        "designation": known(row["designation"]),
        "states": row["states"],
        "description": known(row["description"]),
        "url": row["url"],
        "image_url": known(row["image_url"]),
        "activities": split_list(row["activities"]),
        "fee": fee_text(row["entrance_fee"]),
        "campgrounds": int(row["campgrounds"]),
        "visits": None if visits is None else int(visits),
    }
