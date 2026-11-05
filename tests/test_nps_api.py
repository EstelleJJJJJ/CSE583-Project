"""Tests for the NPS API client, with requests.get replaced by a fake."""

import json

import pytest

from parkmatch import nps_api


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def make_fake_get(records, limit_cap=None, status=200):
    """Build a fake requests.get that pages through ``records``."""
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append({"url": url, "params": dict(params), "headers": dict(headers)})
        if status != 200:
            return FakeResponse(status, {})
        start = int(params["start"])
        limit = int(params["limit"])
        if limit_cap is not None:
            limit = min(limit, limit_cap)
        page = records[start : start + limit]
        payload = {
            "total": str(len(records)),
            "limit": str(limit),
            "start": str(start),
            "data": page,
        }
        return FakeResponse(200, payload)

    fake_get.calls = calls
    return fake_get


def test_fetch_all_pages_until_total(monkeypatch):
    records = [{"id": i} for i in range(5)]
    fake_get = make_fake_get(records, limit_cap=2)
    monkeypatch.setattr(nps_api.requests, "get", fake_get)

    result = nps_api.fetch_all("parks", api_key="k", limit=1000)

    assert result == records
    assert [c["params"]["start"] for c in fake_get.calls] == [0, 2, 4]
    assert fake_get.calls[0]["url"] == "https://developer.nps.gov/api/v1/parks"
    assert fake_get.calls[0]["headers"] == {"X-Api-Key": "k"}


def test_fetch_all_reads_key_from_environment(monkeypatch):
    fake_get = make_fake_get([{"id": 1}])
    monkeypatch.setattr(nps_api.requests, "get", fake_get)
    monkeypatch.setenv("NPS_API_KEY", "from-env")
    assert nps_api.fetch_all("parks") == [{"id": 1}]
    assert fake_get.calls[0]["headers"]["X-Api-Key"] == "from-env"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("NPS_API_KEY", raising=False)
    with pytest.raises(ValueError):
        nps_api.fetch_all("parks")


def test_rate_limit_raises_named_error(monkeypatch):
    monkeypatch.setattr(nps_api.requests, "get", make_fake_get([], status=429))
    with pytest.raises(nps_api.RateLimitError):
        nps_api.fetch_page("parks", "k")


def test_raw_file_name():
    assert nps_api.raw_file_name("parks") == "parks.json"
    assert nps_api.raw_file_name("amenities/parksplaces") == "amenities_parksplaces.json"


def test_download_raw_writes_envelopes(monkeypatch, tmp_path):
    records = [{"parkCode": "olym"}, {"parkCode": "mora"}]
    monkeypatch.setattr(nps_api.requests, "get", make_fake_get(records))

    written = nps_api.download_raw(tmp_path / "raw", api_key="k", endpoints=("parks",))

    path = written["parks"]
    assert path == tmp_path / "raw" / "parks.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["total"] == "2" and payload["data"] == records
