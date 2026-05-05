"""
routes/analysis.py
GET /fraud-analysis — return all fraud analysis records with embedded review info
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database.database import get_db
from models import models
from schemas import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fraud-analysis", tags=["Fraud Analysis"])


@router.get("", response_model=List[schemas.FraudAnalysisDetail])
def get_fraud_analysis(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Return fraud analysis results joined with review information.
    No authentication required.
    """
    try:
        records = (
            db.query(models.FraudAnalysis)
            .options(joinedload(models.FraudAnalysis.review))
            .offset(skip)
            .limit(limit)
            .all()
        )

        result = []
        for fa in records:
            if fa.review is None:
                continue  # skip orphaned records
            result.append(schemas.FraudAnalysisDetail(
                id=fa.id,
                review_id=fa.review_id,
                product_name=fa.review.product_name or "",
                review_text=fa.review.review_text or "",
                rating=fa.review.rating or 0.0,
                source=fa.review.source or "Unknown",
                sentiment=fa.sentiment,
                is_fake=fa.is_fake,
                confidence_score=fa.confidence_score,
                keywords=fa.keywords,
                created_at=fa.created_at,
            ))
        return result
    except Exception as exc:
        logger.error(f"GET /fraud-analysis failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch fraud analysis data")
