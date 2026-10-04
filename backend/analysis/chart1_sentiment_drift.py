from collections import defaultdict
from datetime import datetime, timedelta
from typing import List

from dateutil import parser as date_parser

from analysis.outscraper_client import dominant_tiers, fetch_reviews
from analysis.sentiment import DRIFT_PHRASES, contains_any_phrase, score_sentiment
from analysis.topics import top_keywords


def _parse_dt(value):
    if not value:
        return None
    try:
        return date_parser.parse(value)
    except (ValueError, TypeError):
        return None


def _week_start(dt: datetime) -> str:
    start = dt - timedelta(days=dt.weekday())
    return start.strftime("%Y-%m-%d")


def build_sentiment_drift(search_query: str, review_limit: int = 300) -> dict:
    reviews = fetch_reviews(search_query, review_limit)
    if not reviews:
        return {"dominant_tiers": [], "weekly": [], "drift_alerts": []}

    tiers = dominant_tiers(reviews, top_n=3)

    # Bucket reviews by week
    weeks: dict[str, list[dict]] = defaultdict(list)
    for r in reviews:
        dt = _parse_dt(r["datetime_utc"])
        if dt is None:
            continue
        weeks[_week_start(dt)].append(r)

    weekly_rows = []
    drift_alerts = []
    sorted_weeks = sorted(weeks.keys())

    prev_tier1_count = None
    prev_other_count = None

    for week in sorted_weeks:
        week_reviews = weeks[week]
        counts = {tier: 0 for tier in tiers}
        for r in week_reviews:
            if r["rating"] in counts:
                counts[r["rating"]] += 1

        ratings = [r["rating"] for r in week_reviews]
        rolling_avg = round(sum(ratings) / len(ratings), 2) if ratings else None

        # Text-sentiment layer (VADER), separate from star-rating averages -
        # catches tone shifts that a flat star average can mask.
        texts = [r["text"] for r in week_reviews]
        sentiment_scores = [score_sentiment(t) for t in texts]
        avg_sentiment = round(sum(sentiment_scores) / len(sentiment_scores), 3) if sentiment_scores else 0.0
        week_top_words = top_keywords(texts, top_n=6)

        weekly_rows.append({
            "week_start": week,
            "counts": counts,
            "rolling_avg_rating": rolling_avg,
            "total_reviews": len(week_reviews),
            "avg_sentiment": avg_sentiment,
            "top_words": week_top_words,
        })

        # Drift detection: dominant #1 volume falls while #2/#3 rises, with
        # corroborating "used to be" / "formula change" style language in the
        # lower-tier reviews that week.
        if len(tiers) >= 2:
            tier1, tier2 = tiers[0], tiers[1]
            tier1_count = counts.get(tier1, 0)
            other_count = sum(counts.get(t, 0) for t in tiers[1:])

            if prev_tier1_count is not None:
                tier1_dropped = tier1_count < prev_tier1_count
                others_rose = other_count > prev_other_count
                lower_tier_reviews = [r for r in week_reviews if r["rating"] in tiers[1:]]
                has_drift_language = any(
                    contains_any_phrase(r["text"], DRIFT_PHRASES) for r in lower_tier_reviews
                )

                if tier1_dropped and others_rose and has_drift_language:
                    drift_alerts.append({
                        "week_start": week,
                        "message": (
                            f"Dominant #1 ({tier1}★) volume dropped while lower tiers rose, "
                            f"alongside 'used to be' / 'formula change' style language. "
                            f"Overall average rating may still look flat this week."
                        ),
                    })

            prev_tier1_count = tier1_count
            prev_other_count = other_count

    return {
        "dominant_tiers": tiers,
        "weekly": weekly_rows,
        "drift_alerts": drift_alerts,
    }
