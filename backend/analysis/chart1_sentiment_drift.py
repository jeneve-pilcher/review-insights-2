from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from dateutil import parser as date_parser

from analysis.outscraper_client import dominant_tiers
from analysis.review_utils import has_text, text_reviews
from analysis.sentiment import DRIFT_PHRASES, contains_any_phrase, score_sentiment
from analysis.topics import top_keywords


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


def _week_start(dt: datetime) -> str:
    start = dt - timedelta(days=dt.weekday())
    return start.strftime("%Y-%m-%d")


def _weighted_sentiment(rows: List[dict]):
    """Average tone weighted by how many WRITTEN reviews each week had."""
    usable = [r for r in rows if r["avg_sentiment"] is not None and r["text_reviews"]]
    total = sum(r["text_reviews"] for r in usable)
    if not total:
        return None
    return round(sum(r["avg_sentiment"] * r["text_reviews"] for r in usable) / total, 3)


def _language_summary(written: List[dict], weekly_rows: List[dict]) -> dict:
    """Plain facts from the review text, for the 'Language read' box."""
    hits: Counter = Counter()
    for r in written:
        lowered = r["text"].lower()
        for phrase in DRIFT_PHRASES:
            if phrase in lowered:
                hits[phrase] += 1

    recent = earlier = None
    if len(weekly_rows) >= 6:
        recent = _weighted_sentiment(weekly_rows[-4:])
        earlier = _weighted_sentiment(weekly_rows[:-4])

    return {
        "reviews": len(written),
        "overall_sentiment": _weighted_sentiment(weekly_rows),
        "recent_sentiment": recent,
        "earlier_sentiment": earlier,
        "drift_phrase_hits": [{"phrase": p, "count": c} for p, c in hits.most_common(3)],
        "top_words": top_keywords([r["text"] for r in written], top_n=8),
    }


def _velocity(reviews: List[dict]) -> Optional[dict]:
    """Review pace, freshness and star mix across ALL reviews (star-only
    included) - the same inputs Google's own count and score are built from."""
    dated = []
    for r in reviews:
        dt = _parse_dt(r["datetime_utc"])
        if dt is not None:
            dated.append(dt)
    if not dated:
        return None

    dated.sort()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    recent_cut = now - timedelta(days=28)

    recent_count = sum(1 for dt in dated if dt >= recent_cut)
    earlier_count = len(dated) - recent_count
    earlier_days = (recent_cut - dated[0]).days
    earlier_per_week = round(earlier_count / (earlier_days / 7), 1) if earlier_days >= 14 else None

    star_counts = {s: 0 for s in range(1, 6)}
    for r in reviews:
        star_counts[r["rating"]] += 1

    return {
        "reviews": len(reviews),
        "text_reviews": len(text_reviews(reviews)),
        "avg_rating": round(sum(r["rating"] for r in reviews) / len(reviews), 2),
        "star_counts": star_counts,
        "recent_per_week": round(recent_count / 4, 1),
        "earlier_per_week": earlier_per_week,
        "last_review_date": dated[-1].strftime("%Y-%m-%d"),
        "days_since_last": max(0, (now - dated[-1]).days),
    }


def build_sentiment_drift(reviews: List[dict]) -> dict:
    """Takes an already-fetched review list (no scraping happens here).

    Volume, star tiers and the rolling rating use EVERY review (star-only
    included). Tone, keywords and phrase detection use written reviews only."""
    if not reviews:
        return {"dominant_tiers": [], "weekly": [], "drift_alerts": [], "nlp": None, "velocity": None}

    tiers = dominant_tiers(reviews, top_n=3)

    weeks: dict[str, list[dict]] = defaultdict(list)
    for r in reviews:
        dt = _parse_dt(r["datetime_utc"])
        if dt is None:
            continue
        weeks[_week_start(dt)].append(r)

    weekly_rows = []
    drift_alerts = []
    prev_tier1_count = None
    prev_other_count = None

    for week in sorted(weeks.keys()):
        week_reviews = weeks[week]
        counts = {tier: 0 for tier in tiers}
        for r in week_reviews:
            if r["rating"] in counts:
                counts[r["rating"]] += 1

        ratings = [r["rating"] for r in week_reviews]
        rolling_avg = round(sum(ratings) / len(ratings), 2) if ratings else None

        texts = [r["text"] for r in week_reviews if has_text(r)]
        sentiment_scores = [score_sentiment(t) for t in texts]
        # None (not 0) when nobody wrote anything that week, so the chart shows
        # a gap instead of a fake "neutral" bar.
        avg_sentiment = round(sum(sentiment_scores) / len(sentiment_scores), 3) if sentiment_scores else None

        weekly_rows.append({
            "week_start": week,
            "counts": counts,
            "rolling_avg_rating": rolling_avg,
            "total_reviews": len(week_reviews),
            "text_reviews": len(texts),
            "avg_sentiment": avg_sentiment,
            "top_words": top_keywords(texts, top_n=6) if texts else [],
        })

        if len(tiers) >= 2:
            tier1 = tiers[0]
            tier1_count = counts.get(tier1, 0)
            other_count = sum(counts.get(t, 0) for t in tiers[1:])

            if prev_tier1_count is not None:
                lower_tier_reviews = [r for r in week_reviews if r["rating"] in tiers[1:]]
                has_drift_language = any(
                    contains_any_phrase(r["text"], DRIFT_PHRASES) for r in lower_tier_reviews
                )
                if tier1_count < prev_tier1_count and other_count > prev_other_count and has_drift_language:
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
        "nlp": _language_summary(text_reviews(reviews), weekly_rows),
        "velocity": _velocity(reviews),
    }


# Public alias: review pace, freshness and star mix for any list of reviews.
review_velocity = _velocity
