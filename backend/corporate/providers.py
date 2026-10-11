"""Who may see provider-level data, and what each role gets.

Provider-level data is about INDIVIDUAL doctors, so it is off for every company unless an administrator turns it on, and
even then it is shown only as follows:
  owner, admin   every provider at every location, with names
  manager        every provider at their OWN location (never other locations)
  viewer         practice-level totals only: no names, no individual provider figures
It never appears in tasks, exports, alert emails or AI drafts."""
from typing import Optional

WEIGHTED = ("avg_rating", "bedside", "wait")


def can_see_names(member: dict) -> bool:
    # A manager only ever reaches a location they manage (the route checks that first), so the role is enough here.
    return member["role"] in ("owner", "admin", "manager")


def _summary(providers: list) -> dict:
    def wavg(key):
        pairs = [(p[key], p["reviews"]) for p in providers if p.get(key) is not None and p.get("reviews")]
        total = sum(w for _, w in pairs)
        return round(sum(v * w for v, w in pairs) / total, 2) if total else None
    n = sum(p.get("reviews") or 0 for p in providers)
    verified = sum((p.get("verified_pct") or 0) * (p.get("reviews") or 0) for p in providers)
    return {"providers": len(providers), "reviews": n, "avg_rating": wavg("avg_rating"), "bedside": wavg("bedside"), "wait": wavg("wait"),
            "verified_pct": round(verified / n) if n else None}


def provider_view(org: dict, snapshot: Optional[dict], member: dict) -> dict:
    if not org.get("provider_data_enabled"):
        return {"enabled": False, "level": "none", "checked_at": None, "summary": None, "providers": []}
    providers = (snapshot or {}).get("providers") or []
    base = {"enabled": True, "checked_at": (snapshot or {}).get("providers_checked_at"), "summary": _summary(providers) if providers else None}
    if not can_see_names(member):
        return {**base, "level": "summary", "providers": []}          # viewers: totals only, no names, no individual figures
    return {**base, "level": "full", "providers": sorted(providers, key=lambda p: (p.get("avg_rating") is None, -(p.get("avg_rating") or 0)))}
