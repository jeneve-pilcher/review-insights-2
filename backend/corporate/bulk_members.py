"""Adding many team members at once from a spreadsheet (CSV), optionally emailing each a sign-up invitation.

CSV headers: email (required), role (admin, manager or viewer; blank means viewer). Each valid row becomes a team member, exactly
like adding them one by one. If invitations are on, Supabase also creates the login and emails the person a link to choose a
password, except people on the company's single sign-on domain, who are added without an invitation and simply
sign in with SSO (Supabase sends that email through its own mail settings, not this app's SMTP). A person who already has a login is
just added to the team."""
import csv
import io
import os
import re
from typing import List, Tuple

MAX_ROWS = 200
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROLES = ("admin", "manager", "viewer")


def parse(text: str) -> Tuple[List[Tuple[int, dict]], List[dict]]:
    reader = csv.DictReader(io.StringIO((text or "").strip()))
    headers = {(h or "").strip().lower() for h in (reader.fieldnames or [])}
    if "email" not in headers:
        raise ValueError("The first row must be headers including 'email' (and optionally 'role').")
    rows, errors = [], []
    for i, raw in enumerate(reader, start=2):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items() if k is not None}
        if not any(row.values()):
            continue
        rows.append((i, row))
    if len(rows) > MAX_ROWS:
        raise ValueError(f"Add at most {MAX_ROWS} people at a time.")
    return rows, errors


def _invite(email: str, redirect_to: str):
    """Returns None when the invitation went out, else a short reason."""
    try:
        from supabase_client import get_supabase_admin
        get_supabase_admin().auth.admin.invite_user_by_email(email, {"redirect_to": redirect_to})
        return None
    except Exception as exc:                           # noqa: BLE001
        text = str(exc)
        if "already" in text.lower() and "regist" in text.lower():
            return "already has a login"
        return text[:160] or "the invitation could not be sent"


def run(store, org_id: str, actor_can_add_admins: bool, rows, send_invites: bool, redirect_to: str, duplicate_error,
        sso_domain: str = "") -> dict:
    added, skipped, invite_notes, sso_people = [], [], [], []
    sso_domain = (sso_domain or "").strip().lower()
    for line, row in rows:
        email = row.get("email", "").lower()
        role = (row.get("role") or "viewer").lower()
        if not EMAIL_RE.match(email):
            skipped.append({"row": line, "reason": f"'{row.get('email', '')}' isn't a valid email address"})
            continue
        if role not in ROLES:
            skipped.append({"row": line, "reason": f"role '{role}' isn't admin, manager or viewer"})
            continue
        if role == "admin" and not actor_can_add_admins:
            skipped.append({"row": line, "reason": "only the owner can add an admin"})
            continue
        try:
            store.add_member(org_id, email, role)
        except duplicate_error:
            skipped.append({"row": line, "reason": "already on the team"})
            continue
        added.append({"email": email, "role": role})
        if sso_domain and email.endswith("@" + sso_domain):
            sso_people.append(email)           # signs in with the company's single sign-on: no password, no invitation email
        elif send_invites:
            problem = _invite(email, redirect_to)
            if problem:
                invite_notes.append({"email": email, "reason": problem})
    return {"added": len(added), "people": added, "skipped": skipped,
            "invites_sent": (len(added) - len(invite_notes) - len(sso_people)) if send_invites else 0,
            "invite_problems": invite_notes, "sso_people": sso_people}
