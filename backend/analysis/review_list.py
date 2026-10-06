"""The reviews themselves, as shown under the analysis, ready for the reply workflow."""
import hashlib
from datetime import datetime, timezone
from typing import List, Optional

from dateutil import parser as date_parser

from analysis.pii import redact_pii

MAX_ITEMS = 600
MAX_TEXT = 800


def review_key(r: dict) -> str:
    """Stable id for a review (the same review always gets the same key)."""
    raw = f"{r.get('source', 'google')}|{r.get('datetime_utc')}|{r['rating']}|{(r.get('text') or '')[:80]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _dt(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def build_review_list(reviews: List[dict], limit: int = MAX_ITEMS) -> dict:
    """Newest first. Author names are never included; emails/phones/order numbers are removed
    from the text (best effort)."""
    ordered = sorted(reviews, key=lambda r: (_dt(r.get("datetime_utc")) is not None, _dt(r.get("datetime_utc")) or datetime.min), reverse=True)
    items = []
    for r in ordered[:limit]:
        text = (r.get("text") or "").strip()
        items.append({
            "key": review_key(r),
            "source": r.get("source", "google"),
            "rating": r["rating"],
            "date": r.get("datetime_utc"),
            "text": redact_pii(text)[:MAX_TEXT] if text else "",
            "has_text": bool(text),
        })
    return {"items": items, "total": len(reviews), "shown": len(items)}
