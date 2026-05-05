from sqlalchemy import Column, Integer, String, Text, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.database import Base


class User(Base):
    """Registered user accounts. Auth-compatible (keeps username/password)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)                            # Display name
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)                       # Hashed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reviews = relationship("Review", back_populates="owner")


class Review(Base):
    """Product reviews from various sources."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # New canonical fields
    product_name = Column(String(255), nullable=False)
    review_text = Column(Text, nullable=False)
    rating = Column(Float, nullable=False, default=3.0)
    source = Column(String(100), nullable=False, default="Unknown")
    # Legacy columns kept for backward-compat (nullable)
    product = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    is_fake = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="reviews")
    fraud_analysis = relationship("FraudAnalysis", back_populates="review", uselist=False)


class FraudAnalysis(Base):
    """NLP-based fraud and sentiment analysis results per review."""
    __tablename__ = "fraud_analysis"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, unique=True)
    sentiment = Column(String(20), nullable=False, default="Neutral")   # Positive / Negative / Neutral
    is_fake = Column(Boolean, nullable=False, default=False)
    confidence_score = Column(Float, nullable=False, default=0.5)        # 0.0 – 1.0
    keywords = Column(Text, nullable=True)                               # Comma-separated top keywords
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    review = relationship("Review", back_populates="fraud_analysis")
