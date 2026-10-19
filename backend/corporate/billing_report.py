"""Who is using how many locations, grouped by email domain, and what that comes to under their contract.

An organization's domain is its SSO domain if it has one, otherwise the domain of its OWNER's email. All organizations on
one domain are added together (that is the customer). Public mail domains (gmail.com and so on) say nothing about who the
customer is, so those organizations are each reported on their own and cannot have a contract.

A contract (table billing_contracts) can set a minimum number of locations that is billed even when fewer are used, and its
own price table. Without one, the standard table is used. Only active locations are counted."""
import os
from typing import Dict, List, Optional

from corporate import pricing

PUBLIC_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com", "msn.com", "icloud.com",
    "me.com", "aol.com", "proton.me", "protonmail.com", "gmx.com", "mail.com",
}


def domain_of(email: Optional[str]) -> str:
    e = (email or "").strip().lower()
    return e.rsplit("@", 1)[1] if "@" in e else ""


def admin_emails() -> set:
    return {e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()}


def is_admin(email: Optional[str]) -> bool:
    return (email or "").strip().lower() in admin_emails()


def _org_row(store, org: dict) -> dict:
    members = store.list_members(org["id"])
    owner = next((m for m in members if m.get("role") == "owner"), None)
    owner_email = (owner or {}).get("email") or ""
    domain = (org.get("sso_domain") or domain_of(owner_email)).lower()
    used = sum(1 for l in store.list_locations(org["id"]) if l.get("is_active", True))
    return {"org_id": org["id"], "org_name": org.get("name"), "owner_email": owner_email, "domain": domain, "locations": used}


def _line(key: str, label: str, domain: Optional[str], orgs: List[dict], contract: Optional[dict]) -> dict:
    used = sum(o["locations"] for o in orgs)
    minimum = int((contract or {}).get("minimum_locations") or 0)
    billed = max(used, minimum)          # before the "never pay more than a bigger tier" rule, which pricing.quote applies
    custom = pricing.parse_tiers((contract or {}).get("price_tiers") or "") if contract else None
    table = custom or pricing.tiers()
    q = pricing.quote(billed, table)
    return {
        "key": key, "label": label, "domain": domain, "accounts": len(orgs),
        "organizations": [{"name": o["org_name"], "owner_email": o["owner_email"], "locations": o["locations"]} for o in orgs],
        "locations_used": used, "minimum_locations": minimum, "locations_billed": q["billed_locations"],
        "rate_per_location": q["rate_per_location"],
        "monthly_total": q["monthly_total"], "average_per_location": q["average_per_location"],
        "custom_prices": bool(custom), "tiers": table,
        "contract": contract,
        "price_tiers_invalid": bool(contract and (contract.get("price_tiers") or "").strip() and not custom),
    }


def build(store) -> dict:
    contracts: Dict[str, dict] = {c["domain"]: c for c in store.list_contracts()}
    by_domain: Dict[str, List[dict]] = {}
    singles: List[dict] = []
    for org in store.list_orgs():
        row = _org_row(store, org)
        if row["domain"] and row["domain"] not in PUBLIC_DOMAINS:
            by_domain.setdefault(row["domain"], []).append(row)
        else:
            singles.append(row)
    lines = []
    for domain in sorted(set(by_domain) | set(contracts)):
        c = contracts.get(domain)
        lines.append(_line(domain, (c or {}).get("company_name") or domain, domain, by_domain.get(domain, []), c))
    for row in sorted(singles, key=lambda r: (r["org_name"] or "").lower()):
        lines.append(_line("org:" + row["org_id"], row["org_name"] or "(unnamed)", None, [row], None))
    return {"lines": lines, "totals": {"locations_used": sum(l["locations_used"] for l in lines),
                                       "monthly_total": round(sum(l["monthly_total"] for l in lines), 2)},
            "standard_tiers": pricing.tiers()}


def for_org(store, org: dict) -> dict:
    """What the owner of this organization sees: the billing line their organization falls into."""
    mine = _org_row(store, org)
    report = build(store)
    for line in report["lines"]:
        if any(o["name"] == org.get("name") and o["owner_email"] == mine["owner_email"] for o in line["organizations"]):
            return line
    return _line("org:" + org["id"], org.get("name") or "", None, [mine], None)


def contract_for(store, org: dict) -> Optional[dict]:
    """The contract that applies to this organization (by its domain), or None. Public mail domains never have one."""
    domain = _org_row(store, org)["domain"]
    if not domain or domain in PUBLIC_DOMAINS:
        return None
    return next((c for c in store.list_contracts() if c["domain"] == domain), None)


def has_contract(store, email: Optional[str]) -> bool:
    """True when this person's email domain has a contract, which lets them set up a company without a Pro plan."""
    domain = domain_of(email)
    if not domain or domain in PUBLIC_DOMAINS:
        return False
    return any(c["domain"] == domain for c in store.list_contracts())
