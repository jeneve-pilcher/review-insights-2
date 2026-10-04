from typing import List, Optional

from pydantic import BaseModel, Field


class SetBusinessLocationRequest(BaseModel):
    business_location: str = Field(..., min_length=1)


# Note: these no longer accept a free-text `search_query` from the client.
# Each account has exactly one business_location (set once via
# /api/me/business-location), and every analysis endpoint below uses that
# saved location automatically - this is what stops a single login from
# being used to analyze arbitrary, unrelated businesses.

class SentimentDriftRequest(BaseModel):
    review_limit: int = Field(300, ge=0)


class WaitTimeHeatmapRequest(BaseModel):
    review_limit: int = Field(300, ge=0)
    avg_order_value: float = Field(35.0, ge=0)
    reviews_to_customers_multiplier: float = Field(
        20.0, ge=1,
        description="Assumed number of real customers per review left. Adjust to your business's real ratio.",
    )


class UnifiedAnalysisRequest(BaseModel):
    review_limit: int = Field(300, ge=0)
    avg_order_value: float = Field(35.0, ge=0)
    reviews_to_customers_multiplier: float = Field(20.0, ge=1)


class NegativeReviewsRequest(BaseModel):
    review_limit: int = Field(300, ge=0)
    lookback_days: int = Field(30, ge=1, le=180)
    max_reviews: int = Field(20, ge=1, le=100)


class BusinessInput(BaseModel):
    name: str
    search_query: str


class CompetitorShareRequest(BaseModel):
    # Only competitors go here (1-5 of them) - "Your Business" is injected
    # server-side from the account's saved business_location, not from this list.
    competitors: List[BusinessInput] = Field(..., min_length=1, max_length=5)
    review_limit: int = Field(200, ge=0)


class EnterpriseContactRequest(BaseModel):
    name: str
    email: str
    company_name: Optional[str] = None
    message: str
