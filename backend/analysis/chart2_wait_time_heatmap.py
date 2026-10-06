from collections import Counter, defaultdict
from typing import List

from dateutil import parser as date_parser

from analysis.outscraper_client import dominant_tiers
from analysis.pii import redact_pii
from analysis.review_utils import has_text, text_reviews
from analysis.sentiment import WAIT_TIME_PHRASES, contains_any_phrase

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# 2-hour buckets from 9am to 11pm, matching a typical service window.
HOUR_BUCKETS = [(h, h + 2) for h in range(9, 23, 2)]

MAX_TEXT = 500  # characters of review text sent to the browser


def _parse_dt(value):
    if not value:
        return None
    try:
        return date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None


def _hour_bucket_label(hour: int):
    for start, end in HOUR_BUCKETS:
        if start <= hour < end:
            return f"{start:02d}:00-{end:02d}:00"
    return None


def _grid_hours_label() -> str:
    def part(h):
        return f"{h % 12 or 12}{'am' if h < 12 else 'pm'}"

    return f"{part(HOUR_BUCKETS[0][0])}-{part(HOUR_BUCKETS[-1][1])}"


def _matched_phrases(text: str) -> List[str]:
    lowered = text.lower()
    return [p for p in WAIT_TIME_PHRASES if p in lowered]


def _review_item(r: dict) -> dict:
    """A review as shown on the page: author never included, text scrubbed of
    emails / phone numbers / order numbers (best effort), star-only flagged."""
    text = (r.get("text") or "").strip()
    return {
        "rating": r["rating"],
        "review_date": r["datetime_utc"],
        "has_text": bool(text),
        "text": redact_pii(text)[:MAX_TEXT] if text else "",
        "wait_phrases": _matched_phrases(text) if text else [],
    }


def _wait_scan(reviews: List[dict]):
    """Phrase detection: which reviews talk about waiting / slow service, and
    when (day + hour bucket) they were posted.
    Returns (summary, per-cell mention counts, the mentioning reviews newest first)."""
    mentions = 0
    phrase_counts: Counter = Counter()
    cell_mentions: Counter = Counter()
    mention_rows = []

    for r in reviews:
        text = (r.get("text") or "").strip()
        matched = _matched_phrases(text) if text else []
        if not matched:
            continue
        mentions += 1
        phrase_counts.update(matched)
        dt = _parse_dt(r["datetime_utc"])
        bucket = _hour_bucket_label(dt.hour) if dt else None
        day = DAY_ORDER[dt.weekday()] if dt else None
        if dt and bucket:
            cell_mentions[(day, bucket)] += 1
        item = _review_item(r)
        item["day"] = day if bucket else None   # None = posted outside the grid hours
        item["hour"] = bucket
        mention_rows.append((dt, item))

    mention_rows.sort(key=lambda x: (x[0] is not None, x[0]), reverse=True)

    hotspot = None
    if cell_mentions:
        (day, hour), count = max(cell_mentions.items(), key=lambda kv: (kv[1], kv[0]))
        hotspot = {"day": day, "hour": hour, "mentions": count}

    # Only written reviews can mention waiting, so that's the fair denominator.
    written = len(text_reviews(reviews))
    summary = {
        "mention_count": mentions,
        "total_reviews": written,
        "share_pct": round(100 * mentions / written, 1) if written else 0.0,
        "top_phrases": [{"phrase": p, "count": c} for p, c in phrase_counts.most_common(3)],
        "hotspot": hotspot,
    }
    return summary, cell_mentions, [item for _, item in mention_rows]


def build_wait_summary(reviews: List[dict]) -> dict:
    """Just the language findings (used as the free-tier teaser)."""
    return _wait_scan(reviews)[0]


def build_wait_time_heatmap(
    reviews: List[dict],
    avg_order_value: float = 35.0,
    reviews_to_customers_multiplier: float = 20.0,
) -> dict:
    """
    Takes an already-fetched review list (no scraping happens here).

    `reviews_to_customers_multiplier` is a rough assumption for how many real
    customers correspond to each review left. The dollar figure is a
    heuristic estimate, not a certified financial number.

    Every grid cell carries the exact reviews behind it, and `wait_reviews`
    lists every review that matched a wait phrase, so nothing is a black box.
    """
    if not reviews:
        return {
            "dominant_tiers": [], "matrix": [], "revenue_drag": [], "summary": None,
            "wait_reviews": [], "wait_phrases": WAIT_TIME_PHRASES, "coverage": None,
        }

    summary, cell_mentions, mention_items = _wait_scan(reviews)

    tiers = dominant_tiers(reviews, top_n=3)
    tier1 = tiers[0] if tiers else None

    cells: dict[tuple[str, str], list] = defaultdict(list)
    for r in reviews:
        dt = _parse_dt(r["datetime_utc"])
        if dt is None:
            continue
        bucket = _hour_bucket_label(dt.hour)
        if bucket is None:
            continue
        cells[(DAY_ORDER[dt.weekday()], bucket)].append((dt, r))

    placed = sum(len(v) for v in cells.values())

    total_tier1 = sum(1 for r in reviews if r["rating"] == tier1) if tier1 else 0
    baseline_share = total_tier1 / len(reviews) if reviews else 0

    matrix = []
    revenue_drag = []

    for day in DAY_ORDER:
        for bucket_start, bucket_end in HOUR_BUCKETS:
            bucket_label = f"{bucket_start:02d}:00-{bucket_end:02d}:00"
            entries = sorted(cells.get((day, bucket_label), []), key=lambda e: e[0], reverse=True)
            cell_reviews = [r for _, r in entries]
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
                "wait_mentions": cell_mentions.get((day, bucket_label), 0),
                "reviews": [_review_item(r) for r in cell_reviews],
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
                    revenue_drag.append({
                        "day": day,
                        "hour": bucket_label,
                        "estimated_dollars": round(estimated_customers * avg_order_value, 2),
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
        "summary": summary,
        "wait_reviews": mention_items,
        "wait_phrases": WAIT_TIME_PHRASES,
        "coverage": {
            "total_reviews": len(reviews),
            "on_grid": placed,
            "off_grid": len(reviews) - placed,
            "grid_hours": _grid_hours_label(),
        },
    }
