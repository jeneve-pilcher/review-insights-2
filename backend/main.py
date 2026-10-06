from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import config
from analysis.chart1_sentiment_drift import build_sentiment_drift
from analysis.chart2_wait_time_heatmap import build_wait_summary, build_wait_time_heatmap
from analysis.chart3_competitor_share import build_competitor_share
from analysis.insights import build_revenue_signals, trim_signals_for_preview
from analysis.negative_reviews import build_negative_reviews, negative_summary
from analysis.trends import build_trends, trim_for_preview
from analysis.outscraper_client import fetch_reviews_with_meta, latest_review_date
from analysis.review_utils import text_reviews
from auth import CurrentUser, get_current_user
from billing import router as billing_router
from schemas import (
    EnterpriseContactRequest,
    SetBusinessLocationRequest,
    UnifiedAnalysisRequest,
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
    # Set-once by design: stops one account from being reused to analyze a
    # series of unrelated businesses.
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
# ONE review pull feeds every panel: Sentiment Drift + Weekly Themes (all
# tiers, with a trimmed Trends preview), plus the full Wait-Time Heatmap, Negative
# Review Alerts and Trends for Pro/Enterprise.
# ---------------------------------------------------------
@app.post("/api/analyze/all")
def analyze_all(
    req: UnifiedAnalysisRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    location = _require_business_location(current_user)

    reviews, from_cache = fetch_reviews_with_meta(location, req.months)

    result = {
        "meta": {
            "reviews_analyzed": len(reviews),
            "reviews_with_text": len(text_reviews(reviews)),
            "reviews_star_only": len(reviews) - len(text_reviews(reviews)),
            "months": req.months,
            "latest_review_date": latest_review_date(reviews),
            "from_cache": from_cache,
        },
        "sentiment_drift": build_sentiment_drift(reviews),
        "wait_time_heatmap": None,
        "negative_reviews": None,
        "trends": None,
        "signals": None,
        "competitors": None,
        # Free-tier "taste": language findings only, no charts or review text.
        "wait_time_preview": None,
        "negative_preview": None,
    }

    if current_user.tier in ("pro", "enterprise"):
        result["wait_time_heatmap"] = build_wait_time_heatmap(
            reviews,
            req.avg_order_value,
            req.reviews_to_customers_multiplier,
        )
        result["negative_reviews"] = build_negative_reviews(
            reviews,
            location,
            alert_email=current_user.email,
        )
        result["trends"] = build_trends(reviews)
        result["signals"] = build_revenue_signals(reviews)

        # Optional competitor comparison, in the same click. Your own business
        # reuses the pull above; each competitor is one extra pull.
        competitors = [c for c in req.competitors if c.search_query.strip()]
        if competitors:
            businesses = [{"name": "Your Business", "search_query": location}]
            businesses.extend(c.model_dump() for c in competitors)
            result["competitors"] = build_competitor_share(businesses, req.months, own_reviews=reviews)
    else:
        result["signals"] = trim_signals_for_preview(build_revenue_signals(reviews))
        result["trends"] = trim_for_preview(build_trends(reviews))
        result["wait_time_preview"] = build_wait_summary(reviews)
        result["negative_preview"] = negative_summary(reviews)

    return result


# ---------------------------------------------------------
# Enterprise contact form (public - no auth required)
# ---------------------------------------------------------
@app.post("/api/enterprise-contact")
def enterprise_contact(req: EnterpriseContactRequest):
    # No email/CRM integration wired up yet - this just acknowledges receipt.
    print(f"[enterprise-contact] {req.name} <{req.email}> ({req.company_name}): {req.message}")
    return {"received": True}
