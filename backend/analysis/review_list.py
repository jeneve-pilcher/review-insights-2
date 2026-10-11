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


def build_review_list(reviews: List[dict], web_items: Optional[List[dict]] = None, limit: int = MAX_ITEMS,
                      unrated: Optional[List[dict]] = None) -> dict:
    """Newest first. Author names are never included; emails/phones/order numbers are removed
    from the text (best effort)."""
    entries = []
    for r in reviews:
        text = (r.get("text") or "").strip()
        entries.append((_dt(r.get("datetime_utc")), {
            "key": review_key(r),
            "source": r.get("source", "google"),
            "rating": r["rating"],
            "date": r.get("datetime_utc"),
            "text": redact_pii(text)[:MAX_TEXT] if text else "",
            "has_text": bool(text),
        }))
    # Internet mentions: unrated written items. They can't be replied to here and carry no stars.
    for m in web_items or []:
        text = f"{m['title']}. {m['snippet']}".strip(". ")
        entries.append((_dt(m.get("date")), {
            "key": hashlib.sha1(f"web|{m['url']}".encode("utf-8")).hexdigest(),
            "source": "web",
            "rating": None,
            "date": m.get("date"),
            "text": redact_pii(text)[:MAX_TEXT],
            "has_text": True,
            "url": m["url"],
            "domain": m["domain"],
            "category": m["category"],
            "sentiment": m["sentiment"],
        }))
    # Unrated written reviews from a delivery app (Uber Eats): already shaped, no stars, can't be replied to here.
    for u in unrated or []:
        entries.append((_dt(u.get("date")), u))
    entries.sort(key=lambda e: (e[0] is not None, e[0] or datetime.min), reverse=True)
    items = [e[1] for e in entries[:limit]]
    return {"items": items, "total": len(entries), "shown": len(items)}
