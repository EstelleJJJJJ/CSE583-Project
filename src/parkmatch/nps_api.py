"""Thin client for the National Park Service API (component C1).

The NPS API (https://developer.nps.gov/) answers with JSON pages shaped like
``{"total": "475", "limit": "50", "start": "0", "data": [...]}``. The functions
here page through one endpoint, return its records as plain dicts, and save raw
JSON files that :mod:`parkmatch.snapshot` turns into the bundled tables.

Every call needs a key. A free key comes from
https://www.nps.gov/subjects/developer/get-started.htm and is read from the
``NPS_API_KEY`` environment variable when it is not passed in. ``DEMO_KEY``
also works, but it is limited to 30 requests per hour.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from pathlib import Path

import requests

BASE_URL = "https://developer.nps.gov/api/v1/"
TIMEOUT_SECONDS = 60

# Endpoints the bundled snapshot is built from.
DEFAULT_ENDPOINTS = (
    "parks",
    "campgrounds",
    "visitorcenters",
    "amenities/parksplaces",
    "feespasses",
)
# Endpoints we plan to add later (things to do, with pet and duration fields).
PLANNED_ENDPOINTS = ("thingstodo",)


class RateLimitError(RuntimeError):
    """Raised when the NPS API answers with HTTP 429 (too many requests)."""


def resolve_api_key(api_key: str | None = None) -> str:
    """Return the key to use for a request.

    Args:
        api_key: A key passed by the caller. When it is None or empty, the
            ``NPS_API_KEY`` environment variable is used instead.

    Returns:
        The key as a string.

    Raises:
        ValueError: If no key was passed and the environment variable is not set.
    """
    key = api_key or os.environ.get("NPS_API_KEY", "")
    if not key:
        raise ValueError(
            "No NPS API key found. Pass api_key=... or set the NPS_API_KEY environment variable."
        )
    return key


def raw_file_name(endpoint: str) -> str:
    """Return the file name used for an endpoint's raw download.

    Slashes become underscores, so ``amenities/parksplaces`` is stored as
    ``amenities_parksplaces.json``.

    Args:
        endpoint: Endpoint path relative to the API base URL.

    Returns:
        A file name ending in ``.json``.
    """
    return endpoint.strip("/").replace("/", "_") + ".json"


def fetch_page(endpoint: str, api_key: str, start: int = 0, limit: int = 1000) -> dict:
    """Request one page of an endpoint and return the parsed JSON envelope.

    Args:
        endpoint: Endpoint path relative to the API base URL, such as ``parks``.
        api_key: The API key, sent in the ``X-Api-Key`` header.
        start: Zero-based offset of the first record to return.
        limit: Maximum number of records in the page.

    Returns:
        The decoded JSON object with ``total``, ``limit``, ``start`` and ``data`` keys.

    Raises:
        RateLimitError: If the API answers with HTTP 429.
        requests.HTTPError: For any other error status.
    """
    url = BASE_URL + endpoint.strip("/")
    response = requests.get(
        url,
        params={"start": start, "limit": limit},
        headers={"X-Api-Key": api_key},
        timeout=TIMEOUT_SECONDS,
    )
    if response.status_code == 429:
        raise RateLimitError(
            f"The NPS API rate limit was hit while reading '{endpoint}' (HTTP 429). "
            "DEMO_KEY allows 30 requests per hour. Wait, or use a personal key."
        )
    response.raise_for_status()
    return response.json()


def fetch_all(endpoint: str, api_key: str | None = None, limit: int = 1000) -> list[dict]:
    """Return every record of an endpoint, following ``start`` paging.

    The loop stops when a page comes back empty or when the number of records
    collected reaches the ``total`` reported by the API.

    Args:
        endpoint: Endpoint path relative to the API base URL, such as ``parks``.
        api_key: API key; falls back to the ``NPS_API_KEY`` environment variable.
        limit: Page size. The API accepts up to 1000 for the endpoints we use.

    Returns:
        A list of records as returned in the ``data`` field, in API order.
    """
    key = resolve_api_key(api_key)
    records: list[dict] = []
    start = 0
    while True:
        page = fetch_page(endpoint, key, start=start, limit=limit)
        data = page.get("data") or []
        records.extend(data)
        total = int(page.get("total") or len(records))
        start += len(data)
        if not data or start >= total:
            return records


def download_raw(
    out_dir: str | Path,
    api_key: str | None = None,
    endpoints: Iterable[str] = DEFAULT_ENDPOINTS,
    limit: int = 1000,
) -> dict[str, Path]:
    """Download endpoints and write one ``<endpoint>.json`` file per endpoint.

    Each file keeps the API envelope (``total``, ``limit``, ``start``, ``data``)
    with ``data`` holding all records, which is the shape
    :func:`parkmatch.snapshot.build_snapshot` reads.

    Args:
        out_dir: Folder for the JSON files. It is created when missing.
        api_key: API key; falls back to the ``NPS_API_KEY`` environment variable.
        endpoints: Endpoint paths to download. Defaults to the five the snapshot uses.
        limit: Page size passed to :func:`fetch_all`.

    Returns:
        A dict mapping each endpoint to the path of the file written for it.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for endpoint in endpoints:
        records = fetch_all(endpoint, api_key=api_key, limit=limit)
        path = out / raw_file_name(endpoint)
        envelope = {
            "total": str(len(records)),
            "limit": str(limit),
            "start": "0",
            "data": records,
        }
        path.write_text(json.dumps(envelope, ensure_ascii=False), encoding="utf-8")
        written[endpoint] = path
    return written
