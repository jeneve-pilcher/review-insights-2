import os
import re
import threading
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from dateutil import parser as date_parser
from fastapi import HTTPException
from outscraper import OutscraperClient

import config

# --- Cost / speed controls -------------------------------------------------
# Hard ceiling on reviews pulled per business per fetch. The "last X months"
# window is the real limiter; this is just a safety net so one busy location
# can never run up a surprise bill. Override with REVIEW_FETCH_CAP in .env.
FETCH_CAP = int(os.environ.get("REVIEW_FETCH_CAP", "500"))

# How long a pull is reused before we pay for a fresh one. Repeat clicks on
# "Run Analysis" (and the "Your Business" row in the competitor chart) within
# this window cost nothing. Override with REVIEW_CACHE_TTL_SECONDS in .env.
CACHE_TTL_SECONDS = int(os.environ.get("REVIEW_CACHE_TTL_SECONDS", "1800"))
CACHE_MAX_ENTRIES = 50

_cache: dict = {}
# What Google says about each place we pulled (name, address, city, state), so internet mentions can be limited to that
# location. Kept in memory only, keyed by the search text; contains no review text.
_PLACES: dict = {}


def place_info(search_query: str) -> dict:
    return dict(_PLACES.get((search_query or "").strip().lower(), {}))
_cache_lock = threading.Lock()


def cache_lookup(key):
    """Shared by every review source: the stored value if still fresh, else None."""
    with _cache_lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < CACHE_TTL_SECONDS:
            return hit[1]
    return None


def cache_store(key, value) -> None:
    with _cache_lock:
        _cache[key] = (time.time(), value)
        if len(_cache) > CACHE_MAX_ENTRIES:
            oldest = min(_cache, key=lambda k: _cache[k][0])
            _cache.pop(oldest, None)


def _parse_dt(value) -> Optional[datetime]:
    """Parse to a naive UTC datetime, or None if unparseable."""
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _call_outscraper(client, search_query: str, cutoff_ts: int):
    kwargs = dict(
        reviews_limit=FETCH_CAP,
        limit=1,
        sort="newest",
        # Star-only reviews (no text) are kept: they count toward review
        # volume and the star rating, which is what Google itself uses.
        ignore_empty=False,
    )
    try:
        # `cutoff` makes Outscraper stop once it reaches reviews older than
        # the window, instead of scraping the location's entire history.
        return client.google_maps_business_reviews(search_query, cutoff=cutoff_ts, **kwargs)
    except TypeError:
        # This SDK method doesn't accept `cutoff` (the error is raised before
        # any request is sent, so nothing is billed). Fall back to the
        # capped pull; we still filter by date ourselves below.
        return client.google_maps_business_reviews(search_query, **kwargs)


_GID = re.compile(r"(0x[0-9a-f]+:0x[0-9a-f]+)", re.I)


def google_id_from_link(query: str) -> Optional[str]:
    """The place id inside a Google Maps link (looks like 0x8814af28:0x855b6536), or None."""
    q = (query or "").strip()
    if not re.match(r"https?://", q, re.I):
        return None
    m = _GID.search(q)
    return m.group(1) if m else None


def _found_place(results) -> bool:
    for place in results or []:
        if isinstance(place, dict) and (place.get("name") or place.get("address") or place.get("full_address") or place.get("reviews_data")):
            return True
    return False


def _fetch_fresh(search_query: str, months: int) -> Tuple[List[dict], int]:
    api_key = config.require(config.OUTSCRAPER_API_KEY, "OUTSCRAPER_API_KEY")
    client = OutscraperClient(api_key=api_key)

    window_start = _now_utc() - timedelta(days=months * 30.44)
    cutoff_ts = int(window_start.replace(tzinfo=timezone.utc).timestamp())

    try:
        results = _call_outscraper(client, search_query, cutoff_ts)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error fetching reviews for '{search_query}': {exc}")

    # A Google Maps link sometimes returns nothing (extra tracking parameters, or a link form Outscraper doesn't
    # resolve). The link also carries Google's own place id (0x...:0x...), so try that once before giving up.
    gid = google_id_from_link(search_query)
    if gid and not _found_place(results):
        try:
            results = _call_outscraper(client, gid, cutoff_ts)
        except Exception:
            pass

    normalized = []
    raw_total = 0
    for place in results:
        if isinstance(place, dict) and (place.get("name") or place.get("address") or place.get("full_address")):
            _PLACES[search_query.strip().lower()] = {
                k: place.get(k) for k in ("name", "address", "full_address", "city", "state") if isinstance(place.get(k), str)
            }
        for r in (place.get("reviews_data") or []):
            raw_total += 1
            # Star-only reviews arrive with empty text. They stay in the list
            # (volume, rating, heatmap) and are skipped only by language analysis.
            text = (r.get("review_text") or "").strip()

            rating = r.get("review_rating")
            try:
                rating = int(round(float(rating)))
            except (TypeError, ValueError):
                continue

            dt = _parse_dt(r.get("review_datetime_utc"))
            if dt is not None and dt < window_start:
                continue  # outside the requested window

            normalized.append({
                "text": text,
                "rating": max(1, min(5, rating)),
                "datetime_utc": r.get("review_datetime_utc"),
                "author": r.get("author_title", "Anonymous"),
                "source": "google",
            })

    return normalized, raw_total


def fetch_reviews_with_notes(search_query: str, months: int) -> Tuple[List[dict], bool, List[str]]:
    """Returns (reviews, served_from_cache, notes). Reviews are copies, safe to mutate."""
    key = (search_query.strip().lower(), months, FETCH_CAP)
    hit = cache_lookup(key)
    if hit is not None:
        reviews, notes = hit
        return [dict(r) for r in reviews], True, list(notes)

    reviews, raw_total = _fetch_fresh(search_query, months)
    notes = []
    if raw_total >= FETCH_CAP:
        notes.append(
            f"Google results hit the {FETCH_CAP}-review cap, so older reviews in this window may be missing. "
            "A shorter window avoids that."
        )
    cache_store(key, (reviews, notes))
    return [dict(r) for r in reviews], False, list(notes)


def fetch_reviews_with_meta(search_query: str, months: int) -> Tuple[List[dict], bool]:
    """Returns (reviews, served_from_cache)."""
    reviews, cached, _ = fetch_reviews_with_notes(search_query, months)
    return reviews, cached


def fetch_reviews(search_query: str, months: int = 6) -> List[dict]:
    reviews, _ = fetch_reviews_with_meta(search_query, months)
    return reviews


def latest_review_date(reviews: List[dict]) -> Optional[str]:
    dts = [d for d in (_parse_dt(r.get("datetime_utc")) for r in reviews) if d is not None]
    return max(dts).strftime("%Y-%m-%d") if dts else None


def dominant_tiers(reviews: List[dict], top_n: int = 3) -> List[int]:
    """The `top_n` star ratings that occur most often, ordered by frequency."""
    counts = Counter(r["rating"] for r in reviews)
    return [rating for rating, _ in counts.most_common(top_n)]
