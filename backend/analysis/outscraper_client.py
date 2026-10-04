from typing import List, Optional

from fastapi import HTTPException
from outscraper import OutscraperClient

import config


def fetch_reviews(search_query: str, review_limit: int = 200) -> List[dict]:
    """Fetch and normalize reviews for one business from Outscraper.

    Returns a list of dicts with consistent keys regardless of Outscraper's
    raw field names, so downstream analysis code doesn't need to know about
    the Outscraper API shape.
    """
    api_key = config.require(config.OUTSCRAPER_API_KEY, "OUTSCRAPER_API_KEY")
    client = OutscraperClient(api_key=api_key)

    try:
        results = client.google_maps_business_reviews(
            search_query,
            reviews_limit=review_limit,
            limit=1,
            sort="newest",
            ignore_empty=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error fetching reviews for '{search_query}': {exc}")

    normalized = []
    for place in results:
        for r in (place.get("reviews_data") or []):
            text = r.get("review_text", "")
            if not text or not text.strip():
                continue

            rating = r.get("review_rating")
            try:
                rating = int(round(float(rating)))
            except (TypeError, ValueError):
                continue

            normalized.append({
                "text": text,
                "rating": max(1, min(5, rating)),
                "datetime_utc": r.get("review_datetime_utc"),
                "author": r.get("author_title", "Anonymous"),
            })

    return normalized


def dominant_tiers(reviews: List[dict], top_n: int = 3) -> List[int]:
    """The `top_n` star ratings that occur most often, ordered by frequency."""
    from collections import Counter

    counts = Counter(r["rating"] for r in reviews)
    return [rating for rating, _ in counts.most_common(top_n)]
