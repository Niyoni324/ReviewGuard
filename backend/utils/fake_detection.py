import re

def detect_fake_review(content: str) -> bool:
    """
    A simple rule-based approach to detect if a review might be fake or spam.
    Returns True if it's considered fake/spam, False otherwise.
    """
    if not content:
        return False
        
    content_lower = content.lower()
    
    # 1. Check for spam keywords
    spam_keywords = ['buy now', 'cheap', 'discount', 'free money', 'click here', 'guarantee', '100%']
    for keyword in spam_keywords:
        if keyword in content_lower:
            return True
            
    # 2. Check for excessive capitalization (caps lock ratio > 50% for strings longer than 10 chars)
    if len(content) > 10:
        uppercase_count = sum(1 for c in content if c.isupper())
        alpha_count = sum(1 for c in content if c.isalpha())
        if alpha_count > 0 and (uppercase_count / alpha_count) >= 0.5:
            return True
            
    # 3. Check for repeated words (e.g. "good good good good")
    words = content_lower.split()
    if len(words) >= 4: # Only flag if there's enough length
        # Check if same word is repeated more than 3 times sequentially
        count = 1
        for i in range(1, len(words)):
            if words[i] == words[i-1]:
                count += 1
                if count >= 4:
                    return True
            else:
                count = 1
                
    # 4. Check for very short reviews (e.g., just "ok", "a")
    if len(words) < 2:
        return True
        
    return False