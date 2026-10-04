import stripe
from fastapi import APIRouter, Depends, HTTPException, Request

import config
from auth import CurrentUser, get_current_user
from supabase_client import find_user_id_by_customer_id, set_tier

router = APIRouter(prefix="/api/billing", tags=["billing"])


def _stripe():
    stripe.api_key = config.require(config.STRIPE_SECRET_KEY, "STRIPE_SECRET_KEY")
    return stripe


@router.post("/create-checkout-session")
def create_checkout_session(current_user: CurrentUser = Depends(get_current_user)):
    try:
        s = _stripe()
        price_id = config.require(config.STRIPE_PRICE_ID_PRO, "STRIPE_PRICE_ID_PRO")

        session = s.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=current_user.email,
            client_reference_id=current_user.id,
            success_url=f"{config.FRONTEND_URL}/dashboard?checkout=success",
            cancel_url=f"{config.FRONTEND_URL}/pricing?checkout=cancelled",
            metadata={"user_id": current_user.id},
            subscription_data={"metadata": {"user_id": current_user.id}},
        )
        return {"checkout_url": session.url}
    except HTTPException:
        raise
    except Exception as exc:
        # Raised as a proper HTTPException (not left to bubble up
        # unhandled) so the browser gets a real error message instead of
        # a misleading CORS failure.
        raise HTTPException(status_code=500, detail=f"Could not create checkout session: {exc}")


@router.post("/create-portal-session")
def create_portal_session(current_user: CurrentUser = Depends(get_current_user)):
    """Lets an existing Pro subscriber manage/cancel their subscription."""
    from supabase_client import get_profile

    try:
        s = _stripe()
        profile = get_profile(current_user.id)
        customer_id = profile.get("stripe_customer_id") if profile else None
        if not customer_id:
            raise HTTPException(status_code=400, detail="No active subscription found.")

        session = s.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{config.FRONTEND_URL}/dashboard",
        )
        return {"portal_url": session.url}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not open billing portal: {exc}")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    s = _stripe()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = config.require(config.STRIPE_WEBHOOK_SECRET, "STRIPE_WEBHOOK_SECRET")

    try:
        event = s.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid webhook payload: {exc}")

    event_type = event["type"]
    raw_obj = event["data"]["object"]
    # Newer stripe-python versions return real Stripe objects here, not
    # plain dicts - .get() isn't available on them directly. Converting
    # once up front lets the rest of this function use normal dict access.
    obj = raw_obj.to_dict() if hasattr(raw_obj, "to_dict") else dict(raw_obj)

    if event_type == "checkout.session.completed":
        user_id = (obj.get("metadata") or {}).get("user_id") or obj.get("client_reference_id")
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        if user_id:
            set_tier(user_id, "pro", stripe_customer_id=customer_id, stripe_subscription_id=subscription_id)

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        customer_id = obj.get("customer")
        status_value = obj.get("status")
        user_id = (obj.get("metadata") or {}).get("user_id") or find_user_id_by_customer_id(customer_id)

        if user_id:
            if event_type == "customer.subscription.deleted" or status_value in ("canceled", "unpaid", "incomplete_expired"):
                set_tier(user_id, "free")
            elif status_value == "active":
                set_tier(user_id, "pro")

    return {"received": True}
