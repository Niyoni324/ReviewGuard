"""
services/fraud_detector.py
Performs sentiment analysis and fake-review detection for each Review.
Stores results in the fraud_analysis table.

Primary: TextBlob sentiment
Fallback: Rating-based heuristic if TextBlob is unavailable
"""

import re
import logging
from collections import Counter
from sqlalchemy.orm import Session
from models.models import Review, FraudAnalysis

logger = logging.getLogger(__name__)

# ─────────────────────────── Spam / Fake Signals ────────────────────────────

SPAM_KEYWORDS = [
    "buy now", "click here", "free", "discount", "100% guaranteed",
    "best ever", "cheap", "limited offer", "act now", "win now",
    "money back", "no risk", "exclusive deal",
]

STOPWORDS = {
    "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "with", "this", "that", "was", "are",
    "i", "my", "me", "we", "our", "you", "your", "very", "so", "be",
    "has", "have", "had", "not", "no", "do", "did", "will", "would",
    "been", "he", "she", "they", "their", "from", "as", "by", "its",
}


# ─────────────────────────── Sentiment Analysis ──────────────────────────────

def _sentiment_from_textblob(text: str) -> tuple[str, float]:
    """Return (sentiment_label, polarity_score) using TextBlob."""
    try:
        from textblob import TextBlob
        polarity = TextBlob(text).sentiment.polarity  # -1.0 to 1.0
        if polarity > 0.1:
            label = "Positive"
        elif polarity < -0.1:
            label = "Negative"
        else:
            label = "Neutral"
        # Normalise polarity to 0–1 confidence
        confidence = round(abs(polarity), 3)
        return label, confidence
    except Exception as exc:
        logger.warning(f"TextBlob failed, using rating fallback: {exc}")
        return None, None  # signal to use fallback


def _sentiment_from_rating(rating: float) -> tuple[str, float]:
    """Rule-based fallback: derive sentiment from star rating."""
    if rating >= 4.0:
        return "Positive", round((rating - 3) / 2, 2)
    elif rating <= 2.0:
        return "Negative", round((3 - rating) / 2, 2)
    else:
        return "Neutral", 0.1


def get_sentiment(text: str, rating: float) -> tuple[str, float]:
    label, confidence = _sentiment_from_textblob(text)
    if label is None:
        label, confidence = _sentiment_from_rating(rating)
    return label, max(confidence, 0.05)


# ─────────────────────────── Fake Review Detection ───────────────────────────

def _has_spam_keywords(text_lower: str) -> bool:
    return any(kw in text_lower for kw in SPAM_KEYWORDS)


def _is_all_caps(text: str) -> bool:
    alpha = [c for c in text if c.isalpha()]
    if len(alpha) < 10:
        return False
    return sum(1 for c in alpha if c.isupper()) / len(alpha) >= 0.6


def _has_repeated_words(text_lower: str) -> bool:
    words = re.findall(r"\b\w+\b", text_lower)
    if len(words) < 4:
        return False
    count = 1
    for i in range(1, len(words)):
        if words[i] == words[i - 1]:
            count += 1
            if count >= 4:
                return True
        else:
            count = 1
    return False


def _is_too_short_with_extreme_rating(text: str, rating: float) -> bool:
    return len(text.strip()) < 20 and (rating >= 4.5 or rating <= 1.5)


def is_fake_review(text: str, rating: float) -> tuple[bool, float]:
    """
    Returns (is_fake, confidence_score).
    Higher confidence = more certain the review is fake.
    """
    text_lower = text.lower()
    signals = []

    if _has_spam_keywords(text_lower):
        signals.append(0.45)
    if _is_all_caps(text):
        signals.append(0.35)
    if _has_repeated_words(text_lower):
        signals.append(0.40)
    if _is_too_short_with_extreme_rating(text, rating):
        signals.append(0.50)

    if not signals:
        return False, 0.05

    # Combine signals (don't just sum — use diminishing returns)
    combined = min(signals[0] + sum(s * 0.5 for s in signals[1:]), 0.99)
    return True, round(combined, 3)


# ─────────────────────────── Keyword Extraction ──────────────────────────────

def extract_keywords(text: str, top_n: int = 5) -> str:
    """
    Simple frequency-based keyword extraction.
    Returns a comma-separated string of top_n content words.
    """
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    if not filtered:
        return ""
    most_common = Counter(filtered).most_common(top_n)
    return ", ".join(word for word, _ in most_common)


# ─────────────────────────── Main Pipeline ───────────────────────────────────

def analyze_review(review: Review) -> dict:
    """
    Run full analysis on a single Review object.
    Returns a dict ready to be used for FraudAnalysis creation.
    """
    text = review.review_text or review.content or ""
    rating = review.rating or 3.0

    sentiment, sentiment_confidence = get_sentiment(text, rating)
    fake, fake_confidence = is_fake_review(text, rating)

    # Blend confidences: if fake the fake score dominates
    if fake:
        final_confidence = round((fake_confidence * 0.7) + (sentiment_confidence * 0.3), 3)
    else:
        final_confidence = round(sentiment_confidence, 3)

    return {
        "sentiment": sentiment,
        "is_fake": fake,
        "confidence_score": min(final_confidence, 0.99),
        "keywords": extract_keywords(text),
    }


def process_all_reviews(db: Session) -> int:
    """
    Analyze every Review that doesn't yet have a FraudAnalysis record.
    Returns the count of newly processed reviews.
    """
    already_analyzed_ids = {fa.review_id for fa in db.query(FraudAnalysis).all()}
    pending = db.query(Review).filter(Review.id.notin_(already_analyzed_ids)).all()

    processed = 0
    for review in pending:
        try:
            result = analyze_review(review)
            fa = FraudAnalysis(
                review_id=review.id,
                sentiment=result["sentiment"],
                is_fake=result["is_fake"],
                confidence_score=result["confidence_score"],
                keywords=result["keywords"],
            )
            # Mirror is_fake onto the review record itself
            review.is_fake = result["is_fake"]
            db.add(fa)
            processed += 1
        except Exception as exc:
            logger.error(f"Failed to analyze review {review.id}: {exc}")

    db.commit()
    logger.info(f"Fraud analysis complete: {processed} reviews processed.")
    return processed
