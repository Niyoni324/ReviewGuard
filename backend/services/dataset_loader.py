import os
import sys
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

# Assuming this script can be run standalone or imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import SessionLocal
from models.models import Review

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_amazon_dataset(db: Session = None, csv_path: str = None, limit: int = 5000):
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    if csv_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(base_dir, 'dataset', 'amazon_reviews_2019.csv')

    if db.query(Review).count() > 0:
        logger.info("Database already contains reviews, skipping dataset loading.")
        if close_db:
            db.close()
        return 0

    if not os.path.exists(csv_path):
        err_msg = f"Dataset file not found at {csv_path}"
        logger.error(err_msg)
        if close_db:
            db.close()
        raise FileNotFoundError(err_msg)

    logger.info(f"Reading dataset from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        if close_db:
            db.close()
        raise e

    # Extract required columns and rename
    required_columns = {
        'product_description': 'product_name',
        'review_text': 'review_text',
        'review_rating': 'rating',
        'online_store': 'source'
    }

    missing_columns = [col for col in required_columns.keys() if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns in CSV: {missing_columns}")
        if close_db:
            db.close()
        raise ValueError(f"Missing columns: {missing_columns}")

    # Subset and rename columns
    df = df[list(required_columns.keys())].rename(columns=required_columns)

    # Drop null values
    df.dropna(inplace=True)

    # Limit to specified rows
    df = df.head(limit)

    rows_loaded = len(df)
    logger.info(f"Number of rows loaded: {rows_loaded}")

    if rows_loaded == 0:
        if close_db:
            db.close()
        return 0

    try:
        # Avoid duplicates by checking existing reviews
        existing_reviews = db.query(Review.product_name, Review.review_text).all()
        existing_set = {(r[0], r[1]) for r in existing_reviews}

        new_records = []
        for _, row in df.iterrows():
            if (row['product_name'], row['review_text']) not in existing_set:
                new_review = Review(
                    product_name=str(row['product_name']),
                    review_text=str(row['review_text']),
                    rating=float(row['rating']),
                    source=str(row['source']),
                    created_at=datetime.utcnow()
                )
                new_records.append(new_review)

        if not new_records:
            logger.info("Number inserted: 0 (All loaded rows are duplicates)")
            if close_db:
                db.close()
            return 0

        # Insert reviews using add_all so IDs are populated after flush
        db.add_all(new_records)
        db.flush() # Use flush instead of commit so we do one single commit at the end

        logger.info(f"Number of reviews inserted (flushed): {len(new_records)}")

        # Run fraud detection on inserted reviews
        from services.fraud_detector import analyze_review
        from models.models import FraudAnalysis

        logger.info("Running fraud detection on new reviews...")
        fraud_records = []
        for review in new_records:
            # Call existing analyze_review
            analysis = analyze_review(review)
            
            # Extract and create FraudAnalysis record
            fa = FraudAnalysis(
                review_id=review.id,
                is_fake=analysis['is_fake'],
                confidence_score=analysis['confidence_score'],
                sentiment=analysis['sentiment'],
                keywords=analysis['keywords']
            )
            fraud_records.append(fa)
            
            review.is_fake = analysis['is_fake']

        if fraud_records:
            db.bulk_save_objects(fraud_records)
            logger.info(f"Inserted {len(fraud_records)} records into fraud_analysis table.")

        # Single commit at the end
        db.commit()
        logger.info("Fraud analysis completed and database committed successfully.")

        return len(new_records)

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to insert data into database: {e}")
        return 0
    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    load_amazon_dataset()
