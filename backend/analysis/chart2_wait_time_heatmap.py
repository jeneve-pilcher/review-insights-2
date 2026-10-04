from collections import defaultdict
from datetime import datetime

from dateutil import parser as date_parser

from analysis.outscraper_client import dominant_tiers, fetch_reviews
from analysis.sentiment import WAIT_TIME_PHRASES, contains_any_phrase

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# 2-hour buckets from 9am to 11pm, matching a typical service window.
HOUR_BUCKETS = [(h, h + 2) for h in range(9, 23, 2)]


def _parse_dt(value):
    if not value:
        return None
    try:
        return date_parser.parse(value)
    except (ValueError, TypeError):
        return None


def _hour_bucket_label(hour: int) -> str | None:
    for start, end in HOUR_BUCKETS:
        if start <= hour < end:
            return f"{start:02d}:00-{end:02d}:00"
    return None


def build_wait_time_heatmap(
    search_query: str,
    review_limit: int = 300,
    avg_order_value: float = 35.0,
    reviews_to_customers_multiplier: float = 20.0,
) -> dict:
    """
    `reviews_to_customers_multiplier` is a rough assumption for how many
    actual customers correspond to each review left (most customers don't
    leave a review). Adjust it to roughly match your business's real
    review-to-visit ratio for a more realistic dollar estimate - this is a
    heuristic, not a certified financial figure.
    """
    reviews = fetch_reviews(search_query, review_limit)
    if not reviews:
        return {"dominant_tiers": [], "matrix": [], "revenue_drag": []}

    tiers = dominant_tiers(reviews, top_n=3)
    tier1 = tiers[0] if tiers else None

    cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in reviews:
        dt = _parse_dt(r["datetime_utc"])
        if dt is None:
            continue
        bucket = _hour_bucket_label(dt.hour)
        if bucket is None:
            continue
        day = DAY_ORDER[dt.weekday()]
        cells[(day, bucket)].append(r)

    # Baseline tier-1 share across the whole dataset, to detect cells that
    # underperform their normal mix.
    total_tier1 = sum(1 for r in reviews if r["rating"] == tier1) if tier1 else 0
    baseline_share = total_tier1 / len(reviews) if reviews else 0

    matrix = []
    revenue_drag = []

    for day in DAY_ORDER:
        for bucket_start, bucket_end in HOUR_BUCKETS:
            bucket_label = f"{bucket_start:02d}:00-{bucket_end:02d}:00"
            cell_reviews = cells.get((day, bucket_label), [])
            total_in_cell = len(cell_reviews)

            tier_counts = {t: 0 for t in tiers}
            for r in cell_reviews:
                if r["rating"] in tier_counts:
                    tier_counts[r["rating"]] += 1

            tier_pct = {
                t: (round(100 * tier_counts[t] / total_in_cell, 1) if total_in_cell else 0)
                for t in tiers
            }

            matrix.append({
                "day": day,
                "hour": bucket_label,
                "review_count": total_in_cell,
                "tier_pct": tier_pct,
            })

            if total_in_cell >= 3 and tier1 is not None:
                actual_share = tier_counts[tier1] / total_in_cell
                has_wait_language = any(
                    contains_any_phrase(r["text"], WAIT_TIME_PHRASES) for r in cell_reviews
                )
                shortfall_share = baseline_share - actual_share

                if shortfall_share > 0.15 and has_wait_language:
                    shortfall_reviews = shortfall_share * total_in_cell
                    estimated_customers = shortfall_reviews * reviews_to_customers_multiplier
                    estimated_dollars = round(estimated_customers * avg_order_value, 2)

                    revenue_drag.append({
                        "day": day,
                        "hour": bucket_label,
                        "estimated_dollars": estimated_dollars,
                        "note": (
                            f"{tier1}★ share dropped to {round(actual_share * 100, 1)}% "
                            f"(baseline {round(baseline_share * 100, 1)}%), with wait-time "
                            f"language present. Estimate assumes "
                            f"{reviews_to_customers_multiplier:.0f} customers per review."
                        ),
                    })

    return {
        "dominant_tiers": tiers,
        "matrix": matrix,
        "revenue_drag": revenue_drag,
    }
