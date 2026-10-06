from typing import List


def has_text(review: dict) -> bool:
    """True if the review has a written comment (not just a star rating)."""
    return bool((review.get("text") or "").strip())


def text_reviews(reviews: List[dict]) -> List[dict]:
    return [r for r in reviews if has_text(r)]
