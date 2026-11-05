"""Tests for find_parks, explain_match, compare_parks, search_parks and park_summary."""

import math

import pandas as pd
import pytest

from parkmatch import matcher

NAN = float("nan")


@pytest.fixture
def table():
    """A five-park table with the columns build_park_table() produces."""
    return pd.DataFrame(
        {
            "park_code": ["olym", "mora", "grsm", "wica", "trai"],
            "full_name": [
                "Olympic National Park",
                "Mount Rainier National Park",
                "Great Smoky Mountains National Park",
                "Wind Cave National Park",
                "Some Trail",
            ],
            "name": ["Olympic", "Mount Rainier", "Great Smoky Mountains", "Wind Cave", "Trail"],
            "designation": ["National Park"] * 4 + ["National Scenic Trail"],
            "states": ["WA", "WA", "NC,TN", "SD", "WA,OR"],
            "activities": [
                "Hiking|Camping|Fishing",
                "Hiking|Camping|Skiing",
                "Hiking|Camping",
                "Hiking|Guided Tours",
                NAN,
            ],
            "topics": ["Forests and Woodlands", "Glaciers", "Animals", "Caves", NAN],
            "amenities": [
                "Restroom|Restroom - Accessible|Picnic Table",
                "Restroom|Picnic Table",
                "Restroom - Accessible",
                "Restroom",
                NAN,
            ],
            "entrance_fee_min": [30.0, 30.0, 0.0, 0.0, NAN],
            "fee_per_vehicle": [30.0, 30.0, NAN, NAN, NAN],
            "fee_per_person": [15.0, 15.0, NAN, NAN, NAN],
            "campground_count": [16, 3, 11, 1, 0],
            "rv_campground_count": [10, 2, 9, 1, 0],
            "visitor_center_count": [4, 4, 4, 1, 0],
            "recreation_visits_2024": [3_717_267.0, 1_620_006.0, 12_191_834.0, 500_000.0, NAN],
            "recreation_visits_2025": [3_584_187.0, 1_635_342.0, 11_527_939.0, 450_000.0, NAN],
            "busiest_month": ["August", "July", "July", "July", NAN],
            "quietest_month": ["January", "February", "January", "January", NAN],
            "url": ["u1", "u2", "u3", "u4", "u5"],
        }
    )


def test_states_filter_matches_any_listed_state(table):
    hits = matcher.find_parks(table, states=["tn"])
    assert hits["park_code"].tolist() == ["grsm"]
    hits = matcher.find_parks(table, states=["WA", "SD"])
    assert set(hits["park_code"]) == {"olym", "mora", "wica", "trai"}


def test_max_fee_drops_unknown_unless_asked(table):
    hits = matcher.find_parks(table, max_fee=10)
    assert set(hits["park_code"]) == {"grsm", "wica"}
    hits = matcher.find_parks(table, max_fee=10, include_unknown_fee=True)
    assert set(hits["park_code"]) == {"grsm", "wica", "trai"}


def test_campground_and_visit_bounds(table):
    assert "trai" not in set(matcher.find_parks(table, needs_campground=True)["park_code"])
    hits = matcher.find_parks(table, max_visits=2_000_000)
    assert set(hits["park_code"]) == {"mora", "wica"}
    hits = matcher.find_parks(table, min_visits=1_000_000, year=2024)
    assert hits["park_code"].tolist() == ["grsm", "olym", "mora"]
    with pytest.raises(KeyError):
        matcher.find_parks(table, max_visits=10, year=1999)


def test_soft_criteria_score_and_order(table):
    hits = matcher.find_parks(table, activities=["Hiking", "Skiing"], amenities=["Picnic Table"])
    scores = dict(zip(hits["park_code"], hits["match_score"]))
    assert scores["mora"] == pytest.approx(1.0)
    assert scores["olym"] == pytest.approx(2 / 3)
    assert scores["grsm"] == pytest.approx(1 / 3)
    assert "trai" not in scores
    # Equal scores sort by visits, most visited first.
    assert hits["park_code"].tolist()[:2] == ["mora", "olym"]
    assert hits["park_code"].tolist()[2] == "grsm"


def test_no_soft_criteria_gives_score_one(table):
    hits = matcher.find_parks(table, states=["WA"])
    assert (hits["match_score"] == 1.0).all()
    assert hits["park_code"].tolist() == ["olym", "mora", "trai"]


def test_match_reasons_text(table):
    hits = matcher.find_parks(
        table, states=["WA"], activities=["Hiking", "Skiing"], max_fee=50, needs_campground=True
    )
    reasons = dict(zip(hits["park_code"], hits["match_reasons"]))
    assert (
        reasons["mora"]
        == "In WA; offers Hiking and Skiing; lowest entrance fee $30; 3 campgrounds."
    )
    assert "does not list Skiing" in reasons["olym"]
    assert reasons["olym"].endswith("16 campgrounds.")


def test_explain_match_without_criteria(table):
    row = table.iloc[0]
    assert matcher.explain_match(row) == "No criteria given."
    assert matcher.explain_match(row, max_fee=10) == "Lowest entrance fee $30."
    trail = table.iloc[4]
    assert matcher.explain_match(trail, max_fee=10) == "Fee information not available."
    assert matcher.explain_match(trail, max_visits=5) == "No visitation record for 2025."


def test_compare_parks(table):
    comparison = matcher.compare_parks(table, ["olym", "MORA"])
    assert list(comparison.columns) == ["olym", "mora"]
    assert comparison.loc["full_name", "mora"] == "Mount Rainier National Park"
    assert comparison.loc["recreation_visits_2024", "olym"] == 3_717_267
    assert comparison.loc["activity_count", "olym"] == 3
    assert comparison.loc["amenity: Restroom - Accessible", "olym"] == "yes"
    assert comparison.loc["amenity: Restroom - Accessible", "mora"] == "no"
    assert comparison.loc["rv_campground_count", "olym"] == 10
    with pytest.raises(ValueError):
        matcher.compare_parks(table, ["olym"])
    with pytest.raises(ValueError):
        matcher.compare_parks(table, ["olym", "nope"])


def test_search_parks(table):
    assert matcher.search_parks(table, "RAINIER")["park_code"].tolist() == ["mora"]
    assert matcher.search_parks(table, "national park")["park_code"].tolist() == [
        "grsm",
        "mora",
        "olym",
        "wica",
    ]
    assert matcher.search_parks(table, "   ").empty
    assert matcher.search_parks(table, "zzz").empty


def test_park_summary(table):
    summary = matcher.park_summary(table, "olym")
    assert summary["full_name"] == "Olympic National Park"
    assert summary["states"] == ["WA"]
    assert summary["activities"] == ["Hiking", "Camping", "Fishing"]
    assert summary["fee_text"] == "lowest entrance fee $30"
    assert summary["recreation_visits"] == 3_584_187 and summary["visits_year"] == 2025
    assert summary["busiest_month"] == "August"
    trail = matcher.park_summary(table, "trai")
    assert trail["entrance_fee_min"] is None
    assert trail["fee_text"] == "fee information not available"
    assert trail["recreation_visits"] is None and trail["visits_year"] is None
    assert trail["activities"] == []
    with pytest.raises(ValueError):
        matcher.park_summary(table, "nope")


def test_helpers():
    assert matcher._join_words(["A"]) == "A"
    assert matcher._join_words(["A", "B"]) == "A and B"
    assert matcher._join_words(["A", "B", "C"]) == "A, B and C"
    assert matcher._fee_text(0) == "free entrance"
    assert matcher._fee_text(12.5) == "lowest entrance fee $12.50"
    assert matcher._fee_text(math.nan) == "fee information not available"
