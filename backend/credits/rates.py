"""What each billable action costs US (the "rate card"), and the packs customers buy.

Credit is denominated in API-cost dollars: a $5 pack gives $2.00 of credit (markup 2.5), and a run
deducts what it really costs. These are LIST prices, not your invoices: reconcile against your
vendor bills each month and adjust the RATE_* settings if they drift.
"""
import os
from typing import Dict, List, Optional


def _f(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


# Per unit, in US dollars. Defaults come from each vendor's published list price.
GOOGLE_REVIEW = _f("RATE_GOOGLE_REVIEW_USD", 0.003)               # Outscraper: about $3 per 1,000 reviews
YELP_REVIEW = _f("RATE_YELP_REVIEW_USD", 0.003)                   # not confirmed: Google's rate used as a placeholder
OPENTABLE_REVIEW = _f("RATE_OPENTABLE_REVIEW_USD", 0.00129)       # Apify actor: about $1.29 per 1,000 reviews
DOORDASH_REVIEW = _f("RATE_DOORDASH_REVIEW_USD", 0.0006)          # Apify actor: from about $0.60 per 1,000 reviews
UBEREATS_REVIEW = _f("RATE_UBEREATS_REVIEW_USD", 0.0003)          # Apify actor: about $0.30 per 1,000 reviews
GRUBHUB_REVIEW = _f("RATE_GRUBHUB_REVIEW_USD", 0.00499)           # community actor: about $4.99 per 1,000 results
ZOCDOC_RESULT = _f("RATE_ZOCDOC_RESULT_USD", 0.05)                  # Apify pay-per-result Zocdoc actor: about $0.05 per result
APIFY_RUN_START = _f("RATE_APIFY_RUN_START_USD", 0.005)           # a small per-run fee on the DoorDash / Uber Eats actors (amount unconfirmed)
WEB_SEARCH = _f("RATE_WEB_SEARCH_USD", 0.005)                     # Outscraper Google Search: about half a cent
AI_DRAFT = _f("RATE_AI_DRAFT_USD", 0.002)                         # one AI reply draft (real cost is nearer a tenth of a cent)

AI_SUMMARY = _f("RATE_AI_SUMMARY_USD", 0.004)                       # one AI summary of a location's reviews (about 3,000 tokens in, 400 out on a small model)

MARKUP = _f("CREDIT_MARKUP", 2.5)                                 # customer pays $5 for $2.00 of credit
PACK_PRICES = [float(p) for p in os.environ.get("CREDIT_PACK_PRICES", "10,25,50,100").split(",") if p.strip()]


def rates() -> Dict[str, float]:
    return {
        "google_review": GOOGLE_REVIEW, "yelp_review": YELP_REVIEW, "opentable_review": OPENTABLE_REVIEW,
        "web_search": WEB_SEARCH, "ai_draft": AI_DRAFT, "ai_summary": AI_SUMMARY,
        "doordash_review": DOORDASH_REVIEW, "ubereats_review": UBEREATS_REVIEW, "grubhub_review": GRUBHUB_REVIEW,
        "apify_run_start": APIFY_RUN_START, "zocdoc_result": ZOCDOC_RESULT,
    }


def packs() -> List[dict]:
    """The credit packs on sale. The credit is always price / markup, computed here (never by the browser)."""
    return [{"id": f"p{int(p) if p == int(p) else str(p).replace('.', '_')}", "price_usd": round(p, 2),
             "credit_usd": round(p / MARKUP, 2)} for p in PACK_PRICES]


def find_pack(pack_id: str) -> Optional[dict]:
    return next((p for p in packs() if p["id"] == pack_id), None)


def cost_breakdown(fresh: Optional[Dict[str, int]] = None, searches: int = 0,
                   competitor_reviews: int = 0, drafts: int = 0, summaries: int = 0) -> dict:
    """The API cost of what was actually bought. `fresh` = reviews pulled this time per source (0 when the
    result came from the 30-minute cache, which costs nothing)."""
    fresh = fresh or {}
    lines = []

    def add(label: str, units: int, unit_usd: float):
        if units and units > 0:
            lines.append({"label": label, "units": int(units), "unit_usd": unit_usd, "cost_usd": round(units * unit_usd, 6)})

    add("Google reviews", fresh.get("google", 0), GOOGLE_REVIEW)
    add("Yelp reviews", fresh.get("yelp", 0), YELP_REVIEW)
    add("OpenTable reviews", fresh.get("opentable", 0), OPENTABLE_REVIEW)
    add("DoorDash reviews", fresh.get("doordash", 0), DOORDASH_REVIEW)
    add("Uber Eats reviews", fresh.get("ubereats", 0), UBEREATS_REVIEW)
    add("Grubhub reviews", fresh.get("grubhub", 0), GRUBHUB_REVIEW)
    add("Zocdoc provider results", fresh.get("zocdoc", 0), ZOCDOC_RESULT)
    add("Apify run fees (DoorDash, Uber Eats)", sum(1 for k in ("doordash", "ubereats") if fresh.get(k, 0)), APIFY_RUN_START)
    add("Competitor reviews (Google)", competitor_reviews, GOOGLE_REVIEW)
    add("Web searches", searches, WEB_SEARCH)
    add("AI reply drafts", drafts, AI_DRAFT)
    add("AI summary", summaries, AI_SUMMARY)
    return {"lines": lines, "total_usd": round(sum(l["cost_usd"] for l in lines), 6)}


def describe(breakdown: dict) -> str:
    return ", ".join(f"{l['label']} x{l['units']}" for l in breakdown["lines"]) or "no new data bought"
