from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SetBusinessLocationRequest(BaseModel):
    business_location: str = Field(..., min_length=1)


class AcceptTermsRequest(BaseModel):
    # Which version of the Terms of Service the person agreed to (e.g. "2026-10-06").
    version: str = Field(..., min_length=1, max_length=40)


class SetYelpUrlRequest(BaseModel):
    yelp_url: str = Field(..., min_length=1)


class BusinessInput(BaseModel):
    name: str
    search_query: str


class UnifiedAnalysisRequest(BaseModel):
    # How far back to pull reviews. Smaller = faster and cheaper.
    months: int = Field(6, ge=1, le=60)
    avg_order_value: float = Field(35.0, ge=0)
    reviews_to_customers_multiplier: float = Field(20.0, ge=1)
    # Optional (Pro/Enterprise). Each competitor is one extra review pull; the
    # account's own business is always pulled once and shared by every panel.
    competitors: List[BusinessInput] = Field(default_factory=list, max_length=5)
    # Review platforms to pull (Pro/Enterprise for anything beyond Google). Each is one pull.
    sources: List[Literal["google", "yelp"]] = Field(default_factory=lambda: ["google"])
    # Which pulled platform(s) the panels analyze. Switching is free inside the cache window.
    view: Literal["combined", "google", "yelp"] = "combined"
    # Pro/Enterprise: also search the web for mentions (news, blogs, forums, social). Extra cost.
    mentions: bool = False
    mention_terms: Optional[str] = Field(None, max_length=200)


class EnterpriseContactRequest(BaseModel):
    name: str
    email: str
    company_name: Optional[str] = None
    message: str
