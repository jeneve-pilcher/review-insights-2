from analysis.categorize import THEME_LABELS, classify_themes
from analysis.outscraper_client import dominant_tiers, fetch_reviews
from analysis.topics import top_keywords


def _business_breakdown(name: str, search_query: str, review_limit: int) -> dict:
    reviews = fetch_reviews(search_query, review_limit)
    if not reviews:
        return {"name": name, "dominant_tiers": [], "tiers": []}

    tiers = dominant_tiers(reviews, top_n=3)

    texts = [r["text"] for r in reviews]
    theme_matches = classify_themes(texts)
    for r, themes in zip(reviews, theme_matches):
        r["themes"] = themes

    tier_rows = []
    for tier in tiers:
        tier_reviews = [r for r in reviews if r["rating"] == tier]
        total = len(tier_reviews)

        theme_counts = {label: 0 for label in THEME_LABELS}
        for r in tier_reviews:
            for theme in r["themes"]:
                theme_counts[theme] += 1

        theme_pct = {
            label: (round(100 * count / total, 1) if total else 0)
            for label, count in theme_counts.items()
        }

        tier_rows.append({
            "tier": tier,
            "total_reviews": total,
            "theme_pct": theme_pct,
            "top_keywords": top_keywords([r["text"] for r in tier_reviews]),
        })

    return {"name": name, "dominant_tiers": tiers, "tiers": tier_rows}


def build_competitor_share(businesses: list[dict], review_limit: int = 200) -> dict:
    """
    `businesses` is a list of {"name": str, "search_query": str}, where the
    first entry is conventionally the user's own business.
    """
    results = [
        _business_breakdown(b["name"], b["search_query"], review_limit)
        for b in businesses
    ]
    return {"businesses": results}
