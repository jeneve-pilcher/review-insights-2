from functools import lru_cache

from supabase import Client, create_client

import config


@lru_cache
def get_supabase_admin() -> Client:
    """A Supabase client authenticated with the service role key.

    This bypasses Row Level Security, so it should only be used for
    server-trusted operations: reading/writing profile tiers, and Stripe
    webhook handling. Never expose this key to the frontend.
    """
    url = config.require(config.SUPABASE_URL, "SUPABASE_URL")
    key = config.require(config.SUPABASE_SERVICE_ROLE_KEY, "SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)


def get_profile(user_id: str) -> dict | None:
    client = get_supabase_admin()
    res = client.table("profiles").select("*").eq("id", user_id).single().execute()
    return res.data


def set_tier(user_id: str, tier: str, stripe_customer_id: str | None = None,
             stripe_subscription_id: str | None = None) -> None:
    client = get_supabase_admin()
    payload = {"tier": tier}
    if stripe_customer_id is not None:
        payload["stripe_customer_id"] = stripe_customer_id
    if stripe_subscription_id is not None:
        payload["stripe_subscription_id"] = stripe_subscription_id
    client.table("profiles").update(payload).eq("id", user_id).execute()


def find_user_id_by_customer_id(stripe_customer_id: str) -> str | None:
    client = get_supabase_admin()
    res = (
        client.table("profiles")
        .select("id")
        .eq("stripe_customer_id", stripe_customer_id)
        .single()
        .execute()
    )
    return res.data["id"] if res.data else None


def set_business_location(user_id: str, business_location: str) -> None:
    client = get_supabase_admin()
    client.table("profiles").update({"business_location": business_location}).eq("id", user_id).execute()


def delete_user(user_id: str) -> None:
    """
    Deletes the Supabase auth user outright. `profiles` and
    `analysis_runs` rows are removed automatically via the ON DELETE
    CASCADE foreign keys defined in schema.sql - no manual cleanup needed
    on our end beyond canceling any active Stripe subscription first
    (handled by the caller, since that's a Stripe concern, not a DB one).
    """
    client = get_supabase_admin()
    client.auth.admin.delete_user(user_id)
