"""Written reviews that have no star rating (Uber Eats).

They are shown with your reviews and read for tone, but they are NEVER mixed into star ratings,
review totals, trends, or any other star-based number. Their tone uses the same scorer as web mentions."""
import hashlib
from typing import List

from analysis.pii import redact_pii
from analysis.sentiment import score_sentiment

LABELS = {"ubereats": "Uber Eats"}
DOMAINS = {"ubereats": "ubereats.com"}


def build_unrated(source: str, reviews: List[dict]) -> dict:
    items = []
    for r in reviews:
        text = redact_pii(r["text"])[:800]
        items.append({
            "key": hashlib.sha1(f"{source}|{r.get('datetime_utc')}|{r.get('author')}|{r['text'][:80]}".encode("utf-8")).hexdigest(),
            "source": source, "rating": None, "date": r.get("datetime_utc"), "text": text, "has_text": True,
            "url": r.get("url"), "domain": DOMAINS.get(source, source), "category": "delivery",
            "sentiment": round(score_sentiment(r["text"]), 2),
        })
    scores = [i["sentiment"] for i in items]
    ratings = [r.get("store_rating") for r in reviews if r.get("store_rating") is not None]
    counts = [r.get("store_ratings") for r in reviews if r.get("store_ratings") is not None]
    return {
        "source": source, "label": LABELS.get(source, source), "items": items,
        "summary": {"count": len(items), "avg_sentiment": round(sum(scores) / len(scores), 3) if scores else None,
                    "negative_count": sum(1 for s in scores if s <= -0.25), "positive_count": sum(1 for s in scores if s >= 0.25)},
        "store_rating": ratings[0] if ratings else None,        # the store's own overall rating on that app
        "store_ratings": counts[0] if counts else None,
    }
