"""Tests for the snapshot builder, using tiny inline records instead of real downloads."""

import json
import math

import pandas as pd
import pytest

from parkmatch import snapshot

PARK_RECORDS = [
    {
        "parkCode": "bbbb",
        "fullName": "Bravo National Park",
        "name": "Bravo",
        "designation": "National Park",
        "states": "WA",
        "latitude": "47.5",
        "longitude": "-121.5",
        "description": "  A park   with odd   spacing. ",
        "url": "https://www.nps.gov/bbbb/",
        "activities": [{"name": "Hiking"}, {"name": "Camping"}, {"name": "Hiking"}],
        "topics": [{"name": "Glaciers"}],
        "entranceFees": [
            {"title": "Entrance - Private Vehicle", "cost": "30.00"},
            {"title": "Entrance - Per Person", "cost": "15.00"},
            {"title": "Entrance - Education/Academic Groups", "cost": "0.00"},
            {"title": "Commercial Entrance - Van", "cost": "75.00"},
        ],
        "images": [{"url": "https://img/1.jpg", "altText": "A lake"}],
        "weatherInfo": "Wet.",
    },
    {
        "parkCode": "aaaa",
        "fullName": "Alpha National Historic Site",
        "name": "Alpha",
        "designation": "",
        "states": "NC,TN",
        "latitude": "35.0",
        "longitude": "-83.0",
        "description": "",
        "url": "https://www.nps.gov/aaaa/",
        "activities": [],
        "topics": [],
        "entranceFees": [{"title": "Entrance - Per Person", "cost": "0.00"}],
        "images": [],
        "weatherInfo": "",
    },
    {
        "parkCode": "cccc",
        "fullName": "Charlie National Monument",
        "name": "Charlie",
        "designation": "National Monument",
        "states": "AZ",
        "latitude": "34.0",
        "longitude": "-111.0",
        "description": "Rocks.",
        "url": "https://www.nps.gov/cccc/",
        "activities": [{"name": "Stargazing"}],
        "topics": [{"name": "Night Sky"}],
        "entranceFees": [],
        "images": [],
        "weatherInfo": "",
    },
]

FEE_RECORDS = [
    {"parkCode": "bbbb", "isFeeFreePark": False},
    {"parkCode": "aaaa", "isFeeFreePark": True},
    {"parkCode": "cccc", "isFeeFreePark": "false"},
]

CAMPGROUND_RECORDS = [
    {
        "parkCode": "bbbb",
        "name": "Lake Camp",
        "latitude": "47.6",
        "longitude": "-121.6",
        "url": "https://www.nps.gov/bbbb/camp",
        "campsites": {"totalSites": "40"},
        "numberOfSitesReservable": "25",
        "accessibility": {"rvAllowed": "1", "wheelchairAccess": "Two accessible sites."},
        "amenities": {
            "potableWater": ["Water", " but not potable"],
            "toilets": ["Vault Toilets - year round"],
            "dumpStation": "No",
        },
    },
    {
        "parkCode": "bbbb",
        "name": "Hill Camp",
        "latitude": "",
        "longitude": "",
        "url": "",
        "campsites": {"totalSites": ""},
        "numberOfSitesReservable": "",
        "accessibility": {"rvAllowed": "0", "wheelchairAccess": ""},
        "amenities": {"potableWater": [], "toilets": [], "dumpStation": ""},
    },
]

VISITOR_CENTER_RECORDS = [
    {"parkCode": "bbbb", "name": "Main VC", "latitude": "47.5", "longitude": "-121.5", "url": "v"}
]

AMENITY_RECORDS = [
    [
        {
            "name": "Restroom",
            "parks": [{"parkCode": "bbbb"}, {"parkCode": "aaaa"}, {"parkCode": "bbbb"}],
        }
    ],
    [{"name": "Picnic Table", "parks": [{"parkCode": "bbbb"}]}],
]


def _visitation_rows():
    rows = []
    # BBBB reports every month of 2023 to 2025; AAA1 and AAA2 share a park code via aliases.
    for year in (2023, 2024, 2025):
        for month in range(1, 13):
            rows.append(("BBBB", year, month, "TRV", 100 * month))
            rows.append(("BBBB", year, month, "TOS", 10))
            rows.append(("AAA1", year, month, "TRV", 5))
            rows.append(("AAA2", year, month, "TRV", 7))
    return pd.DataFrame(rows, columns=["UnitCode", "Year", "Month", "Statistic", "Value"])


def test_parks_table_fees_and_text():
    parks = snapshot.parks_table(PARK_RECORDS, FEE_RECORDS).set_index("park_code")
    assert list(parks.index) == ["aaaa", "bbbb", "cccc"]
    # Vehicle and per-person rows count; group and commercial rows do not.
    assert parks.loc["bbbb", "entrance_fee_min"] == 15
    assert parks.loc["bbbb", "fee_per_vehicle"] == 30
    assert bool(parks.loc["bbbb", "fee_free"]) is False
    # A zero-dollar row at a fee-free park means free; blank fields become NaN.
    assert parks.loc["aaaa", "entrance_fee_min"] == 0
    assert math.isnan(parks.loc["aaaa", "fee_per_vehicle"])
    assert math.isnan(parks.loc["aaaa", "designation"])
    assert math.isnan(parks.loc["aaaa", "description"])
    assert math.isnan(parks.loc["aaaa", "activities"])
    # No fee rows and not fee free: unknown.
    assert math.isnan(parks.loc["cccc", "entrance_fee_min"])
    assert parks.loc["bbbb", "activities"] == "Hiking|Camping"
    assert parks.loc["bbbb", "description"] == "A park with odd spacing."
    assert parks.loc["bbbb", "image_alt"] == "A lake"


def test_parks_table_without_fee_records_leaves_fee_free_empty():
    parks = snapshot.parks_table(PARK_RECORDS).set_index("park_code")
    assert math.isnan(parks.loc["aaaa", "fee_free"])
    assert math.isnan(parks.loc["aaaa", "entrance_fee_min"])
    assert parks.loc["bbbb", "entrance_fee_min"] == 15


def test_fee_free_flags_accepts_strings():
    flags = snapshot.fee_free_flags(FEE_RECORDS)
    assert flags == {"bbbb": False, "aaaa": True, "cccc": False}
    assert snapshot.fee_free_flags(None) == {}


def test_campgrounds_table():
    camps = snapshot.campgrounds_table(CAMPGROUND_RECORDS)
    assert camps["name"].tolist() == ["Hill Camp", "Lake Camp"]
    lake = camps.set_index("name").loc["Lake Camp"]
    assert lake["total_sites"] == 40 and lake["reservable_sites"] == 25
    assert bool(lake["rv_allowed"]) is True
    assert lake["potable_water"] == "Water, but not potable"
    hill = camps.set_index("name").loc["Hill Camp"]
    assert hill["total_sites"] == 0 and bool(hill["rv_allowed"]) is False
    assert math.isnan(hill["toilets"]) and math.isnan(hill["latitude"])


def test_amenities_table_unpacks_and_deduplicates():
    amenities = snapshot.amenities_table(AMENITY_RECORDS)
    assert amenities.values.tolist() == [
        ["Picnic Table", "bbbb"],
        ["Restroom", "aaaa"],
        ["Restroom", "bbbb"],
    ]


def test_visitation_tables(tmp_path):
    csv_path = tmp_path / "Main_Data.csv"
    _visitation_rows().to_csv(csv_path, index=False)
    aliases = {"AAA1": "aaaa", "AAA2": "aaaa"}
    annual, monthly = snapshot.visitation_tables(
        csv_path, aliases=aliases, profile_years=(2024, 2025)
    )
    bbbb = annual[annual["park_code"] == "bbbb"].set_index("year")
    assert bbbb.loc[2024, "recreation_visits"] == 100 * 78
    assert bbbb.loc[2024, "overnight_stays"] == 120
    aaaa = annual[annual["park_code"] == "aaaa"]
    assert set(aaaa["unit_code"]) == {"AAA1", "AAA2"}
    assert pd.isna(aaaa["overnight_stays"]).all()
    profile = monthly[monthly["park_code"] == "bbbb"].set_index("month")
    assert len(profile) == 12
    assert profile.loc[12, "mean_recreation_visits"] == 1200
    assert profile["share_of_year"].sum() == pytest.approx(1.0, abs=1e-4)
    # The two alias units are summed before the monthly mean is taken.
    assert monthly[monthly["park_code"] == "aaaa"]["mean_recreation_visits"].eq(12).all()


def test_build_snapshot_writes_all_files(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    for name, records in (
        ("parks.json", PARK_RECORDS),
        ("campgrounds.json", CAMPGROUND_RECORDS),
        ("visitorcenters.json", VISITOR_CENTER_RECORDS),
        ("amenities_parksplaces.json", AMENITY_RECORDS),
        ("feespasses.json", FEE_RECORDS),
    ):
        (raw / name).write_text(json.dumps({"total": str(len(records)), "data": records}))
    csv_path = raw / "Main_Data.csv"
    _visitation_rows().to_csv(csv_path, index=False)
    out = tmp_path / "out"

    counts = snapshot.build_snapshot(raw, csv_path, out, aliases={"AAA1": "aaaa", "AAA2": "aaaa"})

    assert counts == {
        "parks.csv": 3,
        "campgrounds.csv": 2,
        "visitor_centers.csv": 1,
        "amenities.csv": 3,
        "visitation_annual.csv": 9,
        "visitation_monthly.csv": 24,
    }
    for name in snapshot.OUTPUT_FILES:
        assert (out / name).exists()
    notes = (out / "SNAPSHOT.md").read_text()
    assert "10.57830/2317666" in notes and "`AAA1` -> `aaaa`" in notes
    parks = pd.read_csv(out / "parks.csv")
    assert parks["park_code"].tolist() == ["aaaa", "bbbb", "cccc"]
    assert math.isnan(parks.set_index("park_code").loc["cccc", "entrance_fee_min"])


def test_read_raw_accepts_envelope_and_bare_list(tmp_path):
    envelope = tmp_path / "a.json"
    envelope.write_text(json.dumps({"total": "1", "data": [{"x": 1}]}))
    bare = tmp_path / "b.json"
    bare.write_text(json.dumps([{"x": 2}]))
    assert snapshot.read_raw(envelope) == [{"x": 1}]
    assert snapshot.read_raw(bare) == [{"x": 2}]
