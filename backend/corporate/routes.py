import csv
import io
import os
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException

import config
from analysis import pipeline
import features
from analysis.mentions import default_terms, mention_target
from analysis.outscraper_client import place_info
from analysis.delivery_clients import normalize_doordash_url, normalize_grubhub_url, normalize_ubereats_url
from analysis.opentable_client import normalize_opentable_url
from analysis.yelp_client import normalize_yelp_url
from auth import CurrentUser, get_current_user
from corporate import billing_report, bulk_members, metrics, monitor, org_billing
from corporate.permissions import can, can_act_on_location, can_see_location
from corporate.schemas import (
    AlertUpdate,
    BudgetUpdate,
    ImportRequest,
    IndustryUpdate,
    LocationIn,
    LocationUpdate,
    MemberAdd,
    MemberUpdate,
    OrgCreate,
)
from corporate.store import DuplicateMember, get_store
from analysis import industries
from analysis import zocdoc_client
from analysis.industry_trends import themes_in_text
from corporate.providers import can_see_names, provider_view
from corporate import industry_rollup
from branding import public_branding
from credits import rates as credit_rates, wallet

router = APIRouter(prefix="/api/org", tags=["organization"])
internal_router = APIRouter(prefix="/api/internal", tags=["internal"])

ALLOWED_TIERS = {t.strip() for t in os.environ.get("ORG_ALLOWED_TIERS", "pro,enterprise").split(",") if t.strip()}
# An optional monthly spending limit (dollars of credit) for new companies. 0 or blank = no limit.
DEFAULT_LIMIT_USD = float(os.environ.get("DEFAULT_MONTHLY_LIMIT_USD", "0") or 0) or None
MAX_LOCATIONS = int(os.environ.get("MAX_LOCATIONS_PER_ORG", "5000"))
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------------ helpers
def get_member(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    store = get_store()
    m = store.find_membership(current_user.id, current_user.email)
    if not m:
        raise HTTPException(status_code=403, detail="You're not part of an organization yet.")
    return {**m, "user_id": current_user.id, "email": (m.get("email") or current_user.email).lower(),
            "org": store.get_org(m["org_id"])}


def _require(member: dict, action: str) -> None:
    if not can(member, action):
        raise HTTPException(status_code=403, detail="Your role can't do that.")


def _audit(member: dict, action: str, target=None, detail=None) -> None:
    get_store().add_audit(member["org_id"], member["user_id"], member["email"], action, target, detail)


def _fields(req) -> dict:
    return req.model_dump(exclude_unset=True)


def _clean_email(value):
    value = (value or "").strip().lower()
    if not value:
        return None
    if not EMAIL_RE.match(value):
        raise HTTPException(status_code=400, detail=f"'{value}' isn't a valid email address.")
    return value


def _clean_link(value, normalizer):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return normalizer(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# The reservation platforms a location can also be pulled from (through Apify).
EXTRA_LINKS = ("opentable_url", "doordash_url", "ubereats_url", "grubhub_url")


def _other_sources(loc: dict) -> dict:
    """{"opentable": link, ...} for the reservation pages saved on this location."""
    return {col[:-4]: loc[col] for col in EXTRA_LINKS if loc.get(col)}


def _clean_yelp(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return normalize_yelp_url(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _get_location(member: dict, location_id: str, action: str = None) -> dict:
    loc = get_store().get_location(location_id)
    if not loc or loc["org_id"] != member["org_id"] or not can_see_location(member, loc):
        raise HTTPException(status_code=404, detail="Location not found.")   # same answer whether it exists or not
    if action and not can_act_on_location(member, loc, action):
        raise HTTPException(status_code=403, detail="Your role can't do that for this location.")
    return loc


def _visible_locations(member: dict) -> list:
    return [l for l in get_store().list_locations(member["org_id"]) if can_see_location(member, l)]


def _open_alert_counts(member: dict) -> dict:
    counts = {}
    for a in get_store().list_alerts(member["org_id"], status="open", limit=5000):
        counts[a["location_id"]] = counts.get(a["location_id"], 0) + 1
    return counts


SNAPSHOT_FIELDS = ("run_at", "reviews_total", "reviews_google", "reviews_yelp", "avg_rating", "avg_rating_google",
                   "avg_rating_yelp", "prev_avg_rating", "low_star_pct", "recent_per_week", "days_since_last",
                   "avg_sentiment", "wait_share_pct", "negative_count", "rising_topics", "signals")


def _location_row(loc: dict, snap, open_alerts: int, show_providers: bool = False) -> dict:
    row = {k: loc.get(k) for k in ("id", "name", "brand", "region", "google_query", "yelp_url", "opentable_url", "doordash_url", "ubereats_url", "grubhub_url", "manager_email", "is_active")}
    row["snapshot"] = {k: snap.get(k) for k in SNAPSHOT_FIELDS} if snap else None
    row["top_theme"] = ((snap or {}).get("industry") or {}).get("top")      # the industry theme to look at first, if any
    row["open_alerts"] = open_alerts
    # Doctor pages name individual doctors, so they are shown only to people allowed to see provider names.
    row["provider_links"] = (loc.get("provider_links") or []) if show_providers else None
    return row


def _show_provider_names(member: dict) -> bool:
    return bool(member["org"].get("provider_data_enabled")) and can_see_names(member)


def _enforce_budget(member: dict) -> None:
    if monitor.usage_status(get_store(), member["org"])["over"]:
        raise HTTPException(status_code=402, detail="This month's spending limit has been reached. The owner can raise it.")


# --------------------------------------------------------------------- org
@router.post("")
def create_org(req: OrgCreate, current_user: CurrentUser = Depends(get_current_user)):
    store = get_store()
    if current_user.tier not in ALLOWED_TIERS and not billing_report.has_contract(store, current_user.email):
        raise HTTPException(status_code=403, detail="Company accounts need a Pro or Enterprise plan, or a contract for your email domain.")
    if store.find_membership(current_user.id, current_user.email):
        raise HTTPException(status_code=400, detail="You're already part of an organization.")
    org = store.create_org(req.name.strip(), current_user.id, current_user.email, DEFAULT_LIMIT_USD)
    store.add_audit(org["id"], current_user.id, current_user.email.lower(), "org_create", org["name"], {})
    return {"id": org["id"], "name": org["name"]}


def _billing_view(member: dict):
    """The owner sees what the contract bills for their company: locations in use and the monthly amount."""
    if member.get("role") != "owner":
        return None
    try:
        line = billing_report.for_org(get_store(), member["org"])
    except Exception:                                  # noqa: BLE001  (e.g. the contracts table hasn't been created yet)
        return None
    org = member["org"]
    line["subscription"] = {"live": org_billing.is_live(org), "status": org.get("billing_status"),
                            "has_customer": bool(org.get("stripe_customer_id")), "required": org_billing.required()}
    return line


def _require_billing(member: dict) -> None:
    """New locations are only added once the company's billing is set up (REQUIRE_ORG_BILLING=false turns this off)."""
    if not org_billing.required() or org_billing.is_live(member["org"]) or billing_report.is_admin(member.get("email")):
        return
    raise HTTPException(status_code=402, detail="Set up billing first: the owner can do this on the Billing tab.")


@router.post("/billing/checkout")
def billing_checkout(member: dict = Depends(get_member)):
    if member["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only the owner can set up billing.")
    try:
        return {"url": org_billing.checkout_url(get_store(), member["org"], member["email"])}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:                           # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Could not start checkout: {exc}")


@router.post("/billing/portal")
def billing_portal(member: dict = Depends(get_member)):
    if member["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only the owner can manage billing.")
    try:
        return {"url": org_billing.portal_url(member["org"])}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:                           # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Could not open billing: {exc}")


@router.get("")
def get_org(member: dict = Depends(get_member)):
    store = get_store()
    org = member["org"]
    return {
        "org": {"id": org["id"], "name": org["name"], "monthly_budget_usd": org.get("monthly_budget_usd"),
                "industry": org.get("industry") or industries.DEFAULT, "white_label": bool(org.get("white_label")),
                "pack": industries.public_pack(industries.get_pack(org.get("industry"))),
                "provider_data_enabled": bool(org.get("provider_data_enabled")),
                "sso_domain": org.get("sso_domain"),
                "branding": public_branding(org)},
        "role": member["role"],
        "email": member["email"],
        "can": {a: can(member, a) for a in ("manage_members", "manage_admins", "manage_locations", "run_location",
                                            "update_alert", "view_audit", "set_budget")},
        "members": store.list_members(org["id"]) if can(member, "manage_members") else [],
        "usage": monitor.usage_status(store, org),
        "limits": {"max_locations": MAX_LOCATIONS, "monitor_interval_hours": monitor.INTERVAL_HOURS,
                   "monitor_months": monitor.MONITOR_MONTHS},
        # Per-location billing: only the owner sees it.
        "billing": _billing_view(member),
    }


@router.put("/industry")
def set_org_industry(req: IndustryUpdate, member: dict = Depends(get_member)):
    """The company's industry decides which themes and graphs its locations get. Owner and admins can change it."""
    _require(member, "manage_locations")
    if not industries.is_selectable(req.industry):
        raise HTTPException(status_code=400, detail="That industry isn't available yet.")
    old = member["org"].get("industry") or industries.DEFAULT
    get_store().update_org(member["org_id"], industry=req.industry)
    _audit(member, "industry_change", None, {"from": old, "to": req.industry})
    return {"industry": req.industry}


@router.patch("/budget")
def set_budget(req: BudgetUpdate, member: dict = Depends(get_member)):
    _require(member, "set_budget")
    old = member["org"].get("monthly_budget_usd")
    new = round(req.monthly_budget_usd, 2) if req.monthly_budget_usd is not None else None     # None = no limit
    get_store().update_org(member["org_id"], monthly_budget_usd=new)
    _audit(member, "budget_change", None, {"from": old, "to": new})
    return {"monthly_budget_usd": new}


# ----------------------------------------------------------------- members
@router.post("/members")
def add_member(req: MemberAdd, member: dict = Depends(get_member)):
    _require(member, "manage_members")
    if req.role == "admin":
        _require(member, "manage_admins")
    email = _clean_email(req.email)
    if not email:
        raise HTTPException(status_code=400, detail="Enter an email address.")
    try:
        row = get_store().add_member(member["org_id"], email, req.role)
    except DuplicateMember:
        raise HTTPException(status_code=400, detail=f"{email} is already on the team.")
    _audit(member, "member_add", email, {"role": req.role})
    return row


@router.post("/members/import")
def import_members(req: ImportRequest, send_invites: bool = True, member: dict = Depends(get_member)):
    """Add many people from a CSV (email, role), optionally emailing each a sign-up invitation."""
    _require(member, "manage_members")
    try:
        rows, _ = bulk_members.parse(req.csv_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    result = bulk_members.run(get_store(), member["org_id"], can(member, "manage_admins"), rows, send_invites,
                              f"{config.FRONTEND_URL}/login?invited=1", DuplicateMember,
                              sso_domain=member["org"].get("sso_domain") or "")
    _audit(member, "members_import", None, {"added": result["added"], "skipped": len(result["skipped"]), "invites": result["invites_sent"]})
    return result


def _get_target_member(member: dict, member_id: str) -> dict:
    target = get_store().get_member(member_id)
    if not target or target["org_id"] != member["org_id"]:
        raise HTTPException(status_code=404, detail="Team member not found.")
    if target["role"] == "owner":
        raise HTTPException(status_code=400, detail="The owner can't be changed or removed.")
    if target["role"] == "admin" and not can(member, "manage_admins"):
        raise HTTPException(status_code=403, detail="Only the owner can change an admin.")
    return target


@router.patch("/members/{member_id}")
def update_member(member_id: str, req: MemberUpdate, member: dict = Depends(get_member)):
    _require(member, "manage_members")
    target = _get_target_member(member, member_id)
    if req.role == "admin":
        _require(member, "manage_admins")
    row = get_store().update_member(member_id, role=req.role)
    _audit(member, "member_role_change", target["email"], {"from": target["role"], "to": req.role})
    return row


@router.delete("/members/{member_id}")
def remove_member(member_id: str, member: dict = Depends(get_member)):
    _require(member, "manage_members")
    target = _get_target_member(member, member_id)
    get_store().remove_member(member_id)
    _audit(member, "member_remove", target["email"], {"role": target["role"]})
    return {"removed": True}


# --------------------------------------------------------------- locations
def _clean_providers(links) -> list:
    """Zocdoc doctor pages for a location: normalized, de-duplicated, and capped."""
    seen, out = set(), []
    for raw in links or []:
        url = zocdoc_client.normalize_zocdoc_url(raw)
        if url not in seen:
            seen.add(url)
            out.append(url)
    if len(out) > zocdoc_client.MAX_PROVIDERS:
        raise ValueError(f"A location can track up to {zocdoc_client.MAX_PROVIDERS} doctors (each refresh is billed per result).")
    return out


def _validate_location(data: dict, member: dict = None) -> dict:
    out = dict(data)
    if "provider_links" in out:
        links = out["provider_links"] or []
        if links and not ((member or {}).get("org") or {}).get("provider_data_enabled"):
            raise HTTPException(status_code=400, detail="Provider-level data isn't turned on for this company. Ask your account administrator.")
        try:
            out["provider_links"] = _clean_providers(links)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    if "manager_email" in out:
        out["manager_email"] = _clean_email(out["manager_email"])
    if "yelp_url" in out:
        out["yelp_url"] = _clean_yelp(out["yelp_url"])
    if "opentable_url" in out:
        out["opentable_url"] = _clean_link(out["opentable_url"], normalize_opentable_url)
    if "doordash_url" in out:
        out["doordash_url"] = _clean_link(out["doordash_url"], normalize_doordash_url)
    if "ubereats_url" in out:
        out["ubereats_url"] = _clean_link(out["ubereats_url"], normalize_ubereats_url)
    if "grubhub_url" in out:
        out["grubhub_url"] = _clean_link(out["grubhub_url"], normalize_grubhub_url)
    for k in ("name", "google_query", "brand", "region"):
        if k in out and isinstance(out[k], str):
            out[k] = out[k].strip() or None
    return out


@router.get("/locations")
def list_locations(member: dict = Depends(get_member)):
    store = get_store()
    snaps = store.latest_snapshots_for_org(member["org_id"])
    alerts = _open_alert_counts(member)
    show = _show_provider_names(member)
    return [_location_row(l, snaps.get(l["id"]), alerts.get(l["id"], 0), show) for l in _visible_locations(member)]


@router.post("/locations")
def add_location(req: LocationIn, member: dict = Depends(get_member)):
    _require(member, "manage_locations")
    store = get_store()
    _require_billing(member)
    if len(store.list_locations(member["org_id"])) >= MAX_LOCATIONS:
        raise HTTPException(status_code=400, detail=f"This organization is at its limit of {MAX_LOCATIONS} locations.")
    data = _validate_location(_fields(req), member)
    if not data.get("name") or not data.get("google_query"):
        raise HTTPException(status_code=400, detail="A name and a Google search (name + address) are required.")
    loc = store.add_location(member["org_id"], data)
    org_billing.sync_quantity(store, member["org_id"])
    _audit(member, "location_add", loc["name"], {})
    return _location_row(loc, None, 0, _show_provider_names(member))


def parse_locations_csv(text: str):
    """Returns (rows, errors). Headers: name, google_query (aliases: google, address), brand, region,
    yelp_url (alias yelp), opentable_url, doordash_url, ubereats_url, grubhub_url (aliases without _url),
    manager_email (aliases: manager, email)."""
    aliases = {"google": "google_query", "google_maps": "google_query", "address": "google_query",
               "yelp": "yelp_url", "opentable": "opentable_url", "doordash": "doordash_url",
               "ubereats": "ubereats_url", "grubhub": "grubhub_url",
               "manager": "manager_email", "email": "manager_email"}
    reader = csv.DictReader(io.StringIO(text.strip()))
    headers = {aliases.get(h.strip().lower(), h.strip().lower()) for h in (reader.fieldnames or [])}
    if not {"name", "google_query"} <= headers:
        raise ValueError("The first row must have headers including 'name' and 'google_query' "
                         "(optional: brand, region, yelp_url, opentable_url, doordash_url, ubereats_url, grubhub_url, manager_email).")
    rows, errors = [], []
    for i, raw in enumerate(reader, start=2):
        row = {}
        for k, v in raw.items():
            if k is None:
                continue
            row[aliases.get(k.strip().lower(), k.strip().lower())] = (v or "").strip()
        if not any(row.values()):
            continue
        rows.append((i, row))
    return rows, errors


@router.post("/locations/import")
def import_locations(req: ImportRequest, member: dict = Depends(get_member)):
    _require(member, "manage_locations")
    _require_billing(member)
    store = get_store()
    try:
        rows, _ = parse_locations_csv(req.csv_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    existing = store.list_locations(member["org_id"])
    seen = {((l["name"] or "").lower(), (l["google_query"] or "").lower()) for l in existing}
    room = MAX_LOCATIONS - len(existing)
    added, skipped = 0, []

    for line, row in rows:
        if not row.get("name") or not row.get("google_query"):
            skipped.append({"row": line, "reason": "missing name or google_query"})
            continue
        key = (row["name"].lower(), row["google_query"].lower())
        if key in seen:
            skipped.append({"row": line, "reason": "already exists"})
            continue
        if added >= room:
            skipped.append({"row": line, "reason": f"over the {MAX_LOCATIONS}-location limit"})
            continue
        try:
            data = _validate_location({k: row.get(k) for k in ("name", "google_query", "brand", "region", "yelp_url", "opentable_url", "doordash_url", "ubereats_url", "grubhub_url", "manager_email")})
        except HTTPException as exc:
            skipped.append({"row": line, "reason": exc.detail})
            continue
        store.add_location(member["org_id"], data)
        seen.add(key)
        added += 1

    if added:
        org_billing.sync_quantity(store, member["org_id"])
    _audit(member, "locations_import", None, {"added": added, "skipped": len(skipped)})
    if added:
        return {"added": added, "skipped": skipped}


@router.patch("/locations/{location_id}")
def update_location(location_id: str, req: LocationUpdate, member: dict = Depends(get_member)):
    _require(member, "manage_locations")
    loc = _get_location(member, location_id)
    data = _validate_location(_fields(req), member)
    if "name" in data and not data["name"] or "google_query" in data and not data["google_query"]:
        raise HTTPException(status_code=400, detail="Name and Google search can't be empty.")
    row = get_store().update_location(location_id, **data)
    _audit(member, "location_update", loc["name"], {"fields": sorted(data)})
    snap = get_store().latest_snapshot(location_id)
    return _location_row(row, snap, _open_alert_counts(member).get(location_id, 0), _show_provider_names(member))


@router.delete("/locations/{location_id}")
def delete_location(location_id: str, member: dict = Depends(get_member)):
    _require(member, "manage_locations")
    loc = _get_location(member, location_id)
    get_store().delete_location(location_id)
    org_billing.sync_quantity(get_store(), member["org_id"])
    _audit(member, "location_delete", loc["name"], {})
    return {"deleted": True}


@router.post("/locations/{location_id}/run")
def run_location(location_id: str, member: dict = Depends(get_member)):
    loc = _get_location(member, location_id, "run_location")
    res = monitor.run_location(get_store(), member["org"], loc, kind="manual")
    if res["status"] == "skipped":
        raise HTTPException(status_code=402, detail=res["message"])
    if res["status"] == "error":
        raise HTTPException(status_code=502, detail=res["message"])
    _audit(member, "run_manual", loc["name"], {"new_alerts": res["new_alerts"], "fresh_reviews": res["fresh_reviews"]})
    return {"new_alerts": res["new_alerts"], "emailed": res["emailed"], "notes": res["notes"],
            "fresh_reviews": res["fresh_reviews"], "snapshot": res["snapshot"]}


@router.get("/locations/{location_id}/providers")
def location_providers(location_id: str, member: dict = Depends(get_member)):
    """Provider-level numbers for one location, filtered by role: owners and admins see every provider with names, a
    manager sees their own location's providers, a viewer sees practice-level totals only."""
    loc = _get_location(member, location_id)               # a manager can only reach their own location
    view = provider_view(member["org"], get_store().latest_snapshot(location_id), member)
    view["links"] = (loc.get("provider_links") or []) if view["level"] == "full" else []
    return view


@router.get("/locations/{location_id}/history")
def location_history(location_id: str, member: dict = Depends(get_member)):
    _get_location(member, location_id)
    rows = get_store().snapshots(location_id, 30)
    return [{k: r.get(k) for k in SNAPSHOT_FIELDS} for r in reversed(rows)]


@router.get("/locations/{location_id}/analysis")
def location_analysis(location_id: str, months: int = 6, view: str = "combined", mentions: bool = False,
                      member: dict = Depends(get_member)):
    """The full single-business dashboard payload for one location (every panel)."""
    loc = _get_location(member, location_id)
    _enforce_budget(member)
    org_scope = wallet.scope_for_org(member["org_id"])
    wallet.precheck(get_store(), org_scope, 0.0, who="org")        # companies pay from their credit balance
    months = max(1, min(60, months))
    by_source, cached, notes, fresh, unrated = pipeline.pull_reviews_ext(
        loc["google_query"], loc.get("yelp_url"), months, want_yelp=bool(loc.get("yelp_url")), others=_other_sources(loc)
    )
    if sum(fresh.values()):
        get_store().add_usage(member["org_id"], location_id, sum(fresh.values()), "analysis")
    web = None
    if mentions and features.INTERNET_MENTIONS:
        terms, area = mention_target(loc["google_query"], place_info(loc["google_query"]))
        web = pipeline.pull_mentions(terms, months, area=area)
    result = pipeline.assemble(by_source, cached, notes, view=view, months=months, location=loc["name"],
                               paid=True, alert_email=None, competitors=None, mentions=web, unrated=unrated,
                               industry=member["org"].get("industry"), ai_summary=features.AI_SUMMARIES)
    cost = credit_rates.cost_breakdown(fresh, searches=(web or {}).get("searches", 0),
                                       summaries=1 if (result.get("ai_summary") or {}).get("fresh") else 0)
    result["billing"] = wallet.settle(get_store(), org_scope, 0.0, cost, f"Analysis of {loc['name']}")
    return result


# -------------------------------------------------- roll-up and benchmarks
@router.get("/overview")
def overview(member: dict = Depends(get_member)):
    store = get_store()
    locs = _visible_locations(member)
    snaps = store.latest_snapshots_for_org(member["org_id"])
    visible = {l["id"] for l in locs}
    # Everything is restricted to the locations this person may see (alert counts included),
    # so a manager can't learn anything about locations that aren't theirs.
    counts = {k: v for k, v in _open_alert_counts(member).items() if k in visible}
    result = metrics.build_overview(locs, {k: v for k, v in snaps.items() if k in visible}, counts)
    result["usage"] = monitor.usage_status(store, member["org"])
    return result


@router.get("/industry")
def company_industry(member: dict = Depends(get_member)):
    """The company's industry data: headline numbers, theme-by-location grid, rankings and trends. Only the locations
    this person may see are used, so a manager's numbers describe only their own locations."""
    store = get_store()
    locs = _visible_locations(member)
    visible = {l["id"] for l in locs}
    snaps = {k: v for k, v in store.latest_snapshots_for_org(member["org_id"]).items() if k in visible}
    history = {l["id"]: list(reversed(store.snapshots(l["id"], 30))) for l in locs}
    return industry_rollup.build_company_industry(member["org"], locs, snaps, history)


@router.get("/benchmarks")
def benchmarks(group_by: str = "all", member: dict = Depends(get_member)):
    if group_by not in ("all", "brand", "region"):
        raise HTTPException(status_code=400, detail="group_by must be all, brand or region.")
    store = get_store()
    all_locs = store.list_locations(member["org_id"])
    snaps = store.latest_snapshots_for_org(member["org_id"])
    result = metrics.build_benchmarks(all_locs, snaps, group_by)
    if member["role"] == "manager":
        # Managers see how THEY rank against the group, without the other locations' names or numbers.
        mine = {l["id"] for l in all_locs if can_see_location(member, l)}
        result["rows"] = [r for r in result["rows"] if r["location_id"] in mine]
        result["awaiting_first_run"] = []
    return result


# ------------------------------------------------------------ alerts/tasks
@router.get("/alerts")
def list_alerts(status: str = None, location_id: str = None, member: dict = Depends(get_member)):
    store = get_store()
    names = {l["id"]: l for l in store.list_locations(member["org_id"])}
    pack = industries.get_pack(member["org"].get("industry"))
    out = []
    for a in store.list_alerts(member["org_id"], status=status, location_id=location_id):
        loc = names.get(a["location_id"])
        if loc and can_see_location(member, loc):
            # Which of the industry's themes this review touches, so tasks can be filtered by theme.
            out.append({**a, "location_name": loc["name"], "region": loc.get("region"),
                        "themes": themes_in_text(a.get("text") or "", pack)})
    return out


@router.patch("/alerts/{alert_id}")
def update_alert(alert_id: str, req: AlertUpdate, member: dict = Depends(get_member)):
    store = get_store()
    alert = store.get_alert(alert_id)
    if not alert or alert["org_id"] != member["org_id"]:
        raise HTTPException(status_code=404, detail="Alert not found.")
    loc = _get_location(member, alert["location_id"], "update_alert")
    data = _fields(req)
    if "assigned_to" in data:
        assignee = _clean_email(data["assigned_to"])
        if assignee and assignee not in {m["email"] for m in store.list_members(member["org_id"])}:
            raise HTTPException(status_code=400, detail="You can only assign a task to someone on the team.")
        data["assigned_to"] = assignee
    row = store.update_alert(alert_id, **data)
    _audit(member, "alert_update", loc["name"],
           {k: {"from": alert.get(k), "to": row.get(k)} for k in data if alert.get(k) != row.get(k)})
    return {**row, "location_name": loc["name"]}


@router.get("/audit")
def audit_log(member: dict = Depends(get_member)):
    _require(member, "view_audit")
    return get_store().list_audit(member["org_id"], 100)


# -------------------------------------------- scheduled refresh (external cron)
@internal_router.post("/run-due")
def run_due(x_cron_secret: str = Header(None)):
    """For hosts that run cron jobs (e.g. Render): POST here with the X-Cron-Secret header."""
    secret = os.environ.get("CRON_SECRET")
    if not secret or x_cron_secret != secret:
        raise HTTPException(status_code=404, detail="Not found.")      # don't reveal the route exists
    results = monitor.run_due(get_store())
    return {"ran": len(results), "ok": sum(1 for r in results if r["status"] == "ok"),
            "errors": [r["message"] for r in results if r["status"] == "error"]}
