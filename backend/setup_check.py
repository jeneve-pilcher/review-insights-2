"""Checks that the database has everything this version needs, and says plainly what is missing.

The usual cause of a screen that "could not load" is a database update that was never run: new
tables and columns are added by backend/supabase/corporate.sql, and the app can't create them itself."""
from typing import List

SETUP_HINT = ("Run the updated backend/supabase/corporate.sql in the Supabase SQL Editor (paste all of it, then Run), "
              "restart the backend, and reload.")

# (table, column) pairs added by recent updates.
COLUMN_PROBES = [
    ("organizations", "monthly_budget_usd"),
    ("organizations", "white_label"),
    ("organizations", "brand_primary"),
    ("organizations", "sso_domain"),
    ("organizations", "industry"),
    ("profiles", "monthly_limit_usd"),
    ("profiles", "industry"),
    ("profiles", "terms_version"),
    ("profiles", "opentable_url"),
    ("profiles", "doordash_url"),
    ("profiles", "ubereats_url"),
    ("profiles", "grubhub_url"),
    ("location_snapshots", "industry"),
    ("location_snapshots", "providers"),
    ("location_snapshots", "providers_checked_at"),
    ("organizations", "provider_data_enabled"),
    ("locations", "provider_links"),
    ("locations", "opentable_url"),
    ("locations", "doordash_url"),
    ("locations", "ubereats_url"),
    ("locations", "grubhub_url"),
]


def find_problems(store, admin) -> List[str]:
    """Returns one plain sentence per missing piece (empty list = everything is in place)."""
    problems: List[str] = []

    def probe(what: str, fn) -> None:
        try:
            fn()
        except Exception as exc:
            problems.append(f"{what} ({str(exc)[:110]})")

    probe("The usage-credit tables are missing (credit_wallets, credit_ledger, credit_purchases)", lambda: (
        store.credit_balance("setup-check"),
        store.credit_spent("setup-check", "2000-01-01T00:00:00+00:00"),
        store.list_pending_purchases("setup-check"),
    ))
    for table, column in COLUMN_PROBES:
        probe(f"The column {table}.{column} is missing",
              lambda t=table, c=column: admin.table(t).select(c).limit(1).execute())
    return problems


def report(store, admin) -> List[str]:
    """Logs a clear banner at startup if anything is missing. Never raises."""
    try:
        problems = find_problems(store, admin)
    except Exception as exc:
        print(f"[setup] could not run the database check: {exc}")
        return []
    if problems:
        print("\n" + "=" * 78)
        print("[setup] THE DATABASE IS MISSING SOME PARTS THIS VERSION NEEDS:")
        for p in problems:
            print(f"   - {p}")
        print(f"[setup] FIX: {SETUP_HINT}")
        print("=" * 78 + "\n")
    else:
        print("[setup] database check passed: every table and column this version needs is present.")
    return problems
