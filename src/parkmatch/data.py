"""Load the park data that ships with the package and join the two sources.

parks.csv comes from the NPS API (one row per park) and visits.csv comes from
the NPS Visitor Use Statistics (one row per park and year). build_park_table()
joins them on park_code. Lists such as activities are saved as text joined
with "|", and split_list() turns them back into Python lists.
"""

from importlib.resources import files

import pandas as pd

DATA_DIR = files("parkmatch") / "data"


def _read_csv(name: str) -> pd.DataFrame:
    """Read one of the CSV files in the package's data folder."""
    with DATA_DIR.joinpath(name).open("r", encoding="utf-8") as file:
        return pd.read_csv(file)


def load_parks() -> pd.DataFrame:
    """Load the park table, one row per park.

    Returns:
        DataFrame with park_code, full_name, designation, states, latitude,
        longitude, url, description, image_url, activities, topics, amenities,
        campgrounds and entrance_fee. entrance_fee is 0 for fee-free parks and
        NaN when we don't know the fee.
    """
    return _read_csv("parks.csv")


def load_visits() -> pd.DataFrame:
    """Load yearly recreation visits.

    Returns:
        DataFrame with park_code, year (2016 to 2025) and visits.
    """
    return _read_csv("visits.csv")


def build_park_table(year: int = 2025) -> pd.DataFrame:
    """Join the park table with one year of visits.

    Args:
        year: The year of visits to add.

    Returns:
        The park table with an extra visits column. Parks that the visitor
        statistics don't cover get NaN, not 0.
    """
    parks = load_parks()
    visits = load_visits()
    one_year = visits.loc[visits["year"] == year, ["park_code", "visits"]]
    return parks.merge(one_year, on="park_code", how="left")


def split_list(value) -> list[str]:
    """Turn a "|"-joined cell such as "Hiking|Camping" into a list.

    Args:
        value: The cell value. Empty cells (NaN) give an empty list.

    Returns:
        The items as a list of strings.
    """
    if pd.isna(value) or value == "":
        return []
    return str(value).split("|")
