"""Yelp reviews via Outscraper's documented /yelp-reviews endpoint.

Outscraper's Python SDK has no confirmed Yelp method, so this calls the REST
endpoint directly. Anything about the request or response that we couldn't
verify ahead of time is handled defensively, and scripts/test_yelp.py prints
the raw response so a first live pull shows immediately whether anything needs
adjusting.
"""
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests
from fastapi import HTTPException

import config
from analysis import outscraper_client as oc

BASE_URL = os.environ.get("OUTSCRAPER_BASE_URL", "https://api.app.outscraper.com").rstrip("/")

# Hard ceiling on Yelp reviews per pull (a safety net, like the Google cap).
YELP_CAP = int(os.environ.get("YELP_FETCH_CAP", "300"))
# Newest-first ordering is what makes the date cutoff meaningful. If Outscraper
# expects a different value, change it here without touching code.
YELP_SORT = os.environ.get("YELP_SORT", "date_desc")

REQUEST_TIMEOUT = 60
POLL_INTERVAL = 2.0
POLL_TIMEOUT = 120.0


# Real Yelp domains only: rejects look-alikes such as yelp.evil.com.
_YELP_HOST = re.compile(
    r"^(?:[a-z0-9-]+\.)*yelp\.(?:com|ca|co\.uk|com\.au|de|fr|es|it|nl|pt|se|dk|no|fi|at|ch|be|ie|jp|com\.br|com\.mx)$"
)


def normalize_yelp_url(value: str) -> str:
    """Accepts a pasted Yelp link and returns a clean https://<yelp>/biz/<slug>
    URL (tracking junk removed). Raises ValueError with a friendly message."""
    raw = (value or "").strip()
    friendly = (
        "That doesn't look like a Yelp business page. It should look like "
        "https://www.yelp.com/biz/your-business-name"
    )
    if not raw:
        raise ValueError(friendly)
    if "://" not in raw:
        raw = "https://" + raw

    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower()
    parts = [p for p in parsed.path.split("/") if p]
    if not _YELP_HOST.match(host) or len(parts) < 2 or parts[0] != "biz":
        raise ValueError(friendly)
    return f"https://{host}/biz/{parts[1]}"


def _headers() -> dict:
    return {"X-API-KEY": config.require(config.OUTSCRAPER_API_KEY, "OUTSCRAPER_API_KEY")}


def _get(url: str, params: Optional[dict] = None):
    try:
        return requests.get(url, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach Outscraper for Yelp reviews: {exc}")


def _json_or_error(resp, what: str):
    if resp.status_code >= 400:
        snippet = (resp.text or "")[:200]
        raise HTTPException(status_code=502, detail=f"Outscraper returned {resp.status_code} for {what}: {snippet}")
    try:
        return resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail=f"Outscraper sent a response for {what} that wasn't valid JSON.")


def _wait_for_results(payload: dict) -> dict:
    """Outscraper answers slow jobs with 'Pending' + a results link; poll it."""
    location = payload.get("results_location")
    if not location:
        raise HTTPException(status_code=502, detail="Outscraper accepted the Yelp request but gave no results link.")
    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        data = _json_or_error(_get(location), "Yelp reviews (waiting for results)")
        status = str(data.get("status", "")).lower()
        if status == "success":
            return data
        if status in ("error", "failed"):
            raise HTTPException(status_code=502, detail=f"Outscraper could not fetch the Yelp reviews: {data.get('error') or status}")
    raise HTTPException(status_code=504, detail="Outscraper took too long to return the Yelp reviews. Try a shorter time window.")


def _request_reviews(yelp_url: str, limit: int, cutoff_ts: Optional[int]) -> dict:
    params = {
        "query": yelp_url,
        # Both spellings: the REST docs and the SDK use different casings and
        # unknown parameters are ignored.
        "reviewsLimit": limit,
        "reviews_limit": limit,
        "async": "false",
    }
    if cutoff_ts is not None:
        params["cutoff"] = cutoff_ts
    if YELP_SORT:
        params["sort"] = YELP_SORT

    resp = _get(f"{BASE_URL}/yelp-reviews", params)
    payload = _json_or_error(resp, "Yelp reviews")
    if resp.status_code == 202 or str(payload.get("status", "")).lower() == "pending":
        payload = _wait_for_results(payload)
    return payload


def extract_review_dicts(node) -> List[dict]:
    """Finds the individual review objects however Outscraper nested them
    (a flat list, a list per query, or inside a 'reviews_data' / 'data' key)."""
    out: List[dict] = []
    if isinstance(node, list):
        for item in node:
            out.extend(extract_review_dicts(item))
    elif isinstance(node, dict):
        has_rating = "review_rating" in node or "rating" in node
        has_body = any(k in node for k in ("review_text", "text", "datetime_utc", "review_datetime_utc", "timestamp"))
        if has_rating and has_body:
            out.append(node)
        else:
            for key in ("data", "reviews_data", "reviews"):
                if key in node:
                    out.extend(extract_review_dicts(node[key]))
    return out


def _datetime_string(raw: dict) -> Optional[str]:
    for key in ("datetime_utc", "review_datetime_utc", "date"):
        if raw.get(key):
            return str(raw[key])
    ts = raw.get("timestamp") or raw.get("review_timestamp")
    if ts:
        try:
            ts = float(ts)
            if ts > 1e12:  # milliseconds
                ts /= 1000
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError, OverflowError, OSError):
            return None
    return None


def _normalize(raw_reviews: List[dict], window_start: datetime) -> List[dict]:
    out = []
    for r in raw_reviews:
        rating = r.get("review_rating", r.get("rating"))
        try:
            rating = int(round(float(rating)))
        except (TypeError, ValueError):
            continue

        when = _datetime_string(r)
        dt = oc._parse_dt(when)
        if dt is not None and dt < window_start:
            continue  # outside the requested window

        out.append({
            "text": (r.get("review_text") or r.get("text") or "").strip(),
            "rating": max(1, min(5, rating)),
            "datetime_utc": when,
            "author": r.get("author_title", "Anonymous"),
            "source": "yelp",
        })
    return out


def _integrity_notes(raw_reviews: List[dict], cap: int) -> List[str]:
    notes = []
    if len(raw_reviews) >= cap:
        notes.append(f"Yelp results hit the {cap}-review cap, so older reviews in this window may be missing.")
        dts = [d for d in (oc._parse_dt(_datetime_string(r)) for r in raw_reviews) if d is not None]
        if any(a < b for a, b in zip(dts, dts[1:])):
            notes.append("Yelp did not return reviews newest-first, so this may not be your most recent set.")
    return notes


def fetch_yelp_reviews_with_meta(yelp_url: str, months: int) -> Tuple[List[dict], bool, List[str]]:
    """Returns (reviews, served_from_cache, notes). Reviews are copies."""
    key = ("yelp", yelp_url.strip().lower(), months, YELP_CAP)
    hit = oc.cache_lookup(key)
    if hit is not None:
        reviews, notes = hit
        return [dict(r) for r in reviews], True, list(notes)

    window_start = oc._now_utc() - timedelta(days=months * 30.44)
    cutoff_ts = int(window_start.replace(tzinfo=timezone.utc).timestamp())

    payload = _request_reviews(yelp_url, YELP_CAP, cutoff_ts)
    raw = extract_review_dicts(payload.get("data", payload) if isinstance(payload, dict) else payload)

    reviews = _normalize(raw, window_start)
    notes = _integrity_notes(raw, YELP_CAP)
    oc.cache_store(key, (reviews, notes))
    return [dict(r) for r in reviews], False, list(notes)


def fetch_raw(yelp_url: str, limit: int = 5) -> Tuple[dict, List[dict]]:
    """For scripts/test_yelp.py: the untouched response and the review objects found in it."""
    payload = _request_reviews(yelp_url, limit, None)
    return payload, extract_review_dicts(payload.get("data", payload) if isinstance(payload, dict) else payload)
