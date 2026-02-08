"""
Unit tests for the metrics calculator module: app.services.calculator

These are pure unit tests with no database or HTTP dependencies.

Covers:
- calculate_sov
- calculate_accuracy_score
- analyze_sentiment
- calculate_citation_rate
- check_positioning_hit
- calculate_overall_metrics
- get_grade
"""
import pytest

from app.services.calculator import (
    calculate_sov,
    calculate_accuracy_score,
    analyze_sentiment,
    calculate_citation_rate,
    check_positioning_hit,
    calculate_overall_metrics,
    get_grade,
)


# ---------------------------------------------------------------------------
# calculate_sov
# ---------------------------------------------------------------------------

class TestCalculateSov:
    """Share of Voice calculation tests."""

    def test_sov_with_target_brand(self):
        """SOV for a specific brand = (brand mentions / total mentions) * 100."""
        mentions = ["BrandA", "BrandB", "BrandA", "BrandC", "BrandA"]
        result = calculate_sov(mentions, total_models=3, target_brand="BrandA")
        # BrandA appears 3 times out of 5 mentions = 60%
        assert result == 60.0

    def test_sov_with_target_brand_case_insensitive(self):
        """SOV brand matching is case-insensitive."""
        mentions = ["branda", "BRANDA", "BrandB"]
        result = calculate_sov(mentions, total_models=2, target_brand="BrandA")
        # 2 out of 3 = 66.67%
        assert result == pytest.approx(66.67, abs=0.01)

    def test_sov_without_target_brand(self):
        """Without target brand, SOV = (unique brands / total_models) * 100."""
        mentions = ["BrandA", "BrandB", "BrandA"]
        result = calculate_sov(mentions, total_models=5)
        # 2 unique brands / 5 models = 40%
        assert result == 40.0

    def test_sov_empty_mentions(self):
        """Empty mention list returns 0."""
        result = calculate_sov([], total_models=3)
        assert result == 0.0

    def test_sov_single_brand(self):
        """All mentions are the same brand."""
        mentions = ["OnlyBrand", "OnlyBrand", "OnlyBrand"]
        result = calculate_sov(mentions, total_models=3, target_brand="OnlyBrand")
        assert result == 100.0

    def test_sov_target_not_mentioned(self):
        """Target brand not in mentions returns 0."""
        mentions = ["BrandX", "BrandY"]
        result = calculate_sov(mentions, total_models=2, target_brand="BrandZ")
        assert result == 0.0


# ---------------------------------------------------------------------------
# calculate_accuracy_score
# ---------------------------------------------------------------------------

class TestCalculateAccuracyScore:
    """Accuracy score calculation tests."""

    def test_with_evaluator_response(self):
        """Uses the evaluator's score when provided."""
        evaluator = {"accuracy_score": 8}
        result = calculate_accuracy_score("some response", evaluator_response=evaluator)
        assert result == 8

    def test_evaluator_missing_key(self):
        """Falls back to 5 when evaluator dict lacks accuracy_score key."""
        evaluator = {"other_field": 10}
        result = calculate_accuracy_score("some response", evaluator_response=evaluator)
        assert result == 5

    def test_without_evaluator(self):
        """Without evaluator response, returns neutral score of 5."""
        result = calculate_accuracy_score("some response text")
        assert result == 5

    def test_with_fact_sheet_no_evaluator(self):
        """Fact sheet alone still returns 5 (placeholder behavior)."""
        result = calculate_accuracy_score(
            "response text",
            fact_sheet={"founded": "2020", "hq": "San Francisco"},
        )
        assert result == 5


# ---------------------------------------------------------------------------
# analyze_sentiment
# ---------------------------------------------------------------------------

class TestAnalyzeSentiment:
    """Sentiment analysis tests."""

    def test_positive_text(self):
        """Text with positive words returns positive sentiment."""
        score, details = analyze_sentiment("This product is excellent and amazing")
        assert score > 0
        assert "excellent" in details["positive_words_found"]
        assert "amazing" in details["positive_words_found"]

    def test_negative_text(self):
        """Text with negative words returns negative sentiment."""
        score, details = analyze_sentiment("This is terrible and awful service")
        assert score < 0
        assert "terrible" in details["negative_words_found"]
        assert "awful" in details["negative_words_found"]

    def test_neutral_text(self):
        """Text without sentiment words returns 0."""
        score, details = analyze_sentiment("The sky is blue and water is wet")
        assert score == 0.0
        assert details["total_sentiment_words"] == 0

    def test_mixed_text(self):
        """Text with both positive and negative words returns averaged score."""
        score, details = analyze_sentiment("The product is good but the service is bad")
        # good (0.6) and bad (-0.6) should roughly cancel out
        assert -0.1 <= score <= 0.1

    def test_negation_flips_sentiment(self):
        """Negation word before a positive word makes it negative."""
        score, details = analyze_sentiment("This is not good at all")
        # "not good" should flip "good" from positive to negative
        assert score < 0

    def test_intensifier_amplifies(self):
        """Intensifier word before a sentiment word amplifies the score."""
        # Without intensifier
        base_score, _ = analyze_sentiment("It is good")
        # With intensifier
        intensified_score, details = analyze_sentiment("It is very good")

        assert abs(intensified_score) > abs(base_score)
        assert "very" in details["intensifiers_found"]

    def test_brand_context(self):
        """Brand context tracking finds mentions."""
        score, details = analyze_sentiment(
            "Apple makes excellent products",
            brand_context="apple"
        )
        assert score > 0
        assert len(details["context_mentions"]) > 0

    def test_empty_text(self):
        """Empty text returns 0 sentiment."""
        score, details = analyze_sentiment("")
        assert score == 0.0


# ---------------------------------------------------------------------------
# calculate_citation_rate
# ---------------------------------------------------------------------------

class TestCalculateCitationRate:
    """Citation rate calculation tests."""

    def test_normal_case(self):
        """Standard citation rate calculation."""
        result = calculate_citation_rate(answers_with_links=3, total_mentions=10)
        assert result == 30.0

    def test_zero_mentions(self):
        """Zero total mentions returns 0 to avoid division by zero."""
        result = calculate_citation_rate(answers_with_links=5, total_mentions=0)
        assert result == 0.0

    def test_all_cited(self):
        """All mentions have links = 100%."""
        result = calculate_citation_rate(answers_with_links=10, total_mentions=10)
        assert result == 100.0

    def test_none_cited(self):
        """No mentions have links = 0%."""
        result = calculate_citation_rate(answers_with_links=0, total_mentions=10)
        assert result == 0.0

    def test_fractional_result(self):
        """Result is rounded to 2 decimal places."""
        result = calculate_citation_rate(answers_with_links=1, total_mentions=3)
        assert result == pytest.approx(33.33, abs=0.01)


# ---------------------------------------------------------------------------
# check_positioning_hit
# ---------------------------------------------------------------------------

class TestCheckPositioningHit:
    """Positioning hit detection tests."""

    def test_hit_when_brand_and_keyword_near(self):
        """Returns True when brand and positioning keyword co-occur."""
        response = "Apple is known for innovative design and premium quality devices"
        result = check_positioning_hit(
            response=response,
            brand="Apple",
            positioning_keywords=["innovative", "premium"],
        )
        assert result is True

    def test_miss_when_no_keyword(self):
        """Returns False when positioning keywords are absent."""
        response = "Apple released a new phone this year"
        result = check_positioning_hit(
            response=response,
            brand="Apple",
            positioning_keywords=["innovative", "premium"],
        )
        assert result is False

    def test_miss_when_no_brand(self):
        """Returns False when brand is not mentioned."""
        response = "The innovative product has premium quality"
        result = check_positioning_hit(
            response=response,
            brand="BrandXYZ",
            positioning_keywords=["innovative", "premium"],
        )
        assert result is False

    def test_hit_case_insensitive(self):
        """Brand and keyword matching is case-insensitive."""
        response = "APPLE is very INNOVATIVE in its approach"
        result = check_positioning_hit(
            response=response,
            brand="apple",
            positioning_keywords=["innovative"],
        )
        assert result is True

    def test_multiword_brand(self):
        """Multi-word brand names are detected."""
        response = "Open AI is the most innovative company in artificial intelligence"
        result = check_positioning_hit(
            response=response,
            brand="Open AI",
            positioning_keywords=["innovative"],
        )
        assert result is True

    def test_empty_response(self):
        """Empty response text returns False."""
        result = check_positioning_hit(
            response="",
            brand="Apple",
            positioning_keywords=["innovative"],
        )
        assert result is False

    def test_empty_keywords(self):
        """Empty keywords list returns False."""
        result = check_positioning_hit(
            response="Apple makes great products",
            brand="Apple",
            positioning_keywords=[],
        )
        assert result is False


# ---------------------------------------------------------------------------
# calculate_overall_metrics
# ---------------------------------------------------------------------------

class TestCalculateOverallMetrics:
    """Overall metrics calculation tests."""

    def test_all_high_scores(self):
        """High scores across all metrics produce high overall score."""
        result = calculate_overall_metrics(
            sov_score=90.0,
            accuracy_score=9,
            sentiment_score=0.8,
            citation_rate=85.0,
            positioning_hit=True,
        )
        assert result["overall_score"] > 80
        assert result["overall_grade"] in ("A+", "A", "B+")
        assert result["positioning_hit"] is True

    def test_all_low_scores(self):
        """Low scores produce low overall score."""
        result = calculate_overall_metrics(
            sov_score=5.0,
            accuracy_score=2,
            sentiment_score=-0.8,
            citation_rate=5.0,
            positioning_hit=False,
        )
        assert result["overall_score"] < 30
        assert result["overall_grade"] == "F"

    def test_mixed_scores(self):
        """Mixed scores produce a moderate overall score."""
        result = calculate_overall_metrics(
            sov_score=50.0,
            accuracy_score=5,
            sentiment_score=0.0,
            citation_rate=50.0,
            positioning_hit=False,
        )
        # sov: 50*0.25=12.5, accuracy: 50*0.35=17.5, sentiment: 50*0.20=10, citation: 50*0.20=10
        # total = 50.0
        assert result["overall_score"] == pytest.approx(50.0, abs=1.0)

    def test_weights_sum_to_one(self):
        """The internal weights should sum to 1.0 for proper averaging."""
        # This is a structural/design test
        weights = {"sov": 0.25, "accuracy": 0.35, "sentiment": 0.20, "citation": 0.20}
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_return_structure(self):
        """Return dict contains all expected keys."""
        result = calculate_overall_metrics(
            sov_score=50.0,
            accuracy_score=5,
            sentiment_score=0.0,
            citation_rate=50.0,
            positioning_hit=True,
        )
        expected_keys = {
            "sov_score", "accuracy_score", "sentiment_score",
            "citation_rate", "positioning_hit",
            "overall_score", "overall_grade",
        }
        assert set(result.keys()) == expected_keys


# ---------------------------------------------------------------------------
# get_grade
# ---------------------------------------------------------------------------

class TestGetGrade:
    """Grade boundary tests."""

    @pytest.mark.parametrize("score,expected_grade", [
        (95, "A+"),
        (90, "A+"),
        (89, "A"),
        (85, "A"),
        (84, "B+"),
        (80, "B+"),
        (79, "B"),
        (75, "B"),
        (74, "C+"),
        (70, "C+"),
        (69, "C"),
        (65, "C"),
        (64, "D"),
        (50, "D"),
        (49, "F"),
        (0, "F"),
    ])
    def test_grade_boundaries(self, score, expected_grade):
        """Each score maps to the correct letter grade."""
        assert get_grade(score) == expected_grade

    def test_grade_negative_score(self):
        """Negative score returns F."""
        assert get_grade(-10) == "F"

    def test_grade_above_100(self):
        """Score above 100 returns A+."""
        assert get_grade(110) == "A+"
