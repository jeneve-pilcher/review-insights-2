"""Storage for organizations, locations, snapshots, alerts, audit and usage.

Two implementations share one interface: MemoryStore (tests, local experiments)
and SupabaseStore (production, using the same service-role client as the rest of
the app). Emails are always stored lowercase.
"""
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _copy(row):
    return dict(row) if row is not None else None


class DuplicateMember(Exception):
    pass


class DuplicateRef(Exception):
    """The same purchase (Stripe session) was credited twice."""


# ----------------------------------------------------------------------------
class MemoryStore:
    def __init__(self):
        self._lock = threading.RLock()
        self.orgs: Dict[str, dict] = {}
        self.members: Dict[str, dict] = {}
        self.locations: Dict[str, dict] = {}
        self.snapshot_rows: List[dict] = []
        self.alerts: Dict[str, dict] = {}
        self.audit_rows: List[dict] = []
        self.usage_rows: List[dict] = []
        self.reply_rows: Dict[tuple, dict] = {}
        self.wallets: Dict[str, float] = {}
        self.ledger_rows: List[dict] = []
        self.purchases: Dict[str, dict] = {}

    # ---- organizations & members
    def create_org(self, name, owner_id, owner_email, monthly_budget_usd=None):
        with self._lock:
            org = {"id": str(uuid.uuid4()), "name": name, "owner_id": owner_id,
                   "monthly_budget_usd": monthly_budget_usd, "created_at": now_iso()}
            self.orgs[org["id"]] = org
            member = {"id": str(uuid.uuid4()), "org_id": org["id"], "user_id": owner_id,
                      "email": owner_email.lower(), "role": "owner", "created_at": now_iso()}
            self.members[member["id"]] = member
            return _copy(org)

    def get_org(self, org_id):
        with self._lock:
            return _copy(self.orgs.get(org_id))

    def list_orgs(self):
        with self._lock:
            return [_copy(o) for o in self.orgs.values()]

    def find_org_by_sso_domain(self, domain):
        with self._lock:
            return next((_copy(o) for o in self.orgs.values() if o.get("sso_domain") == domain), None)

    def update_org(self, org_id, **fields):
        with self._lock:
            self.orgs[org_id].update(fields)
            return _copy(self.orgs[org_id])

    def find_membership(self, user_id, email):
        with self._lock:
            for m in self.members.values():
                if m["user_id"] == user_id:
                    return _copy(m)
            for m in self.members.values():
                if m["user_id"] is None and m["email"] == (email or "").lower():
                    m["user_id"] = user_id          # first login by an invited email links the account
                    return _copy(m)
            return None

    def list_members(self, org_id):
        with self._lock:
            return sorted((_copy(m) for m in self.members.values() if m["org_id"] == org_id),
                          key=lambda m: m["created_at"])

    def get_member(self, member_id):
        with self._lock:
            return _copy(self.members.get(member_id))

    def add_member(self, org_id, email, role):
        with self._lock:
            email = email.lower()
            if any(m["org_id"] == org_id and m["email"] == email for m in self.members.values()):
                raise DuplicateMember(email)
            m = {"id": str(uuid.uuid4()), "org_id": org_id, "user_id": None, "email": email,
                 "role": role, "created_at": now_iso()}
            self.members[m["id"]] = m
            return _copy(m)

    def update_member(self, member_id, **fields):
        with self._lock:
            self.members[member_id].update(fields)
            return _copy(self.members[member_id])

    def remove_member(self, member_id):
        with self._lock:
            self.members.pop(member_id, None)

    # ---- locations
    def add_location(self, org_id, data):
        with self._lock:
            loc = {"id": str(uuid.uuid4()), "org_id": org_id, "name": data["name"],
                   "brand": data.get("brand"), "region": data.get("region"),
                   "google_query": data["google_query"], "yelp_url": data.get("yelp_url"),
                   "opentable_url": data.get("opentable_url"),
                   "doordash_url": data.get("doordash_url"), "ubereats_url": data.get("ubereats_url"), "grubhub_url": data.get("grubhub_url"), "provider_links": data.get("provider_links") or [],
                   "manager_email": (data.get("manager_email") or None) and data["manager_email"].lower(),
                   "is_active": True, "created_at": now_iso()}
            self.locations[loc["id"]] = loc
            return _copy(loc)

    def list_locations(self, org_id):
        with self._lock:
            return sorted((_copy(l) for l in self.locations.values() if l["org_id"] == org_id),
                          key=lambda l: l["name"].lower())

    def get_location(self, location_id):
        with self._lock:
            return _copy(self.locations.get(location_id))

    def update_location(self, location_id, **fields):
        with self._lock:
            if fields.get("manager_email"):
                fields["manager_email"] = fields["manager_email"].lower()
            self.locations[location_id].update(fields)
            return _copy(self.locations[location_id])

    def delete_location(self, location_id):
        with self._lock:
            self.locations.pop(location_id, None)
            self.snapshot_rows = [s for s in self.snapshot_rows if s["location_id"] != location_id]
            self.alerts = {k: a for k, a in self.alerts.items() if a["location_id"] != location_id}

    # ---- snapshots
    def add_snapshot(self, location_id, snapshot):
        with self._lock:
            row = {"id": str(uuid.uuid4()), "location_id": location_id,
                   **{k: v for k, v in snapshot.items() if k != "id"}}
            row.setdefault("run_at", now_iso())
            self.snapshot_rows.append(row)
            return _copy(row)

    def snapshots(self, location_id, limit=30):
        with self._lock:
            rows = [r for r in self.snapshot_rows if r["location_id"] == location_id]
            return [_copy(r) for r in sorted(rows, key=lambda r: r["run_at"], reverse=True)[:limit]]

    def latest_snapshot(self, location_id):
        rows = self.snapshots(location_id, 1)
        return rows[0] if rows else None

    def latest_snapshots_for_org(self, org_id):
        return {l["id"]: s for l in self.list_locations(org_id)
                if (s := self.latest_snapshot(l["id"])) is not None}

    # ---- alerts / tasks
    def add_alert_if_new(self, alert):
        with self._lock:
            if any(a["location_id"] == alert["location_id"] and a["review_key"] == alert["review_key"]
                   for a in self.alerts.values()):
                return None
            row = {"id": str(uuid.uuid4()), "status": "open", "assigned_to": None, "note": None,
                   "created_at": now_iso(), "updated_at": now_iso(), **alert}
            self.alerts[row["id"]] = row
            return _copy(row)

    def list_alerts(self, org_id, status=None, location_id=None, limit=200):
        with self._lock:
            rows = [a for a in self.alerts.values() if a["org_id"] == org_id
                    and (status is None or a["status"] == status)
                    and (location_id is None or a["location_id"] == location_id)]
            rows.sort(key=lambda a: a["created_at"], reverse=True)
            return [_copy(a) for a in rows[:limit]]

    def get_alert(self, alert_id):
        with self._lock:
            return _copy(self.alerts.get(alert_id))

    def update_alert(self, alert_id, **fields):
        with self._lock:
            self.alerts[alert_id].update(fields)
            self.alerts[alert_id]["updated_at"] = now_iso()
            return _copy(self.alerts[alert_id])

    # ---- audit & usage
    def add_audit(self, org_id, user_id, user_email, action, target=None, detail=None):
        with self._lock:
            self.audit_rows.append({"id": str(uuid.uuid4()), "org_id": org_id, "user_id": user_id,
                                    "user_email": user_email, "action": action, "target": target,
                                    "detail": detail or {}, "created_at": now_iso()})

    def list_audit(self, org_id, limit=100):
        with self._lock:
            rows = [r for r in self.audit_rows if r["org_id"] == org_id]
            return [_copy(r) for r in sorted(rows, key=lambda r: r["created_at"], reverse=True)[:limit]]

    def add_usage(self, org_id, location_id, reviews, kind):
        with self._lock:
            self.usage_rows.append({"id": str(uuid.uuid4()), "org_id": org_id, "location_id": location_id,
                                    "reviews": int(reviews), "kind": kind, "created_at": now_iso()})

    def usage_reviews(self, org_id, since_iso):
        with self._lock:
            return sum(u["reviews"] for u in self.usage_rows
                       if u["org_id"] == org_id and u["created_at"] >= since_iso)


    # ---- review replies (drafts / sent), per scope ("user:<id>" or "loc:<location id>")
    def get_replies(self, scope):
        with self._lock:
            return {k: _copy(r) for (sc, k), r in self.reply_rows.items() if sc == scope}

    def save_reply(self, scope, review_key, fields):
        with self._lock:
            row = self.reply_rows.get((scope, review_key))
            if row:
                row.update(fields)
                row["updated_at"] = now_iso()
            else:
                row = {"id": str(uuid.uuid4()), "scope": scope, "review_key": review_key,
                       "created_at": now_iso(), "updated_at": now_iso(), **fields}
                self.reply_rows[(scope, review_key)] = row
            return _copy(row)

    # ---- credits: wallets, ledger, purchases (scope = "user:<id>" or "org:<id>")
    def credit_balance(self, scope):
        with self._lock:
            return float(self.wallets.get(scope, 0.0))

    def apply_credit(self, scope, amount, kind, *, cost_usd=0.0, allowance_usd=0.0, description="", ref=None, floor=0.0):
        with self._lock:
            if kind == "purchase" and ref and any(r["kind"] == "purchase" and r["ref"] == ref for r in self.ledger_rows):
                raise DuplicateRef(ref)
            old = self.wallets.get(scope, 0.0)
            new = min(old, max(old + amount, floor)) if amount < 0 else old + amount
            self.wallets[scope] = new
            self.ledger_rows.append({"id": str(uuid.uuid4()), "scope": scope, "kind": kind, "amount_usd": round(new - old, 6),
                                     "cost_usd": cost_usd, "allowance_usd": allowance_usd, "description": description, "ref": ref,
                                     "balance_after": round(new, 6), "created_at": now_iso()})
            return round(new, 6)

    def allowance_used(self, scope, since_iso):
        with self._lock:
            return round(sum(r["allowance_usd"] for r in self.ledger_rows
                             if r["scope"] == scope and r["kind"] == "usage" and r["created_at"] >= since_iso), 6)

    def credit_spent(self, scope, since_iso):
        """Dollars of usage (what the runs actually cost) recorded for this wallet since `since_iso`."""
        with self._lock:
            return round(sum(r["cost_usd"] for r in self.ledger_rows
                             if r["scope"] == scope and r["kind"] == "usage" and r["created_at"] >= since_iso), 6)

    def list_ledger(self, scope, limit=20):
        with self._lock:
            rows = [r for r in self.ledger_rows if r["scope"] == scope]
            return [_copy(r) for r in sorted(rows, key=lambda r: r["created_at"], reverse=True)[:limit]]

    def add_purchase(self, session_id, scope, user_id, user_email, price_usd, credit_usd):
        with self._lock:
            row = {"id": str(uuid.uuid4()), "session_id": session_id, "scope": scope, "user_id": user_id,
                   "user_email": user_email, "price_usd": price_usd, "credit_usd": credit_usd,
                   "status": "pending", "created_at": now_iso(), "paid_at": None}
            self.purchases[session_id] = row
            return _copy(row)

    def get_purchase(self, session_id):
        with self._lock:
            return _copy(self.purchases.get(session_id))

    def list_pending_purchases(self, scope, limit=10):
        with self._lock:
            rows = [p for p in self.purchases.values() if p["scope"] == scope and p["status"] == "pending"]
            return [_copy(p) for p in sorted(rows, key=lambda p: p["created_at"], reverse=True)[:limit]]

    def mark_purchase_paid(self, session_id):
        with self._lock:
            if session_id in self.purchases:
                self.purchases[session_id].update(status="paid", paid_at=now_iso())


# ----------------------------------------------------------------------------
class SupabaseStore:
    """Same interface, backed by Supabase tables (see supabase/corporate.sql)."""

    def __init__(self, client=None):
        self._client = client

    @property
    def c(self):
        if self._client is None:
            from supabase_client import get_supabase_admin   # lazy: keeps tests free of the real client
            self._client = get_supabase_admin()
        return self._client

    def _t(self, name):
        return self.c.table(name)

    @staticmethod
    def _rows(resp):
        return resp.data or []

    @staticmethod
    def _one(resp):
        rows = resp.data or []
        return rows[0] if rows else None

    # ---- organizations & members
    def create_org(self, name, owner_id, owner_email, monthly_budget_usd=None):
        org = self._one(self._t("organizations").insert(
            {"name": name, "owner_id": owner_id, "monthly_budget_usd": monthly_budget_usd}).execute())
        self._t("org_members").insert(
            {"org_id": org["id"], "user_id": owner_id, "email": owner_email.lower(), "role": "owner"}).execute()
        return org

    def get_org(self, org_id):
        return self._one(self._t("organizations").select("*").eq("id", org_id).limit(1).execute())

    def list_orgs(self):
        return self._rows(self._t("organizations").select("*").execute())

    def find_org_by_sso_domain(self, domain):
        return self._one(self._t("organizations").select("*").eq("sso_domain", domain).limit(1).execute())

    def update_org(self, org_id, **fields):
        self._t("organizations").update(fields).eq("id", org_id).execute()
        return self.get_org(org_id)

    def find_membership(self, user_id, email):
        row = self._one(self._t("org_members").select("*").eq("user_id", user_id).limit(1).execute())
        if row:
            return row
        row = self._one(self._t("org_members").select("*").eq("email", (email or "").lower()).limit(1).execute())
        if row and row.get("user_id") is None:
            self._t("org_members").update({"user_id": user_id}).eq("id", row["id"]).execute()
            row["user_id"] = user_id
            return row
        return None

    def list_members(self, org_id):
        return self._rows(self._t("org_members").select("*").eq("org_id", org_id).order("created_at").execute())

    def get_member(self, member_id):
        return self._one(self._t("org_members").select("*").eq("id", member_id).limit(1).execute())

    def add_member(self, org_id, email, role):
        email = email.lower()
        existing = self._one(self._t("org_members").select("*").eq("org_id", org_id).eq("email", email).limit(1).execute())
        if existing:
            raise DuplicateMember(email)
        return self._one(self._t("org_members").insert({"org_id": org_id, "email": email, "role": role}).execute())

    def update_member(self, member_id, **fields):
        self._t("org_members").update(fields).eq("id", member_id).execute()
        return self.get_member(member_id)

    def remove_member(self, member_id):
        self._t("org_members").delete().eq("id", member_id).execute()

    # ---- locations
    def add_location(self, org_id, data):
        row = {"org_id": org_id, "name": data["name"], "brand": data.get("brand"), "region": data.get("region"),
               "google_query": data["google_query"], "yelp_url": data.get("yelp_url"),
                   "opentable_url": data.get("opentable_url"),
                   "doordash_url": data.get("doordash_url"), "ubereats_url": data.get("ubereats_url"), "grubhub_url": data.get("grubhub_url"), "provider_links": data.get("provider_links") or [],
               "manager_email": (data.get("manager_email") or None) and data["manager_email"].lower(),
               "is_active": True}
        return self._one(self._t("locations").insert(row).execute())

    def list_locations(self, org_id):
        rows = self._rows(self._t("locations").select("*").eq("org_id", org_id).execute())
        # Sorted here, not by the database: SQL sort order depends on collation settings.
        return sorted(rows, key=lambda l: (l["name"] or "").lower())

    def get_location(self, location_id):
        return self._one(self._t("locations").select("*").eq("id", location_id).limit(1).execute())

    def update_location(self, location_id, **fields):
        if fields.get("manager_email"):
            fields["manager_email"] = fields["manager_email"].lower()
        self._t("locations").update(fields).eq("id", location_id).execute()
        return self.get_location(location_id)

    def delete_location(self, location_id):
        # snapshots and alerts are removed by ON DELETE CASCADE
        self._t("locations").delete().eq("id", location_id).execute()

    # ---- snapshots
    OPTIONAL_SNAPSHOT_COLUMNS = ("industry", "providers", "providers_checked_at")

    def add_snapshot(self, location_id, snapshot):
        row = {**{k: v for k, v in snapshot.items() if k != "id"}, "location_id": location_id}
        row.setdefault("run_at", now_iso())
        # A database update that adds an optional column may not have been run yet. The check itself must still be
        # saved, so drop the optional columns the database complains about (it names one at a time) and try again.
        for _ in range(len(self.OPTIONAL_SNAPSHOT_COLUMNS) + 1):
            try:
                return self._one(self._t("location_snapshots").insert(row).execute())
            except Exception as exc:
                msg = str(exc).lower()
                missing = [k for k in self.OPTIONAL_SNAPSHOT_COLUMNS if k in row and (f"'{k}'" in msg or f'"{k}"' in msg)]
                if not missing:
                    raise
                for k in missing:
                    row.pop(k)
        raise RuntimeError("could not save the check")

    def snapshots(self, location_id, limit=30):
        return self._rows(self._t("location_snapshots").select("*").eq("location_id", location_id)
                          .order("run_at", desc=True).limit(limit).execute())

    def latest_snapshot(self, location_id):
        rows = self.snapshots(location_id, 1)
        return rows[0] if rows else None

    def latest_snapshots_for_org(self, org_id):
        ids = [l["id"] for l in self.list_locations(org_id)]
        if not ids:
            return {}
        rows = self._rows(self._t("location_snapshots").select("*").in_("location_id", ids)
                          .order("run_at", desc=True).limit(len(ids) * 5).execute())
        out = {}
        for r in rows:                       # newest first, so the first one seen per location is its latest
            out.setdefault(r["location_id"], r)
        for lid in ids:                      # a location whose latest fell outside the page: ask directly
            if lid not in out:
                s = self.latest_snapshot(lid)
                if s:
                    out[lid] = s
        return out

    # ---- alerts / tasks
    def add_alert_if_new(self, alert):
        try:
            return self._one(self._t("review_alerts").insert(alert).execute())
        except Exception as exc:
            if "23505" in str(exc) or "duplicate" in str(exc).lower():
                return None                  # already known: the unique (location_id, review_key) index says so
            raise

    def list_alerts(self, org_id, status=None, location_id=None, limit=200):
        q = self._t("review_alerts").select("*").eq("org_id", org_id)
        if status:
            q = q.eq("status", status)
        if location_id:
            q = q.eq("location_id", location_id)
        return self._rows(q.order("created_at", desc=True).limit(limit).execute())

    def get_alert(self, alert_id):
        return self._one(self._t("review_alerts").select("*").eq("id", alert_id).limit(1).execute())

    def update_alert(self, alert_id, **fields):
        self._t("review_alerts").update({**fields, "updated_at": now_iso()}).eq("id", alert_id).execute()
        return self.get_alert(alert_id)

    # ---- audit & usage
    def add_audit(self, org_id, user_id, user_email, action, target=None, detail=None):
        self._t("audit_log").insert({"org_id": org_id, "user_id": user_id, "user_email": user_email,
                                     "action": action, "target": target, "detail": detail or {}}).execute()

    def list_audit(self, org_id, limit=100):
        return self._rows(self._t("audit_log").select("*").eq("org_id", org_id)
                          .order("created_at", desc=True).limit(limit).execute())

    def add_usage(self, org_id, location_id, reviews, kind):
        self._t("usage_events").insert({"org_id": org_id, "location_id": location_id,
                                        "reviews": int(reviews), "kind": kind}).execute()

    def usage_reviews(self, org_id, since_iso):
        rows = self._rows(self._t("usage_events").select("reviews").eq("org_id", org_id)
                          .gte("created_at", since_iso).execute())
        return sum(r["reviews"] for r in rows)

    # ---- review replies
    def get_replies(self, scope):
        rows = self._rows(self._t("review_replies").select("*").eq("scope", scope).limit(5000).execute())
        return {r["review_key"]: r for r in rows}

    def save_reply(self, scope, review_key, fields):
        def current():
            return self._one(self._t("review_replies").select("*").eq("scope", scope)
                             .eq("review_key", review_key).limit(1).execute())

        def update(row):
            self._t("review_replies").update({**fields, "updated_at": now_iso()}).eq("id", row["id"]).execute()
            return current()

        row = current()
        if row:
            return update(row)
        try:
            return self._one(self._t("review_replies").insert(
                {"scope": scope, "review_key": review_key, **fields}).execute())
        except Exception as exc:
            if "23505" in str(exc) or "duplicate" in str(exc).lower():   # lost a race with another save: update instead
                return update(current())
            raise

    # ---- credits
    def credit_balance(self, scope):
        row = self._one(self._t("credit_wallets").select("*").eq("scope", scope).limit(1).execute())
        return float(row["balance_usd"]) if row else 0.0

    def apply_credit(self, scope, amount, kind, *, cost_usd=0.0, allowance_usd=0.0, description="", ref=None, floor=0.0):
        # One atomic database function: it locks the wallet row, clamps at the floor, writes the ledger
        # row, and rejects a repeat purchase reference (so a payment can never be credited twice).
        try:
            resp = self.c.rpc("credit_apply", {
                "p_scope": scope, "p_amount": amount, "p_kind": kind, "p_cost": cost_usd, "p_allowance": allowance_usd,
                "p_description": description, "p_ref": ref, "p_floor": floor,
            }).execute()
        except Exception as exc:
            if "23505" in str(exc) or "duplicate" in str(exc).lower():
                raise DuplicateRef(ref)
            raise
        return round(float(resp.data), 6)

    def allowance_used(self, scope, since_iso):
        rows = self._rows(self._t("credit_ledger").select("allowance_usd").eq("scope", scope).eq("kind", "usage")
                          .gte("created_at", since_iso).execute())
        return round(sum(float(r["allowance_usd"] or 0) for r in rows), 6)

    def credit_spent(self, scope, since_iso):
        rows = self._rows(self._t("credit_ledger").select("cost_usd").eq("scope", scope).eq("kind", "usage")
                          .gte("created_at", since_iso).execute())
        return round(sum(float(r["cost_usd"] or 0) for r in rows), 6)

    def list_ledger(self, scope, limit=20):
        return self._rows(self._t("credit_ledger").select("*").eq("scope", scope).order("created_at", desc=True).limit(limit).execute())

    def add_purchase(self, session_id, scope, user_id, user_email, price_usd, credit_usd):
        return self._one(self._t("credit_purchases").insert({
            "session_id": session_id, "scope": scope, "user_id": user_id, "user_email": user_email,
            "price_usd": price_usd, "credit_usd": credit_usd, "status": "pending"}).execute())

    def get_purchase(self, session_id):
        return self._one(self._t("credit_purchases").select("*").eq("session_id", session_id).limit(1).execute())

    def list_pending_purchases(self, scope, limit=10):
        return self._rows(self._t("credit_purchases").select("*").eq("scope", scope).eq("status", "pending")
                          .order("created_at", desc=True).limit(limit).execute())

    def mark_purchase_paid(self, session_id):
        self._t("credit_purchases").update({"status": "paid", "paid_at": now_iso()}).eq("session_id", session_id).execute()


# ----------------------------------------------------------------------------
_store = None
_store_lock = threading.Lock()


def get_store():
    global _store
    with _store_lock:
        if _store is None:
            _store = SupabaseStore()
        return _store


def set_store(store) -> None:
    global _store
    with _store_lock:
        _store = store
