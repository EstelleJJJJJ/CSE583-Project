"""Tests for the bundled tables and the joined park table."""

import math

import pandas as pd

import parkmatch
from parkmatch import data

PARK_COLUMNS = [
    "park_code",
    "full_name",
    "name",
    "designation",
    "states",
    "latitude",
    "longitude",
    "description",
    "url",
    "activities",
    "topics",
    "entrance_fee_min",
    "fee_per_vehicle",
    "fee_per_person",
    "fee_free",
    "image_url",
    "image_alt",
    "weather_info",
]


def test_load_parks_shape_and_columns():
    parks = parkmatch.load_parks()
    assert list(parks.columns) == PARK_COLUMNS
    assert len(parks) == 475
    assert parks["park_code"].is_unique
    assert parks["park_code"].str.len().eq(4).all()
    assert parks["latitude"].notna().all() and parks["longitude"].notna().all()


def test_other_loaders_have_expected_columns():
    assert list(parkmatch.load_campgrounds().columns) == [
        "park_code",
        "name",
        "latitude",
        "longitude",
        "total_sites",
        "reservable_sites",
        "rv_allowed",
        "potable_water",
        "toilets",
        "dump_station",
        "wheelchair_access",
        "url",
    ]
    assert list(parkmatch.load_visitor_centers().columns) == [
        "park_code",
        "name",
        "latitude",
        "longitude",
        "url",
    ]
    assert list(parkmatch.load_amenities().columns) == ["amenity", "park_code"]
    assert list(parkmatch.load_visitation().columns) == [
        "park_code",
        "unit_code",
        "year",
        "recreation_visits",
        "overnight_stays",
    ]
    assert list(parkmatch.load_monthly_profile().columns) == [
        "park_code",
        "month",
        "mean_recreation_visits",
        "share_of_year",
    ]


def test_monthly_profile_has_twelve_months_per_park():
    profile = parkmatch.load_monthly_profile()
    counts = profile.groupby("park_code").size()
    assert (counts == 12).all()
    shares = profile.dropna(subset=["share_of_year"]).groupby("park_code")["share_of_year"].sum()
    assert ((shares - 1).abs() < 1e-3).all()


def test_visitation_check_values():
    visits = parkmatch.load_visitation()
    annual = visits.groupby(["park_code", "year"])["recreation_visits"].sum()
    assert annual[("grsm", 2024)] == 12_191_834
    assert annual[("zion", 2024)] == 4_946_592
    assert annual[("olym", 2024)] == 3_717_267
    assert annual[("mora", 2024)] == 1_620_006
    # Sequoia and Kings Canyon report separately in IRMA and are summed into seki.
    seki_units = set(visits.loc[visits["park_code"] == "seki", "unit_code"])
    assert seki_units == {"SEQU", "KICA"}


def test_unknown_fee_stays_nan_and_fee_free_is_zero():
    parks = parkmatch.load_parks().set_index("park_code")
    # Fee free according to the feespasses endpoint, no fee rows: free, not unknown.
    free = parks[parks["fee_free"].eq(True) & parks["fee_per_vehicle"].isna()]
    assert len(free) > 300
    assert (free["entrance_fee_min"] == 0).all()
    # Not fee free and no per-vehicle or per-person row: the fee is unknown, not 0.
    unknown = parks[parks["fee_free"].eq(False) & parks["entrance_fee_min"].isna()]
    assert len(unknown) >= 1
    assert "colt" in unknown.index
    # A park with listed fees keeps them; the minimum is the per-person rate.
    assert parks.loc["olym", "fee_per_vehicle"] == 30
    assert parks.loc["olym", "fee_per_person"] == 15
    assert parks.loc["olym", "entrance_fee_min"] == 15


def test_build_park_table_one_row_per_park():
    table = parkmatch.build_park_table()
    assert len(table) == 475
    assert table["park_code"].is_unique
    for column in (
        "campground_count",
        "rv_campground_count",
        "has_campground",
        "visitor_center_count",
        "amenities",
        "recreation_visits_2024",
        "recreation_visits_2025",
        "busiest_month",
        "quietest_month",
    ):
        assert column in table.columns
    assert (table["rv_campground_count"] <= table["campground_count"]).all()
    assert table["has_campground"].eq(table["campground_count"] > 0).all()


def test_build_park_table_keeps_missing_visitation_as_nan():
    table = parkmatch.build_park_table().set_index("park_code")
    # Ala Kahakai National Historic Trail has no visitation series at all.
    assert math.isnan(table.loc["alka", "recreation_visits_2025"])
    assert pd.isna(table.loc["alka", "busiest_month"])
    # Olympic has one, and August is its busiest month in the 2021 to 2025 profile.
    assert table.loc["olym", "recreation_visits_2025"] == 3_584_187
    assert table.loc["olym", "busiest_month"] == "August"
    assert table.loc["olym", "quietest_month"] == "January"


def test_split_multi_and_list_values():
    assert data.split_multi("Hiking|Camping| Fishing ") == ["Hiking", "Camping", "Fishing"]
    assert data.split_multi(float("nan")) == []
    assert data.split_multi(None) == []
    frame = pd.DataFrame({"activities": ["Hiking|Camping", "Hiking", float("nan")]})
    counts = data.list_values(frame, "activities")
    assert counts["Hiking"] == 2 and counts["Camping"] == 1


def test_month_name():
    assert data.month_name(7) == "July"
    assert data.month_name(7.0) == "July"
    assert math.isnan(data.month_name(float("nan")))
