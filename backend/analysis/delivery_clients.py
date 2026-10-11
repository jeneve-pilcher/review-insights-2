"""DoorDash, Uber Eats and Grubhub reviews through Apify actors.

  DoorDash  e-commerce/doordash-reviews-scraper (maintained by Apify). Documented output: rating, text,
            date, user, placeInfo. Its input fields aren't documented on the page, so two shapes are tried.
  Uber Eats e-commerce/ubereats-reviews-scraper (maintained by Apify). Documented output: authorName, date
            ("12/31/23"), text, placeInfo{rating, numberOfRatings, ...}. There is NO star rating per review,
            only the store's overall rating, so these are "unrated" written reviews.
  Grubhub   easyapi/grubhub-restaurant-reviews-scraper (community). Input restaurantUrls + maxItems; output
            star_rating (1-5), content, reviewer, review_created_date (epoch milliseconds).
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

DOORDASH_ACTOR = os.environ.get("APIFY_DOORDASH_ACTOR", "e-commerce/doordash-reviews-scraper")
UBEREATS_ACTOR = os.environ.get("APIFY_UBEREATS_ACTOR", "e-commerce/ubereats-reviews-scraper")
GRUBHUB_ACTOR = os.environ.get("APIFY_GRUBHUB_ACTOR", "easyapi/grubhub-restaurant-reviews-scraper")
DOORDASH_CAP = int(os.environ.get("DOORDASH_FETCH_CAP", "200"))
UBEREATS_CAP = int(os.environ.get("UBEREATS_FETCH_CAP", "200"))
GRUBHUB_CAP = int(os.environ.get("GRUBHUB_FETCH_CAP", "200"))

NOTE_UBEREATS = "Uber Eats reviews have no star ratings, so they're read for tone and topics but never counted in your ratings."


# ----------------------------------------------------------------------------- link checks
def _parts(value: str):
    raw = (value or "").strip()
    if not raw:
        return "", []
    if "://" not in raw:
        raw = "https://" + raw
    p = urlparse(raw)
    return (p.netloc or "").lower(), [x for x in p.path.split("/") if x]


def normalize_doordash_url(value: str) -> str:
    """https://www.doordash.com/store/<name>-<id>[/<id>/]"""
    friendly = "That doesn't look like a DoorDash store page. It should look like https://www.doordash.com/store/your-restaurant-city-123456/"
    host, parts = _parts(value)
    if re.match(r"^[a-z]{2}(-[A-Za-z]{2})?$", parts[0] if parts else ""):
        parts = parts[1:]                                      # a locale prefix such as /en-CA/
    if not re.match(r"^(?:www\.)?doordash\.com$", host) or len(parts) < 2 or parts[0] != "store" or not re.search(r"-\d+$", parts[1]):
        raise ValueError(friendly)
    extra = f"{parts[2]}/" if len(parts) > 2 and parts[2].isdigit() else ""
    return f"https://www.doordash.com/store/{parts[1]}/{extra}"


def normalize_ubereats_url(value: str) -> str:
    """https://www.ubereats.com/[cc/]store/<name>/<id>"""
    friendly = "That doesn't look like an Uber Eats store page. It should look like https://www.ubereats.com/store/your-restaurant/abc123"
    host, parts = _parts(value)
    prefix = ""
    if parts and re.match(r"^[a-z]{2}$", parts[0]):
        prefix, parts = f"{parts[0]}/", parts[1:]               # a country prefix such as /ca/
    if not re.match(r"^(?:www\.)?ubereats\.com$", host) or len(parts) < 3 or parts[0] != "store":
        raise ValueError(friendly)
    return f"https://www.ubereats.com/{prefix}store/{parts[1]}/{parts[2]}"


def normalize_grubhub_url(value: str) -> str:
    """https://www.grubhub.com/restaurant/<name>/<id>/"""
    friendly = "That doesn't look like a Grubhub restaurant page. It should look like https://www.grubhub.com/restaurant/your-restaurant/123456/"
    host, parts = _parts(value)
    if not re.match(r"^(?:www\.)?grubhub\.com$", host) or len(parts) < 3 or parts[0] != "restaurant" or not parts[2].isdigit():
        raise ValueError(friendly)
    return f"https://www.grubhub.com/restaurant/{parts[1]}/{parts[2]}/"


# ----------------------------------------------------------------------------- shared helpers
def _stars(value) -> Optional[int]:
    try:
        return max(1, min(5, int(round(float(value)))))
    except (TypeError, ValueError):
        return None


def _when(value) -> Optional[str]:
    """Any date shape -> 'YYYY-MM-DD HH:MM:SS' (UTC), or None. Handles ISO, '12/31/23' and epoch milliseconds."""
    if value in (None, "", 0):
        return None
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip().isdigit() and len(value.strip()) >= 10):
            n = float(value)
            dt = datetime.fromtimestamp(n / 1000 if n > 1e11 else n, tz=timezone.utc)
        else:
            dt = date_parser.parse(str(value))
    except (ValueError, TypeError, OverflowError, OSError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")


def _name(value) -> str:
    if isinstance(value, dict):
        value = value.get("name") or value.get("firstName") or value.get("displayName")
    return str(value).strip() if value else "Anonymous"


def _in_window(when: Optional[str], window_start: datetime) -> bool:
    dt = oc._parse_dt(when)
    return dt is None or dt >= window_start


def _cached_or_run(key, months, build):
    """Shared cache wrapper: build() -> (reviews, notes). Returns (reviews, cached, notes) with copies."""
    hit = oc.cache_lookup(key)
    if hit is not None:
        reviews, notes = hit
        return [dict(r) for r in reviews], True, list(notes)
    reviews, notes = build(oc._now_utc() - timedelta(days=months * 30.44))
    oc.cache_store(key, (reviews, notes))
    return [dict(r) for r in reviews], False, list(notes)


def _cap_note(label: str, cap: int, count: int) -> List[str]:
    return [f"{label} results hit the {cap}-review cap, so older reviews in this window may be missing."] if count >= cap else []


# ----------------------------------------------------------------------------- DoorDash (rated)
def _doordash_normalize(items: List[dict], window_start: datetime) -> List[dict]:
    out, seen = [], set()
    for it in items:
        if not isinstance(it, dict):
            continue
        rating = _stars(it.get("rating"))
        if rating is None:
            continue
        text = str(it.get("text") or it.get("content") or "").strip()
        when = _when(it.get("date"))
        author = _name(it.get("user") or it.get("userName") or it.get("authorName"))
        sig = (author, when, text[:60])
        if sig in seen:
            continue
        seen.add(sig)
        if _in_window(when, window_start):
            out.append({"text": text, "rating": rating, "datetime_utc": when, "author": author, "source": "doordash"})
    return out


def _doordash_run(url: str) -> List[dict]:
    first_error: Optional[HTTPException] = None
    for cap_field in ("maxReviewsPerPlace", "maxReviews"):    # the input field isn't documented: try both
        try:
            rows = apify_client.run_actor(DOORDASH_ACTOR, {"startUrls": [{"url": url}], cap_field: DOORDASH_CAP}, max_items=DOORDASH_CAP)
        except HTTPException as exc:
            first_error = first_error or exc
            continue
        if rows:
            return rows
    if first_error:
        raise first_error
    return []


def fetch_doordash_reviews_with_meta(url: str, months: int) -> Tuple[List[dict], bool, List[str]]:
    def build(window_start):
        rows = _doordash_run(url)
        return _doordash_normalize(rows, window_start), _cap_note("DoorDash", DOORDASH_CAP, len(rows))
    return _cached_or_run(("doordash", url.lower(), months, DOORDASH_CAP), months, build)


# ----------------------------------------------------------------------------- Grubhub (rated)
def _grubhub_normalize(items: List[dict], window_start: datetime) -> List[dict]:
    out, seen = [], set()
    for it in items:
        if not isinstance(it, dict):
            continue
        rating = _stars(it.get("star_rating"))
        if rating is None:
            continue
        rid = it.get("id")
        if rid is not None:
            if rid in seen:
                continue
            seen.add(rid)
        when = _when(it.get("review_created_date"))
        if _in_window(when, window_start):
            out.append({"text": str(it.get("content") or "").strip(), "rating": rating, "datetime_utc": when,
                        "author": _name(it.get("reviewer")), "source": "grubhub"})
    return out


def _grubhub_run(url: str, limit: int) -> List[dict]:
    return apify_client.run_actor(GRUBHUB_ACTOR, {"restaurantUrls": [url], "maxItems": limit}, max_items=limit)


def fetch_grubhub_reviews_with_meta(url: str, months: int) -> Tuple[List[dict], bool, List[str]]:
    def build(window_start):
        rows = _grubhub_run(url, GRUBHUB_CAP)
        return _grubhub_normalize(rows, window_start), _cap_note("Grubhub", GRUBHUB_CAP, len(rows))
    return _cached_or_run(("grubhub", url.lower(), months, GRUBHUB_CAP), months, build)


# ----------------------------------------------------------------------------- Uber Eats (UNRATED)
def _ubereats_normalize(items: List[dict], window_start: datetime) -> List[dict]:
    out, seen = [], set()
    for it in items:
        if not isinstance(it, dict):
            continue
        text = str(it.get("text") or "").strip()
        if not text:
            continue                                           # a review with no words has nothing to analyze and no stars
        when = _when(it.get("date"))
        author = _name(it.get("authorName"))
        sig = (author, when, text[:60])
        if sig in seen:
            continue
        seen.add(sig)
        place = it.get("placeInfo") if isinstance(it.get("placeInfo"), dict) else {}
        if _in_window(when, window_start):
            out.append({"text": text, "rating": None, "datetime_utc": when, "author": author, "source": "ubereats",
                        "store_rating": place.get("rating"), "store_ratings": place.get("numberOfRatings"), "url": place.get("url")})
    return out


def _ubereats_run(url: str, limit: int) -> List[dict]:
    return apify_client.run_actor(UBEREATS_ACTOR, {"startUrls": [{"url": url}], "maxReviewsPerPlace": limit}, max_items=limit)


def fetch_ubereats_reviews_with_meta(url: str, months: int) -> Tuple[List[dict], bool, List[str]]:
    def build(window_start):
        rows = _ubereats_run(url, UBEREATS_CAP)
        reviews = _ubereats_normalize(rows, window_start)
        for r in reviews:
            r["url"] = r.get("url") or url          # fall back to the store page the owner saved
        return reviews, (([NOTE_UBEREATS] if reviews else []) + _cap_note("Uber Eats", UBEREATS_CAP, len(rows)))
    return _cached_or_run(("ubereats", url.lower(), months, UBEREATS_CAP), months, build)


# ----------------------------------------------------------------------------- for scripts/test_apify.py
RAW = {
    "doordash": (_doordash_run, _doordash_normalize, "doordash"),
    "ubereats": (lambda url: _ubereats_run(url, 5), _ubereats_normalize, "ubereats"),
    "grubhub": (lambda url: _grubhub_run(url, 5), _grubhub_normalize, "grubhub"),
}
