"""OpenTable reviews through an Apify actor (default: parsebird/opentable-reviews-scraper).

Documented output per review: reviewId, rating (1-5), text, author, date (ISO), visitDate,
foodRating/serviceRating/..., publicRestaurantReply. Reviews come newest first, and only from
diners who actually booked and dined, so every review has a star rating.
"""
import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from dateutil import parser as date_parser

from analysis import apify_client
from analysis import outscraper_client as oc

ACTOR = os.environ.get("APIFY_OPENTABLE_ACTOR", "parsebird/opentable-reviews-scraper")
FETCH_CAP = int(os.environ.get("OPENTABLE_FETCH_CAP", "200"))

_HOST = re.compile(r"^(?:www\.)?opentable\.(?:com|ca|co\.uk|com\.au|de|jp|ie|com\.mx|es|nl|be|ch|se|dk|ae|sg|hk)$")


def normalize_opentable_url(value: str) -> str:
    """Accepts a pasted OpenTable restaurant link; returns a clean https://<host>/r/<slug> URL."""
    raw = (value or "").strip()
    friendly = "That doesn't look like an OpenTable restaurant page. It should look like https://www.opentable.com/r/your-restaurant-city"
    if not raw:
        raise ValueError(friendly)
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower()
    parts = [p for p in parsed.path.split("/") if p]
    if not _HOST.match(host) or len(parts) < 2 or parts[0] != "r":
        raise ValueError(friendly)
    return f"https://{host}/r/{parts[1]}"


def _stars(value) -> Optional[int]:
    try:
        return max(1, min(5, int(round(float(value)))))
    except (TypeError, ValueError):
        return None


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


def _normalize(items: List[dict], window_start: datetime) -> List[dict]:
    out, seen = [], set()
    for it in items:
        if not isinstance(it, dict):
            continue
        rating = _stars(it.get("rating"))
        if rating is None:
            continue
        rid = it.get("reviewId")
        if rid is not None:
            if rid in seen:
                continue
            seen.add(rid)
        when = _when(it.get("date") or it.get("submittedDate") or it.get("visitDate"))
        dt = oc._parse_dt(when)
        if dt is not None and dt < window_start:
            continue                                  # outside the requested window
        review = {
            "text": str(it.get("text") or "").strip(),
            "rating": rating,
            "datetime_utc": when,
            "author": it.get("author") or "Anonymous",
            "source": "opentable",
        }
        # food / service / ambience / value scores: used by the fine-dining pack's sub-ratings graph
        sub = {k: _stars(it.get(f)) for k, f in (("food", "foodRating"), ("service", "serviceRating"),
                                                  ("ambience", "ambienceRating"), ("value", "valueRating"))}
        sub = {k: v for k, v in sub.items() if v is not None}
        if sub:
            review["sub"] = sub
        out.append(review)
    return out


def fetch_opentable_reviews_with_meta(url: str, months: int) -> Tuple[List[dict], bool, List[str]]:
    """Returns (reviews, served_from_cache, notes). Reviews are copies."""
    key = ("opentable", url.strip().lower(), months, FETCH_CAP)
    hit = oc.cache_lookup(key)
    if hit is not None:
        reviews, notes = hit
        return [dict(r) for r in reviews], True, list(notes)

    window_start = oc._now_utc() - timedelta(days=months * 30.44)
    items = apify_client.run_actor(ACTOR, {"startUrls": [{"url": url}], "results_wanted": FETCH_CAP}, max_items=FETCH_CAP)
    reviews = _normalize(items, window_start)

    notes = []
    if len(items) >= FETCH_CAP:
        notes.append(f"OpenTable results hit the {FETCH_CAP}-review cap, so older reviews in this window may be missing.")
    oc.cache_store(key, (reviews, notes))
    return [dict(r) for r in reviews], False, list(notes)


def fetch_raw(url: str, limit: int = 5) -> List[dict]:
    """For scripts/test_apify.py: the untouched rows."""
    return apify_client.run_actor(ACTOR, {"startUrls": [{"url": url}], "results_wanted": limit}, max_items=limit)
