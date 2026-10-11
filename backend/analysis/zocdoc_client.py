"""Provider-level data from Zocdoc, through an Apify actor (default: silentflow/zocdoc-scraper-ppr, pay per result).

Verified against the actor's documentation (silentflow/zocdoc-scraper): input startUrls [{url}] (doctor profile pages),
maxReviews, skipAvailability; output rows with dataType "doctor" (name, specialty, overallRating, bedsideMannerRating,
waitTimeRating, reviewCount) and dataType "review" (doctorUrl, reviewRating, reviewBedsideManner, reviewWaitTime,
reviewText, reviewDate, isVerified). Review rows carry NO patient names. We keep only numbers, never review text, and
a provider's name only because the doctor's public profile is what is being measured.

This is an opt-in feature: nothing here runs unless an administrator has enabled provider-level data for a company."""
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from dateutil import parser as date_parser

from analysis import apify_client
from analysis import outscraper_client as oc

ACTOR = os.environ.get("APIFY_ZOCDOC_ACTOR", "silentflow/zocdoc-scraper-ppr")
MAX_REVIEWS = int(os.environ.get("ZOCDOC_MAX_REVIEWS", "10"))
MAX_PROVIDERS = int(os.environ.get("ZOCDOC_MAX_PROVIDERS", "10"))   # per location
RECENT_DAYS = 28
MIN_RECENT, MIN_EARLIER = 3, 5

_HOST = re.compile(r"^(?:www\.)?zocdoc\.com$")


def normalize_zocdoc_url(value: str) -> str:
    """https://www.zocdoc.com/doctor/<name>-<id>"""
    friendly = "That doesn't look like a Zocdoc doctor page. It should look like https://www.zocdoc.com/doctor/jane-doe-md-12345"
    raw = (value or "").strip()
    if not raw:
        raise ValueError(friendly)
    if "://" not in raw:
        raw = "https://" + raw
    p = urlparse(raw)
    parts = [x for x in p.path.split("/") if x]
    if not _HOST.match((p.netloc or "").lower()) or len(parts) < 2 or parts[0] != "doctor" or not re.search(r"-\d+$", parts[1]):
        raise ValueError(friendly)
    return f"https://www.zocdoc.com/doctor/{parts[1]}"


def _num(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _when(v) -> Optional[datetime]:
    try:
        dt = date_parser.parse(str(v))
    except (ValueError, TypeError, OverflowError):
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def _avg(xs) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def summarize_providers(rows: List[dict], window_start: datetime) -> List[dict]:
    """One summary per doctor, from the actor's rows. Numbers only: no review text, no reviewer details."""
    docs: Dict[str, dict] = {}
    revs: Dict[str, list] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        kind = row.get("dataType")
        if kind == "doctor" and row.get("url"):
            docs[normalize_zocdoc_url(row["url"])] = row
        elif kind == "review" and row.get("doctorUrl"):
            try:
                url = normalize_zocdoc_url(row["doctorUrl"])
            except ValueError:
                continue
            dt = _when(row.get("reviewDate"))
            if dt is not None and dt < window_start:
                continue
            revs.setdefault(url, []).append((dt, _num(row.get("reviewRating")), _num(row.get("reviewBedsideManner")),
                                              _num(row.get("reviewWaitTime")), bool(row.get("isVerified")),))
    out = []
    for url in sorted(set(docs) | set(revs)):
        d = docs.get(url, {})
        rs = revs.get(url, [])
        dated = [r for r in rs if r[0] is not None]
        cutoff = max(r[0] for r in dated) - timedelta(days=RECENT_DAYS) if dated else None
        recent = [r[1] for r in dated if r[0] > cutoff and r[1] is not None]
        earlier = [r[1] for r in dated if r[0] <= cutoff and r[1] is not None]
        out.append({
            "url": url, "name": d.get("name") or url.rsplit("/", 1)[-1], "specialty": d.get("specialty"),
            "reviews": len(rs), "avg_rating": _avg(r[1] for r in rs), "bedside": _avg(r[2] for r in rs), "wait": _avg(r[3] for r in rs),
            "verified_pct": round(100 * sum(1 for r in rs if r[4]) / len(rs)) if rs else None,
            "recent_avg": _avg(recent) if len(recent) >= MIN_RECENT else None, "earlier_avg": _avg(earlier) if len(earlier) >= MIN_EARLIER else None,
            "profile_rating": _num(d.get("overallRating")), "profile_reviews": d.get("reviewCount"),
        })
        o = out[-1]
        o["change"] = round(o["recent_avg"] - o["earlier_avg"], 2) if o["recent_avg"] is not None and o["earlier_avg"] is not None else None
    return out


def fetch_providers(urls: List[str], months: int) -> Tuple[List[dict], int]:
    """Runs the actor for these doctor pages. Returns (per-provider summaries, number of rows bought)."""
    urls = [normalize_zocdoc_url(u) for u in urls][:MAX_PROVIDERS]
    if not urls:
        return [], 0
    run_input = {"startUrls": [{"url": u} for u in urls], "maxReviews": MAX_REVIEWS, "skipAvailability": True}
    rows = apify_client.run_actor(ACTOR, run_input, max_items=len(urls) * (MAX_REVIEWS + 1))
    window_start = oc._now_utc() - timedelta(days=months * 30.44)
    return summarize_providers(rows, window_start), len(rows)
