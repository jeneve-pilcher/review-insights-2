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
from corporate.store import get_store
from email_alerts import send_email

MONITOR_MONTHS = int(os.environ.get("MONITOR_MONTHS", "3"))                # smaller window = cheaper scheduled runs
INTERVAL_HOURS = float(os.environ.get("MONITOR_INTERVAL_HOURS", "24"))     # how often each location refreshes
ALERT_LOOKBACK_DAYS = int(os.environ.get("ALERT_LOOKBACK_DAYS", "7"))      # only reviews this recent become alerts
TICK_MINUTES = float(os.environ.get("SCHEDULER_TICK_MINUTES", "30"))
MAX_RUNS_PER_TICK = int(os.environ.get("MAX_RUNS_PER_TICK", "10"))
COST_PER_1K_REVIEWS = float(os.environ.get("COST_PER_1K_REVIEWS", "3.0"))  # for the dollar estimate shown to users
ERROR_BACKOFF_HOURS = 6.0

SOURCE_LABELS = {"google": "Google", "yelp": "Yelp"}

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


def usage_status(store, org: dict, now: Optional[datetime] = None) -> dict:
    now = now or _utcnow()
    used = store.usage_reviews(org["id"], month_start_iso(now))
    budget = org.get("monthly_budget_reviews") or 0
    return {
        "used": used,
        "budget": budget,
        "remaining": max(0, budget - used),
        "est_cost_usd": round(used / 1000 * COST_PER_1K_REVIEWS, 2),
        "over": used >= budget,
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
                "message": f"This month's review budget ({status['budget']:,}) has been used."}

    try:
        by_source, cached_flags, notes, fresh = pipeline.pull_reviews(
            location["google_query"], location.get("yelp_url"), months, want_yelp=bool(location.get("yelp_url"))
        )
    except Exception as exc:                                  # one bad location must never stop the others
        detail = getattr(exc, "detail", None) or str(exc)
        return {"status": "error", "message": f"{location['name']}: {detail}"}

    bought = sum(fresh.values())
    if bought:
        store.add_usage(org["id"], location["id"], bought, kind)

    prev = store.latest_snapshot(location["id"])
    snap = metrics.compute_snapshot(by_source, months=months, fresh=fresh, notes=notes,
                                    prev_avg_rating=prev.get("avg_rating") if prev else None)
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
