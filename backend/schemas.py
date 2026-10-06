from typing import List, Optional

from pydantic import BaseModel, Field


class SetBusinessLocationRequest(BaseModel):
    business_location: str = Field(..., min_length=1)


class BusinessInput(BaseModel):
    name: str
    search_query: str


class UnifiedAnalysisRequest(BaseModel):
    # How far back to pull reviews. Smaller = faster and cheaper.
    months: int = Field(6, ge=1, le=24)
    avg_order_value: float = Field(35.0, ge=0)
    reviews_to_customers_multiplier: float = Field(20.0, ge=1)
    # Optional (Pro/Enterprise). Each competitor is one extra review pull; the
    # account's own business is always pulled once and shared by every panel.
    competitors: List[BusinessInput] = Field(default_factory=list, max_length=5)


class EnterpriseContactRequest(BaseModel):
    name: str
    email: str
    company_name: Optional[str] = None
    message: str
