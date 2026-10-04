from datetime import datetime, timedelta, timezone

from dateutil import parser as date_parser

from analysis.outscraper_client import fetch_reviews
from analysis.pii import redact_pii
from email_alerts import send_email

NEGATIVE_RATING_THRESHOLD = 2  # 1-2 star reviews are treated as "negative"


def _parse_dt(value):
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def build_negative_reviews(
    search_query: str,
    review_limit: int = 300,
    lookback_days: int = 30,
    max_reviews: int = 20,
    alert_email: str | None = None,
    alert_lookback_hours: int = 24,
) -> dict:
    reviews = fetch_reviews(search_query, review_limit)
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    negative = []
    for r in reviews:
        if r["rating"] > NEGATIVE_RATING_THRESHOLD:
            continue
        dt = _parse_dt(r["datetime_utc"])
        if dt is None or dt < cutoff:
            continue
        negative.append({
            "rating": r["rating"],
            "review_date": r["datetime_utc"],
            # Author name is dropped entirely; review text is best-effort
            # scrubbed of emails/phone numbers/order numbers before display.
            "redacted_text": redact_pii(r["text"]),
            "_dt": dt,
        })

    negative.sort(key=lambda r: r["_dt"], reverse=True)
    negative = negative[:max_reviews]
    for r in negative:
        del r["_dt"]

    # Alert only on reviews from the last `alert_lookback_hours` - avoids
    # re-notifying about the same old negative reviews every time someone
    # opens the dashboard.
    alert_cutoff = datetime.now(timezone.utc) - timedelta(hours=alert_lookback_hours)
    recent_count = sum(
        1 for r in negative
        if _parse_dt(r["review_date"]) and _parse_dt(r["review_date"]) >= alert_cutoff
    )

    alert_sent = False
    if recent_count > 0 and alert_email:
        body_lines = [
            f"{recent_count} new negative review(s) (1-2 star) in the last {alert_lookback_hours}h for '{search_query}'.",
            "",
            "Personal details have been stripped where detected. Log in to the dashboard to respond.",
            "",
        ]
        for r in negative[:5]:
            body_lines.append(f"- {r['rating']}★ ({r['review_date']}): {r['redacted_text'][:200]}")

        alert_sent = send_email(
            to_email=alert_email,
            subject=f"⚠️ {recent_count} new negative review(s) - {search_query}",
            body="\n".join(body_lines),
        )

    return {
        "negative_reviews": negative,
        "recent_count": recent_count,
        "alert_sent": alert_sent,
    }
