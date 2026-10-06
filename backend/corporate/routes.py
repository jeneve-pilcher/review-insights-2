import csv
import io
import os
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException

import config
from analysis import pipeline
from analysis.mentions import default_terms
from analysis.yelp_client import normalize_yelp_url
from auth import CurrentUser, get_current_user
from corporate import metrics, monitor
from corporate.permissions import can, can_act_on_location, can_see_location
from corporate.schemas import (
    AlertUpdate,
    BudgetUpdate,
    ImportRequest,
    LocationIn,
    LocationUpdate,
    MemberAdd,
    MemberUpdate,
    OrgCreate,
)
from corporate.store import DuplicateMember, get_store

router = APIRouter(prefix="/api/org", tags=["organization"])
internal_router = APIRouter(prefix="/api/internal", tags=["internal"])

ALLOWED_TIERS = {t.strip() for t in os.environ.get("ORG_ALLOWED_TIERS", "pro,enterprise").split(",") if t.strip()}
DEFAULT_BUDGET = int(os.environ.get("DEFAULT_MONTHLY_BUDGET_REVIEWS", "5000"))
MAX_LOCATIONS = int(os.environ.get("MAX_LOCATIONS_PER_ORG", "500"))
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


def _location_row(loc: dict, snap, open_alerts: int) -> dict:
    row = {k: loc.get(k) for k in ("id", "name", "brand", "region", "google_query", "yelp_url", "manager_email", "is_active")}
    row["snapshot"] = {k: snap.get(k) for k in SNAPSHOT_FIELDS} if snap else None
    row["open_alerts"] = open_alerts
    return row


def _enforce_budget(member: dict) -> None:
    if monitor.usage_status(get_store(), member["org"])["over"]:
        raise HTTPException(status_code=402, detail="This month's review budget has been used. The owner can raise it.")


# --------------------------------------------------------------------- org
@router.post("")
def create_org(req: OrgCreate, current_user: CurrentUser = Depends(get_current_user)):
    store = get_store()
    if current_user.tier not in ALLOWED_TIERS:
        raise HTTPException(status_code=403, detail="Multi-location features need a Pro or Enterprise plan.")
    if store.find_membership(current_user.id, current_user.email):
        raise HTTPException(status_code=400, detail="You're already part of an organization.")
    org = store.create_org(req.name.strip(), current_user.id, current_user.email, DEFAULT_BUDGET)
    store.add_audit(org["id"], current_user.id, current_user.email.lower(), "org_create", org["name"], {})
    return {"id": org["id"], "name": org["name"]}


@router.get("")
def get_org(member: dict = Depends(get_member)):
    store = get_store()
    org = member["org"]
    return {
        "org": {"id": org["id"], "name": org["name"], "monthly_budget_reviews": org["monthly_budget_reviews"]},
        "role": member["role"],
        "email": member["email"],
        "can": {a: can(member, a) for a in ("manage_members", "manage_admins", "manage_locations", "run_location",
                                            "update_alert", "view_audit", "set_budget")},
        "members": store.list_members(org["id"]) if can(member, "manage_members") else [],
        "usage": monitor.usage_status(store, org),
        "limits": {"max_locations": MAX_LOCATIONS, "monitor_interval_hours": monitor.INTERVAL_HOURS,
                   "monitor_months": monitor.MONITOR_MONTHS},
    }


@router.patch("/budget")
def set_budget(req: BudgetUpdate, member: dict = Depends(get_member)):
    _require(member, "set_budget")
    old = member["org"]["monthly_budget_reviews"]
    get_store().update_org(member["org_id"], monthly_budget_reviews=req.monthly_budget_reviews)
    _audit(member, "budget_change", None, {"from": old, "to": req.monthly_budget_reviews})
    return {"monthly_budget_reviews": req.monthly_budget_reviews}


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
def _validate_location(data: dict) -> dict:
    out = dict(data)
    if "manager_email" in out:
        out["manager_email"] = _clean_email(out["manager_email"])
    if "yelp_url" in out:
        out["yelp_url"] = _clean_yelp(out["yelp_url"])
    for k in ("name", "google_query", "brand", "region"):
        if k in out and isinstance(out[k], str):
            out[k] = out[k].strip() or None
    return out


@router.get("/locations")
def list_locations(member: dict = Depends(get_member)):
    store = get_store()
    snaps = store.latest_snapshots_for_org(member["org_id"])
    alerts = _open_alert_counts(member)
    return [_location_row(l, snaps.get(l["id"]), alerts.get(l["id"], 0)) for l in _visible_locations(member)]


@router.post("/locations")
def add_location(req: LocationIn, member: dict = Depends(get_member)):
    _require(member, "manage_locations")
    store = get_store()
    if len(store.list_locations(member["org_id"])) >= MAX_LOCATIONS:
        raise HTTPException(status_code=400, detail=f"This organization is at its limit of {MAX_LOCATIONS} locations.")
    data = _validate_location(_fields(req))
    if not data.get("name") or not data.get("google_query"):
        raise HTTPException(status_code=400, detail="A name and a Google search (name + address) are required.")
    loc = store.add_location(member["org_id"], data)
    _audit(member, "location_add", loc["name"], {})
    return _location_row(loc, None, 0)


def parse_locations_csv(text: str):
    """Returns (rows, errors). Headers: name, google_query (aliases: google, address), brand, region,
    yelp_url (alias yelp), manager_email (aliases: manager, email)."""
    aliases = {"google": "google_query", "google_maps": "google_query", "address": "google_query",
               "yelp": "yelp_url", "manager": "manager_email", "email": "manager_email"}
    reader = csv.DictReader(io.StringIO(text.strip()))
    headers = {aliases.get(h.strip().lower(), h.strip().lower()) for h in (reader.fieldnames or [])}
    if not {"name", "google_query"} <= headers:
        raise ValueError("The first row must have headers including 'name' and 'google_query' "
                         "(optional: brand, region, yelp_url, manager_email).")
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
            data = _validate_location({k: row.get(k) for k in ("name", "google_query", "brand", "region", "yelp_url", "manager_email")})
        except HTTPException as exc:
            skipped.append({"row": line, "reason": exc.detail})
            continue
        store.add_location(member["org_id"], data)
        seen.add(key)
        added += 1

    _audit(member, "locations_import", None, {"added": added, "skipped": len(skipped)})
    return {"added": added, "skipped": skipped}


@router.patch("/locations/{location_id}")
def update_location(location_id: str, req: LocationUpdate, member: dict = Depends(get_member)):
    _require(member, "manage_locations")
    loc = _get_location(member, location_id)
    data = _validate_location(_fields(req))
    if "name" in data and not data["name"] or "google_query" in data and not data["google_query"]:
        raise HTTPException(status_code=400, detail="Name and Google search can't be empty.")
    row = get_store().update_location(location_id, **data)
    _audit(member, "location_update", loc["name"], {"fields": sorted(data)})
    snap = get_store().latest_snapshot(location_id)
    return _location_row(row, snap, _open_alert_counts(member).get(location_id, 0))


@router.delete("/locations/{location_id}")
def delete_location(location_id: str, member: dict = Depends(get_member)):
    _require(member, "manage_locations")
    loc = _get_location(member, location_id)
    get_store().delete_location(location_id)
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
    months = max(1, min(60, months))
    by_source, cached, notes, fresh = pipeline.pull_reviews(
        loc["google_query"], loc.get("yelp_url"), months, want_yelp=bool(loc.get("yelp_url"))
    )
    if sum(fresh.values()):
        get_store().add_usage(member["org_id"], location_id, sum(fresh.values()), "analysis")
    web = pipeline.pull_mentions(default_terms(loc["google_query"]), months) if mentions else None
    return pipeline.assemble(by_source, cached, notes, view=view, months=months, location=loc["name"],
                             paid=True, alert_email=None, competitors=None, mentions=web)


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
    out = []
    for a in store.list_alerts(member["org_id"], status=status, location_id=location_id):
        loc = names.get(a["location_id"])
        if loc and can_see_location(member, loc):
            out.append({**a, "location_name": loc["name"], "region": loc.get("region")})
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
