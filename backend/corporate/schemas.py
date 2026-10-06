from typing import Literal, Optional

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
    manager_email: Optional[str] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=160)
    google_query: Optional[str] = Field(None, min_length=1)
    brand: Optional[str] = None
    region: Optional[str] = None
    yelp_url: Optional[str] = None
    manager_email: Optional[str] = None
    is_active: Optional[bool] = None


class ImportRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)


class AlertUpdate(BaseModel):
    status: Optional[Literal["open", "acknowledged", "resolved"]] = None
    assigned_to: Optional[str] = None
    note: Optional[str] = Field(None, max_length=1000)


class BudgetUpdate(BaseModel):
    monthly_budget_reviews: int = Field(..., ge=0, le=10_000_000)
