from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# ─────────────────────────── USER SCHEMAS ────────────────────────────────────

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    name: Optional[str] = None

class UserResponse(UserBase):
    id: int
    name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────── REVIEW SCHEMAS ──────────────────────────────────

class ReviewBase(BaseModel):
    product_name: str
    review_text: str
    rating: float
    source: Optional[str] = "Unknown"

class ReviewCreate(ReviewBase):
    """Schema used when a user submits a new review (auth required)."""
    # Legacy aliases so existing frontend POST still works
    product: Optional[str] = None
    content: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    product_name: str
    review_text: str
    rating: float
    source: str
    is_fake: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────── FRAUD ANALYSIS SCHEMAS ──────────────────────────

class FraudAnalysisResponse(BaseModel):
    id: int
    review_id: int
    sentiment: str
    is_fake: bool
    confidence_score: float
    keywords: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FraudAnalysisDetail(BaseModel):
    """Extended response that includes review info for the /fraud-analysis endpoint."""
    id: int
    review_id: int
    product_name: str
    review_text: str
    rating: float
    source: str
    sentiment: str
    is_fake: bool
    confidence_score: float
    keywords: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────── DASHBOARD SCHEMA ────────────────────────────────

class DashboardStats(BaseModel):
    totalReviews: int
    suspiciousReviews: int
    activeUsers: int
    flaggedProducts: int
    fake_reviews_count: int
    genuine_reviews_count: int
    average_rating: float
    trends: dict


# ─────────────────────────── JWT TOKEN SCHEMAS ───────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
