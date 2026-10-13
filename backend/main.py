from datetime import datetime, timezone

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

import config
from analysis import pipeline
import features
from analysis.mentions import default_terms, mention_target
from analysis.competitor_input import clean_competitors
from analysis.outscraper_client import place_info
from analysis import industries
from branding import allow_lookup, domain_of, public_branding
from analysis.delivery_clients import normalize_doordash_url, normalize_grubhub_url, normalize_ubereats_url
from analysis.opentable_client import normalize_opentable_url
from analysis.yelp_client import normalize_yelp_url
from auth import CurrentUser, get_current_user
from billing import router as billing_router
from corporate import monitor
from corporate.store import get_store
from credits import rates as credit_rates, wallet
from credits.routes import router as credits_router
from corporate.routes import internal_router, router as org_router
from replies import router as replies_router
from schemas import (
    AcceptTermsRequest,
    EnterpriseContactRequest,
    SetBusinessLocationRequest,
    SetIndustryRequest,
    SetLinksRequest,
    SetPlatformUrlRequest,
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
app.include_router(credits_router)


@app.on_event("startup")
def _start_monitor():
    # Say plainly in the logs if a database update (corporate.sql) hasn't been run yet.
    try:
        from setup_check import report
        report(get_store(), get_supabase_admin())
    except Exception as exc:
        print(f"[setup] skipped the database check: {exc}")
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
        "opentable_url": profile.get("opentable_url"),
        "doordash_url": profile.get("doordash_url"),
        "ubereats_url": profile.get("ubereats_url"),
        "grubhub_url": profile.get("grubhub_url"),
        "monthly_limit_usd": profile.get("monthly_limit_usd"),
        "industry": profile.get("industry") or industries.DEFAULT,
        "industry_set": bool(profile.get("industry")),      # False = still on the default; the dashboard asks them to choose
        "branding": _branding_for(membership),
        "org_role": membership["role"] if membership else None,
        "terms_version": profile.get("terms_version"),
        "terms_accepted_at": profile.get("terms_accepted_at"),
    }


def _branding_for(membership) -> Optional[dict]:
    """The company's white-label look, for anyone who belongs to a company that has it."""
    if not membership:
        return None
    try:
        return public_branding(get_store().get_org(membership["org_id"]))
    except Exception:
        return None


@app.get("/api/industries")
def list_industries():
    """The industries a business can pick. Static and public: no account details."""
    return {"default": industries.DEFAULT, "industries": industries.catalog()}


@app.put("/api/me/industry")
def set_my_industry(req: SetIndustryRequest, current_user: CurrentUser = Depends(get_current_user)):
    """Chooses which industry's themes and graphs this account gets. Unlike the business itself, it can be changed."""
    if not industries.is_selectable(req.industry):
        raise HTTPException(status_code=400, detail="That industry isn't available yet.")
    try:
        get_supabase_admin().table("profiles").update({"industry": req.industry}).eq("id", current_user.id).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not save your industry. If you just updated, run the SQL in the README first. ({exc})")
    return {"industry": req.industry}


@app.get("/api/branding")
def branding_for_email(request: Request, email: str = ""):
    """Public, used by the login page BEFORE sign-in: the brand details for a work email's domain, if that company has
    white-label branding. Rate limited, and it returns nothing but brand details."""
    ip = request.client.host if request.client else "unknown"
    if not allow_lookup(ip):
        raise HTTPException(status_code=429, detail="Too many lookups. Please wait a minute.")
    domain = domain_of(email)
    if not domain:
        return {"branding": None}
    try:
        org = get_store().find_org_by_sso_domain(domain)
    except Exception:
        return {"branding": None}
    return {"branding": public_branding(org)}


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


PLATFORM_NORMALIZERS = {"opentable": normalize_opentable_url, "doordash": normalize_doordash_url,
                        "ubereats": normalize_ubereats_url, "grubhub": normalize_grubhub_url}
PLATFORM_NAMES = {"opentable": "OpenTable", "doordash": "DoorDash", "ubereats": "Uber Eats", "grubhub": "Grubhub"}


@app.post("/api/me/platform-url")
def set_my_platform_url(
    req: SetPlatformUrlRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Saves an OpenTable, DoorDash, Uber Eats or Grubhub page for this account (set once, like the Yelp page)."""
    column = f"{req.platform}_url"
    profile = get_profile(current_user.id) or {}
    if profile.get(column):
        raise HTTPException(
            status_code=400,
            detail=f"A {PLATFORM_NAMES[req.platform]} page is already set for this account. Contact support to change it.",
        )
    try:
        url = PLATFORM_NORMALIZERS[req.platform](req.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        get_supabase_admin().table("profiles").update({column: url}).eq("id", current_user.id).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not save your {PLATFORM_NAMES[req.platform]} link. If you just applied this update, run the "
                f"SQL in the README first (it adds the {column} column). ({exc})"
            ),
        )
    return {"platform": req.platform, "url": url}


LINK_NORMALIZERS = {
    "yelp_url": normalize_yelp_url, "opentable_url": normalize_opentable_url,
    "doordash_url": normalize_doordash_url, "ubereats_url": normalize_ubereats_url, "grubhub_url": normalize_grubhub_url,
}


@app.post("/api/me/links")
def set_my_links(req: SetLinksRequest, current_user: CurrentUser = Depends(get_current_user)):
    """Saves several review-page links at once (used by first-time setup and the "Your pages" form).

    All or nothing: every link is checked first, and nothing is saved if any is invalid. Like the business
    location these are set once, but sending the same link again is harmless, so a retry after a failure works."""
    if current_user.tier not in ("pro", "enterprise"):
        raise HTTPException(status_code=403, detail="Connecting Yelp, OpenTable, DoorDash, Uber Eats and Grubhub is a Pro feature.")

    profile = get_profile(current_user.id) or {}
    updates = {}
    for column, normalize in LINK_NORMALIZERS.items():
        raw = getattr(req, column)
        if raw is None or not raw.strip():
            continue
        try:
            url = normalize(raw)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        existing = profile.get(column)
        if existing and existing != url:
            name = column[:-4].replace("ubereats", "uber eats").title()
            raise HTTPException(status_code=400, detail=f"A {name} page is already set for this account. Contact support to change it.")
        if not existing:
            updates[column] = url

    if updates:
        try:
            get_supabase_admin().table("profiles").update(updates).eq("id", current_user.id).execute()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=("Could not save your links. If you just applied this update, run the SQL in the README first "
                        f"(it adds the link columns). ({exc})"),
            )
    return {"links": updates}


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

    # Usage billing: the monthly plan allowance is spent first, then prepaid credit. Spending stops for the
    # month once the account's own monthly spending limit (if it set one) has been reached.
    credit_scope = wallet.scope_for_user(current_user.id)
    allowance = wallet.allowance_for_tier(current_user.tier)
    wallet.precheck(get_store(), credit_scope, allowance, who="user", tier=current_user.tier,
                    limit_usd=profile.get("monthly_limit_usd"))

    yelp_url = profile.get("yelp_url") if paid else None

    # Reservation and delivery platforms (OpenTable, DoorDash, Uber Eats, Grubhub): paid only, and only the ones ticked for this run.
    others = {
        src: profile.get(f"{src}_url")
        for src in ("opentable", "doordash", "ubereats", "grubhub")
        if paid and src in req.sources
    }
    reviews_by_source, cached_flags, notes, fresh, unrated = pipeline.pull_reviews_ext(
        location, yelp_url, req.months, want_yelp=paid and "yelp" in req.sources, others=others
    )
    mentions = None
    if paid and req.mentions and features.INTERNET_MENTIONS:
        custom = (req.mention_terms or "").strip()
        terms, area = (custom, None) if custom else mention_target(location, place_info(location))
        mentions = pipeline.pull_mentions(terms, req.months, req.mention_pages, area=area, location_note=not custom)

    result = pipeline.assemble(
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
        competitors=clean_competitors([c.model_dump() for c in req.competitors]),
        mentions=mentions,
        unrated=unrated,
        industry=profile.get("industry"),
        ai_summary=features.AI_SUMMARIES,
    )

    # Charge what this run actually cost. Anything served from the 30-minute cache was already paid for.
    cost = credit_rates.cost_breakdown(
        fresh,
        searches=(mentions or {}).get("searches", 0),
        competitor_reviews=(result.get("competitors") or {}).get("fresh_reviews", 0),
        summaries=1 if (result.get("ai_summary") or {}).get("fresh") else 0,
    )
    result["billing"] = wallet.settle(get_store(), credit_scope, allowance, cost, "Analysis")
    return result


# ---------------------------------------------------------
# Enterprise contact form (public - no auth required)
# ---------------------------------------------------------
@app.post("/api/enterprise-contact")
def enterprise_contact(req: EnterpriseContactRequest):
    # No email/CRM integration wired up yet - this just acknowledges receipt.
    print(f"[enterprise-contact] {req.name} <{req.email}> ({req.company_name}): {req.message}")
    return {"received": True}
