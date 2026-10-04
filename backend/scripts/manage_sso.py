"""
Manage enterprise customers' SAML SSO connections in Supabase.

This is an operator tool, not a public API - run it manually (or from a
private internal script) when onboarding/updating/removing an enterprise
customer's SSO connection. It talks to Supabase's Auth Admin SSO API using
your service_role key, which must never be exposed to the frontend.

Prerequisite: SAML SSO must be enabled on your Supabase project. This is a
paid add-on (Team/Enterprise Supabase plans) and may require contacting
Supabase support to turn on for your project - it is not available by
default on Free/Pro Supabase plans.

Usage:

  # Register a new enterprise customer's IdP (via a metadata URL - most IdPs
  # like Okta/Azure AD/Google Workspace provide one)
  python manage_sso.py create \
      --domain acmecorp.com \
      --metadata-url https://acmecorp.okta.com/app/abc123/sso/saml/metadata

  # Or via a downloaded metadata XML file instead of a URL
  python manage_sso.py create --domain acmecorp.com --metadata-file acme_metadata.xml

  # List all registered SSO providers
  python manage_sso.py list

  # Remove a customer's SSO connection (e.g. contract ends)
  python manage_sso.py delete --provider-id <uuid-from-list>
"""

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")


def _require_config():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set (check your .env).", file=sys.stderr)
        sys.exit(1)


def _headers():
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def _base_url():
    return f"{SUPABASE_URL.rstrip('/')}/auth/v1/admin/sso/providers"


def _print_response(resp: requests.Response):
    try:
        body = resp.json()
    except ValueError:
        body = resp.text

    if not resp.ok:
        print(f"Error {resp.status_code}:", file=sys.stderr)
        print(json.dumps(body, indent=2) if isinstance(body, dict) else body, file=sys.stderr)
        sys.exit(1)

    print(json.dumps(body, indent=2))


def cmd_create(args):
    _require_config()

    if not args.metadata_url and not args.metadata_file:
        print("Provide either --metadata-url or --metadata-file.", file=sys.stderr)
        sys.exit(1)

    payload = {
        "type": "saml",
        "domains": [d.strip() for d in args.domain.split(",")],
        "attribute_mapping": {
            "keys": {
                "email": {"name": args.email_attribute},
            }
        },
    }

    if args.metadata_url:
        payload["metadata_url"] = args.metadata_url
    else:
        with open(args.metadata_file, "r") as f:
            payload["metadata_xml"] = f.read()

    resp = requests.post(_base_url(), headers=_headers(), json=payload, timeout=30)
    _print_response(resp)


def cmd_list(args):
    _require_config()
    resp = requests.get(_base_url(), headers=_headers(), timeout=30)
    _print_response(resp)


def cmd_get(args):
    _require_config()
    resp = requests.get(f"{_base_url()}/{args.provider_id}", headers=_headers(), timeout=30)
    _print_response(resp)


def cmd_delete(args):
    _require_config()
    resp = requests.delete(f"{_base_url()}/{args.provider_id}", headers=_headers(), timeout=30)
    _print_response(resp)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_create = subparsers.add_parser("create", help="Register a new enterprise customer's SAML SSO connection")
    p_create.add_argument("--domain", required=True, help="Comma-separated email domain(s), e.g. acmecorp.com")
    p_create.add_argument("--metadata-url", help="URL to the IdP's SAML metadata XML")
    p_create.add_argument("--metadata-file", help="Path to a local SAML metadata XML file")
    p_create.add_argument("--email-attribute", default="email", help="SAML attribute name mapped to email (default: 'email')")
    p_create.set_defaults(func=cmd_create)

    p_list = subparsers.add_parser("list", help="List all registered SSO providers")
    p_list.set_defaults(func=cmd_list)

    p_get = subparsers.add_parser("get", help="Get one SSO provider by ID")
    p_get.add_argument("--provider-id", required=True)
    p_get.set_defaults(func=cmd_get)

    p_delete = subparsers.add_parser("delete", help="Remove an enterprise customer's SSO connection")
    p_delete.add_argument("--provider-id", required=True)
    p_delete.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
