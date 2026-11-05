"""Build the bundled CSV tables from raw NPS downloads (component C2, use case UC7).

Inputs are the raw JSON files written by :func:`parkmatch.nps_api.download_raw`
(``parks.json``, ``campgrounds.json``, ``visitorcenters.json``,
``amenities_parksplaces.json`` and ``feespasses.json``) and ``Main_Data.csv``
from the NPS Visitor Use Statistics data package. Outputs are the six CSV files
in ``parkmatch/data`` that :mod:`parkmatch.data` loads, plus
``parkmatch/data/SNAPSHOT.md``, which records where the inputs came from and when.

Run it as a script to rebuild the tables::

    python -m parkmatch.snapshot --raw-dir data/raw --visitation data/raw/Main_Data.csv

Add ``--download`` to fetch the raw JSON files first (needs ``NPS_API_KEY``).
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
from collections.abc import Iterable, Mapping
from pathlib import Path

import pandas as pd
import requests

from parkmatch.data import MULTI_SEP
from parkmatch.nps_api import DEFAULT_ENDPOINTS, download_raw

# Where Main_Data.csv comes from (NPS DataStore reference 2317666, DOI 10.57830/2317666).
VISITATION_URL = "https://irma.nps.gov/DataStore/DownloadFile/756959?Reference=2317666"

# IRMA reporting units whose code differs from the NPS API park code. Everything
# else is matched by lowercasing the unit code. Units that share a park code are
# summed. See SNAPSHOT.md for the reasoning behind each entry.
UNIT_ALIASES: dict[str, str] = {
    "SEQU": "seki",  # Sequoia NP; the API lists Sequoia and Kings Canyon as one unit
    "KICA": "seki",  # Kings Canyon NP
    "ROLA": "noca",  # Ross Lake NRA; the API's noca page is the North Cascades complex
    "LACH": "noca",  # Lake Chelan NRA
    "JEFM": "thje",  # Thomas Jefferson Memorial
    "NCPE": "nace",  # National Capital Parks-East
    "OBRI": "obed",  # Obed Wild and Scenic River
    "PERL": "valr",  # Pearl Harbor National Memorial (API code kept from the old name)
    "PRPA": "whho",  # President's Park (White House)
}

# First and last year averaged in the monthly profile.
PROFILE_YEARS = (2021, 2025)

# Raw file for each output table. The fees file is optional; without it the
# fee_free column is empty and parks with no fee rows keep an unknown fee.
RAW_FILES = {
    "parks": "parks.json",
    "campgrounds": "campgrounds.json",
    "visitor_centers": "visitorcenters.json",
    "amenities": "amenities_parksplaces.json",
    "fees": "feespasses.json",
}
OUTPUT_FILES = (
    "parks.csv",
    "campgrounds.csv",
    "visitor_centers.csv",
    "amenities.csv",
    "visitation_annual.csv",
    "visitation_monthly.csv",
)

# Fee rows that describe what an ordinary visitor pays to get in. Commercial tour
# rows, group and school rates and timed-entry reservations are left out.
VEHICLE_FEE_TITLE = "Entrance - Private Vehicle"
PERSON_FEE_TITLE = "Entrance - Per Person"
MOTORCYCLE_FEE_TITLE = "Entrance - Motorcycle"
INDIVIDUAL_FEE_TITLES = (VEHICLE_FEE_TITLE, PERSON_FEE_TITLE, MOTORCYCLE_FEE_TITLE)

NAN = float("nan")


def read_raw(path: str | Path) -> list:
    """Read a raw JSON download and return its list of records.

    Args:
        path: A file written by :func:`parkmatch.nps_api.download_raw` or saved
            by hand from the API. Both the API envelope (a dict with a ``data``
            key) and a bare list are accepted.

    Returns:
        The records as a list.
    """
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        return list(payload.get("data") or [])
    return list(payload)


def join_multi(values: Iterable[str] | None) -> str | float:
    """Join values into one ``|``-separated string.

    Values are stripped, empty ones dropped and repeats removed while keeping
    the original order. The NPS campground feed sometimes splits a phrase on
    its comma (``["Water", " but not potable"]``); a value that starts with a
    space is glued back onto the previous one.

    Args:
        values: Strings to join. None gives NaN.

    Returns:
        The joined string, or NaN when nothing is left to join.
    """
    if values is None:
        return NAN
    parts: list[str] = []
    for value in values:
        text = str(value)
        if text.startswith(" ") and parts:
            parts[-1] = parts[-1] + "," + text.rstrip()
            continue
        text = text.strip()
        if text and text not in parts:
            parts.append(text)
    return MULTI_SEP.join(parts) if parts else NAN


def _text(value: object) -> str | float:
    """Collapse whitespace in a text field; empty text becomes NaN."""
    if value is None:
        return NAN
    text = " ".join(str(value).split())
    return text if text else NAN


def _number(value: object) -> float:
    """Parse a numeric string; blanks and junk become NaN."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return NAN


def _count(value: object) -> int:
    """Parse a count that the API gives as a string, treating blanks as 0."""
    number = _number(value)
    return 0 if math.isnan(number) else int(number)


def _fee_columns(fees: list[dict], fee_free: object) -> tuple[float, float, float]:
    """Return (entrance_fee_min, fee_per_vehicle, fee_per_person) for one park.

    ``entrance_fee_min`` is the lowest non-zero fee among the per-vehicle,
    per-person and motorcycle rows. A park that lists no such row is 0 when
    the ``feespasses`` endpoint marks it fee free and NaN (unknown) otherwise.
    Zero-dollar rows are ignored because they usually describe walk-in or
    group entry at a park that still charges per vehicle.
    """
    listed = []
    for fee in fees or []:
        title = str(fee.get("title", ""))
        cost = _number(fee.get("cost"))
        if title in INDIVIDUAL_FEE_TITLES and not math.isnan(cost):
            listed.append((title, cost))
    fee_min = min((cost for _, cost in listed if cost > 0), default=NAN)
    if math.isnan(fee_min) and fee_free is True:
        fee_min = 0.0
    per_vehicle = next((cost for title, cost in listed if title == VEHICLE_FEE_TITLE), NAN)
    per_person = next((cost for title, cost in listed if title == PERSON_FEE_TITLE), NAN)
    return fee_min, per_vehicle, per_person


def fee_free_flags(records: list[dict] | None) -> dict[str, bool]:
    """Map park codes to the ``isFeeFreePark`` flag of the ``feespasses`` endpoint.

    Args:
        records: Records from the ``feespasses`` endpoint, or None when the
            file was not downloaded.

    Returns:
        Dict from park code to True or False; empty when ``records`` is None.
    """
    flags: dict[str, bool] = {}
    for record in records or []:
        value = record.get("isFeeFreePark")
        if isinstance(value, str):
            value = value.strip().lower() == "true"
        flags[record["parkCode"]] = bool(value)
    return flags


def parks_table(records: list[dict], fee_records: list[dict] | None = None) -> pd.DataFrame:
    """Flatten ``parks`` records into one row per park unit.

    Args:
        records: Records from the ``parks`` endpoint.
        fee_records: Records from the ``feespasses`` endpoint, used for the
            ``fee_free`` column. None leaves that column empty (NaN).

    Returns:
        DataFrame with the ``parks.csv`` columns, sorted by park code.
    """
    flags = fee_free_flags(fee_records)
    rows = []
    for record in records:
        code = record["parkCode"]
        fee_free = flags.get(code, NAN) if flags else NAN
        fee_min, per_vehicle, per_person = _fee_columns(record.get("entranceFees") or [], fee_free)
        images = record.get("images") or []
        first_image = images[0] if images else {}
        rows.append(
            {
                "park_code": code,
                "full_name": _text(record.get("fullName")),
                "name": _text(record.get("name")),
                "designation": _text(record.get("designation")),
                "states": _text(record.get("states")),
                "latitude": _number(record.get("latitude")),
                "longitude": _number(record.get("longitude")),
                "description": _text(record.get("description")),
                "url": _text(record.get("url")),
                "activities": join_multi(a["name"] for a in record.get("activities") or []),
                "topics": join_multi(t["name"] for t in record.get("topics") or []),
                "entrance_fee_min": fee_min,
                "fee_per_vehicle": per_vehicle,
                "fee_per_person": per_person,
                "fee_free": fee_free,
                "image_url": _text(first_image.get("url")),
                "image_alt": _text(first_image.get("altText")),
                "weather_info": _text(record.get("weatherInfo")),
            }
        )
    return pd.DataFrame(rows).sort_values("park_code").reset_index(drop=True)


def campgrounds_table(records: list[dict]) -> pd.DataFrame:
    """Flatten ``campgrounds`` records into one row per campground.

    Args:
        records: Records from the ``campgrounds`` endpoint.

    Returns:
        DataFrame with the ``campgrounds.csv`` columns, sorted by park code and name.
    """
    rows = []
    for record in records:
        amenities = record.get("amenities") or {}
        access = record.get("accessibility") or {}
        sites = record.get("campsites") or {}
        rows.append(
            {
                "park_code": record["parkCode"],
                "name": _text(record.get("name")),
                "latitude": _number(record.get("latitude")),
                "longitude": _number(record.get("longitude")),
                "total_sites": _count(sites.get("totalSites")),
                "reservable_sites": _count(record.get("numberOfSitesReservable")),
                "rv_allowed": str(access.get("rvAllowed", "")).strip() == "1",
                "potable_water": join_multi(amenities.get("potableWater")),
                "toilets": join_multi(amenities.get("toilets")),
                "dump_station": _text(amenities.get("dumpStation")),
                "wheelchair_access": _text(access.get("wheelchairAccess")),
                "url": _text(record.get("url")),
            }
        )
    return pd.DataFrame(rows).sort_values(["park_code", "name"]).reset_index(drop=True)


def visitor_centers_table(records: list[dict]) -> pd.DataFrame:
    """Flatten ``visitorcenters`` records into one row per visitor center.

    Args:
        records: Records from the ``visitorcenters`` endpoint.

    Returns:
        DataFrame with the ``visitor_centers.csv`` columns, sorted by park code and name.
    """
    rows = [
        {
            "park_code": record["parkCode"],
            "name": _text(record.get("name")),
            "latitude": _number(record.get("latitude")),
            "longitude": _number(record.get("longitude")),
            "url": _text(record.get("url")),
        }
        for record in records
    ]
    return pd.DataFrame(rows).sort_values(["park_code", "name"]).reset_index(drop=True)


def amenities_table(items: list) -> pd.DataFrame:
    """Turn ``amenities/parksplaces`` records into a long amenity-park table.

    Each record of that endpoint is a one-element list holding
    ``{"name": ..., "parks": [{"parkCode": ...}, ...]}``; bare dicts are
    accepted too.

    Args:
        items: Records from the ``amenities/parksplaces`` endpoint.

    Returns:
        DataFrame with columns amenity and park_code, one row per link,
        without duplicates, sorted by amenity and park code.
    """
    rows = []
    for item in items:
        entries = item if isinstance(item, list) else [item]
        for entry in entries:
            for park in entry.get("parks") or []:
                rows.append({"amenity": entry["name"], "park_code": park["parkCode"]})
    table = pd.DataFrame(rows, columns=["amenity", "park_code"]).drop_duplicates()
    return table.sort_values(["amenity", "park_code"]).reset_index(drop=True)


def visitation_tables(
    csv_path: str | Path,
    aliases: Mapping[str, str] = UNIT_ALIASES,
    profile_years: tuple[int, int] = PROFILE_YEARS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarize ``Main_Data.csv`` into annual totals and a monthly profile.

    Only two statistics are kept: TRV (recreation visits) and TOS (total
    overnight stays). ``park_code`` is the unit code lowercased, or the alias
    from ``aliases`` when there is one. The annual table keeps one row per
    original unit and year; the monthly table sums the units that share a
    park code first, then averages each month over the profile years.

    Args:
        csv_path: Path to ``Main_Data.csv`` (columns UnitCode, Year, Month,
            Statistic, Value).
        aliases: Mapping from IRMA unit code to NPS API park code.
        profile_years: First and last year, inclusive, averaged in the profile.

    Returns:
        A pair ``(annual, monthly)`` with the ``visitation_annual.csv`` and
        ``visitation_monthly.csv`` columns.
    """
    data = pd.read_csv(
        csv_path,
        usecols=["UnitCode", "Year", "Month", "Statistic", "Value"],
        dtype={"UnitCode": str, "Statistic": str},
    )
    data = data.loc[data["Statistic"].isin(["TRV", "TOS"])].copy()
    data["park_code"] = data["UnitCode"].map(lambda code: aliases.get(code, code.lower()))

    annual = (
        data.groupby(["park_code", "UnitCode", "Year", "Statistic"])["Value"]
        .sum()
        .unstack("Statistic")
        .reset_index()
        .rename(
            columns={
                "UnitCode": "unit_code",
                "Year": "year",
                "TRV": "recreation_visits",
                "TOS": "overnight_stays",
            }
        )
    )
    for column in ("recreation_visits", "overnight_stays"):
        if column not in annual.columns:
            annual[column] = NAN
        annual[column] = annual[column].astype("Int64")
    annual = annual[["park_code", "unit_code", "year", "recreation_visits", "overnight_stays"]]
    annual = annual.sort_values(["park_code", "unit_code", "year"]).reset_index(drop=True)

    first, last = profile_years
    recent = data.loc[(data["Statistic"] == "TRV") & data["Year"].between(first, last)]
    by_month = recent.groupby(["park_code", "Year", "Month"])["Value"].sum()
    monthly = (
        by_month.groupby(["park_code", "Month"])
        .mean()
        .rename("mean_recreation_visits")
        .reset_index()
        .rename(columns={"Month": "month"})
    )
    totals = monthly.groupby("park_code")["mean_recreation_visits"].transform("sum")
    monthly["share_of_year"] = (monthly["mean_recreation_visits"] / totals).where(totals > 0)
    monthly["mean_recreation_visits"] = monthly["mean_recreation_visits"].round(1)
    monthly["share_of_year"] = monthly["share_of_year"].round(5)
    monthly = monthly.sort_values(["park_code", "month"]).reset_index(drop=True)
    return annual, monthly


def download_visitation(dest: str | Path, url: str = VISITATION_URL) -> Path:
    """Download ``Main_Data.csv`` (about 72 MB) from the NPS DataStore.

    Args:
        dest: Where to save the file. Parent folders are created.
        url: Download URL; the default is the 2025 data package file.

    Returns:
        The path written.
    """
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as response:
        response.raise_for_status()
        with open(path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1 << 20):
                handle.write(chunk)
    return path


def build_snapshot(
    raw_dir: str | Path,
    visitation_csv: str | Path,
    out_dir: str | Path,
    aliases: Mapping[str, str] = UNIT_ALIASES,
    profile_years: tuple[int, int] = PROFILE_YEARS,
) -> dict[str, int]:
    """Build all six bundled CSV files.

    Args:
        raw_dir: Folder holding the raw JSON files named in ``RAW_FILES``.
        visitation_csv: Path to ``Main_Data.csv``.
        out_dir: Folder for the CSV files. It is created when missing.
        aliases: Mapping from IRMA unit code to NPS API park code.
        profile_years: First and last year, inclusive, averaged in the profile.

    Returns:
        Dict mapping each output file name to its number of rows.
    """
    raw = Path(raw_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    fees_path = raw / RAW_FILES["fees"]
    fee_records = read_raw(fees_path) if fees_path.exists() else None
    tables = {
        "parks.csv": parks_table(read_raw(raw / RAW_FILES["parks"]), fee_records),
        "campgrounds.csv": campgrounds_table(read_raw(raw / RAW_FILES["campgrounds"])),
        "visitor_centers.csv": visitor_centers_table(read_raw(raw / RAW_FILES["visitor_centers"])),
        "amenities.csv": amenities_table(read_raw(raw / RAW_FILES["amenities"])),
    }
    annual, monthly = visitation_tables(
        visitation_csv, aliases=aliases, profile_years=profile_years
    )
    tables["visitation_annual.csv"] = annual
    tables["visitation_monthly.csv"] = monthly

    counts = {}
    for name, table in tables.items():
        table.to_csv(out / name, index=False, encoding="utf-8")
        counts[name] = len(table)
    write_snapshot_notes(out / "SNAPSHOT.md", counts, aliases, profile_years)
    return counts


def write_snapshot_notes(
    path: str | Path,
    counts: Mapping[str, int],
    aliases: Mapping[str, str] = UNIT_ALIASES,
    profile_years: tuple[int, int] = PROFILE_YEARS,
    date: datetime.date | None = None,
) -> Path:
    """Write ``SNAPSHOT.md``: where the tables came from, when, and how to rebuild them.

    Args:
        path: Where to write the markdown file.
        counts: Row counts per output file, as returned by :func:`build_snapshot`.
        aliases: The alias table that was applied.
        profile_years: First and last year of the monthly profile.
        date: Snapshot date; today when None.

    Returns:
        The path written.
    """
    day = date or datetime.date.today()
    first, last = profile_years
    lines = [
        "# Data snapshot",
        "",
        f"Built on {day.isoformat()} with `python -m parkmatch.snapshot`. Only the files below",
        "ship with the package; the raw downloads are not committed.",
        "",
        "## Sources",
        "",
        "- NPS API (https://developer.nps.gov/, a free key from",
        "  https://www.nps.gov/subjects/developer/get-started.htm): endpoints `parks`,",
        "  `campgrounds`, `visitorcenters`, `amenities/parksplaces` and `feespasses`,",
        "  fetched with `limit=1000`.",
        "- NPS Visitor Use Statistics Data Package, 2025, `Main_Data.csv`, NPS DataStore",
        "  reference 2317666, DOI 10.57830/2317666, public domain:",
        f"  {VISITATION_URL}",
        "  Statistics used: TRV (recreation visits) and TOS (total overnight stays).",
        "",
        "## Files",
        "",
    ]
    lines += [f"- `{name}`: {rows:,} rows" for name, rows in counts.items()]
    lines += [
        "",
        f"`visitation_monthly.csv` averages each month over {first} to {last}.",
        "",
        "## Unit code aliases",
        "",
        "IRMA unit codes are matched to API park codes by lowercasing. These codes differ",
        "and are mapped by hand; units that share a park code are summed:",
        "",
    ]
    lines += [f"- `{unit}` -> `{code}`" for unit, code in aliases.items()]
    lines += [
        "",
        "IRMA codes with no API counterpart are kept under their lowercased code and",
        "do not join to any park. API units with no visitation series keep NaN visits.",
        "",
        "## Rebuild",
        "",
        "```",
        "export NPS_API_KEY=...",
        "python -m parkmatch.snapshot --download --download-visitation \\",
        "    --raw-dir data/raw --visitation data/raw/Main_Data.csv",
        "```",
        "",
    ]
    out = Path(path)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point: ``python -m parkmatch.snapshot``.

    Args:
        argv: Arguments to parse; None means ``sys.argv[1:]``.

    Returns:
        Process exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        prog="python -m parkmatch.snapshot",
        description="Rebuild the bundled ParkMatch CSV tables from raw NPS downloads.",
    )
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="folder with parks.json, campgrounds.json, visitorcenters.json, "
        "amenities_parksplaces.json and feespasses.json (default: data/raw)",
    )
    parser.add_argument(
        "--visitation",
        default="data/raw/Main_Data.csv",
        help="path to Main_Data.csv from the NPS Visitor Use Statistics package",
    )
    parser.add_argument(
        "--out-dir",
        default=str(Path(__file__).parent / "data"),
        help="where to write the CSV files (default: the package's data folder)",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="download the raw JSON files into --raw-dir first (needs NPS_API_KEY)",
    )
    parser.add_argument(
        "--download-visitation",
        action="store_true",
        help="download Main_Data.csv to the --visitation path first (about 72 MB)",
    )
    args = parser.parse_args(argv)

    if args.download:
        written = download_raw(args.raw_dir, endpoints=DEFAULT_ENDPOINTS)
        for endpoint, path in written.items():
            print(f"downloaded {endpoint} -> {path}")
    if args.download_visitation:
        print(f"downloaded visitation -> {download_visitation(args.visitation)}")

    counts = build_snapshot(args.raw_dir, args.visitation, args.out_dir)
    for name, rows in counts.items():
        print(f"{name}: {rows} rows")
    print(f"written to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
