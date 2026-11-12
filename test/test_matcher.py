"""Tests for the matcher functions, using a small made-up table."""

import pandas as pd
import pytest

from park_matching import matcher


@pytest.fixture
def table():
    return pd.DataFrame(
        {
            "park_code": ["aaaa", "bbbb", "cccc", "dddd"],
            "full_name": ["Alpha National Park", "Bravo Lake", "Charlie Trail", "Delta Park"],
            "designation": ["National Park", "National Recreation Area", float("nan"), "Park"],
            "states": ["WA", "WA,OR", "TN,NC", "CA"],
            "description": ["a", "b", "c", "d"],
            "url": ["u1", "u2", "u3", "u4"],
            "image_url": ["i1", "i2", "i3", "i4"],
            "activities": ["Hiking|Camping", "Hiking|Boating", "Hiking", float("nan")],
            "amenities": ["Restroom", "Restroom|Picnic Table", float("nan"), "Restroom"],
            "campgrounds": [3, 1, 0, 2],
            "entrance_fee": [30.0, 0.0, float("nan"), 10.0],
            "visits": [1000.0, 5000.0, float("nan"), 200.0],
        }
    )


def test_states_filter_includes_multi_state_parks(table):
    assert set(matcher.find_parks(table, states=["or"])["park_code"]) == {"bbbb"}
    assert set(matcher.find_parks(table, states=["WA"])["park_code"]) == {"aaaa", "bbbb"}


def test_max_fee_leaves_out_unknown_fees(table):
    assert set(matcher.find_parks(table, max_fee=20)["park_code"]) == {"bbbb", "dddd"}


def test_needs_campground(table):
    assert "cccc" not in set(matcher.find_parks(table, needs_campground=True)["park_code"])


def test_score_and_order(table):
    hits = matcher.find_parks(table, activities=["Hiking", "Camping"])
    assert list(hits["park_code"]) == ["aaaa", "bbbb", "cccc"]
    assert list(hits["match_score"]) == [1.0, 0.5, 0.5]  # ties sorted by visits


def test_no_scored_criteria_gives_score_one(table):
    hits = matcher.find_parks(table, states=["WA"])
    assert list(hits["match_score"]) == [1.0, 1.0]
    assert list(hits["park_code"]) == ["bbbb", "aaaa"]


def test_match_reasons(table):
    hits = matcher.find_parks(
        table, activities=["Hiking"], amenities=["Picnic Table"], max_fee=50, needs_campground=True
    )
    reasons = dict(zip(hits["park_code"], hits["match_reasons"]))
    assert reasons["bbbb"] == "Has Hiking and Picnic Table; free entrance; 1 campground."
    assert reasons["aaaa"] == "Has Hiking; missing Picnic Table; entrance fee $30; 3 campgrounds."


def test_no_match_gives_empty_table(table):
    assert matcher.find_parks(table, states=["NY"]).empty


def test_compare_parks(table):
    comparison = matcher.compare_parks(table, ["aaaa", "bbbb"])
    assert list(comparison.columns) == ["aaaa", "bbbb"]
    assert comparison.loc["campgrounds", "aaaa"] == 3
    with pytest.raises(ValueError):
        matcher.compare_parks(table, ["aaaa", "zzzz"])


def test_search_parks(table):
    assert list(matcher.search_parks(table, "LAKE")["park_code"]) == ["bbbb"]
    assert matcher.search_parks(table, "nothing like this").empty


def test_park_summary(table):
    summary = matcher.park_summary(table, "cccc")
    assert summary["activities"] == ["Hiking"]
    assert summary["fee"] == "entrance fee unknown"
    assert summary["designation"] is None and summary["visits"] is None
    with pytest.raises(ValueError):
        matcher.park_summary(table, "zzzz")


def test_fee_text():
    assert matcher.fee_text(0) == "free entrance"
    assert matcher.fee_text(12.5) == "entrance fee $12.5"
    assert matcher.fee_text(float("nan")) == "entrance fee unknown"
