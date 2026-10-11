"""Pulls reviews for a location, stores a snapshot, turns new negative reviews into
tasks and emails the right manager - on demand or on a schedule."""
import hashlib
import os
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from dateutil import parser as date_parser

import config
from analysis import pipeline
from analysis.pii import redact_pii
from analysis.review_utils import has_text
from corporate import metrics
from analysis import zocdoc_client
from corporate.store import get_store
from credits import rates as credit_rates, wallet
from email_alerts import send_email

MONITOR_MONTHS = int(os.environ.get("MONITOR_MONTHS", "3"))                # smaller window = cheaper scheduled runs
INTERVAL_HOURS = float(os.environ.get("MONITOR_INTERVAL_HOURS", "24"))     # how often each location refreshes
ALERT_LOOKBACK_DAYS = int(os.environ.get("ALERT_LOOKBACK_DAYS", "7"))      # only reviews this recent become alerts
TICK_MINUTES = float(os.environ.get("SCHEDULER_TICK_MINUTES", "30"))
MAX_RUNS_PER_TICK = int(os.environ.get("MAX_RUNS_PER_TICK", "10"))
ERROR_BACKOFF_HOURS = 6.0

SOURCE_LABELS = {"google": "Google", "yelp": "Yelp", "opentable": "OpenTable", "doordash": "DoorDash", "grubhub": "Grubhub"}
# Only platforms whose reviews have stars feed scheduled checks. Uber Eats (no stars) can't change a snapshot or raise a
# task, so a scheduled check never pays to pull it.
RATED_EXTRA = ("opentable", "doordash", "grubhub")
# Provider-level data costs about $0.05 per result, so scheduled checks refresh it at most this often.
PROVIDER_REFRESH_DAYS = int(os.environ.get("PROVIDER_REFRESH_DAYS", "7"))

_error_backoff: Dict[str, datetime] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: str) -> datetime:
    dt = date_parser.parse(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _naive_utc(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


# ------------------------------------------------------------------ budget
def month_start_iso(now: datetime) -> str:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def _providers_for_snapshot(store, org: dict, location: dict, prev: Optional[dict], now: datetime, kind: str, notes: list):
    """Provider-level numbers for this check: fetched when the company has the feature on and the location has doctor
    pages, otherwise (or when the last fetch is recent) carried forward. Returns (providers or None, fetched_at)."""
    links = location.get("provider_links") or []
    if not org.get("provider_data_enabled") or not links:
        return None, None
    old = (prev or {}).get("providers")
    old_at = (prev or {}).get("providers_checked_at")
    if kind == "monitor" and old is not None and old_at:
        try:
            age = now - datetime.fromisoformat(str(old_at).replace("Z", "+00:00"))
            if age < timedelta(days=PROVIDER_REFRESH_DAYS):
                return old, old_at                    # fresh enough: costs nothing
        except ValueError:
            pass
    try:
        providers, rows_bought = zocdoc_client.fetch_providers(links, 3)
    except Exception as exc:
        notes.append(f"Provider data couldn't be refreshed ({getattr(exc, 'detail', exc)}); showing the last numbers.")
        return old, old_at
    if rows_bought:
        wallet.settle(store, wallet.scope_for_org(org["id"]), 0.0, credit_rates.cost_breakdown({"zocdoc": rows_bought}),
                      f"Provider data for {location['name']}")
    return providers, now.isoformat()


def usage_status(store, org: dict, now: Optional[datetime] = None) -> dict:
    """This month's spending against the company's optional monthly spending limit, in dollars of credit.
    No limit set (None) means nothing here ever pauses: the credit balance is then the only cap."""
    now = now or _utcnow()
    try:
        ls = wallet.limit_status(store, wallet.scope_for_org(org["id"]), org.get("monthly_budget_usd"), now)
    except Exception as exc:
        # The credit tables aren't there yet (the database update wasn't run). The company screen must still
        # load, so report "nothing spent, nothing paused" instead of failing. The startup check explains why.
        print(f"[credits] could not read spending for org {org.get('id')}; showing none: {exc}")
        limit = org.get("monthly_budget_usd")
        ls = {"spent_usd": 0.0, "limit_usd": float(limit) if limit else None, "remaining_usd": None, "over": False}
    return {
        "spent_usd": ls["spent_usd"],
        "budget_usd": ls["limit_usd"],
        "remaining_usd": ls["remaining_usd"],
        "over": ls["over"],
        "reviews_bought": store.usage_reviews(org["id"], month_start_iso(now)),
    }


# ------------------------------------------------------------------ alerts
def review_key(location_id: str, r: dict) -> str:
    raw = f"{location_id}|{r.get('source', 'google')}|{r.get('datetime_utc')}|{r['rating']}|{(r.get('text') or '')[:80]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def new_negative_candidates(reviews: List[dict], now: datetime, lookback_days: int) -> List[dict]:
    cutoff = now.astimezone(timezone.utc).replace(tzinfo=None) - timedelta(days=lookback_days)
    out = []
    for r in reviews:
        dt = _naive_utc(r.get("datetime_utc"))
        if r["rating"] <= 2 and dt is not None and dt >= cutoff:
            out.append(r)
    return out


def _owner_email(store, org: dict) -> Optional[str]:
    for m in store.list_members(org["id"]):
        if m["role"] == "owner":
            return m["email"]
    return None


def _alert_email(location: dict, alerts: List[dict]):
    n = len(alerts)
    where = location["name"] + (f" ({location['region']})" if location.get("region") else "")
    subject = f"⚠️ {n} new negative review{'s' if n != 1 else ''} - {location['name']}"
    lines = [f"{n} new 1-2 star review{'s' if n != 1 else ''} for {where}.", "",
             "Personal details have been stripped where detected.", ""]
    for a in alerts[:5]:
        detail = a["text"][:200] if a["has_text"] else "star rating only, no written comment"
        lines.append(f"- {a['rating']}★ on {SOURCE_LABELS.get(a['source'], a['source'])} ({a['review_date']}): {detail}")
    if n > 5:
        lines.append(f"...and {n - 5} more.")
    lines += ["", f"Open your task list: {getattr(config, 'FRONTEND_URL', '')}/org"]
    return subject, "\n".join(lines)


# ------------------------------------------------------------------- runs
def run_location(store, org: dict, location: dict, *, now: Optional[datetime] = None,
                 months: Optional[int] = None, notify: bool = True, kind: str = "monitor") -> dict:
    now = now or _utcnow()
    months = months or MONITOR_MONTHS

    status = usage_status(store, org, now)
    if status["over"]:
        return {"status": "skipped", "reason": "budget",
                "message": f"This month's spending limit (${status['budget_usd']:,.2f}) has been reached."}

    # Companies have no plan allowance: every pull comes out of the company's credit balance.
    try:
        wallet.precheck(store, wallet.scope_for_org(org["id"]), 0.0, who="org")
    except Exception as exc:
        return {"status": "skipped", "reason": "credits", "message": getattr(exc, "detail", None) or str(exc)}

    try:
        by_source, cached_flags, notes, fresh = pipeline.pull_reviews(
            location["google_query"], location.get("yelp_url"), months, want_yelp=bool(location.get("yelp_url")),
            others={src: location[f"{src}_url"] for src in RATED_EXTRA if location.get(f"{src}_url")},
        )
    except Exception as exc:                                  # one bad location must never stop the others
        detail = getattr(exc, "detail", None) or str(exc)
        return {"status": "error", "message": f"{location['name']}: {detail}"}

    bought = sum(fresh.values())
    if bought:
        store.add_usage(org["id"], location["id"], bought, kind)
    wallet.settle(store, wallet.scope_for_org(org["id"]), 0.0, credit_rates.cost_breakdown(fresh),
                  f"{'Scheduled check' if kind == 'monitor' else 'Check'} of {location['name']}")

    prev = store.latest_snapshot(location["id"])
    providers, providers_at = _providers_for_snapshot(store, org, location, prev, now, kind, notes)
    snap = metrics.compute_snapshot(by_source, months=months, fresh=fresh, notes=notes,
                                    prev_avg_rating=prev.get("avg_rating") if prev else None,
                                    industry=org.get("industry"), providers=providers, providers_checked_at=providers_at)
    snap["run_at"] = now.isoformat()
    saved = store.add_snapshot(location["id"], snap)

    inserted = []
    reviews = [r for rs in by_source.values() for r in rs]
    for r in new_negative_candidates(reviews, now, ALERT_LOOKBACK_DAYS):
        text = (r.get("text") or "").strip()
        row = store.add_alert_if_new({
            "org_id": org["id"], "location_id": location["id"], "review_key": review_key(location["id"], r),
            "source": r.get("source", "google"), "rating": r["rating"], "review_date": r.get("datetime_utc"),
            "text": redact_pii(text)[:500] if text else "", "has_text": bool(text),
        })
        if row:
            inserted.append(row)

    emailed = False
    if inserted and notify:
        recipient = location.get("manager_email") or _owner_email(store, org)
        if recipient:
            subject, body = _alert_email(location, inserted)
            emailed = bool(send_email(to_email=recipient, subject=subject, body=body))

    return {"status": "ok", "snapshot": saved, "new_alerts": len(inserted), "emailed": emailed,
            "notes": notes, "fresh_reviews": bought}


def run_due(store, now: Optional[datetime] = None, max_runs: Optional[int] = None) -> List[dict]:
    """Refreshes the locations that are overdue, oldest first, within each org's budget."""
    now = now or _utcnow()
    max_runs = MAX_RUNS_PER_TICK if max_runs is None else max_runs

    due = []
    for org in store.list_orgs():
        if usage_status(store, org, now)["over"]:
            continue                                          # nothing to do until next month
        try:
            wallet.precheck(store, wallet.scope_for_org(org["id"]), 0.0, who="org")
        except Exception:
            continue                                          # out of credit: paused until the owner adds more
        for loc in store.list_locations(org["id"]):
            if not loc.get("is_active", True):
                continue
            backoff = _error_backoff.get(loc["id"])
            if backoff and now < backoff:
                continue
            snap = store.latest_snapshot(loc["id"])
            last = _parse_iso(snap["run_at"]) if snap else None
            if last is None or now - last >= timedelta(hours=INTERVAL_HOURS):
                due.append((last or datetime.min.replace(tzinfo=timezone.utc), org, loc))

    due.sort(key=lambda x: x[0])
    results = []
    for _, org, loc in due[:max_runs]:
        res = run_location(store, org, loc, now=now)
        res["location_id"] = loc["id"]
        if res["status"] == "error":
            _error_backoff[loc["id"]] = now + timedelta(hours=ERROR_BACKOFF_HOURS)
        results.append(res)
    return results


# --------------------------------------------------------------- scheduler
_stop = threading.Event()


def start_scheduler():
    """Background loop inside the API process. Safe to leave on: it does nothing until
    an organization has locations. For several API instances use the cron endpoint instead."""
    if os.environ.get("ENABLE_SCHEDULER", "true").lower() not in ("1", "true", "yes"):
        return None

    def loop():
        if _stop.wait(60):                                    # let the app finish starting
            return
        while True:
            try:
                results = run_due(get_store())
                if results:
                    print(f"[scheduler] ran {len(results)} location(s): "
                          f"{sum(1 for r in results if r['status'] == 'ok')} ok")
            except Exception as exc:
                print(f"[scheduler] tick failed: {exc}")
            if _stop.wait(TICK_MINUTES * 60):
                return

    t = threading.Thread(target=loop, name="review-monitor", daemon=True)
    t.start()
    return t
