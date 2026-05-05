"""
main.py — ReviewGuard FastAPI Application Entry Point

Startup sequence:
  1. Create all DB tables (if not exist)
  2. Seed users + dataset if DB is empty
  3. Run fraud analysis on any unanalyzed reviews
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import engine, Base, SessionLocal
from routes import auth, users, reviews, analytics, analysis

# ─────────────────────────── Logging ─────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────────── Startup / Shutdown ───────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before the server begins accepting requests."""
    logger.info("ReviewGuard server starting up…")

    # 1. Ensure all tables exist (never drops existing data)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified / created.")
    except Exception as e:
        logger.error(f"Database connection or table creation failed: {e}")
        # Log error and prevent crash

    # 2. Seed data only when the reviews table is empty
    db = SessionLocal()
    try:
        from models.models import Review
        review_count = db.query(Review).count()

        if review_count == 0:
            logger.info("Reviews table is empty — loading dataset…")
            
            # Try to load the real dataset. No mock data fallback.
            from services.dataset_loader import load_amazon_dataset
            try:
                inserted = load_amazon_dataset(db, limit=5000)
                if inserted > 0:
                    logger.info(f"Successfully loaded {inserted} real reviews from dataset.")
            except FileNotFoundError as e:
                logger.error(f"Dataset file missing: {e}. Raising error without mock fallback.")
                raise e
            except Exception as e:
                logger.error(f"An unexpected error occurred during dataset loading: {e}")
                raise e
        else:
            logger.info(f"Database already has {review_count} reviews — skipping seed.")

        # Still run fraud analysis on any reviews that are missing it
        from services.fraud_detector import process_all_reviews
        processed = process_all_reviews(db)
        if processed:
            logger.info(f"Analyzed {processed} previously unanalyzed reviews.")

    except FileNotFoundError as exc:
        logger.error("Halting server startup due to missing dataset file.")
        raise exc
    except Exception as exc:
        logger.error(f"Startup seeding failed: {exc}", exc_info=True)
    finally:
        db.close()

    logger.info("ReviewGuard is ready to serve requests.")
    yield
    logger.info("ReviewGuard server shutting down.")


# ─────────────────────────── App Instance ────────────────────────────────────

app = FastAPI(
    title="ReviewGuard API",
    description=(
        "Fake review detection platform. "
        "Automatically ingests, analyzes and flags suspicious reviews. "
        "Visit /docs for interactive API explorer."
    ),
    version="2.0.0",
    lifespan=lifespan,
)


# ─────────────────────────── CORS ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Open for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────── Routers ─────────────────────────────────────────

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(analytics.router)
app.include_router(analysis.router)


# ─────────────────────────── Health Check ────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "message": "ReviewGuard API v2.0 is running.",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Quick liveness probe."""
    return {"status": "healthy"}

