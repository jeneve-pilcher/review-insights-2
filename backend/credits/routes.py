"""Credit balance, buying credit packs (Stripe Checkout) and confirming a payment.

Security: the price and the credit amount come from OUR pack list, never from the browser. A payment
only adds credit after we ask Stripe whether that exact session was paid (and for the right amount),
and a database rule makes it impossible to credit the same session twice."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import config
from analysis import delivery_clients, opentable_client, outscraper_client, yelp_client
from auth import CurrentUser, get_current_user
from corporate.store import DuplicateRef, get_store
from supabase_client import get_profile, get_supabase_admin
from credits import rates, wallet
from setup_check import SETUP_HINT

router = APIRouter(prefix="/api/credits", tags=["credits"])


def _field(obj, name, default=None):
    """Stripe objects behave like dicts in some versions and like objects in others."""
    try:
        return obj[name]
    except Exception:
        return getattr(obj, name, default)


def _resolve(current_user: CurrentUser, scope: str) -> dict:
    store = get_store()
    if scope == "org":
        m = store.find_membership(current_user.id, current_user.email)
        if not m:
            raise HTTPException(status_code=403, detail="You're not part of an organization yet.")
        org = store.get_org(m["org_id"])
        return {"scope": wallet.scope_for_org(org["id"]), "allowance": 0.0, "can_buy": m["role"] == "owner",
                "can_set_limit": m["role"] == "owner", "limit_usd": org.get("monthly_budget_usd"),
                "who": "org", "org_id": org["id"], "name": org["name"]}
    paid = current_user.tier in ("pro", "enterprise")
    return {"scope": wallet.scope_for_user(current_user.id), "allowance": wallet.allowance_for_tier(current_user.tier),
            "can_buy": paid, "can_set_limit": paid, "who": "user", "org_id": None, "name": None,
            "limit_usd": (get_profile(current_user.id) or {}).get("monthly_limit_usd")}


def _stripe():
    import stripe
    key = getattr(config, "STRIPE_SECRET_KEY", None)
    if not key:
        raise HTTPException(status_code=500, detail="Payments aren't set up on this server (no Stripe key).")
    stripe.api_key = key
    return stripe


def _credit_purchase(purchase: dict, actor: CurrentUser) -> Optional[dict]:
    """Asks Stripe whether this session was paid and, if so, credits it exactly once.
    Returns {"credited": bool, ...} or None while it's still unpaid."""
    store = get_store()
    session = _stripe().checkout.Session.retrieve(purchase["session_id"])
    if _field(session, "payment_status") != "paid":
        return None
    if _field(session, "amount_total") != int(round(float(purchase["price_usd"]) * 100)):
        print(f"[credits] amount mismatch for {purchase['session_id']}: not crediting")
        return {"credited": False, "error": "The amount paid didn't match the pack. Contact support."}
    meta = _field(session, "metadata") or {}
    if _field(meta, "scope") != purchase["scope"]:
        print(f"[credits] scope mismatch for {purchase['session_id']}: not crediting")
        return {"credited": False, "error": "This payment doesn't match your account. Contact support."}

    try:
        balance = store.apply_credit(purchase["scope"], float(purchase["credit_usd"]), "purchase",
                                     description=f"Credit pack ${float(purchase['price_usd']):.2f}", ref=purchase["session_id"])
        credited = True
    except DuplicateRef:
        balance, credited = store.credit_balance(purchase["scope"]), False
    store.mark_purchase_paid(purchase["session_id"])

    if credited and purchase["scope"].startswith("org:"):
        store.add_audit(purchase["scope"][4:], actor.id, actor.email.lower(), "credit_purchase", None,
                        {"price_usd": purchase["price_usd"], "credit_usd": purchase["credit_usd"]})
    return {"credited": credited, "credit_usd": purchase["credit_usd"], "balance_usd": round(float(balance), 6)}


def _reconcile(ctx: dict, current_user: CurrentUser) -> None:
    """Credits purchases that were paid but never confirmed (for example the buyer closed the tab)."""
    store = get_store()
    try:
        for p in store.list_pending_purchases(ctx["scope"]):
            try:
                _credit_purchase(p, current_user)
            except HTTPException:
                continue
    except Exception as exc:
        print(f"[credits] reconcile skipped: {exc}")


@router.get("")
def get_credits(scope: str = "user", current_user: CurrentUser = Depends(get_current_user)):
    ctx = _resolve(current_user, scope)
    store = get_store()
    _reconcile(ctx, current_user)
    try:
        st = wallet.status(store, ctx["scope"], ctx["allowance"])
        ls = wallet.limit_status(store, ctx["scope"], ctx["limit_usd"])
        recent_rows = store.list_ledger(ctx["scope"], 15)
    except Exception as exc:
        # Almost always: the credit tables don't exist because the database update wasn't run. Say so.
        print(f"[credits] could not read the credit tables: {exc}")
        raise HTTPException(status_code=503, detail=f"Usage credit isn't set up in the database yet. {SETUP_HINT} ({str(exc)[:120]})")
    return {
        "scope": scope,
        "name": ctx["name"],
        **st,
        "monthly_limit_usd": ls["limit_usd"],
        "spent_this_month_usd": ls["spent_usd"],
        "limit_remaining_usd": ls["remaining_usd"],
        "limit_reached": ls["over"],
        "can_set_limit": ctx["can_set_limit"],
        "enforced": wallet.ENFORCED,
        "markup": rates.MARKUP,
        "packs": rates.packs(),
        "can_buy": ctx["can_buy"],
        "rates": rates.rates(),
        "caps": {"google": outscraper_client.FETCH_CAP, "yelp": yelp_client.YELP_CAP, "opentable": opentable_client.FETCH_CAP,
                 "doordash": delivery_clients.DOORDASH_CAP, "ubereats": delivery_clients.UBEREATS_CAP,
                 "grubhub": delivery_clients.GRUBHUB_CAP, "searches_per_page": 2},
        "recent": [{k: r.get(k) for k in ("created_at", "kind", "amount_usd", "cost_usd", "allowance_usd", "description", "balance_after")}
                   for r in recent_rows],
    }


class CheckoutRequest(BaseModel):
    pack_id: str = Field(..., min_length=1, max_length=20)
    scope: Literal["user", "org"] = "user"


class ConfirmRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=200)


class LimitRequest(BaseModel):
    scope: Literal["user", "org"] = "user"
    monthly_limit_usd: Optional[float] = Field(None, gt=0, le=1_000_000)   # None = no limit


@router.put("/limit")
def set_limit(req: LimitRequest, current_user: CurrentUser = Depends(get_current_user)):
    """Sets (or clears) the monthly spending limit, in dollars of API usage. Usage stops for the month once it
    is reached. Individuals set their own; for a company only the owner can."""
    ctx = _resolve(current_user, req.scope)
    if not ctx["can_set_limit"]:
        raise HTTPException(
            status_code=403,
            detail="Only the company owner can set the company's spending limit." if ctx["who"] == "org"
            else "Spending limits are for Pro and Enterprise accounts.",
        )
    if req.monthly_limit_usd is not None and req.monthly_limit_usd <= 0:
        raise HTTPException(status_code=400, detail="Enter an amount above $0, or leave it blank for no limit.")
    new = round(req.monthly_limit_usd, 2) if req.monthly_limit_usd is not None else None
    old = ctx["limit_usd"]

    if ctx["who"] == "org":
        store = get_store()
        store.update_org(ctx["org_id"], monthly_budget_usd=new)
        store.add_audit(ctx["org_id"], current_user.id, current_user.email.lower(), "budget_change", None, {"from": old, "to": new})
    else:
        try:
            get_supabase_admin().table("profiles").update({"monthly_limit_usd": new}).eq("id", current_user.id).execute()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Could not save your limit. If you just applied this update, run the SQL in the README first. ({exc})",
            )
    return {"monthly_limit_usd": new}


@router.post("/checkout")
def checkout(req: CheckoutRequest, current_user: CurrentUser = Depends(get_current_user)):
    ctx = _resolve(current_user, req.scope)
    if not ctx["can_buy"]:
        raise HTTPException(
            status_code=403,
            detail="Only the company owner can buy company credit." if ctx["who"] == "org"
            else "Credit is for Pro and Enterprise accounts. Upgrade to buy credit.",
        )
    pack = rates.find_pack(req.pack_id)
    if not pack:
        raise HTTPException(status_code=400, detail="That credit pack doesn't exist.")

    stripe = _stripe()
    frontend = getattr(config, "FRONTEND_URL", "")
    session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=current_user.email,
        line_items=[{"quantity": 1, "price_data": {
            "currency": "usd", "unit_amount": int(round(pack["price_usd"] * 100)),
            "product_data": {"name": f"${pack['credit_usd']:.2f} API credit",
                             "description": "Prepaid usage credit for reviews, web searches and reply drafts."}}}],
        metadata={"scope": ctx["scope"], "pack_id": pack["id"], "user_id": current_user.id, "credit_usd": str(pack["credit_usd"])},
        success_url=f"{frontend}/dashboard?credits=success&scope={req.scope}&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{frontend}/dashboard?credits=cancelled",
    )
    session_id, url = _field(session, "id"), _field(session, "url")
    get_store().add_purchase(session_id, ctx["scope"], current_user.id, current_user.email.lower(), pack["price_usd"], pack["credit_usd"])
    return {"checkout_url": url}


@router.post("/confirm")
def confirm(req: ConfirmRequest, current_user: CurrentUser = Depends(get_current_user)):
    purchase = get_store().get_purchase(req.session_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="That purchase wasn't found.")
    if purchase["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="That purchase belongs to someone else.")
    result = _credit_purchase(purchase, current_user)
    if result is None:
        return {"status": "pending", "credited": False}
    if result.get("error"):
        raise HTTPException(status_code=409, detail=result["error"])
    return {"status": "paid", **result}
