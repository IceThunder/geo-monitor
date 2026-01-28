"""
Metric calculation services.
"""
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal
import re
import math
from collections import Counter
from datetime import datetime, timedelta


def calculate_sov(brand_mentions: List[str], total_models: int, target_brand: Optional[str] = None) -> float:
    """
    Calculate enhanced Share of Voice (SOV).
    
    SOV = (目标品牌提及次数 / 总品牌提及次数) × 100%
    
    Args:
        brand_mentions: List of brand names mentioned.
        total_models: Total number of models queried.
        target_brand: Specific brand to calculate SOV for.
        
    Returns:
        SOV percentage (0-100).
    """
    if not brand_mentions:
        return 0.0
    
    if target_brand:
        # Calculate SOV for specific brand
        target_mentions = sum(1 for brand in brand_mentions if brand.lower() == target_brand.lower())
        return round((target_mentions / len(brand_mentions)) * 100, 2)
    else:
        # Calculate overall brand diversity SOV
        unique_brands = len(set(brand_mentions))
        return round((unique_brands / max(total_models, 1)) * 100, 2)


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


def analyze_sentiment(text: str, brand_context: Optional[str] = None) -> Tuple[float, Dict[str, Any]]:
    """
    Enhanced sentiment analysis with context awareness.
    
    Returns:
        Tuple of (sentiment_score, analysis_details)
        sentiment_score: -1 to 1 (negative to positive)
        analysis_details: Dictionary with detailed analysis
    """
    # Enhanced sentiment lexicon
    positive_words = {
        "excellent": 1.0, "outstanding": 1.0, "exceptional": 1.0,
        "great": 0.8, "good": 0.6, "nice": 0.4, "decent": 0.3,
        "recommend": 0.7, "love": 0.9, "perfect": 1.0, "amazing": 0.9,
        "reliable": 0.7, "trusted": 0.8, "quality": 0.6, "innovative": 0.7
    }
    
    negative_words = {
        "terrible": -1.0, "awful": -1.0, "horrible": -1.0,
        "bad": -0.6, "poor": -0.7, "worst": -1.0, "hate": -0.9,
        "avoid": -0.8, "disappointing": -0.6, "unreliable": -0.7,
        "expensive": -0.4, "slow": -0.3, "complicated": -0.3
    }
    
    # Intensifiers and negations
    intensifiers = {"very": 1.5, "extremely": 2.0, "quite": 1.2, "really": 1.3}
    negations = ["not", "no", "never", "nothing", "nobody", "nowhere", "neither", "nor"]
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    sentiment_scores = []
    analysis_details = {
        "positive_words_found": [],
        "negative_words_found": [],
        "intensifiers_found": [],
        "negations_found": [],
        "context_mentions": []
    }
    
    for i, word in enumerate(words):
        score = 0
        intensity = 1.0
        negated = False
        
        # Check for negations in previous 2 words
        if i > 0 and words[i-1] in negations:
            negated = True
        elif i > 1 and words[i-2] in negations:
            negated = True
        
        # Check for intensifiers in previous word
        if i > 0 and words[i-1] in intensifiers:
            intensity = intensifiers[words[i-1]]
            analysis_details["intensifiers_found"].append(words[i-1])
        
        # Calculate sentiment score
        if word in positive_words:
            score = positive_words[word] * intensity
            analysis_details["positive_words_found"].append(word)
        elif word in negative_words:
            score = negative_words[word] * intensity
            analysis_details["negative_words_found"].append(word)
        
        # Apply negation
        if negated:
            score = -score
            analysis_details["negations_found"].append(f"negated {word}")
        
        if score != 0:
            sentiment_scores.append(score)
        
        # Track brand context mentions
        if brand_context and brand_context.lower() in word:
            analysis_details["context_mentions"].append(word)
    
    # Calculate final sentiment score
    if not sentiment_scores:
        final_score = 0.0
    else:
        # Use weighted average with decay for distant words
        final_score = sum(sentiment_scores) / len(sentiment_scores)
        final_score = max(-1.0, min(1.0, final_score))  # Clamp to [-1, 1]
    
    analysis_details["total_sentiment_words"] = len(sentiment_scores)
    analysis_details["raw_scores"] = sentiment_scores
    
    return round(final_score, 3), analysis_details


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


def calculate_competitive_analysis(
    brand_data: List[Dict[str, Any]], 
    target_brand: str
) -> Dict[str, Any]:
    """
    Calculate competitive analysis metrics.
    
    Args:
        brand_data: List of brand performance data
        target_brand: The brand to analyze against competitors
        
    Returns:
        Dictionary with competitive analysis results
    """
    if not brand_data:
        return {}
    
    # Find target brand data
    target_data = None
    competitors = []
    
    for brand in brand_data:
        if brand.get("name", "").lower() == target_brand.lower():
            target_data = brand
        else:
            competitors.append(brand)
    
    if not target_data:
        return {"error": "Target brand not found in data"}
    
    # Calculate competitive metrics
    target_sov = target_data.get("sov_score", 0)
    target_accuracy = target_data.get("accuracy_score", 0)
    target_sentiment = target_data.get("sentiment_score", 0)
    
    competitor_sovs = [c.get("sov_score", 0) for c in competitors]
    competitor_accuracies = [c.get("accuracy_score", 0) for c in competitors]
    competitor_sentiments = [c.get("sentiment_score", 0) for c in competitors]
    
    # Calculate rankings and percentiles
    all_sovs = competitor_sovs + [target_sov]
    all_accuracies = competitor_accuracies + [target_accuracy]
    all_sentiments = competitor_sentiments + [target_sentiment]
    
    sov_rank = sorted(all_sovs, reverse=True).index(target_sov) + 1
    accuracy_rank = sorted(all_accuracies, reverse=True).index(target_accuracy) + 1
    sentiment_rank = sorted(all_sentiments, reverse=True).index(target_sentiment) + 1
    
    return {
        "target_brand": target_brand,
        "total_competitors": len(competitors),
        "rankings": {
            "sov_rank": sov_rank,
            "accuracy_rank": accuracy_rank,
            "sentiment_rank": sentiment_rank,
            "overall_rank": round((sov_rank + accuracy_rank + sentiment_rank) / 3, 1)
        },
        "performance_vs_average": {
            "sov_vs_avg": round(target_sov - (sum(competitor_sovs) / len(competitor_sovs) if competitor_sovs else 0), 2),
            "accuracy_vs_avg": round(target_accuracy - (sum(competitor_accuracies) / len(competitor_accuracies) if competitor_accuracies else 0), 2),
            "sentiment_vs_avg": round(target_sentiment - (sum(competitor_sentiments) / len(competitor_sentiments) if competitor_sentiments else 0), 2)
        },
        "market_share": {
            "sov_share": round((target_sov / sum(all_sovs)) * 100, 2) if sum(all_sovs) > 0 else 0
        }
    }


def calculate_trend_analysis(
    historical_data: List[Dict[str, Any]], 
    metric: str,
    periods: int = 7
) -> Dict[str, Any]:
    """
    Calculate trend analysis for a specific metric.
    
    Args:
        historical_data: List of historical metric data points
        metric: The metric to analyze (sov_score, accuracy_score, etc.)
        periods: Number of periods to analyze
        
    Returns:
        Dictionary with trend analysis results
    """
    if len(historical_data) < 2:
        return {"error": "Insufficient data for trend analysis"}
    
    # Sort data by timestamp
    sorted_data = sorted(historical_data, key=lambda x: x.get("timestamp", datetime.min))
    
    # Extract metric values
    values = [float(d.get(metric, 0)) for d in sorted_data[-periods:]]
    
    if len(values) < 2:
        return {"error": "Insufficient values for trend analysis"}
    
    # Calculate trend metrics
    current_value = values[-1]
    previous_value = values[-2]
    first_value = values[0]
    
    # Calculate changes
    period_change = current_value - previous_value
    period_change_pct = (period_change / previous_value * 100) if previous_value != 0 else 0
    
    total_change = current_value - first_value
    total_change_pct = (total_change / first_value * 100) if first_value != 0 else 0
    
    # Calculate moving average
    moving_avg = sum(values) / len(values)
    
    # Calculate volatility (standard deviation)
    variance = sum((x - moving_avg) ** 2 for x in values) / len(values)
    volatility = math.sqrt(variance)
    
    # Determine trend direction
    if len(values) >= 3:
        recent_trend = "increasing" if values[-1] > values[-2] > values[-3] else \
                      "decreasing" if values[-1] < values[-2] < values[-3] else "stable"
    else:
        recent_trend = "increasing" if period_change > 0 else "decreasing" if period_change < 0 else "stable"
    
    return {
        "metric": metric,
        "current_value": round(current_value, 2),
        "previous_value": round(previous_value, 2),
        "period_change": round(period_change, 2),
        "period_change_pct": round(period_change_pct, 2),
        "total_change": round(total_change, 2),
        "total_change_pct": round(total_change_pct, 2),
        "moving_average": round(moving_avg, 2),
        "volatility": round(volatility, 2),
        "trend_direction": recent_trend,
        "data_points": len(values),
        "analysis_period": periods
    }


def calculate_brand_health_score(
    sov_score: float,
    accuracy_score: int,
    sentiment_score: float,
    citation_rate: float,
    positioning_hits: int,
    total_mentions: int,
    competitive_rank: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive brand health score.
    
    Args:
        sov_score: Share of Voice score (0-100)
        accuracy_score: Accuracy score (1-10)
        sentiment_score: Sentiment score (-1 to 1)
        citation_rate: Citation rate (0-100)
        positioning_hits: Number of positioning keyword hits
        total_mentions: Total brand mentions
        competitive_rank: Rank among competitors (optional)
        
    Returns:
        Dictionary with brand health analysis
    """
    # Normalize all scores to 0-100 scale
    sov_normalized = min(100, max(0, sov_score))
    accuracy_normalized = min(100, max(0, (accuracy_score - 1) * 11.11))  # 1-10 to 0-100
    sentiment_normalized = min(100, max(0, (sentiment_score + 1) * 50))  # -1 to 1 to 0-100
    citation_normalized = min(100, max(0, citation_rate))
    
    # Calculate positioning effectiveness
    positioning_rate = (positioning_hits / max(total_mentions, 1)) * 100
    positioning_normalized = min(100, positioning_rate)
    
    # Define weights for different aspects of brand health
    weights = {
        "visibility": 0.25,      # SOV
        "credibility": 0.25,     # Accuracy + Citation
        "perception": 0.25,      # Sentiment
        "positioning": 0.15,     # Positioning hits
        "competitive": 0.10      # Competitive position
    }
    
    # Calculate component scores
    visibility_score = sov_normalized
    credibility_score = (accuracy_normalized * 0.7 + citation_normalized * 0.3)
    perception_score = sentiment_normalized
    positioning_score = positioning_normalized
    
    # Competitive score (if available)
    if competitive_rank:
        # Convert rank to score (lower rank = higher score)
        competitive_score = max(0, 100 - (competitive_rank - 1) * 10)
    else:
        competitive_score = 50  # Neutral if no competitive data
    
    # Calculate weighted overall score
    overall_score = (
        visibility_score * weights["visibility"] +
        credibility_score * weights["credibility"] +
        perception_score * weights["perception"] +
        positioning_score * weights["positioning"] +
        competitive_score * weights["competitive"]
    )
    
    # Determine health status
    if overall_score >= 80:
        health_status = "Excellent"
        health_color = "green"
    elif overall_score >= 65:
        health_status = "Good"
        health_color = "lightgreen"
    elif overall_score >= 50:
        health_status = "Fair"
        health_color = "yellow"
    elif overall_score >= 35:
        health_status = "Poor"
        health_color = "orange"
    else:
        health_status = "Critical"
        health_color = "red"
    
    # Identify strengths and weaknesses
    component_scores = {
        "visibility": visibility_score,
        "credibility": credibility_score,
        "perception": perception_score,
        "positioning": positioning_score,
        "competitive": competitive_score
    }
    
    strengths = [k for k, v in component_scores.items() if v >= 70]
    weaknesses = [k for k, v in component_scores.items() if v < 50]
    
    return {
        "overall_score": round(overall_score, 1),
        "health_status": health_status,
        "health_color": health_color,
        "grade": get_grade(overall_score),
        "component_scores": {
            "visibility": round(visibility_score, 1),
            "credibility": round(credibility_score, 1),
            "perception": round(perception_score, 1),
            "positioning": round(positioning_score, 1),
            "competitive": round(competitive_score, 1)
        },
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": _generate_recommendations(weaknesses, component_scores)
    }


def _generate_recommendations(weaknesses: List[str], scores: Dict[str, float]) -> List[str]:
    """
    Generate actionable recommendations based on weaknesses.
    
    Args:
        weaknesses: List of weak areas
        scores: Component scores
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    if "visibility" in weaknesses:
        recommendations.append("Increase content marketing and SEO efforts to improve brand visibility")
    
    if "credibility" in weaknesses:
        if scores.get("credibility", 0) < 40:
            recommendations.append("Focus on accuracy in brand communications and obtain more authoritative citations")
        else:
            recommendations.append("Improve fact-checking processes and seek more quality backlinks")
    
    if "perception" in weaknesses:
        recommendations.append("Implement reputation management strategies to improve brand sentiment")
    
    if "positioning" in weaknesses:
        recommendations.append("Strengthen brand positioning by consistently using key positioning terms")
    
    if "competitive" in weaknesses:
        recommendations.append("Analyze competitor strategies and differentiate brand positioning")
    
    if not recommendations:
        recommendations.append("Continue current strategies while monitoring for optimization opportunities")
    
    return recommendations
