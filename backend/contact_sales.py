"""The Enterprise "Contact sales" form: emails the request to SALES_EMAIL and also saves it, so it is not lost if email fails.

Email goes out through the same SMTP settings as the alert emails (SMTP_HOST and friends). If those are not set, nothing can be
emailed: the request is then only saved (table contact_requests) and printed in the server log."""
import os
import re
import threading
import time
from collections import defaultdict, deque

DEFAULT_SALES_EMAIL = "jenevepilcher189@gmail.com"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PER_HOUR = 5                                  # per sender address
ALL_PER_HOUR = 40                             # across everyone: this form is public, so it must not become a spam pipe
_hits = defaultdict(deque)
_lock = threading.Lock()


def sales_email() -> str:
    return (os.environ.get("SALES_EMAIL") or DEFAULT_SALES_EMAIL).strip()


def allow(key: str, now=None, limit: int = PER_HOUR) -> bool:
    now = now if now is not None else time.time()
    with _lock:
        q = _hits[key]
        while q and q[0] <= now - 3600:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


def clean(text, limit: int) -> str:
    """One field, trimmed and cut to a sane length, with control characters removed (nothing here ever goes into an email header)."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", (text or "")).strip()[:limit]


def build(name, email, company, message) -> dict:
    fields = {"name": clean(name, 120), "email": clean(email, 254), "company_name": clean(company, 160), "message": clean(message, 4000)}
    if not fields["name"] or not fields["message"]:
        raise ValueError("Please enter your name and a message.")
    if not EMAIL_RE.match(fields["email"]):
        raise ValueError("Please enter a valid email address.")
    return fields


def email_text(f: dict) -> tuple:
    subject = "Enterprise enquiry" + (f" - {f['company_name']}" if f["company_name"] else "")
    subject = subject.replace("\r", " ").replace("\n", " ")[:150]
    body = (f"New Enterprise enquiry from the website.\n\nName: {f['name']}\nEmail (reply to this address): {f['email']}\n"
            f"Company: {f['company_name'] or '(not given)'}\n\nMessage:\n{f['message']}\n")
    return subject, body


def submit(fields: dict, send_email, save) -> dict:
    """Saves the request, then emails it. Returns what happened, for the server log (the visitor is only told it was received)."""
    saved = False
    try:
        save(fields)
        saved = True
    except Exception as exc:                   # noqa: BLE001  (e.g. the table has not been created yet)
        print(f"[contact-sales] could not save the request: {exc}")
    subject, body = email_text(fields)
    emailed = bool(send_email(to_email=sales_email(), subject=subject, body=body))
    if not emailed:
        print(f"[contact-sales] NOT EMAILED (SMTP missing or failed). Saved={saved}. {fields['name']} <{fields['email']}>: {fields['message'][:300]}")
    return {"saved": saved, "emailed": emailed}
