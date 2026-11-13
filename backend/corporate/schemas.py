from typing import List, Literal, Optional

from pydantic import Field

from sanitize import SafeModel


class OrgCreate(SafeModel):
    name: str = Field(..., min_length=1, max_length=120)


class MemberAdd(SafeModel):
    email: str = Field(..., min_length=3, max_length=254)
    role: Literal["admin", "manager", "viewer"] = "manager"


class MemberUpdate(SafeModel):
    role: Literal["admin", "manager", "viewer"]


class LocationIn(SafeModel):
    name: str = Field(..., min_length=1, max_length=160)
    google_query: str = Field(..., min_length=1, max_length=300)
    brand: Optional[str] = Field(None, max_length=120)
    region: Optional[str] = Field(None, max_length=120)
    yelp_url: Optional[str] = Field(None, max_length=500)
    opentable_url: Optional[str] = Field(None, max_length=500)
    doordash_url: Optional[str] = Field(None, max_length=500)
    ubereats_url: Optional[str] = Field(None, max_length=500)
    grubhub_url: Optional[str] = Field(None, max_length=500)
    provider_links: Optional[List[str]] = Field(None, max_length=50)     # Zocdoc doctor pages; only when provider-level data is enabled
    manager_email: Optional[str] = Field(None, max_length=254)


class LocationUpdate(SafeModel):
    name: Optional[str] = Field(None, min_length=1, max_length=160)
    google_query: Optional[str] = Field(None, min_length=1, max_length=300)
    brand: Optional[str] = Field(None, max_length=120)
    region: Optional[str] = Field(None, max_length=120)
    yelp_url: Optional[str] = Field(None, max_length=500)
    opentable_url: Optional[str] = Field(None, max_length=500)
    doordash_url: Optional[str] = Field(None, max_length=500)
    ubereats_url: Optional[str] = Field(None, max_length=500)
    grubhub_url: Optional[str] = Field(None, max_length=500)
    provider_links: Optional[List[str]] = Field(None, max_length=50)     # Zocdoc doctor pages; only when provider-level data is enabled
    manager_email: Optional[str] = Field(None, max_length=254)
    is_active: Optional[bool] = None


class ImportRequest(SafeModel):
    csv_text: str = Field(..., min_length=1, max_length=1_000_000)


class AlertUpdate(SafeModel):
    status: Optional[Literal["open", "acknowledged", "resolved"]] = None
    assigned_to: Optional[str] = Field(None, max_length=254)
    note: Optional[str] = Field(None, max_length=1000)


class BudgetUpdate(SafeModel):
    # Dollars of credit the company may spend per month. Leave empty (null) for no limit.
    monthly_budget_usd: Optional[float] = Field(None, gt=0, le=1_000_000)


class IndustryUpdate(SafeModel):
    industry: str = Field(..., min_length=1, max_length=40)
