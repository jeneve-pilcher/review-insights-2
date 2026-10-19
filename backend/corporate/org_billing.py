"""Charging a company by number of locations through Stripe.

One Stripe subscription per organization. Its price is a volume tiered price built from the tier table (the standard
one, or the contract's own), and its quantity is the number of locations being billed: the active locations, but never fewer
than the contract's minimum, and at least 1. The quantity is set on the server from the database, never from the browser.
When locations are added or deleted the quantity is updated in Stripe and the difference is prorated on the next invoice.

Stripe's own tier maths produces the charge; corporate/pricing.py produces the same figure for display, so they agree."""
import os
from typing import Optional, Tuple

import stripe

import config
from corporate import billing_report, pricing

LIVE = ("active", "trialing", "past_due")


def required() -> bool:
    """Companies must have billing set up before adding locations. REQUIRE_ORG_BILLING=false turns the rule off (for testing)."""
    return os.environ.get("REQUIRE_ORG_BILLING", "true").strip().lower() not in ("0", "false", "no", "off")


def _stripe():
    stripe.api_key = config.require(config.STRIPE_SECRET_KEY, "STRIPE_SECRET_KEY")
    return stripe


def is_live(org: dict) -> bool:
    return bool(org.get("stripe_subscription_id")) and (org.get("billing_status") in LIVE)


def quantity_and_table(store, org: dict) -> Tuple[int, list]:
    """(locations to bill, the price table that applies)."""
    used = sum(1 for l in store.list_locations(org["id"]) if l.get("is_active", True))
    contract = billing_report.contract_for(store, org)
    minimum = int((contract or {}).get("minimum_locations") or 0)
    custom = pricing.parse_tiers((contract or {}).get("price_tiers") or "") if contract else None
    table = custom or pricing.tiers()
    return pricing.billed_locations(max(used, minimum, 1), table), table


def ensure_price(s, table: list) -> str:
    key = pricing.lookup_key(table)
    found = s.Price.list(lookup_keys=[key], active=True, limit=1)
    if found["data"]:
        return found["data"][0]["id"]
    product = s.Product.create(name="Review Insights: price per location")
    price = s.Price.create(
        currency="usd", product=product["id"], recurring={"interval": "month"},
        billing_scheme="tiered", tiers_mode="volume", tiers=pricing.stripe_tiers(table),
        lookup_key=key, metadata={"table": key},
    )
    return price["id"]


def checkout_url(store, org: dict, owner_email: str) -> str:
    s = _stripe()
    if is_live(org):
        raise ValueError("Billing is already set up. Use Manage billing.")
    qty, table = quantity_and_table(store, org)
    price_id = ensure_price(s, table)
    who = {"customer": org["stripe_customer_id"]} if org.get("stripe_customer_id") else {"customer_email": owner_email}
    session = s.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": qty}],
        **who,
        client_reference_id=org["id"],
        metadata={"org_id": org["id"]},
        subscription_data={"metadata": {"org_id": org["id"]}},
        success_url=f"{config.FRONTEND_URL}/dashboard?org_billing=success",
        cancel_url=f"{config.FRONTEND_URL}/dashboard?org_billing=cancelled",
    )
    return session.url


def portal_url(org: dict) -> str:
    s = _stripe()
    if not org.get("stripe_customer_id"):
        raise ValueError("Billing hasn't been set up yet.")
    return s.billing_portal.Session.create(customer=org["stripe_customer_id"], return_url=f"{config.FRONTEND_URL}/dashboard").url


def sync_quantity(store, org_id: str) -> Optional[int]:
    """Make Stripe's quantity match the locations being billed. Never raises: a failure here must not block adding a location
    (the next add or delete corrects it). Returns the new quantity, or None."""
    try:
        org = store.get_org(org_id)
        if not org or not is_live(org):
            return None
        s = _stripe()
        qty, _ = quantity_and_table(store, org)
        sub = s.Subscription.retrieve(org["stripe_subscription_id"])
        item = sub["items"]["data"][0]
        if int(item.get("quantity") or 0) == qty:
            return qty
        s.SubscriptionItem.modify(item["id"], quantity=qty, proration_behavior="create_prorations")
        return qty
    except Exception as exc:
        print(f"[org-billing] could not update the quantity for {org_id}: {exc}")
        return None


def record_subscription(store, org_id: str, customer_id: Optional[str], subscription_id: Optional[str], status: Optional[str]) -> None:
    if not store.get_org(org_id):
        return
    fields = {"billing_status": status}
    if customer_id:
        fields["stripe_customer_id"] = customer_id
    if subscription_id:
        fields["stripe_subscription_id"] = subscription_id
    store.update_org(org_id, **fields)
