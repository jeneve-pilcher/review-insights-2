"""Credit balances and the plan allowance.

Order of spending: the monthly plan allowance first (Free and Pro/Enterprise accounts), then credit.
Companies have no allowance: everything comes from the company's credit balance. A run is allowed to
start only if something is available; the actual cost is deducted afterwards (never more than the real
API cost). A single run can push the balance slightly negative (bounded by an overdraft floor), after
which further runs are blocked until credit is added.
"""
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException

ENFORCED = os.environ.get("CREDITS_ENFORCED", "true").lower() in ("1", "true", "yes")
FREE_ALLOWANCE = float(os.environ.get("FREE_ALLOWANCE_USD", "1.00"))
PRO_ALLOWANCE = float(os.environ.get("PLAN_INCLUDED_USD_PRO", "10.00"))
ENTERPRISE_ALLOWANCE = float(os.environ.get("PLAN_INCLUDED_USD_ENTERPRISE", "10.00"))
MIN_RUN_USD = float(os.environ.get("MIN_RUN_BALANCE_USD", "0.10"))
OVERDRAFT_USD = float(os.environ.get("CREDIT_OVERDRAFT_USD", "2.00"))


def scope_for_user(user_id: str) -> str:
    return f"user:{user_id}"


def scope_for_org(org_id: str) -> str:
    return f"org:{org_id}"


def allowance_for_tier(tier: str) -> float:
    return {"pro": PRO_ALLOWANCE, "enterprise": ENTERPRISE_ALLOWANCE}.get(tier, FREE_ALLOWANCE)


def month_start_iso(now: Optional[datetime] = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def status(store, scope: str, allowance: float, now: Optional[datetime] = None) -> dict:
    balance = float(store.credit_balance(scope))
    used = float(store.allowance_used(scope, month_start_iso(now)))
    remaining = max(0.0, allowance - used)
    return {
        "balance_usd": round(balance, 6),
        "allowance_usd": round(allowance, 6),
        "allowance_used_usd": round(min(used, allowance), 6),
        "allowance_remaining_usd": round(remaining, 6),
        "available_usd": round(remaining + max(0.0, balance), 6),
    }


def limit_status(store, scope: str, limit_usd: Optional[float], now: Optional[datetime] = None) -> dict:
    """This month's API spending against an optional monthly spending limit (None = no limit).
    "Spent" is what the runs actually cost (the plan allowance's share included), taken from the ledger."""
    spent = float(store.credit_spent(scope, month_start_iso(now)))
    limit = float(limit_usd) if limit_usd else None
    return {
        "spent_usd": round(spent, 4),
        "limit_usd": limit,
        "remaining_usd": None if limit is None else round(max(0.0, limit - spent), 4),
        "over": limit is not None and spent >= limit,
    }


def _limit_message(who: str, limit: float) -> str:
    subject = "Your company has" if who == "org" else "You've"
    return (f"{subject} reached the monthly spending limit of ${limit:,.2f}. Usage resumes next month, "
            "or the limit can be raised.")


def _blocked_message(who: str, tier: Optional[str], st: dict) -> str:
    if who == "org":
        return ("Your company's credit balance is used up, so this can't run. The company owner can add credit "
                f"(balance ${st['balance_usd']:.2f}).")
    if tier == "free" or tier is None:
        return "You've used this month's free allowance. Upgrade to Pro to keep analyzing."
    return (f"You've used your ${st['allowance_usd']:.2f} monthly plan allowance and have "
            f"${max(0.0, st['balance_usd']):.2f} of credit left. Buy credit to keep going.")


def precheck(store, scope: str, allowance: float, *, who: str = "user", tier: Optional[str] = None,
             limit_usd: Optional[float] = None) -> None:
    """Raises HTTPException(402) if the monthly spending limit has been reached, or if there's nothing to
    spend. The run that crosses the limit is allowed to finish; the next one is refused. If the credit tables
    are unreachable (for example the SQL hasn't been run yet) it logs and lets the request through."""
    if not ENFORCED:
        return
    try:
        st = status(store, scope, allowance)
        over = limit_status(store, scope, limit_usd)["over"] if limit_usd else False
    except Exception as exc:
        print(f"[credits] could not read balance for {scope}; allowing the request: {exc}")
        return
    if over:
        raise HTTPException(status_code=402, detail=_limit_message(who, float(limit_usd)))
    if st["available_usd"] < MIN_RUN_USD:
        raise HTTPException(status_code=402, detail=_blocked_message(who, tier, st))


def settle(store, scope: str, allowance: float, breakdown: dict, description: str, *, ref: Optional[str] = None) -> Optional[dict]:
    """Charges what a run actually cost: plan allowance first, then credit. Returns a summary for the UI,
    or None when billing is off or the credit tables can't be reached."""
    if not ENFORCED:
        return None
    cost = float(breakdown["total_usd"])
    try:
        if cost <= 0:
            st = status(store, scope, allowance)
            return {"cost_usd": 0.0, "from_allowance_usd": 0.0, "from_credit_usd": 0.0, "balance_usd": st["balance_usd"],
                    "allowance_remaining_usd": st["allowance_remaining_usd"], "lines": []}
        st = status(store, scope, allowance)
        from_allowance = min(cost, st["allowance_remaining_usd"])
        from_credit = round(cost - from_allowance, 6)
        balance = store.apply_credit(scope, -from_credit, "usage", cost_usd=cost, allowance_usd=from_allowance,
                                     description=f"{description}: {', '.join(l['label'] + ' x' + str(l['units']) for l in breakdown['lines'])}",
                                     ref=ref, floor=-OVERDRAFT_USD)
        return {"cost_usd": round(cost, 6), "from_allowance_usd": round(from_allowance, 6), "from_credit_usd": from_credit,
                "balance_usd": round(float(balance), 6),
                "allowance_remaining_usd": round(st["allowance_remaining_usd"] - from_allowance, 6), "lines": breakdown["lines"]}
    except Exception as exc:
        print(f"[credits] could not record a charge of ${cost:.4f} for {scope}: {exc}")
        return None
