"""Billing page for the operator (you): locations in use per customer email domain, and the amount under each contract.
Only emails listed in ADMIN_EMAILS can use it; everyone else gets a plain 404."""
import csv
import io
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

import features
from auth import CurrentUser, get_current_user
from corporate import billing_report, pricing
from corporate.store import get_store

router = APIRouter(prefix="/api/admin/billing", tags=["admin-billing"])
DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not features.COMPANY_PAGE or not billing_report.is_admin(current_user.email):
        raise HTTPException(status_code=404, detail="Not found.")     # don't reveal that the page exists
    return current_user


class ContractIn(BaseModel):
    company_name: Optional[str] = Field(None, max_length=120)
    minimum_locations: int = Field(0, ge=0, le=100000)
    price_tiers: Optional[str] = Field(None, max_length=300)
    starts_on: Optional[str] = Field(None, max_length=20)
    ends_on: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)


def _domain(value: str) -> str:
    d = (value or "").strip().lower()
    if not DOMAIN_RE.match(d):
        raise HTTPException(status_code=400, detail="That doesn't look like a domain (for example acme.com).")
    if d in billing_report.PUBLIC_DOMAINS:
        raise HTTPException(status_code=400, detail=f"{d} is a public mail domain, so it can't identify a customer.")
    return d


@router.get("")
def report(_: CurrentUser = Depends(require_admin)):
    return billing_report.build(get_store())


@router.put("/contracts/{domain}")
def save_contract(domain: str, req: ContractIn, _: CurrentUser = Depends(require_admin)):
    d = _domain(domain)
    tiers = (req.price_tiers or "").strip()
    if tiers and pricing.parse_tiers(tiers) is None:
        raise HTTPException(status_code=400, detail='Prices must look like "1:49,500:39" and start at 1 location.')
    fields = {"company_name": (req.company_name or "").strip() or None, "minimum_locations": req.minimum_locations,
              "price_tiers": tiers or None, "starts_on": (req.starts_on or "").strip() or None,
              "ends_on": (req.ends_on or "").strip() or None, "notes": (req.notes or "").strip() or None}
    return get_store().save_contract(d, fields)


@router.delete("/contracts/{domain}")
def delete_contract(domain: str, _: CurrentUser = Depends(require_admin)):
    get_store().delete_contract(_domain(domain))
    return {"deleted": True}


@router.get("/export.csv")
def export_csv(_: CurrentUser = Depends(require_admin)):
    data = billing_report.build(get_store())
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["customer", "domain", "accounts", "locations_used", "minimum_locations", "locations_billed",
                "monthly_total_usd", "average_per_location_usd", "custom_prices", "contract_ends"])
    for l in data["lines"]:
        w.writerow([l["label"], l["domain"] or "", l["accounts"], l["locations_used"], l["minimum_locations"],
                    l["locations_billed"], l["monthly_total"], l["average_per_location"], "yes" if l["custom_prices"] else "no",
                    (l["contract"] or {}).get("ends_on") or ""])
    return Response(out.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="location-billing.csv"'})
