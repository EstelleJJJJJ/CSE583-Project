"""Tests for loading and joining the data that ships with the package."""

import math

import parkmatch
from parkmatch.data import split_list


def test_load_parks():
    parks = parkmatch.load_parks()
    assert len(parks) == 475
    assert parks["park_code"].is_unique
    for column in ["park_code", "full_name", "states", "activities", "amenities", "entrance_fee"]:
        assert column in parks.columns


def test_entrance_fee_known_free_and_unknown():
    parks = parkmatch.load_parks().set_index("park_code")
    assert parks.loc["olym", "entrance_fee"] == 15  # the per-person fee is the lowest
    assert parks.loc["noca", "entrance_fee"] == 0  # marked fee free by the NPS
    assert math.isnan(parks.loc["colt", "entrance_fee"])  # not fee free, but no fee listed


def test_load_visits_matches_published_numbers():
    visits = parkmatch.load_visits().set_index(["park_code", "year"])
    assert visits.loc[("grsm", 2024), "visits"] == 12_191_834  # NPS Statistical Abstract 2024
    assert visits.loc[("seki", 2024), "visits"] == 2_008_962  # Sequoia plus Kings Canyon


def test_build_park_table_joins_visits():
    table = parkmatch.build_park_table(year=2025).set_index("park_code")
    assert len(table) == 475
    assert table.loc["olym", "visits"] == 3_584_187
    assert math.isnan(table.loc["alka", "visits"])  # a trail with no visitor statistics


def test_split_list():
    assert split_list("Hiking|Camping") == ["Hiking", "Camping"]
    assert split_list(float("nan")) == []
