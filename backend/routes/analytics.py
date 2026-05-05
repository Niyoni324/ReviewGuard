"""
routes/analytics.py
GET /analytics/dashboard — aggregate stats for the dashboard
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.database import get_db
from models import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns aggregated stats matching the keys expected by the frontend:
      totalReviews, suspiciousReviews, activeUsers, flaggedProducts,
      fake_reviews_count, genuine_reviews_count, average_rating, trends
    """
    try:
        total_reviews = db.query(func.count(models.Review.id)).scalar() or 0

        fake_count = (
            db.query(func.count(models.Review.id))
            .filter(models.Review.is_fake == True)
            .scalar() or 0
        )
        genuine_count = total_reviews - fake_count

        active_users = db.query(func.count(models.User.id)).scalar() or 0

        flagged_products = (
            db.query(func.count(func.distinct(models.Review.product_name)))
            .filter(models.Review.is_fake == True)
            .scalar() or 0
        )

        avg_rating_raw = (
            db.query(func.avg(models.Review.rating)).scalar()
        )
        avg_rating = round(float(avg_rating_raw), 2) if avg_rating_raw else 0.0

        return {
            # Keys used by the frontend Dashboard component
            "totalReviews": total_reviews,
            "suspiciousReviews": fake_count,
            "activeUsers": active_users,
            "flaggedProducts": flagged_products,
            # Extra keys for completeness
            "fake_reviews_count": fake_count,
            "genuine_reviews_count": genuine_count,
            "average_rating": avg_rating,
            "trends": {
                "totalReviews": "+0%",
                "suspiciousReviews": "+0%",
                "activeUsers": "+0%",
                "flaggedProducts": "0%",
            },
        }
    except Exception as exc:
        logger.error(f"GET /analytics/dashboard failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard statistics")
