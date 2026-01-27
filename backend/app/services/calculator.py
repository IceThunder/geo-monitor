"""
Metric calculation services.
"""
from typing import List, Dict, Optional


def calculate_sov(brand_mentions: List[str], total_models: int) -> float:
    """
    Calculate Share of Voice (SOV).
    
    SOV = (品牌提及次数 / 查询模型总数) × 100%
    
    Args:
        brand_mentions: List of brand names mentioned.
        total_models: Total number of models queried.
        
    Returns:
        SOV percentage (0-100).
    """
    if total_models == 0 or not brand_mentions:
        return 0.0
    
    unique_brands = len(set(brand_mentions))
    return round((unique_brands / total_models) * 100, 2)


def calculate_accuracy_score(
    response: str, 
    fact_sheet: Optional[Dict] = None,
    evaluator_response: Optional[Dict] = None
) -> int:
    """
    Calculate accuracy score (1-10).
    
    This can be done via:
    1. Direct comparison with fact sheet
    2. LLM evaluation (preferred)
    
    Args:
        response: The model's response to evaluate.
        fact_sheet: Brand fact sheet for comparison.
        evaluator_response: Pre-computed evaluation from LLM.
        
    Returns:
        Accuracy score (1-10).
    """
    if evaluator_response:
        return evaluator_response.get("accuracy_score", 5)
    
    # Placeholder: without evaluation, return neutral score
    return 5


def analyze_sentiment(text: str) -> float:
    """
    Analyze sentiment of text.
    
    Returns:
        Sentiment score (-1 to 1).
        -1: Negative
         0: Neutral
         1: Positive
    """
    # Simplified sentiment analysis
    # In production, use a proper NLP model or LLM
    
    positive_words = ["good", "great", "excellent", "best", "recommend", "love", "perfect"]
    negative_words = ["bad", "worst", "terrible", "avoid", "hate", "poor", "fail"]
    
    text_lower = text.lower()
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total = positive_count + negative_count
    if total == 0:
        return 0.0
    
    score = (positive_count - negative_count) / total
    return round(score, 2)


def calculate_citation_rate(answers_with_links: int, total_mentions: int) -> float:
    """
    Calculate Citation Rate (CR).
    
    CR = (包含品牌链接的回答数 / 品牌总提及数) × 100%
    
    Args:
        answers_with_links: Number of answers containing brand links.
        total_mentions: Total number of brand mentions.
        
    Returns:
        Citation rate percentage (0-100).
    """
    if total_mentions == 0:
        return 0.0
    
    return round((answers_with_links / total_mentions) * 100, 2)


def check_positioning_hit(
    response: str, 
    brand: str, 
    positioning_keywords: List[str],
    window_size: int = 50
) -> bool:
    """
    Check if brand name and positioning keywords co-occur in the response.
    
    Uses a sliding window approach to detect proximity.
    
    Args:
        response: The model's response text.
        brand: The brand name to check.
        positioning_keywords: List of positioning keywords.
        window_size: Token window size for co-occurrence detection.
        
    Returns:
        True if positioning hit detected.
    """
    tokens = response.split()
    brand_tokens = brand.lower().split()
    
    for i, token in enumerate(tokens):
        token_lower = token.lower()
        
        # Check if token is part of brand name
        if any(bt in token_lower for bt in brand_tokens):
            # Get window
            start = max(0, i - window_size)
            end = min(len(tokens), i + window_size + 1)
            window_text = " ".join(tokens[start:end]).lower()
            
            # Check for positioning keywords
            if any(pk.lower() in window_text for pk in positioning_keywords):
                return True
    
    return False


def calculate_brand_mentions(response: Dict) -> List[str]:
    """
    Extract brand mentions from model response.
    
    Args:
        response: Parsed JSON response from the model.
        
    Returns:
        List of brand names mentioned.
    """
    brands = response.get("brands", [])
    return [b.get("name") for b in brands if b.get("name")]


def calculate_overall_metrics(
    sov_score: float,
    accuracy_score: int,
    sentiment_score: float,
    citation_rate: float,
    positioning_hit: bool,
) -> Dict:
    """
    Calculate overall quality score from individual metrics.
    
    Args:
        sov_score: Share of Voice score (0-100).
        accuracy_score: Accuracy score (1-10).
        sentiment_score: Sentiment score (-1 to 1).
        citation_rate: Citation rate (0-100).
        positioning_hit: Whether positioning keywords were hit.
        
    Returns:
        Dictionary with overall metrics.
    """
    # Normalize scores to 0-100 scale
    sov_normalized = sov_score
    accuracy_normalized = accuracy_score * 10  # 1-10 to 10-100
    sentiment_normalized = (sentiment_score + 1) * 50  # -1 to 1 to 0-100
    citation_normalized = citation_rate
    
    # Calculate weighted overall score
    # Weights can be adjusted based on business priorities
    weights = {
        "sov": 0.25,
        "accuracy": 0.35,
        "sentiment": 0.20,
        "citation": 0.20,
    }
    
    overall_score = (
        sov_normalized * weights["sov"] +
        accuracy_normalized * weights["accuracy"] +
        sentiment_normalized * weights["sentiment"] +
        citation_normalized * weights["citation"]
    )
    
    return {
        "sov_score": sov_score,
        "accuracy_score": accuracy_score,
        "sentiment_score": sentiment_score,
        "citation_rate": citation_rate,
        "positioning_hit": positioning_hit,
        "overall_score": round(overall_score, 2),
        "overall_grade": get_grade(overall_score),
    }


def get_grade(score: float) -> str:
    """
    Convert numerical score to letter grade.
    
    Args:
        score: Numerical score (0-100).
        
    Returns:
        Letter grade (A+, A, B+, B, C+, C, D, F).
    """
    if score >= 90:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 80:
        return "B+"
    elif score >= 75:
        return "B"
    elif score >= 70:
        return "C+"
    elif score >= 65:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "F"
