"""
routes/reviews.py
GET  /reviews        — public list of all reviews (no auth required)
POST /reviews        — create a review (auth required)
GET  /reviews/{id}   — single review
DELETE /reviews/{id} — delete own review (auth required)
POST /fetch-reviews  — trigger data ingestion + fraud analysis (background)
POST /load-dataset   — manually trigger real dataset loading
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from database.database import get_db
from models import models
from schemas import schemas
from utils.auth_utils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["Reviews"])


# ─────────────────────────── Background job ──────────────────────────────────

def _run_fetch_and_analyze(db: Session):
    """Background task: fetch new reviews (using real dataset) and run fraud analysis."""
    try:
        from services.dataset_loader import load_amazon_dataset
        from services.fraud_detector import process_all_reviews

        inserted = load_amazon_dataset(db, limit=5000)
        processed = process_all_reviews(db)
        logger.info(f"Background fetch complete — {inserted} inserted, {processed} reviews analyzed.")
    except Exception as exc:
        logger.error(f"Background fetch-reviews task failed: {exc}")

def _run_load_dataset(db: Session):
    """Background task: load real dataset and run fraud analysis."""
    try:
        from services.dataset_loader import load_amazon_dataset
        inserted = load_amazon_dataset(db, limit=5000)
        logger.info(f"Background dataset load complete — {inserted} records inserted.")
    except Exception as exc:
        logger.error(f"Background load-dataset task failed: {exc}")


# ─────────────────────────── Endpoints ───────────────────────────────────────

@router.get("", response_model=List[schemas.ReviewResponse])
def get_reviews(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return up to `limit` reviews. No authentication required."""
    try:
        reviews = db.query(models.Review).offset(skip).limit(limit).all()
        return reviews
    except Exception as exc:
        logger.error(f"GET /reviews failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch reviews")


@router.get("/{review_id}", response_model=schemas.ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail=f"Review {review_id} not found")
    return review


@router.post("", response_model=schemas.ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Submit a new review. Runs fake-detection synchronously."""
    from services.fraud_detector import analyze_review as _analyze

    # Support legacy fields (product / content) from older frontend
    product_name = review.product_name or review.product or "Unknown Product"
    review_text  = review.review_text  or review.content  or ""

    new_review = models.Review(
        user_id=current_user.id,
        product_name=product_name,
        review_text=review_text,
        rating=review.rating,
        source=review.source or "Unknown",
        product=product_name,
        content=review_text,
    )
    db.add(new_review)
    db.flush()

    # Immediate fraud analysis
    result = _analyze(new_review)
    new_review.is_fake = result["is_fake"]
    fa = models.FraudAnalysis(
        review_id=new_review.id,
        sentiment=result["sentiment"],
        is_fake=result["is_fake"],
        confidence_score=result["confidence_score"],
        keywords=result["keywords"],
    )
    db.add(fa)
    db.commit()
    db.refresh(new_review)
    return new_review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail=f"Review {review_id} not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(review)
    db.commit()
    return None


@router.post("/fetch-reviews", status_code=status.HTTP_202_ACCEPTED)
def fetch_reviews(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Trigger background ingestion of new mock reviews + fraud analysis.
    Returns immediately with 202 Accepted.
    """
    background_tasks.add_task(_run_fetch_and_analyze, db)
    return {"message": "Review ingestion started in background. Check /reviews shortly."}

@router.post("/load-dataset", status_code=status.HTTP_202_ACCEPTED)
def load_dataset(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Manually trigger loading the real Amazon dataset.
    Returns immediately with 202 Accepted.
    """
    background_tasks.add_task(_run_load_dataset, db)
    return {"message": "Dataset loading started in background. This may take a moment."}
