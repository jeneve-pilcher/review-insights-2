from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class OrgCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class MemberAdd(BaseModel):
    email: str = Field(..., min_length=3)
    role: Literal["admin", "manager", "viewer"] = "manager"


class MemberUpdate(BaseModel):
    role: Literal["admin", "manager", "viewer"]


class LocationIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    google_query: str = Field(..., min_length=1)
    brand: Optional[str] = None
    region: Optional[str] = None
    yelp_url: Optional[str] = None
    opentable_url: Optional[str] = None
    doordash_url: Optional[str] = None
    ubereats_url: Optional[str] = None
    grubhub_url: Optional[str] = None
    provider_links: Optional[List[str]] = None      # Zocdoc doctor pages; only when provider-level data is enabled
    manager_email: Optional[str] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=160)
    google_query: Optional[str] = Field(None, min_length=1)
    brand: Optional[str] = None
    region: Optional[str] = None
    yelp_url: Optional[str] = None
    opentable_url: Optional[str] = None
    doordash_url: Optional[str] = None
    ubereats_url: Optional[str] = None
    grubhub_url: Optional[str] = None
    provider_links: Optional[List[str]] = None      # Zocdoc doctor pages; only when provider-level data is enabled
    manager_email: Optional[str] = None
    is_active: Optional[bool] = None


class ImportRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)


class AlertUpdate(BaseModel):
    status: Optional[Literal["open", "acknowledged", "resolved"]] = None
    assigned_to: Optional[str] = None
    note: Optional[str] = Field(None, max_length=1000)


class BudgetUpdate(BaseModel):
    # Dollars of credit the company may spend per month. Leave empty (null) for no limit.
    monthly_budget_usd: Optional[float] = Field(None, gt=0, le=1_000_000)


class IndustryUpdate(BaseModel):
    industry: str = Field(..., min_length=1, max_length=40)
