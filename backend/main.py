from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import config
from analysis import pipeline
from analysis.mentions import default_terms
from analysis.yelp_client import normalize_yelp_url
from auth import CurrentUser, get_current_user
from billing import router as billing_router
from corporate import monitor
from corporate.store import get_store
from corporate.routes import internal_router, router as org_router
from replies import router as replies_router
from schemas import (
    AcceptTermsRequest,
    EnterpriseContactRequest,
    SetBusinessLocationRequest,
    SetYelpUrlRequest,
    UnifiedAnalysisRequest,
)
from supabase_client import delete_user, get_profile, get_supabase_admin, set_business_location

app = FastAPI(title="Review Insights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(billing_router)
app.include_router(org_router)
app.include_router(internal_router)
app.include_router(replies_router)


@app.on_event("startup")
def _start_monitor():
    # Always-on monitoring: refreshes each location on a schedule (see corporate/monitor.py).
    monitor.start_scheduler()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/me")
def me(current_user: CurrentUser = Depends(get_current_user)):
    profile = get_profile(current_user.id) or {}
    try:
        membership = get_store().find_membership(current_user.id, current_user.email)
    except Exception:
        membership = None   # the company tables haven't been created yet: carry on as a single-business account
    return {
        "id": current_user.id,
        "email": current_user.email,
        "tier": current_user.tier,
        "business_location": current_user.business_location,
        "yelp_url": profile.get("yelp_url"),
        "org_role": membership["role"] if membership else None,
        "terms_version": profile.get("terms_version"),
        "terms_accepted_at": profile.get("terms_accepted_at"),
    }


@app.post("/api/me/accept-terms")
def accept_terms(req: AcceptTermsRequest, current_user: CurrentUser = Depends(get_current_user)):
    """Records which version of the Terms of Service this person agreed to, and when."""
    accepted_at = datetime.now(timezone.utc).isoformat()
    try:
        get_supabase_admin().table("profiles").update(
            {"terms_version": req.version.strip(), "terms_accepted_at": accepted_at}
        ).eq("id", current_user.id).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not record your agreement. If you just applied this update, run the terms SQL in "
                f"Supabase first (see README). ({exc})"
            ),
        )
    return {"terms_version": req.version.strip(), "terms_accepted_at": accepted_at}


@app.post("/api/me/business-location")
def set_my_business_location(
    req: SetBusinessLocationRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    # Set-once by design: stops one account from being reused to analyze a
    # series of unrelated businesses.
    if current_user.business_location:
        raise HTTPException(
            status_code=400,
            detail="Business location is already set for this account. Contact support to change it.",
        )
    set_business_location(current_user.id, req.business_location)
    return {"business_location": req.business_location}


@app.post("/api/me/yelp-url")
def set_my_yelp_url(
    req: SetYelpUrlRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    # Set-once for the same reason as the business location.
    profile = get_profile(current_user.id) or {}
    if profile.get("yelp_url"):
        raise HTTPException(
            status_code=400,
            detail="A Yelp page is already set for this account. Contact support to change it.",
        )
    try:
        url = normalize_yelp_url(req.yelp_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        get_supabase_admin().table("profiles").update({"yelp_url": url}).eq("id", current_user.id).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not save your Yelp link. If you just applied this update, add the column in "
                f"Supabase first: alter table public.profiles add column if not exists yelp_url text. ({exc})"
            ),
        )
    return {"yelp_url": url}


@app.delete("/api/me")
def delete_my_account(current_user: CurrentUser = Depends(get_current_user)):
    # Cancel any active Stripe subscription first so the person isn't
    # billed again after their account no longer exists.
    profile = get_profile(current_user.id)
    subscription_id = profile.get("stripe_subscription_id") if profile else None

    if subscription_id and config.STRIPE_SECRET_KEY:
        try:
            import stripe
            stripe.api_key = config.STRIPE_SECRET_KEY
            stripe.Subscription.delete(subscription_id)
        except Exception as exc:
            print(f"[delete-account] Could not cancel subscription {subscription_id}: {exc}")

    delete_user(current_user.id)
    return {"deleted": True}


def _require_business_location(current_user: CurrentUser) -> str:
    if not current_user.business_location:
        raise HTTPException(
            status_code=400,
            detail="Set your business location first (one-time setup) before running analysis.",
        )
    return current_user.business_location


# ---------------------------------------------------------
# ONE click, ONE pull per platform. Google is always pulled once; Yelp is pulled
# once more if you're on Pro/Enterprise, have saved your Yelp page, and ticked it.
# Every panel is built from those pulls (see analysis/pipeline.py). Switching `view`
# (combined / google / yelp) re-analyzes the same reviews, so it costs nothing
# inside the cache window.
# ---------------------------------------------------------
@app.post("/api/analyze/all")
def analyze_all(
    req: UnifiedAnalysisRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    location = _require_business_location(current_user)
    paid = current_user.tier in ("pro", "enterprise")

    profile = get_profile(current_user.id) or {}
    yelp_url = profile.get("yelp_url") if paid else None

    reviews_by_source, cached_flags, notes, _fresh = pipeline.pull_reviews(
        location, yelp_url, req.months, want_yelp=paid and "yelp" in req.sources
    )
    mentions = None
    if paid and req.mentions:
        terms = (req.mention_terms or "").strip() or default_terms(location)
        mentions = pipeline.pull_mentions(terms, req.months)

    return pipeline.assemble(
        reviews_by_source,
        cached_flags,
        notes,
        view=req.view,
        months=req.months,
        location=location,
        paid=paid,
        avg_order_value=req.avg_order_value,
        reviews_to_customers_multiplier=req.reviews_to_customers_multiplier,
        alert_email=current_user.email,
        competitors=[c.model_dump() for c in req.competitors if c.search_query.strip()],
        mentions=mentions,
    )


# ---------------------------------------------------------
# Enterprise contact form (public - no auth required)
# ---------------------------------------------------------
@app.post("/api/enterprise-contact")
def enterprise_contact(req: EnterpriseContactRequest):
    # No email/CRM integration wired up yet - this just acknowledges receipt.
    print(f"[enterprise-contact] {req.name} <{req.email}> ({req.company_name}): {req.message}")
    return {"received": True}
