"""The single analysis pipeline, shared by the one-business dashboard and the
corporate (multi-location) features, so they can never drift apart."""
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException

from analysis.chart1_sentiment_drift import build_sentiment_drift
from analysis.chart2_wait_time_heatmap import build_wait_summary, build_wait_time_heatmap
from analysis.chart3_competitor_share import build_competitor_share
from analysis.insights import build_revenue_signals, trim_signals_for_preview
from analysis.mentions import build_mentions, mention_signals
from analysis.mentions_client import fetch_mentions_with_meta
from analysis.negative_reviews import build_negative_reviews, negative_summary
from analysis.outscraper_client import fetch_reviews_with_notes, latest_review_date
from analysis.platforms import build_platform_comparison
from analysis.review_list import build_review_list
from analysis.review_utils import text_reviews
from analysis.trends import build_trends, trim_for_preview
from analysis.yelp_client import fetch_yelp_reviews_with_meta


def pull_reviews(location: str, yelp_url: Optional[str], months: int, want_yelp: bool):
    """One pull per platform. Returns (reviews_by_source, cached_flags, notes, fresh)
    where `fresh` is how many reviews were actually bought (0 when served from cache)."""
    google_reviews, google_cached, google_notes = fetch_reviews_with_notes(location, months)
    reviews_by_source = {"google": google_reviews}
    cached_flags = [google_cached]
    fresh = {"google": 0 if google_cached else len(google_reviews)}
    notes: List[str] = list(google_notes)

    if want_yelp:
        if yelp_url:
            try:
                yelp_reviews, yelp_cached, yelp_notes = fetch_yelp_reviews_with_meta(yelp_url, months)
                reviews_by_source["yelp"] = yelp_reviews
                cached_flags.append(yelp_cached)
                fresh["yelp"] = 0 if yelp_cached else len(yelp_reviews)
                notes.extend(yelp_notes)
            except HTTPException as exc:
                # A Yelp problem must not take down the Google analysis.
                notes.append(f"Yelp reviews couldn't be loaded, so this analysis uses Google only. ({exc.detail})")
        else:
            notes.append("Add your Yelp page link to include Yelp reviews.")
    return reviews_by_source, cached_flags, notes, fresh


def pull_mentions(terms: str, months: int) -> dict:
    """One web-search pull (two searches). A failure never breaks the analysis."""
    try:
        items, cached, notes = fetch_mentions_with_meta(terms, months)
        return {"items": items, "terms": terms, "notes": notes, "cached": cached, "failed": False}
    except HTTPException as exc:
        return {"items": [], "terms": terms, "failed": True, "cached": False,
                "notes": [f"Internet mentions couldn't be loaded. ({exc.detail})"]}


def assemble(
    reviews_by_source: Dict[str, List[dict]],
    cached_flags: List[bool],
    notes: List[str],
    *,
    view: str,
    months: int,
    location: str,
    paid: bool,
    avg_order_value: float = 35.0,
    reviews_to_customers_multiplier: float = 20.0,
    alert_email: Optional[str] = None,
    competitors: Optional[List[dict]] = None,
    mentions: Optional[dict] = None,
) -> dict:
    """Builds every panel from reviews that were already pulled (no scraping here)."""
    view = view if (view == "combined" or view in reviews_by_source) else "combined"
    if view == "combined":
        reviews = [r for rs in reviews_by_source.values() for r in rs]
    else:
        reviews = reviews_by_source[view]

    written = len(text_reviews(reviews))
    result = {
        "meta": {
            "reviews_analyzed": len(reviews),
            "reviews_with_text": written,
            "reviews_star_only": len(reviews) - written,
            "months": months,
            "latest_review_date": latest_review_date(reviews),
            "from_cache": all(cached_flags),
            "view": view,
            "sources": list(reviews_by_source.keys()),
            "by_source": {
                src: {"reviews": len(rs), "with_text": len(text_reviews(rs))}
                for src, rs in reviews_by_source.items()
            },
            "notes": notes,
        },
        "sentiment_drift": build_sentiment_drift(reviews),
        "wait_time_heatmap": None,
        "negative_reviews": None,
        "trends": None,
        "signals": None,
        "competitors": None,
        "platforms": None,
        # Free-tier "taste": language findings only, no charts or review text.
        "wait_time_preview": None,
        "negative_preview": None,
        "review_list": None,
        "mentions": None,
    }

    if paid:
        # Time of day is only meaningful for Google (other platforms may give just a date).
        google_in_view = [r for r in reviews if r.get("source", "google") == "google"]
        result["wait_time_heatmap"] = build_wait_time_heatmap(
            google_in_view, avg_order_value, reviews_to_customers_multiplier
        )
        result["negative_reviews"] = build_negative_reviews(reviews, location, alert_email=alert_email)
        result["trends"] = build_trends(reviews)
        result["signals"] = build_revenue_signals(reviews)
        result["platforms"] = build_platform_comparison(reviews_by_source)
        result["review_list"] = build_review_list(reviews)

        # Internet mentions (news, blogs, forums, social): analyzed alongside the reviews, and a
        # complaint rising in reviews is checked against what the web is saying.
        if mentions is not None:
            trends = result["trends"] or {}
            negative_topics = [t["term"] for t in trends.get("rising", []) if t.get("tone") == "negative"][:6] \
                if trends.get("status") == "ok" else []
            result["mentions"] = build_mentions(mentions["items"], mentions["terms"], negative_topics, mentions.get("failed", False))
            result["mentions"]["notes"] = mentions.get("notes", [])
            if result["signals"].get("status") == "ok":
                result["signals"]["signals"].extend(mention_signals(result["mentions"]))

        # Competitors compare Google to Google: your own Google reviews are reused
        # (no extra pull); each competitor is one extra pull.
        if competitors:
            businesses = [{"name": "Your Business", "search_query": location}] + competitors
            result["competitors"] = build_competitor_share(
                businesses, months, own_reviews=reviews_by_source["google"]
            )
    else:
        result["signals"] = trim_signals_for_preview(build_revenue_signals(reviews))
        result["trends"] = trim_for_preview(build_trends(reviews))
        result["wait_time_preview"] = build_wait_summary(reviews)
        result["negative_preview"] = negative_summary(reviews)

    return result
