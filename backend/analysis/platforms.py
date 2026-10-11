from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from dateutil import parser as date_parser

from analysis.chart1_sentiment_drift import review_velocity
from analysis.review_utils import text_reviews

SOURCE_LABELS = {"google": "Google", "yelp": "Yelp", "opentable": "OpenTable", "doordash": "DoorDash",
                 "grubhub": "Grubhub", "ubereats": "Uber Eats"}


def _label(source: str) -> str:
    return SOURCE_LABELS.get(source, source.title())


def _parse_dt(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def mix_shift(reviews: List[dict], min_each: int = 10, threshold_pts: float = 15.0) -> Optional[dict]:
    """Did the share of reviews coming from each platform change between the
    recent third of the window and the earlier part? If so, a combined average
    can move without any real change in how customers feel."""
    sources = {r.get("source", "google") for r in reviews}
    if len(sources) < 2:
        return None

    dated = sorted(((dt, r) for r in reviews if (dt := _parse_dt(r.get("datetime_utc"))) is not None), key=lambda x: x[0])
    if len(dated) < 2 * min_each:
        return None
    first, last = dated[0][0], dated[-1][0]
    span = (last - first).days
    if span < 28:
        return None

    split = last - timedelta(days=max(14, span / 3))
    base = [r for dt, r in dated if dt < split]
    rec = [r for dt, r in dated if dt >= split]
    if len(base) < min_each or len(rec) < min_each:
        return None

    shares = {}
    for src in sorted(sources):
        shares[src] = {
            "earlier_pct": round(100 * sum(1 for r in base if r.get("source", "google") == src) / len(base), 1),
            "recent_pct": round(100 * sum(1 for r in rec if r.get("source", "google") == src) / len(rec), 1),
        }

    # Name the platform that GAINED share: "Yelp went from 0% to 36%" reads
    # better than "Google went from 100% to 64%" and says the same thing.
    biggest_src = max(shares, key=lambda s: shares[s]["recent_pct"] - shares[s]["earlier_pct"])
    diff = shares[biggest_src]["recent_pct"] - shares[biggest_src]["earlier_pct"]
    shifted = diff >= threshold_pts
    message = ""
    if shifted:
        message = (
            f"Your platform mix changed: {_label(biggest_src)} went from "
            f"{shares[biggest_src]['earlier_pct']:.0f}% to {shares[biggest_src]['recent_pct']:.0f}% of your "
            f"reviews. A combined average can move because of that alone, so check each platform's own view."
        )
    return {"shifted": shifted, "sources": shares, "message": message}


def _row(source: str, reviews: List[dict]) -> dict:
    n = len(reviews)
    vel = review_velocity(reviews) if reviews else None
    low = sum(1 for r in reviews if r["rating"] <= 2)
    return {
        "source": source,
        "label": _label(source),
        "reviews": n,
        "text_reviews": len(text_reviews(reviews)),
        "avg_rating": round(sum(r["rating"] for r in reviews) / n, 2) if n else None,
        "low_star_pct": round(100 * low / n, 1) if n else None,
        "star_counts": vel["star_counts"] if vel else {str(s): 0 for s in range(1, 6)},
        "recent_per_week": vel["recent_per_week"] if vel else None,
        "earlier_per_week": vel["earlier_per_week"] if vel else None,
        "last_review_date": vel["last_review_date"] if vel else None,
        "days_since_last": vel["days_since_last"] if vel else None,
    }


def _web_row(mentions: dict) -> dict:
    s = mentions["summary"]
    dates = [d for d in (_parse_dt(i.get("date")) for i in mentions["items"]) if d is not None]
    return {
        "source": "web", "label": "Web mentions", "kind": "mentions",
        "reviews": s["count"], "text_reviews": s["count"],
        "avg_rating": None, "low_star_pct": None,                 # no stars: never mixed into rating math
        "avg_sentiment": s["avg_sentiment"], "negative_count": s["negative_count"], "positive_count": s["positive_count"],
        "star_counts": {str(i): 0 for i in range(1, 6)},
        "recent_per_week": None, "earlier_per_week": None,
        "last_review_date": max(dates).strftime("%Y-%m-%d") if dates else None, "days_since_last": None,
    }


def _unrated_row(b: dict) -> dict:
    s = b["summary"]
    dates = [d for d in (_parse_dt(i.get("date")) for i in b["items"]) if d is not None]
    return {
        "source": b["source"], "label": b["label"], "kind": "unrated",
        "reviews": s["count"], "text_reviews": s["count"], "avg_rating": None, "low_star_pct": None,
        "avg_sentiment": s["avg_sentiment"], "negative_count": s["negative_count"], "positive_count": s["positive_count"],
        "star_counts": {str(i): 0 for i in range(1, 6)}, "recent_per_week": None, "earlier_per_week": None,
        "last_review_date": max(dates).strftime("%Y-%m-%d") if dates else None, "days_since_last": None,
        "store_rating": b.get("store_rating"), "store_ratings": b.get("store_ratings"),   # the app's own average, shown separately
    }


def build_platform_comparison(reviews_by_source: Dict[str, List[dict]], mentions: Optional[dict] = None,
                              unrated: Optional[Dict[str, dict]] = None) -> dict:
    """Side-by-side numbers for every platform that was pulled, plus the mix-shift check."""
    everything = [r for rs in reviews_by_source.values() for r in rs]
    rows = [_row(src, rs) for src, rs in reviews_by_source.items()]
    if mentions and mentions.get("status") == "ok":
        rows.append(_web_row(mentions))
    for b in (unrated or {}).values():
        rows.append(_unrated_row(b))
    return {"platforms": rows, "mix": mix_shift(everything)}
