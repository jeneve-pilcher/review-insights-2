from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import config
from analysis.chart1_sentiment_drift import build_sentiment_drift
from analysis.chart2_wait_time_heatmap import build_wait_time_heatmap
from analysis.chart3_competitor_share import build_competitor_share
from analysis.negative_reviews import build_negative_reviews
from auth import CurrentUser, get_current_user, require_tier
from billing import router as billing_router
from schemas import (
    CompetitorShareRequest,
    EnterpriseContactRequest,
    NegativeReviewsRequest,
    SentimentDriftRequest,
    SetBusinessLocationRequest,
    UnifiedAnalysisRequest,
    WaitTimeHeatmapRequest,
)
from supabase_client import delete_user, get_profile, set_business_location

app = FastAPI(title="Review Insights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(billing_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/me")
def me(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "tier": current_user.tier,
        "business_location": current_user.business_location,
    }


@app.post("/api/me/business-location")
def set_my_business_location(
    req: SetBusinessLocationRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    # Set-once by design: this is what stops a single account from being
    # reused to analyze a series of unrelated businesses. Changing an
    # already-set location is intentionally not self-serve.
    if current_user.business_location:
        raise HTTPException(
            status_code=400,
            detail="Business location is already set for this account. Contact support to change it.",
        )
    set_business_location(current_user.id, req.business_location)
    return {"business_location": req.business_location}


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
            # Don't block account deletion on a Stripe hiccup - log and
            # continue, since the person still wants their account gone.
            print(f"[delete-account] Could not cancel subscription {subscription_id}: {exc}")

    # Deletes the Supabase auth user; profiles/analysis_runs rows cascade-delete.
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
# Chart 1 - available on every tier (including free)
# ---------------------------------------------------------
@app.post("/api/analyze/sentiment-drift")
def analyze_sentiment_drift(
    req: SentimentDriftRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    location = _require_business_location(current_user)
    return build_sentiment_drift(location, req.review_limit)


# ---------------------------------------------------------
# Chart 2 - Pro / Enterprise only
# ---------------------------------------------------------
@app.post("/api/analyze/wait-time-heatmap")
def analyze_wait_time_heatmap(
    req: WaitTimeHeatmapRequest,
    current_user: CurrentUser = Depends(require_tier("pro", "enterprise")),
):
    location = _require_business_location(current_user)
    return build_wait_time_heatmap(
        location,
        req.review_limit,
        req.avg_order_value,
        req.reviews_to_customers_multiplier,
    )


# ---------------------------------------------------------
# Unified fetch - Chart 1 always, Chart 2 only if the tier allows it.
# Lets the frontend load everything from one form/button instead of two.
# ---------------------------------------------------------
@app.post("/api/analyze/all")
def analyze_all(
    req: UnifiedAnalysisRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    location = _require_business_location(current_user)
    sentiment_drift = build_sentiment_drift(location, req.review_limit)

    wait_time_heatmap = None
    if current_user.tier in ("pro", "enterprise"):
        wait_time_heatmap = build_wait_time_heatmap(
            location,
            req.review_limit,
            req.avg_order_value,
            req.reviews_to_customers_multiplier,
        )

    return {"sentiment_drift": sentiment_drift, "wait_time_heatmap": wait_time_heatmap}


# ---------------------------------------------------------
# Negative review alerts - Pro / Enterprise only
# ---------------------------------------------------------
@app.post("/api/analyze/negative-reviews")
def analyze_negative_reviews(
    req: NegativeReviewsRequest,
    current_user: CurrentUser = Depends(require_tier("pro", "enterprise")),
):
    location = _require_business_location(current_user)
    return build_negative_reviews(
        location,
        req.review_limit,
        req.lookback_days,
        req.max_reviews,
        alert_email=current_user.email,
    )


# ---------------------------------------------------------
# Chart 3 - Pro / Enterprise only. "Your Business" is always the account's
# saved location, injected here - only the competitor list is client-supplied.
# ---------------------------------------------------------
@app.post("/api/analyze/competitor-share")
def analyze_competitor_share(
    req: CompetitorShareRequest,
    current_user: CurrentUser = Depends(require_tier("pro", "enterprise")),
):
    location = _require_business_location(current_user)
    businesses = [{"name": "Your Business", "search_query": location}]
    businesses.extend(c.model_dump() for c in req.competitors)
    return build_competitor_share(businesses, req.review_limit)


# ---------------------------------------------------------
# Enterprise contact form (public - no auth required)
# ---------------------------------------------------------
@app.post("/api/enterprise-contact")
def enterprise_contact(req: EnterpriseContactRequest):
    # No email/CRM integration wired up yet - this just acknowledges receipt.
    # Hook this up to your email provider (e.g. SendGrid, Postmark) or a
    # Slack/webhook notification before relying on it in production.
    print(f"[enterprise-contact] {req.name} <{req.email}> ({req.company_name}): {req.message}")
    return {"received": True}
