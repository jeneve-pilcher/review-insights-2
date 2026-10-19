"""Per-location pricing for companies. One table, used by the price calculator and by Stripe, so they cannot disagree.

The model is "volume" pricing: ALL of a company's locations are charged the price of the tier its size falls in. With the defaults
below, 600 locations are 600 x $29, because 500 to 999 is the $29 tier. To avoid the usual cliff (a company just under a tier line
paying more than a bigger one), nobody is billed more than they would be at the start of a bigger tier: such a company is simply
billed as if it had that many locations, which costs less.

THE DEFAULT PRICES ARE PLACEHOLDERS. Set your own with LOCATION_PRICE_TIERS, as "from:price" pairs, where `from` is the
smallest number of locations in the tier and `price` is dollars per location per month:
    LOCATION_PRICE_TIERS=1:49,250:39,500:29,1000:19
"""
import hashlib
import os
from typing import List, Optional

DEFAULT_TIERS = "1:49,250:39,500:29,1000:19"


def parse_tiers(raw: str) -> Optional[List[dict]]:
    """"from:price" pairs -> tier list, or None when the text isn't a valid table (must start at 1 location,
    increasing starts, positive prices)."""
    pairs = []
    try:
        for part in (raw or "").split(","):
            start, price = part.strip().split(":")
            pairs.append((int(start), float(price)))
    except ValueError:
        return None
    pairs = sorted(set(pairs))
    if not pairs or pairs[0][0] != 1 or any(p <= 0 for _, p in pairs) or len({s for s, _ in pairs}) != len(pairs):
        return None
    out = []
    for i, (start, price) in enumerate(pairs):
        end = pairs[i + 1][0] - 1 if i + 1 < len(pairs) else None
        out.append({"from": start, "to": end, "price_per_location": round(price, 2)})
    return out


def tiers() -> List[dict]:
    """The standard table: LOCATION_PRICE_TIERS, or the defaults when that is missing or invalid."""
    return parse_tiers(os.environ.get("LOCATION_PRICE_TIERS", DEFAULT_TIERS)) or parse_tiers(DEFAULT_TIERS)


def rate_for(count: int, table: Optional[List[dict]] = None) -> float:
    """The price per location for a company of this size (every location pays it)."""
    price = None
    for t in (table or tiers()):
        if count >= t["from"]:
            price = t["price_per_location"]
    return price


def billed_locations(count: int, table: Optional[List[dict]] = None) -> int:
    """How many locations are billed: the real count, unless a bigger tier's starting size would cost less in total."""
    count = max(1, int(count))
    table = table or tiers()
    best, best_cost = count, count * rate_for(count, table)
    for t in table:
        if t["from"] > count:
            cost = t["from"] * t["price_per_location"]
            if cost < best_cost:
                best, best_cost = t["from"], cost
    return best


def monthly_total(count: int, table: Optional[List[dict]] = None) -> float:
    table = table or tiers()
    n = billed_locations(count, table)
    return round(n * rate_for(n, table), 2)


def quote(count: int, table: Optional[List[dict]] = None) -> dict:
    count = max(1, int(count))
    table = table or tiers()
    total = monthly_total(count, table)
    n = billed_locations(count, table)
    return {"locations": count, "billed_locations": n, "rate_per_location": rate_for(n, table),
            "monthly_total": total, "average_per_location": round(total / count, 2)}


def stripe_tiers(table: Optional[List[dict]] = None) -> List[dict]:
    """A table in Stripe's format (cents). Used with Stripe's volume mode: every unit is charged the price of the tier reached."""
    out = []
    for t in (table or tiers()):
        out.append({"up_to": t["to"] if t["to"] is not None else "inf", "unit_amount": int(round(t["price_per_location"] * 100))})
    return out


def lookup_key(table: Optional[List[dict]] = None) -> str:
    """Changes whenever the table (or the pricing mode) changes, so a new table gets a new Stripe price and old subscriptions keep theirs."""
    digest = hashlib.sha256(repr(("volume", table or tiers())).encode()).hexdigest()[:10]
    return f"review_insights_location_{digest}"
