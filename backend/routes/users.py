"""
routes/users.py
GET /users    — list all users (public, no auth required for dashboard)
GET /users/me — current authenticated user
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from models import models
from schemas import schemas
from utils.auth_utils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[schemas.UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return all registered users. No authentication required."""
    try:
        users = db.query(models.User).offset(skip).limit(limit).all()
        return users
    except Exception as exc:
        logger.error(f"GET /users failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user
