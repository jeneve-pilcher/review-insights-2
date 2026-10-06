import hashlib
import threading
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from dateutil import parser as date_parser

from analysis.pii import redact_pii
from analysis.review_utils import has_text
from analysis.sentiment import score_sentiment
from analysis.trends import terms_for_text, top_terms
from email_alerts import send_email

NEGATIVE_RATING_THRESHOLD = 2  # 1-2 star reviews are treated as "negative"

# Remembers which negative reviews we've already emailed about (per
# recipient), so clicking Run Analysis repeatedly doesn't re-send the same
# alert. In-memory only: resets when the backend restarts.
_alerted: dict = {}
_alerted_lock = threading.Lock()


def _parse_dt(value):
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError, OverflowError):
        return None


def _review_key(location: str, review_date, rating, text: str) -> str:
    raw = f"{location}|{review_date}|{rating}|{text[:80]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _collect(reviews: List[dict], location_label: str) -> List[dict]:
    """Every 1-2 star review, star-only ones included: a 1-star with no
    comment still hurts the score and still deserves attention."""
    negative = []
    for r in reviews:
        if r["rating"] > NEGATIVE_RATING_THRESHOLD:
            continue
        dt = _parse_dt(r["datetime_utc"])
        if dt is None:
            continue
        negative.append({
            "rating": r["rating"],
            "review_date": r["datetime_utc"],
            "text": r["text"],
            "source": r.get("source", "google"),
            "_dt": dt,
            "_key": _review_key(location_label, r["datetime_utc"], r["rating"], r["text"]),
        })
    negative.sort(key=lambda r: r["_dt"], reverse=True)
    return negative


def _summary(negative: List[dict], total_reviews: int, top: List[dict]) -> dict:
    written = sum(1 for n in negative if has_text(n))
    return {
        "count": len(negative),
        "text_count": written,
        "star_only_count": len(negative) - written,
        "total_reviews": total_reviews,
        "share_pct": round(100 * len(negative) / total_reviews, 1) if total_reviews else 0.0,
        "top_terms": top[:5],
    }


def negative_summary(reviews: List[dict]) -> dict:
    """Just the findings, with no review text (the free-tier teaser)."""
    negative = _collect(reviews, "")
    top = top_terms([n["text"] for n in negative if has_text(n)], n=5)
    return _summary(negative, len(reviews), top)


def build_negative_reviews(
    reviews: List[dict],
    location_label: str,
    max_reviews: int = 20,
    alert_email: Optional[str] = None,
    alert_lookback_hours: int = 24,
) -> dict:
    """Takes an already-fetched review list (no scraping happens here)."""
    negative_all = _collect(reviews, location_label)

    top = top_terms([n["text"] for n in negative_all if has_text(n)], n=10)
    rank = {t["term"]: i for i, t in enumerate(top)}
    summary = _summary(negative_all, len(reviews), top)

    shown = negative_all[:max_reviews]

    alert_cutoff = datetime.now(timezone.utc) - timedelta(hours=alert_lookback_hours)
    recent = [r for r in shown if r["_dt"] >= alert_cutoff]

    alert_sent = False
    new_recent = recent
    if alert_email:
        with _alerted_lock:
            seen = _alerted.setdefault(alert_email, set())
            new_recent = [r for r in recent if r["_key"] not in seen]

    if new_recent and alert_email:
        body_lines = [
            f"{len(new_recent)} new negative review(s) (1-2 star) in the last {alert_lookback_hours}h for '{location_label}'.",
            "",
            "Personal details have been stripped where detected. Log in to the dashboard to respond.",
            "",
        ]
        for r in new_recent[:5]:
            if has_text(r):
                detail = redact_pii(r["text"])[:200]
            else:
                detail = "star rating only, no written comment"
            body_lines.append(f"- {r['rating']}★ ({r['review_date']}): {detail}")

        alert_sent = send_email(
            to_email=alert_email,
            subject=f"⚠️ {len(new_recent)} new negative review(s) - {location_label}",
            body="\n".join(body_lines),
        )
        if alert_sent:
            with _alerted_lock:
                _alerted.setdefault(alert_email, set()).update(r["_key"] for r in new_recent)

    items = []
    for r in shown:
        written = has_text(r)
        topics = []
        if written:
            topics = sorted((t for t in terms_for_text(r["text"]) if t in rank), key=lambda t: rank[t])[:3]
        items.append({
            "rating": r["rating"],
            "review_date": r["review_date"],
            "has_text": written,
            "source": r.get("source", "google"),
            # Author name is dropped entirely; text is best-effort scrubbed
            # of emails/phone numbers/order numbers before display.
            "redacted_text": redact_pii(r["text"]) if written else "",
            "sentiment": round(score_sentiment(r["text"]), 2) if written else None,
            "topics": topics,
        })

    return {
        "negative_reviews": items,
        "recent_count": len(recent),
        "alert_sent": alert_sent,
        "summary": summary,
    }
