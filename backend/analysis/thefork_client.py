"""TheFork reviews through an Apify actor (default: parsebird/thefork-scraper).

Documented output: ONE row per restaurant with a `reviews` array of
{id, rating_value (1-10), meal_date, review_body, reviewer_name, likes}. TheFork's page only
exposes about the 20 most recent reviews per restaurant. Its scores are out of 10, so they are
converted to the 5-star scale used everywhere else.
"""
import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from dateutil import parser as date_parser
from fastapi import HTTPException

from analysis import apify_client
from analysis import outscraper_client as oc

ACTOR = os.environ.get("APIFY_THEFORK_ACTOR", "parsebird/thefork-scraper")
MAX_REVIEWS = int(os.environ.get("THEFORK_MAX_REVIEWS", "50"))

_HOST = re.compile(r"^(?:www\.)?thefork\.(com|fr|de|it|es)$")
_LANG = {"com": "en", "fr": "fr", "de": "de", "it": "it", "es": "es"}
NOTE_LIMIT = "TheFork only shows about the 20 most recent reviews per restaurant, so this is a recent sample."
NOTE_SCALE = "TheFork scores are out of 10; they're converted to the 5-star scale used here."


def normalize_thefork_url(value: str) -> str:
    """Accepts a pasted TheFork restaurant link; returns https://<host>/restaurant/<slug>-r<id>."""
    raw = (value or "").strip()
    friendly = "That doesn't look like a TheFork restaurant page. It should look like https://www.thefork.com/restaurant/your-restaurant-r123456"
    if not raw:
        raise ValueError(friendly)
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower()
    parts = [p for p in parsed.path.split("/") if p]
    if not _HOST.match(host) or len(parts) < 2 or parts[0] != "restaurant" or not re.search(r"-r\d+$", parts[1]):
        raise ValueError(friendly)
    return f"https://{host}/restaurant/{parts[1]}"


def _stars_from_ten(value) -> Optional[int]:
    """1-10 -> 1-5, rounding halves up (10,9->5  8,7->4  6,5->3  4,3->2  2,1->1)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return max(1, min(5, int(v / 2 + 0.5)))


def _when(value) -> Optional[str]:
    if not value:
        return None
    try:
        dt = date_parser.parse(str(value))
    except (ValueError, TypeError, OverflowError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _normalize(rows: List[dict], window_start: datetime) -> List[dict]:
    out, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        for r in row.get("reviews") or []:
            if not isinstance(r, dict):
                continue
            rating = _stars_from_ten(r.get("rating_value"))
            if rating is None:
                continue
            rid = r.get("id")
            if rid is not None:
                if rid in seen:
                    continue
                seen.add(rid)
            when = _when(r.get("meal_date"))        # the meal date is the closest date TheFork gives
            dt = oc._parse_dt(when)
            if dt is not None and dt < window_start:
                continue
            out.append({
                "text": str(r.get("review_body") or "").strip(),
                "rating": rating,
                "datetime_utc": when,
                "author": r.get("reviewer_name") or "Anonymous",
                "source": "thefork",
            })
    return out


def _inputs(url: str, host_tld: str):
    """The actor's docs describe startUrls as 'an array of URLs' without saying whether items are
    plain strings or {url} objects, so try the object form first and the plain form second."""
    base = {"maxRestaurants": 1, "maxReviews": MAX_REVIEWS, "maxPhotos": 0, "language": _LANG.get(host_tld, "en")}
    return [{**base, "startUrls": [{"url": url}]}, {**base, "startUrls": [url]}]


def _run(url: str) -> List[dict]:
    tld = _HOST.match(urlparse(url).netloc.lower()).group(1)
    first_error: Optional[HTTPException] = None
    for run_input in _inputs(url, tld):
        try:
            rows = apify_client.run_actor(ACTOR, run_input, max_items=5)
        except HTTPException as exc:
            first_error = first_error or exc
            continue
        if rows:
            return rows
    if first_error:
        raise first_error
    return []


def fetch_thefork_reviews_with_meta(url: str, months: int) -> Tuple[List[dict], bool, List[str]]:
    """Returns (reviews, served_from_cache, notes). Reviews are copies."""
    key = ("thefork", url.strip().lower(), months, MAX_REVIEWS)
    hit = oc.cache_lookup(key)
    if hit is not None:
        reviews, notes = hit
        return [dict(r) for r in reviews], True, list(notes)

    window_start = oc._now_utc() - timedelta(days=months * 30.44)
    reviews = _normalize(_run(url), window_start)
    notes = [NOTE_LIMIT, NOTE_SCALE] if reviews else []
    oc.cache_store(key, (reviews, notes))
    return [dict(r) for r in reviews], False, list(notes)


def fetch_raw(url: str) -> List[dict]:
    """For scripts/test_apify.py: the untouched rows."""
    return _run(url)
