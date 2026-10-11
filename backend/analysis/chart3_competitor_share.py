from analysis.categorize import THEME_LABELS, classify_themes
from analysis.outscraper_client import dominant_tiers, fetch_reviews_with_meta
from analysis.review_utils import has_text
from analysis.topics import top_keywords


def _business_breakdown(name: str, search_query: str, months: int, reviews=None) -> dict:
    # `reviews` is passed in for the account's own business (already pulled for
    # every other panel); competitors are fetched here, one pull each.
    fresh = 0                       # reviews actually bought for this business (0 if cached or passed in)
    if reviews is None:
        reviews, cached = fetch_reviews_with_meta(search_query, months)
        fresh = 0 if cached else len(reviews)
    if not reviews:
        return {"name": name, "dominant_tiers": [], "tiers": [], "fresh_reviews": fresh}

    # Tiers come from ALL reviews (star-only included). Themes can only be read
    # from written reviews, and only the top-3 tiers are ever shown, so only
    # those get classified.
    tiers = dominant_tiers(reviews, top_n=3)
    relevant_text = [r for r in reviews if r["rating"] in tiers and has_text(r)]
    theme_matches = classify_themes([r["text"] for r in relevant_text])
    for r, themes in zip(relevant_text, theme_matches):
        r["themes"] = themes

    tier_rows = []
    for tier in tiers:
        tier_all = [r for r in reviews if r["rating"] == tier]
        tier_text = [r for r in relevant_text if r["rating"] == tier]
        total_text = len(tier_text)

        theme_counts = {label: 0 for label in THEME_LABELS}
        for r in tier_text:
            for theme in r["themes"]:
                theme_counts[theme] += 1

        # Percentages are "share of this tier's WRITTEN reviews", because a
        # star-only review has no words to assign a theme to.
        theme_pct = {
            label: (round(100 * count / total_text, 1) if total_text else 0)
            for label, count in theme_counts.items()
        }

        tier_rows.append({
            "tier": tier,
            "total_reviews": len(tier_all),
            "text_reviews": total_text,
            "theme_pct": theme_pct,
            "top_keywords": top_keywords([r["text"] for r in tier_text]),
        })

    return {"name": name, "dominant_tiers": tiers, "tiers": tier_rows, "fresh_reviews": fresh}


def build_competitor_share(businesses: list[dict], months: int = 6, own_reviews=None) -> dict:
    """
    `businesses` is a list of {"name": str, "search_query": str}; the first
    entry is the account's own business. When `own_reviews` is given, that
    business uses it directly (no second pull); every competitor costs one pull.
    """
    results = []
    for i, b in enumerate(businesses):
        reviews = [dict(r) for r in own_reviews] if (i == 0 and own_reviews is not None) else None
        results.append(_business_breakdown(b["name"], b["search_query"], months, reviews))
    return {"businesses": results, "fresh_reviews": sum(r.get("fresh_reviews", 0) for r in results)}
