"""The single analysis pipeline, shared by the one-business dashboard and the
corporate (multi-location) features, so they can never drift apart."""
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException

from analysis.chart1_sentiment_drift import build_sentiment_drift
from analysis.chart2_wait_time_heatmap import build_wait_summary, build_wait_time_heatmap
from analysis.chart3_competitor_share import build_competitor_share
from analysis.insights import build_revenue_signals, trim_signals_for_preview
from analysis.mentions import build_mentions, mention_signals
from analysis.mentions_client import effective_pages, fetch_mentions_with_meta, searches_for
from analysis.negative_reviews import build_negative_reviews, negative_summary
from analysis.outscraper_client import fetch_reviews_with_notes, latest_review_date
from analysis.platforms import build_platform_comparison
from analysis.review_list import build_review_list
from analysis.review_utils import text_reviews
from analysis.trends import build_trends, trim_for_preview
from analysis.delivery_clients import (
    fetch_doordash_reviews_with_meta,
    fetch_grubhub_reviews_with_meta,
    fetch_ubereats_reviews_with_meta,
)
from analysis.opentable_client import fetch_opentable_reviews_with_meta
from analysis.clinical import neutral_copies
from analysis.industries import get_pack, public_pack
from analysis.industry_trends import build_industry_trends
from analysis.subratings import build_subratings
from analysis.unrated import build_unrated
from analysis.yelp_client import fetch_yelp_reviews_with_meta


# Reservation-platform sources (pulled through Apify): source id -> (display name, fetch function)
RESERVATION_SOURCES = {
    "opentable": ("OpenTable", fetch_opentable_reviews_with_meta),
    "doordash": ("DoorDash", fetch_doordash_reviews_with_meta),
    "grubhub": ("Grubhub", fetch_grubhub_reviews_with_meta),
    "ubereats": ("Uber Eats", fetch_ubereats_reviews_with_meta),
}
# Sources whose reviews carry NO star rating. They are kept apart from the rated reviews so they can
# never reach a star-based number.
UNRATED_SOURCES = {"ubereats"}


def pull_reviews(*args, **kwargs):
    """Same as pull_reviews_ext, without the unrated reviews: (reviews_by_source, cached_flags, notes, fresh)."""
    return pull_reviews_ext(*args, **kwargs)[:4]


def pull_reviews_ext(location: str, yelp_url: Optional[str], months: int, want_yelp: bool,
                     others: Optional[Dict[str, Optional[str]]] = None):
    """One pull per platform. Returns (reviews_by_source, cached_flags, notes, fresh, unrated)
    where `fresh` is how many reviews were actually bought (0 when served from cache) and `unrated` maps
    a source with no star ratings (Uber Eats) to its reviews.

    `others` maps a reservation platform ("opentable", "doordash", "grubhub", "ubereats") to its saved page link, or None
    if the person asked for it but hasn't saved one. Only the platforms listed are pulled."""
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

    unrated: Dict[str, list] = {}
    for source, link in (others or {}).items():
        label, fetch = RESERVATION_SOURCES[source]
        if not link:
            notes.append(f"Add your {label} page link to include {label} reviews.")
            continue
        try:
            reviews, cached, source_notes = fetch(link, months)
            if source in UNRATED_SOURCES:
                unrated[source] = reviews
            else:
                reviews_by_source[source] = reviews
            cached_flags.append(cached)
            fresh[source] = 0 if cached else len(reviews)
            notes.extend(source_notes)
        except HTTPException as exc:
            # One platform failing must not take down the rest of the analysis.
            notes.append(f"{label} reviews couldn't be loaded, so this analysis skips them. ({exc.detail})")
    return reviews_by_source, cached_flags, notes, fresh, unrated


def pull_mentions(terms: str, months: int, pages: Optional[int] = None) -> dict:
    """One web-search pull: 2 searches x `pages` pages, each billable. A failure never breaks the analysis.
    `searches` is how many billable searches this pull actually made (0 if served from cache)."""
    try:
        items, cached, notes = fetch_mentions_with_meta(terms, months, pages)
        return {"items": items, "terms": terms, "notes": notes, "cached": cached, "failed": False,
                "pages": effective_pages(pages), "searches": 0 if cached else searches_for(terms, pages)}
    except HTTPException as exc:
        return {"items": [], "terms": terms, "failed": True, "cached": False, "pages": effective_pages(pages), "searches": 0,
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
    unrated: Optional[Dict[str, list]] = None,
    industry: Optional[str] = None,
) -> dict:
    """Builds every panel from reviews that were already pulled (no scraping here)."""
    view = view if (view == "combined" or view in reviews_by_source) else "combined"
    if view == "combined":
        reviews = [r for rs in reviews_by_source.values() for r in rs]
    else:
        reviews = reviews_by_source[view]

    # Internet mentions are unrated written items. They join the language analysis, the review list and
    # the platform comparison, but are NEVER counted as star reviews or mixed into any rating.
    web_items = []
    if paid and mentions is not None:
        web_items = build_mentions(mentions["items"], mentions["terms"], [], mentions.get("failed", False))["items"]

    # Written reviews with no stars (Uber Eats): shown and read for tone, never counted in any star number.
    unrated_built = {}
    if paid:
        unrated_built = {src: build_unrated(src, revs) for src, revs in (unrated or {}).items() if revs}

    # Healthcare: clinical words ("pain", "infection") describe the condition, not the experience, so tone scoring sees
    # neutral copies. The reviews shown and every star number use the originals.
    tone_reviews = neutral_copies(reviews) if get_pack(industry).get("clinical") else reviews

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
        "sentiment_drift": build_sentiment_drift(tone_reviews, web_items, unrated_built),
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
        "industry": None,
    }

    if paid:
        # Time of day is only meaningful for Google (other platforms may give just a date).
        google_in_view = [r for r in reviews if r.get("source", "google") == "google"]
        result["wait_time_heatmap"] = build_wait_time_heatmap(
            google_in_view, avg_order_value, reviews_to_customers_multiplier
        )
        result["negative_reviews"] = build_negative_reviews(reviews, location, alert_email=alert_email)
        result["trends"] = build_trends(tone_reviews)
        result["signals"] = build_revenue_signals(tone_reviews)

        # A complaint rising in reviews is checked against what the web is saying.
        if mentions is not None:
            trends = result["trends"] or {}
            negative_topics = [t["term"] for t in trends.get("rising", []) if t.get("tone") == "negative"][:6] \
                if trends.get("status") == "ok" else []
            result["mentions"] = build_mentions(mentions["items"], mentions["terms"], negative_topics, mentions.get("failed", False))
            result["mentions"]["notes"] = mentions.get("notes", [])
            result["mentions"]["searches"] = mentions.get("searches", 0)
            result["mentions"]["pages"] = mentions.get("pages")
            if result["signals"].get("status") == "ok":
                result["signals"]["signals"].extend(mention_signals(result["mentions"]))
            if web_items:
                result["meta"]["web_mentions"] = len(web_items)
                result["meta"]["by_source"]["web"] = {"reviews": len(web_items), "with_text": len(web_items)}

        if unrated_built:
            result["meta"]["unrated_sources"] = {s: b["summary"]["count"] for s, b in unrated_built.items()}
            for s, b in unrated_built.items():
                result["meta"]["by_source"][s] = {"reviews": b["summary"]["count"], "with_text": b["summary"]["count"]}

        # The industry pack: this industry's themes and graphs. Reads reviews only; changes no star number.
        pack = get_pack(industry)
        result["industry"] = {
            "pack": public_pack(pack),
            "trends": build_industry_trends(reviews, pack),
            "subratings": build_subratings(reviews) if pack.get("subratings") else None,
        }

        result["platforms"] = build_platform_comparison(reviews_by_source, result["mentions"], unrated_built)
        result["review_list"] = build_review_list(reviews, web_items, unrated=[i for b in unrated_built.values() for i in b["items"]])

        # Competitors compare Google to Google: your own Google reviews are reused
        # (no extra pull); each competitor is one extra pull.
        if competitors:
            businesses = [{"name": "Your Business", "search_query": location}] + competitors
            result["competitors"] = build_competitor_share(
                businesses, months, own_reviews=reviews_by_source["google"]
            )
    else:
        result["signals"] = trim_signals_for_preview(build_revenue_signals(tone_reviews))
        result["trends"] = trim_for_preview(build_trends(tone_reviews))
        result["wait_time_preview"] = build_wait_summary(reviews)
        result["negative_preview"] = negative_summary(reviews)

    return result
