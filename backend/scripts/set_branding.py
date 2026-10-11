"""Administrator tool: turn on (or change) a company's white-label branding when a deal is signed.

Run it in the backend container. Examples:

    docker compose exec backend python scripts/set_branding.py --org "Acme Foods" --enable \
        --primary "#0a5c36" --accent "#c28a00" --name "Acme Insights" \
        --logo "https://acme.com/logo.png" --sso-domain acme.com --industry casual_dining

    docker compose exec backend python scripts/set_branding.py --org "Acme Foods" --disable

Colors are checked for readability (white button text must be legible on the primary color). The SSO domain is what the
login page uses to recognise the company before sign-in; it must also be set up as an SSO connection in Supabase.
White-label is deliberately NOT self-serve: only an administrator running this tool can enable it.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from branding import apply_branding, derive_palette  # noqa: E402
from corporate.store import get_store  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--org", required=True, help="the company's name (or its id)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--enable", action="store_true", help="turn white-label branding on")
    g.add_argument("--disable", action="store_true", help="turn it off (settings are kept)")
    p.add_argument("--primary", help="main brand color, hex, e.g. #0a5c36")
    p.add_argument("--accent", help="accent color, hex")
    p.add_argument("--name", help="brand name shown in the app and on the login page")
    p.add_argument("--logo", help="https:// link to the logo image")
    p.add_argument("--sso-domain", help="the company's email domain, e.g. acme.com")
    p.add_argument("--industry", help="casual_dining, fine_dining, general, urgent_care, dental or primary_care")
    p.add_argument("--providers", choices=["on", "off"], help="turn provider-level (individual doctor) data on or off for this company")
    a = p.parse_args()

    try:
        org = apply_branding(get_store(), a.org, enable=True if a.enable else (False if a.disable else None),
                             primary=a.primary, accent=a.accent, name=a.name, logo_url=a.logo,
                             sso_domain=a.sso_domain, industry=a.industry,
                             provider_data=None if a.providers is None else a.providers == "on")
    except ValueError as exc:
        print(f"Not saved: {exc}")
        sys.exit(1)

    print(f"Saved for '{org['name']}':")
    print(f"  white-label: {'ON' if org.get('white_label') else 'off'}   industry: {org.get('industry') or 'casual_dining (default)'}")
    print(f"  brand name:  {org.get('brand_name') or '(company name)'}   logo: {org.get('brand_logo_url') or '(none)'}")
    print(f"  SSO domain:  {org.get('sso_domain') or '(none)'}")
    print(f"  provider-level data: {'ON' if org.get('provider_data_enabled') else 'off'}")
    if org.get("brand_primary"):
        print(f"  palette:     {derive_palette(org['brand_primary'], org.get('brand_accent'))}")


if __name__ == "__main__":
    main()
