from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SetBusinessLocationRequest(BaseModel):
    business_location: str = Field(..., min_length=1)


class AcceptTermsRequest(BaseModel):
    # Which version of the Terms of Service the person agreed to (e.g. "2026-10-06").
    version: str = Field(..., min_length=1, max_length=40)


class SetPlatformUrlRequest(BaseModel):
    platform: Literal["opentable", "doordash", "ubereats", "grubhub"]
    url: str = Field(..., min_length=1)


class SetIndustryRequest(BaseModel):
    industry: str = Field(..., min_length=1, max_length=40)


class SetLinksRequest(BaseModel):
    """The review pages an account connects, all in one save. Send only the ones being added."""
    yelp_url: Optional[str] = None
    opentable_url: Optional[str] = None
    doordash_url: Optional[str] = None
    ubereats_url: Optional[str] = None
    grubhub_url: Optional[str] = None


class SetYelpUrlRequest(BaseModel):
    yelp_url: str = Field(..., min_length=1)


class BusinessInput(BaseModel):
    name: str
    search_query: str


class CompetitorsRequest(BaseModel):
    months: int = Field(6, ge=1, le=60)
    competitors: List[BusinessInput] = Field(default_factory=list, max_length=5)


class UnifiedAnalysisRequest(BaseModel):
    # How far back to pull reviews. Smaller = faster and cheaper.
    months: int = Field(6, ge=1, le=60)
    # False when the page re-reads the same reviews for another view (combined / Google / Yelp): not a new press.
    count_toward_limit: bool = True
    avg_order_value: float = Field(35.0, ge=0)
    reviews_to_customers_multiplier: float = Field(20.0, ge=1)
    # Optional (Pro/Enterprise). Each competitor is one extra review pull; the
    # account's own business is always pulled once and shared by every panel.
    competitors: List[BusinessInput] = Field(default_factory=list, max_length=5)
    # Review platforms to pull (Pro/Enterprise for anything beyond Google). Each is one pull.
    sources: List[Literal["google", "yelp", "opentable", "doordash", "ubereats", "grubhub"]] = Field(default_factory=lambda: ["google"])
    # Which pulled platform(s) the panels analyze. Switching is free inside the cache window.
    view: Literal["combined", "google", "yelp", "opentable", "doordash", "grubhub"] = "combined"
    # Pro/Enterprise: also search the web for mentions (news, blogs, forums, social). Extra cost.
    mentions: bool = False
    mention_terms: Optional[str] = Field(None, max_length=200)
    # How deep to search: pages per search (about 10 results each). More pages = more mentions = more cost.
    mention_pages: int = Field(2, ge=1, le=5)


class EnterpriseContactRequest(BaseModel):
    name: str
    email: str
    company_name: Optional[str] = None
    message: str
