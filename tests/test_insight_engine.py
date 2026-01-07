"""
Tests for KIE InsightEngine

Tests insight extraction, statistical analysis, and narrative arc generation.
"""

import pytest
import pandas as pd
import numpy as np

from kie.insights.engine import InsightEngine
from kie.insights.statistical import StatisticalAnalyzer
from kie.insights.schema import (
    InsightType,
    InsightSeverity,
    InsightCategory,
    Evidence,
)


@pytest.fixture
def engine():
    """Create a fresh InsightEngine for each test."""
    return InsightEngine()


@pytest.fixture
def sample_comparison_data():
    """Create sample data for comparison insights."""
    return {
        "North": 1000000.0,
        "South": 800000.0,
        "East": 600000.0,
        "West": 400000.0,
    }


@pytest.fixture
def sample_trend_data():
    """Create sample data for trend insights."""
    return {
        "periods": ["Q1", "Q2", "Q3", "Q4"],
        "values": [100.0, 120.0, 140.0, 160.0],
    }


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for auto-extraction."""
    return pd.DataFrame({
        "region": ["North", "South", "East", "West", "North", "South"],
        "revenue": [1000, 800, 600, 400, 1100, 850],
        "quarter": ["Q1", "Q1", "Q1", "Q1", "Q2", "Q2"],
    })


class TestBasicInsightCreation:
    """Test basic insight creation."""

    def test_create_basic_insight(self, engine):
        """Test creating a basic insight."""
        insight = engine.create_insight(
            headline="Revenue is Growing",
            supporting_text="Revenue increased by 20% year over year.",
            insight_type=InsightType.TREND,
            severity=InsightSeverity.KEY,
            category=InsightCategory.FINDING,
        )

        assert insight.headline == "Revenue is Growing"
        assert "20%" in insight.supporting_text
        assert insight.insight_type == InsightType.TREND
        assert insight.severity == InsightSeverity.KEY
        assert insight.category == InsightCategory.FINDING
        assert insight.id.startswith("insight_")

    def test_insight_id_generation(self, engine):
        """Test that insight IDs are unique and sequential."""
        insight1 = engine.create_insight(
            headline="First Insight",
            supporting_text="Supporting text",
        )
        insight2 = engine.create_insight(
            headline="Second Insight",
            supporting_text="Supporting text",
        )

        assert insight1.id != insight2.id
        assert insight1.id == "insight_001"
        assert insight2.id == "insight_002"

    def test_insight_with_evidence(self, engine):
        """Test creating insight with evidence."""
        evidence = [
            Evidence(
                evidence_type="metric",
                reference="revenue_total",
                value=1000000,
                label="Total Revenue",
            ),
        ]

        insight = engine.create_insight(
            headline="Revenue Milestone Reached",
            supporting_text="Revenue exceeded $1M for the first time.",
            evidence=evidence,
        )

        assert len(insight.evidence) == 1
        assert insight.evidence[0].evidence_type == "metric"
        assert insight.evidence[0].value == 1000000

    def test_insight_with_tags(self, engine):
        """Test creating insight with tags."""
        insight = engine.create_insight(
            headline="Test Insight",
            supporting_text="Text",
            tags=["revenue", "growth", "key-metric"],
        )

        assert len(insight.tags) == 3
        assert "revenue" in insight.tags
        assert "growth" in insight.tags

    def test_insight_confidence_score(self, engine):
        """Test insight confidence score."""
        insight = engine.create_insight(
            headline="Test",
            supporting_text="Text",
            confidence=0.95,
        )

        assert insight.confidence == 0.95


class TestComparisonInsights:
    """Test comparison insight generation."""

    def test_comparison_insight_basic(self, engine, sample_comparison_data):
        """Test basic comparison insight."""
        insight = engine.create_comparison_insight(
            metric_name="Revenue",
            values=sample_comparison_data,
        )

        assert "North" in insight.headline
        assert "Leads" in insight.headline
        assert insight.insight_type == InsightType.COMPARISON
        assert insight.category == InsightCategory.FINDING
        assert len(insight.evidence) >= 2

    def test_comparison_leader_calculation(self, engine, sample_comparison_data):
        """Test that comparison correctly identifies leader."""
        insight = engine.create_comparison_insight(
            metric_name="Revenue",
            values=sample_comparison_data,
        )

        # North should be leader with 1M out of 2.8M total = ~35.7%
        assert "North" in insight.headline
        assert "35%" in insight.headline or "36%" in insight.headline

    def test_comparison_with_chart(self, engine, sample_comparison_data):
        """Test comparison insight with chart path."""
        insight = engine.create_comparison_insight(
            metric_name="Revenue",
            values=sample_comparison_data,
            chart_path="/charts/revenue_comparison.json",
        )

        # Should have chart evidence first
        assert insight.evidence[0].evidence_type == "chart"
        assert insight.evidence[0].reference == "/charts/revenue_comparison.json"
        assert insight.suggested_slide_type == "chart"

    def test_comparison_empty_values(self, engine):
        """Test comparison with empty values raises error."""
        with pytest.raises(ValueError, match="Values dict cannot be empty"):
            engine.create_comparison_insight(
                metric_name="Revenue",
                values={},
            )

    def test_comparison_single_value(self, engine):
        """Test comparison with single value."""
        insight = engine.create_comparison_insight(
            metric_name="Revenue",
            values={"North": 1000},
        )

        assert "North" in insight.headline
        assert "100%" in insight.supporting_text

    def test_comparison_severity_threshold(self, engine):
        """Test that high-share leaders get KEY severity."""
        # Leader with >40% share should be KEY
        insight_high_share = engine.create_comparison_insight(
            metric_name="Revenue",
            values={"Leader": 500, "Other": 100},
        )
        assert insight_high_share.severity == InsightSeverity.KEY

        # Leader with <40% share should be SUPPORTING
        insight_low_share = engine.create_comparison_insight(
            metric_name="Revenue",
            values={"A": 300, "B": 250, "C": 250},
        )
        assert insight_low_share.severity == InsightSeverity.SUPPORTING


class TestTrendInsights:
    """Test trend insight generation."""

    def test_trend_insight_basic(self, engine, sample_trend_data):
        """Test basic trend insight."""
        insight = engine.create_trend_insight(
            metric_name="Revenue",
            periods=sample_trend_data["periods"],
            values=sample_trend_data["values"],
        )

        assert insight.insight_type == InsightType.TREND
        assert insight.category == InsightCategory.FINDING
        assert "Revenue" in insight.headline

    def test_trend_growth_detection(self, engine):
        """Test trend growth detection."""
        insight = engine.create_trend_insight(
            metric_name="Revenue",
            periods=["Q1", "Q2", "Q3"],
            values=[100, 110, 120],
        )

        # 20% growth should be detected
        assert "Grow" in insight.headline or "increase" in insight.supporting_text.lower()

    def test_trend_decline_detection(self, engine):
        """Test trend decline detection."""
        insight = engine.create_trend_insight(
            metric_name="Revenue",
            periods=["Q1", "Q2", "Q3"],
            values=[120, 110, 100],
        )

        # Decline should be detected
        assert "Decline" in insight.headline

    def test_trend_stable_detection(self, engine):
        """Test stable trend detection."""
        insight = engine.create_trend_insight(
            metric_name="Revenue",
            periods=["Q1", "Q2", "Q3"],
            values=[100, 102, 101],
        )

        # Small changes should be "stable"
        assert "Stable" in insight.headline or "stable" in insight.headline.lower()

    def test_trend_with_chart(self, engine, sample_trend_data):
        """Test trend insight with chart path."""
        insight = engine.create_trend_insight(
            metric_name="Revenue",
            periods=sample_trend_data["periods"],
            values=sample_trend_data["values"],
            chart_path="/charts/revenue_trend.json",
        )

        assert insight.evidence[0].evidence_type == "chart"
        assert insight.suggested_slide_type == "chart"

    def test_trend_minimum_periods(self, engine):
        """Test that trend requires at least 2 periods."""
        with pytest.raises(ValueError, match="at least 2 periods"):
            engine.create_trend_insight(
                metric_name="Revenue",
                periods=["Q1"],
                values=[100],
            )

    def test_trend_mismatched_periods(self, engine):
        """Test that trend requires matching periods and values."""
        with pytest.raises(ValueError, match="at least 2 periods"):
            engine.create_trend_insight(
                metric_name="Revenue",
                periods=["Q1", "Q2"],
                values=[100],
            )

    def test_trend_confidence_from_r_squared(self, engine):
        """Test that confidence is derived from R-squared."""
        # Perfect linear trend should have high confidence
        insight = engine.create_trend_insight(
            metric_name="Revenue",
            periods=["Q1", "Q2", "Q3", "Q4"],
            values=[100, 200, 300, 400],
        )

        # Confidence should be high (close to 0.95)
        assert insight.confidence >= 0.9

    def test_trend_severity_threshold(self, engine):
        """Test that large changes get KEY severity."""
        # >15% change should be KEY
        insight_large = engine.create_trend_insight(
            metric_name="Revenue",
            periods=["Q1", "Q2"],
            values=[100, 120],
        )
        assert insight_large.severity == InsightSeverity.KEY

        # <15% change should be SUPPORTING
        insight_small = engine.create_trend_insight(
            metric_name="Revenue",
            periods=["Q1", "Q2"],
            values=[100, 110],
        )
        assert insight_small.severity == InsightSeverity.SUPPORTING


class TestOutlierInsights:
    """Test outlier insight generation."""

    def test_outlier_detection_basic(self, engine):
        """Test basic outlier detection."""
        data = pd.Series([10, 12, 11, 13, 10, 12, 100])  # 100 is clear outlier

        insight = engine.create_outlier_insight(
            metric_name="Sales",
            series=data,
        )

        assert insight is not None
        assert insight.insight_type == InsightType.OUTLIER
        assert "Outlier" in insight.headline

    def test_outlier_with_labels(self, engine):
        """Test outlier detection with labels."""
        data = pd.Series([10, 12, 11, 100])
        labels = pd.Series(["Store A", "Store B", "Store C", "Store D"])

        insight = engine.create_outlier_insight(
            metric_name="Sales",
            series=data,
            labels=labels,
        )

        # Should mention Store D in supporting text
        assert "Store D" in insight.supporting_text

    def test_outlier_none_when_no_outliers(self, engine):
        """Test that no insight is returned when no outliers."""
        data = pd.Series([10, 12, 11, 13, 10, 12, 11])  # No outliers

        insight = engine.create_outlier_insight(
            metric_name="Sales",
            series=data,
        )

        assert insight is None

    def test_outlier_percentage_calculation(self, engine):
        """Test outlier percentage calculation."""
        data = pd.Series([10] * 9 + [100])  # 1 outlier out of 10 = 10%

        insight = engine.create_outlier_insight(
            metric_name="Sales",
            series=data,
        )

        assert insight is not None
        assert "10" in insight.headline or "10.0" in insight.headline

    def test_outlier_severity_threshold(self, engine):
        """Test that high outlier percentage gets KEY severity."""
        # >5% outliers should be KEY
        data = pd.Series([10] * 18 + [100, 200])  # 2/20 = 10%
        insight = engine.create_outlier_insight("Sales", data)
        assert insight.severity == InsightSeverity.KEY

        # <5% outliers should be SUPPORTING
        data = pd.Series([10] * 98 + [100, 200])  # 2/100 = 2%
        insight = engine.create_outlier_insight("Sales", data)
        assert insight.severity == InsightSeverity.SUPPORTING


class TestConcentrationInsights:
    """Test concentration insight generation."""

    def test_concentration_high_risk(self, engine):
        """Test high concentration risk detection."""
        insight = engine.create_concentration_insight(
            dimension="Revenue by Product",
            top_item="Product A",
            top_share=80.0,
            total_items=10,
        )

        assert "High" in insight.headline
        assert insight.severity == InsightSeverity.KEY
        assert insight.category == InsightCategory.IMPLICATION

    def test_concentration_moderate_risk(self, engine):
        """Test moderate concentration risk detection."""
        insight = engine.create_concentration_insight(
            dimension="Revenue by Customer",
            top_item="Customer X",
            top_share=60.0,
            total_items=20,
        )

        assert "Moderate" in insight.headline
        assert insight.severity == InsightSeverity.KEY

    def test_concentration_low_risk(self, engine):
        """Test low concentration risk detection."""
        insight = engine.create_concentration_insight(
            dimension="Revenue by Region",
            top_item="North",
            top_share=30.0,
            total_items=5,
        )

        assert "Low" in insight.headline
        assert insight.severity == InsightSeverity.SUPPORTING

    def test_concentration_with_chart(self, engine):
        """Test concentration insight with chart."""
        insight = engine.create_concentration_insight(
            dimension="Revenue",
            top_item="Leader",
            top_share=50.0,
            total_items=10,
            chart_path="/charts/concentration.json",
        )

        assert insight.evidence[0].evidence_type == "chart"

    def test_concentration_diversification_recommendation(self, engine):
        """Test that high concentration suggests diversification."""
        insight = engine.create_concentration_insight(
            dimension="Revenue",
            top_item="Leader",
            top_share=75.0,
            total_items=10,
        )

        assert "divers" in insight.supporting_text.lower()


class TestCorrelationInsights:
    """Test correlation insight generation."""

    def test_correlation_positive(self, engine):
        """Test positive correlation detection."""
        var1 = pd.Series([1, 2, 3, 4, 5])
        var2 = pd.Series([2, 4, 6, 8, 10])

        insight = engine.create_correlation_insight(
            var1_name="Marketing Spend",
            var2_name="Revenue",
            var1=var1,
            var2=var2,
        )

        assert insight is not None
        assert "Correlation" in insight.headline
        assert "positive" in insight.supporting_text.lower()

    def test_correlation_negative(self, engine):
        """Test negative correlation detection."""
        var1 = pd.Series([1, 2, 3, 4, 5])
        var2 = pd.Series([10, 8, 6, 4, 2])

        insight = engine.create_correlation_insight(
            var1_name="Price",
            var2_name="Demand",
            var1=var1,
            var2=var2,
        )

        assert insight is not None
        assert "negative" in insight.supporting_text.lower()

    def test_correlation_none_when_negligible(self, engine):
        """Test that negligible correlation returns None."""
        var1 = pd.Series([1, 2, 3, 4, 5])
        var2 = pd.Series([5, 2, 8, 1, 6])  # Random, no correlation

        insight = engine.create_correlation_insight(
            var1_name="X",
            var2_name="Y",
            var1=var1,
            var2=var2,
        )

        assert insight is None

    def test_correlation_strength_classification(self, engine):
        """Test correlation strength classification."""
        # Strong correlation
        var1 = pd.Series(range(100))
        var2 = pd.Series([x * 2 + np.random.normal(0, 1) for x in range(100)])

        insight = engine.create_correlation_insight(
            var1_name="X",
            var2_name="Y",
            var1=var1,
            var2=var2,
        )

        assert insight is not None
        assert insight.insight_type == InsightType.CORRELATION


class TestRecommendationInsights:
    """Test recommendation insight generation."""

    def test_recommendation_basic(self, engine):
        """Test basic recommendation creation."""
        insight = engine.create_recommendation(
            action="Diversify Product Portfolio",
            rationale="High concentration in single product creates risk.",
            expected_impact="Reduced dependency on single revenue source.",
        )

        assert insight.category == InsightCategory.RECOMMENDATION
        assert "Diversify" in insight.headline

    def test_recommendation_with_supporting_insights(self, engine):
        """Test recommendation with supporting insights."""
        insight = engine.create_recommendation(
            action="Increase Marketing Budget",
            rationale="Strong correlation between marketing and revenue.",
            expected_impact="Projected 20% revenue increase.",
            supporting_insights=["insight_001", "insight_002"],
        )

        assert len(insight.evidence) == 1
        assert insight.evidence[0].evidence_type == "insight_reference"

    def test_recommendation_priority_severity(self, engine):
        """Test that priority affects severity."""
        high_priority = engine.create_recommendation(
            action="Act Now",
            rationale="Urgent",
            expected_impact="High",
            priority="high",
        )
        assert high_priority.severity == InsightSeverity.KEY

        low_priority = engine.create_recommendation(
            action="Consider Later",
            rationale="Not urgent",
            expected_impact="Low",
            priority="low",
        )
        assert low_priority.severity == InsightSeverity.SUPPORTING


class TestAutoExtraction:
    """Test automatic insight extraction."""

    def test_auto_extract_basic(self, engine):
        """Test basic auto-extraction with outliers."""
        # Create data with clear outlier to trigger insight
        df = pd.DataFrame({
            "revenue": [100, 110, 105, 108, 112, 1000],  # 1000 is clear outlier
        })

        insights = engine.auto_extract(
            df=df,
            value_column="revenue",
        )

        # Should find outlier insight
        assert len(insights) > 0
        assert any(i.insight_type == InsightType.OUTLIER for i in insights)

    def test_auto_extract_with_groups(self, engine, sample_dataframe):
        """Test auto-extraction with grouping."""
        insights = engine.auto_extract(
            df=sample_dataframe,
            value_column="revenue",
            group_column="region",
        )

        # Should include comparison insights
        comparison_insights = [i for i in insights if i.insight_type == InsightType.COMPARISON]
        assert len(comparison_insights) > 0

    def test_auto_extract_with_time(self, engine):
        """Test auto-extraction with time series."""
        df = pd.DataFrame({
            "month": ["Jan", "Feb", "Mar", "Apr"],
            "revenue": [100, 120, 140, 160],
        })

        insights = engine.auto_extract(
            df=df,
            value_column="revenue",
            time_column="month",
        )

        # Should include trend insights
        trend_insights = [i for i in insights if i.insight_type == InsightType.TREND]
        assert len(trend_insights) > 0

    def test_auto_extract_concentration_detection(self, engine):
        """Test that auto-extract detects concentration."""
        df = pd.DataFrame({
            "product": ["A", "B", "C", "D"],
            "revenue": [1000, 100, 50, 50],  # A dominates
        })

        insights = engine.auto_extract(
            df=df,
            value_column="revenue",
            group_column="product",
        )

        concentration_insights = [i for i in insights if i.insight_type == InsightType.CONCENTRATION]
        assert len(concentration_insights) > 0


class TestCatalogBuilding:
    """Test insight catalog building."""

    def test_build_catalog_basic(self, engine):
        """Test basic catalog building."""
        insights = [
            engine.create_insight(
                headline="Finding 1",
                supporting_text="Text",
                category=InsightCategory.FINDING,
                severity=InsightSeverity.KEY,
            ),
            engine.create_insight(
                headline="Finding 2",
                supporting_text="Text",
                category=InsightCategory.FINDING,
                severity=InsightSeverity.SUPPORTING,
            ),
        ]

        catalog = engine.build_catalog(
            insights=insights,
            business_question="What drives revenue?",
        )

        assert catalog.business_question == "What drives revenue?"
        assert len(catalog.insights) == 2

    def test_catalog_narrative_arc(self, engine):
        """Test catalog narrative arc structure."""
        insights = [
            engine.create_insight(
                headline="Key Finding",
                supporting_text="Text",
                category=InsightCategory.FINDING,
                severity=InsightSeverity.KEY,
            ),
            engine.create_insight(
                headline="Implication",
                supporting_text="Text",
                category=InsightCategory.IMPLICATION,
            ),
            engine.create_insight(
                headline="Recommendation",
                supporting_text="Text",
                category=InsightCategory.RECOMMENDATION,
            ),
        ]

        catalog = engine.build_catalog(insights, "Question?")
        arc = catalog.narrative_arc

        assert "key_findings" in arc
        assert "implications" in arc
        assert "recommendations" in arc
        assert len(arc["key_findings"]) == 1
        assert len(arc["implications"]) == 1
        assert len(arc["recommendations"]) == 1

    def test_catalog_with_data_summary(self, engine):
        """Test catalog with data summary."""
        insights = [
            engine.create_insight(
                headline="Test",
                supporting_text="Text",
            ),
        ]

        data_summary = {
            "rows": 100,
            "columns": 5,
            "date_range": "2024-Q1",
        }

        catalog = engine.build_catalog(
            insights=insights,
            business_question="Test?",
            data_summary=data_summary,
        )

        assert catalog.data_summary["rows"] == 100
        assert catalog.data_summary["date_range"] == "2024-Q1"


class TestInsightRanking:
    """Test insight ranking."""

    def test_rank_by_severity(self, engine):
        """Test that KEY insights rank higher than SUPPORTING."""
        insights = [
            engine.create_insight(
                headline="Supporting",
                supporting_text="Text",
                severity=InsightSeverity.SUPPORTING,
            ),
            engine.create_insight(
                headline="Key",
                supporting_text="Text",
                severity=InsightSeverity.KEY,
            ),
        ]

        ranked = engine.rank_insights(insights)

        assert ranked[0].headline == "Key"
        assert ranked[1].headline == "Supporting"

    def test_rank_by_confidence(self, engine):
        """Test that confidence affects ranking."""
        insights = [
            engine.create_insight(
                headline="Low Confidence",
                supporting_text="Text",
                severity=InsightSeverity.KEY,
                confidence=0.5,
            ),
            engine.create_insight(
                headline="High Confidence",
                supporting_text="Text",
                severity=InsightSeverity.KEY,
                confidence=0.95,
            ),
        ]

        ranked = engine.rank_insights(insights)

        assert ranked[0].headline == "High Confidence"

    def test_rank_with_statistical_significance(self, engine):
        """Test that statistical significance boosts ranking."""
        insights = [
            engine.create_insight(
                headline="Not Significant",
                supporting_text="Text",
                severity=InsightSeverity.KEY,
                statistical_significance=0.1,  # Not significant
            ),
            engine.create_insight(
                headline="Significant",
                supporting_text="Text",
                severity=InsightSeverity.KEY,
                statistical_significance=0.01,  # Significant
            ),
        ]

        ranked = engine.rank_insights(insights)

        assert ranked[0].headline == "Significant"


class TestSlideSequenceGeneration:
    """Test conversion to slide sequence."""

    def test_to_slide_sequence_basic(self, engine):
        """Test basic slide sequence generation."""
        insights = [
            engine.create_insight(
                headline="Finding",
                supporting_text="Text",
                category=InsightCategory.FINDING,
                severity=InsightSeverity.KEY,
            ),
        ]

        catalog = engine.build_catalog(insights, "Question?")
        slides = engine.to_slide_sequence(catalog)

        assert len(slides) >= 1  # At least section slide

    def test_slide_sequence_with_chart(self, engine):
        """Test slide sequence includes chart slides."""
        insight = engine.create_comparison_insight(
            metric_name="Revenue",
            values={"A": 100, "B": 80},
            chart_path="/charts/revenue.json",
        )

        catalog = engine.build_catalog([insight], "Question?")
        slides = engine.to_slide_sequence(catalog)

        # Find the content slide (not section)
        content_slides = [s for s in slides if s.get("type") == "chart"]
        assert len(content_slides) > 0
        assert content_slides[0]["chart_path"] == "/charts/revenue.json"

    def test_slide_sequence_sections(self, engine):
        """Test that slide sequence includes section dividers."""
        insights = [
            engine.create_insight(
                headline="Finding",
                supporting_text="Text",
                category=InsightCategory.FINDING,
                severity=InsightSeverity.KEY,
            ),
            engine.create_insight(
                headline="Recommendation",
                supporting_text="Text",
                category=InsightCategory.RECOMMENDATION,
            ),
        ]

        catalog = engine.build_catalog(insights, "Question?")
        slides = engine.to_slide_sequence(catalog)

        section_slides = [s for s in slides if s.get("type") == "section"]
        assert len(section_slides) >= 2  # At least 2 sections


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_insight_list_catalog(self, engine):
        """Test catalog with no insights."""
        catalog = engine.build_catalog([], "Question?")

        assert len(catalog.insights) == 0
        assert catalog.business_question == "Question?"

    def test_insight_with_no_evidence(self, engine):
        """Test insight creation without evidence."""
        insight = engine.create_insight(
            headline="Test",
            supporting_text="Text",
        )

        assert len(insight.evidence) == 0

    def test_custom_statistical_analyzer(self):
        """Test using custom StatisticalAnalyzer."""
        analyzer = StatisticalAnalyzer(significance_level=0.01)
        engine = InsightEngine(statistical_analyzer=analyzer)

        assert engine.stats.significance_level == 0.01

    def test_insight_with_zero_confidence(self, engine):
        """Test insight with zero confidence."""
        insight = engine.create_insight(
            headline="Uncertain",
            supporting_text="Text",
            confidence=0.0,
        )

        assert insight.confidence == 0.0
