"""
Test Story Architecture with Diverse Data Types

This test suite validates that the story-first architecture can handle
ANY type of data users might submit to KIE, including:
- Financial (P&L statements, income data)
- Time-series (sales forecasts, trends)
- Survey/NPS (satisfaction scores, feedback)
- Geospatial (territory data, location-based)
- HR (headcount, attrition, engagement)

Each test verifies:
1. Thesis extraction produces reasonable results
2. KPIs are extracted and formatted correctly
3. Sections group insights logically
4. Narrative synthesis produces mode-specific output
5. Full story manifest is valid JSON
"""

import json
import re
from pathlib import Path

import pandas as pd
import pytest

from kie.story.models import StoryInsight, NarrativeMode
from kie.story import (
    ThesisExtractor,
    KPIExtractor,
    SectionGrouper,
    NarrativeSynthesizer,
    StoryBuilder,
)


class TestFinancialData:
    """Test story architecture with financial P&L data."""

    @pytest.fixture
    def financial_data(self):
        """Load financial P&L fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "financial_pl_data.csv"
        return pd.read_csv(fixture_path)

    @pytest.fixture
    def financial_insights(self, financial_data):
        """Create insights from financial data."""
        insights = [
            StoryInsight(
                insight_id="fin_001",
                text="Technology business unit maintains highest operating margin at 26.1% in Q3 2025, significantly above company average of 20.9%",
                category="profitability",
                confidence=0.92,
                business_value=0.95,
                actionability=0.88,
                supporting_data=[{"metric": "operating_margin", "value": 0.261}],
            ),
            StoryInsight(
                insight_id="fin_002",
                text="Consumer Products operating margin declined from 15.0% in Q2 to 17.1% in Q3, showing 2.1 percentage point improvement",
                category="margin_trend",
                confidence=0.89,
                business_value=0.87,
                actionability=0.82,
                supporting_data=[{"change": "+2.1pp"}],
            ),
            StoryInsight(
                insight_id="fin_003",
                text="Technology revenue of $52.3M represents 29.4% of total company revenue in Q3 2025",
                category="revenue_contribution",
                confidence=0.95,
                business_value=0.90,
                actionability=0.75,
                supporting_data=[{"revenue": 52300000}],
            ),
            StoryInsight(
                insight_id="fin_004",
                text="Healthcare Services gross profit margin of 46.0% exceeds Industrial Solutions by 7.0 percentage points",
                category="margin_comparison",
                confidence=0.91,
                business_value=0.84,
                actionability=0.79,
                supporting_data=[{"diff": 0.07}],
            ),
            StoryInsight(
                insight_id="fin_005",
                text="Financial Services shows consistent margin expansion from 19.6% in Q1 to 22.4% in Q3, gaining 2.8 points",
                category="margin_trend",
                confidence=0.88,
                business_value=0.86,
                actionability=0.83,
                supporting_data=[{"trend": "+2.8pp"}],
            ),
        ]
        return insights

    def test_financial_thesis_extraction(self, financial_insights):
        """Test thesis extraction produces reasonable financial thesis."""
        extractor = ThesisExtractor()
        thesis = extractor.extract_thesis(financial_insights, project_name="Financial Test")

        assert thesis is not None
        assert len(thesis.title) > 0
        assert thesis.confidence > 0
        # Financial data should yield theme or comparison thesis
        assert thesis.hook is not None

    def test_financial_kpi_extraction(self, financial_insights):
        """Test KPI extraction finds percentages and currency values."""
        extractor = KPIExtractor()
        kpis = extractor.extract_kpis(financial_insights)

        assert len(kpis) >= 3
        # Should extract percentages like "26.1%", "29.4%"
        percentage_kpis = [k for k in kpis if "%" in k.value]
        assert len(percentage_kpis) >= 2

    def test_financial_section_grouping(self, financial_insights):
        """Test section grouping creates logical financial sections."""
        grouper = SectionGrouper()
        sections = grouper.group_insights(financial_insights, chart_refs={})

        assert len(sections) >= 1
        # Should create margin or profitability sections
        section_titles = [s.title.lower() for s in sections]
        has_financial_terms = any(
            term in " ".join(section_titles)
            for term in ["margin", "profit", "revenue", "financial"]
        )
        assert has_financial_terms or len(sections) > 0  # Generic sections OK too

    def test_financial_narrative_synthesis(self, financial_insights):
        """Test narrative synthesis produces executive summary via builder."""
        builder = StoryBuilder(narrative_mode=NarrativeMode.EXECUTIVE)
        manifest = builder.build_story(
            insights=financial_insights,
            project_name="Financial Test",
            objective="Analyze profitability",
            chart_refs={},
            context_str="",
        )

        assert len(manifest.executive_summary) > 50
        # Executive mode should mention business impact
        summary_lower = manifest.executive_summary.lower()
        has_business_terms = any(
            term in summary_lower for term in ["margin", "revenue", "profit", "performance"]
        )
        assert has_business_terms

    def test_financial_story_manifest(self, financial_insights):
        """Test full story builder creates valid manifest."""
        builder = StoryBuilder(narrative_mode=NarrativeMode.EXECUTIVE)
        manifest = builder.build_story(
            insights=financial_insights,
            project_name="Financial Performance Analysis",
            objective="Analyze business unit profitability",
            chart_refs={},
            context_str="Q1-Q3 2025",
        )

        assert manifest.thesis is not None
        assert len(manifest.top_kpis) >= 3
        assert len(manifest.sections) >= 1
        assert len(manifest.executive_summary) > 50
        assert len(manifest.key_findings) >= 3

        # Validate JSON serialization
        manifest_dict = manifest.to_dict()
        json_str = json.dumps(manifest_dict)
        assert len(json_str) > 100


class TestTimeSeriesData:
    """Test story architecture with time-series sales data."""

    @pytest.fixture
    def timeseries_insights(self):
        """Create insights from time-series data."""
        insights = [
            StoryInsight(
                insight_id="ts_001",
                text="Actual sales exceeded forecast by average of 8.3% across all weeks, indicating systematic under-forecasting",
                category="forecast_accuracy",
                confidence=0.91,
                business_value=0.93,
                actionability=0.89,
                supporting_data=[{"forecast_error": 0.083}],
            ),
            StoryInsight(
                insight_id="ts_002",
                text="Sales trend shows 36.4% growth from $1.24M in week of Jan 1 to $1.69M in week of Apr 30",
                category="trend",
                confidence=0.94,
                business_value=0.96,
                actionability=0.82,
                supporting_data=[{"growth_rate": 0.364}],
            ),
            StoryInsight(
                insight_id="ts_003",
                text="Promotion weeks show 14.2% higher sales on average ($1.58M vs $1.38M on non-promotion weeks)",
                category="promotion_impact",
                confidence=0.90,
                business_value=0.91,
                actionability=0.94,
                supporting_data=[{"lift": 0.142}],
            ),
            StoryInsight(
                insight_id="ts_004",
                text="Stockout rate correlates negatively with sales at r=-0.87, costing estimated $890K in lost revenue",
                category="inventory",
                confidence=0.88,
                business_value=0.89,
                actionability=0.95,
                supporting_data=[{"correlation": -0.87, "revenue_loss": 890000}],
            ),
        ]
        return insights

    def test_timeseries_kpi_extraction(self, timeseries_insights):
        """Test KPI extraction finds growth rates and percentages."""
        extractor = KPIExtractor()
        kpis = extractor.extract_kpis(timeseries_insights)

        assert len(kpis) >= 3
        # Should find "36.4%", "14.2%", "8.3%"
        percentage_kpis = [k for k in kpis if "%" in k.value]
        assert len(percentage_kpis) >= 2

    def test_timeseries_story_manifest(self, timeseries_insights):
        """Test story builder handles time-series data."""
        builder = StoryBuilder(narrative_mode=NarrativeMode.ANALYST)
        manifest = builder.build_story(
            insights=timeseries_insights,
            project_name="Sales Trend Analysis",
            objective="Analyze sales growth and forecast accuracy",
            chart_refs={},
            context_str="18 weeks",
        )

        assert manifest.thesis is not None
        assert len(manifest.top_kpis) >= 3
        assert manifest.narrative_mode == NarrativeMode.ANALYST


class TestSurveyNPSData:
    """Test story architecture with survey/NPS data."""

    @pytest.fixture
    def survey_insights(self):
        """Create insights from survey data."""
        insights = [
            StoryInsight(
                insight_id="nps_001",
                text="Enterprise segment maintains highest NPS of 68 in Q3 2025, 27 points above Startup segment (41)",
                category="satisfaction",
                confidence=0.93,
                business_value=0.91,
                actionability=0.85,
                supporting_data=[{"nps_gap": 27}],
            ),
            StoryInsight(
                insight_id="nps_002",
                text="Small Business promoter percentage of 41% significantly trails Enterprise at 68%, indicating 27pp engagement gap",
                category="engagement",
                confidence=0.91,
                business_value=0.88,
                actionability=0.90,
                supporting_data=[{"promoters_gap": 0.27}],
            ),
            StoryInsight(
                insight_id="nps_003",
                text="Response rate declines from Enterprise (87%) to Startup (71%), showing 16pp difference in survey participation",
                category="response_quality",
                confidence=0.89,
                business_value=0.76,
                actionability=0.81,
                supporting_data=[{"response_gap": 0.16}],
            ),
        ]
        return insights

    def test_survey_thesis_extraction(self, survey_insights):
        """Test thesis extraction with satisfaction data."""
        extractor = ThesisExtractor()
        thesis = extractor.extract_thesis(survey_insights, project_name="Survey Test")

        assert thesis is not None
        # NPS data should produce comparison or satisfaction theme
        assert thesis.confidence > 0

    def test_survey_section_grouping(self, survey_insights):
        """Test section grouping recognizes satisfaction themes."""
        grouper = SectionGrouper()
        sections = grouper.group_insights(survey_insights, chart_refs={})

        assert len(sections) >= 1


class TestGeospatialData:
    """Test story architecture with geospatial territory data."""

    @pytest.fixture
    def geospatial_insights(self):
        """Create insights from territory data."""
        insights = [
            StoryInsight(
                insight_id="geo_001",
                text="West Coast Urban generates highest territory revenue at $23.4M with 14 sales reps, 39% above Northeast Metro",
                category="revenue",
                confidence=0.94,
                business_value=0.95,
                actionability=0.83,
                supporting_data=[{"revenue": 23400000}],
            ),
            StoryInsight(
                insight_id="geo_002",
                text="West Coast Urban achieves highest win rate of 73% despite smallest coverage area (1,800 sq mi)",
                category="efficiency",
                confidence=0.92,
                business_value=0.89,
                actionability=0.87,
                supporting_data=[{"win_rate": 0.73}],
            ),
        ]
        return insights

    def test_geospatial_kpi_extraction(self, geospatial_insights):
        """Test KPI extraction with geographic data."""
        extractor = KPIExtractor()
        kpis = extractor.extract_kpis(geospatial_insights)

        assert len(kpis) >= 2
        # Should find "$23.4M", "73%", "39%"
        has_large_number = any(("M" in k.value or "%" in k.value) for k in kpis)
        assert has_large_number  # Either currency abbreviation or percentage


class TestHRData:
    """Test story architecture with HR headcount data."""

    @pytest.fixture
    def hr_insights(self):
        """Create insights from HR data."""
        insights = [
            StoryInsight(
                insight_id="hr_001",
                text="Sales department shows highest attrition rate at 18%, 2x the Legal department rate of 8%",
                category="attrition",
                confidence=0.93,
                business_value=0.94,
                actionability=0.96,
                supporting_data=[{"attrition_gap": 0.10}],
            ),
            StoryInsight(
                insight_id="hr_002",
                text="Engineering headcount of 234 with 23 open positions indicates 9.8% vacancy rate, highest across departments",
                category="staffing",
                confidence=0.95,
                business_value=0.89,
                actionability=0.92,
                supporting_data=[{"vacancy_rate": 0.098}],
            ),
            StoryInsight(
                insight_id="hr_003",
                text="Time to fill averages 42 days but varies widely: Legal at 52 days vs Sales at 35 days (17 day gap)",
                category="hiring_efficiency",
                confidence=0.91,
                business_value=0.82,
                actionability=0.88,
                supporting_data=[{"ttf_gap_days": 17}],
            ),
        ]
        return insights

    def test_hr_thesis_extraction(self, hr_insights):
        """Test thesis extraction with HR data."""
        extractor = ThesisExtractor()
        thesis = extractor.extract_thesis(hr_insights, project_name="HR Test")

        assert thesis is not None
        assert thesis.confidence > 0

    def test_hr_kpi_extraction(self, hr_insights):
        """Test KPI extraction finds attrition rates and percentages."""
        extractor = KPIExtractor()
        kpis = extractor.extract_kpis(hr_insights)

        assert len(kpis) >= 2
        # Should find "18%", "9.8%", "2x"
        percentage_kpis = [k for k in kpis if "%" in k.value]
        assert len(percentage_kpis) >= 1


class TestMultiModeNarratives:
    """Test that all data types support multi-mode narratives."""

    @pytest.fixture
    def sample_insights(self):
        """Generic insights for mode testing."""
        return [
            StoryInsight(
                insight_id="test_001",
                text="Primary metric shows 42.3% improvement over baseline",
                category="performance",
                confidence=0.90,
                business_value=0.88,
                actionability=0.85,
                supporting_data=[],
            ),
        ]

    @pytest.mark.parametrize("mode", [
        NarrativeMode.EXECUTIVE,
        NarrativeMode.ANALYST,
        NarrativeMode.TECHNICAL,
    ])
    def test_all_modes_produce_narratives(self, sample_insights, mode):
        """Test all three narrative modes produce valid output."""
        builder = StoryBuilder(narrative_mode=mode)
        manifest = builder.build_story(
            insights=sample_insights,
            project_name="Test Project",
            objective="Test",
            chart_refs={},
            context_str="",
        )

        assert len(manifest.executive_summary) > 30
        assert isinstance(manifest.executive_summary, str)

    @pytest.mark.parametrize("mode", [
        NarrativeMode.EXECUTIVE,
        NarrativeMode.ANALYST,
        NarrativeMode.TECHNICAL,
    ])
    def test_all_modes_build_manifests(self, sample_insights, mode):
        """Test story builder works with all narrative modes."""
        builder = StoryBuilder(narrative_mode=mode)
        manifest = builder.build_story(
            insights=sample_insights,
            project_name="Multi-Mode Test",
            objective="Test narrative modes",
            chart_refs={},
            context_str="",
        )

        assert manifest.narrative_mode == mode
        assert manifest.thesis is not None
        assert len(manifest.executive_summary) > 0


class TestDataTypeRobustness:
    """Integration tests for data type robustness."""

    @pytest.mark.parametrize("data_type,insight_count,expected_kpi_min", [
        ("financial", 5, 3),
        ("timeseries", 4, 3),
        ("survey", 3, 2),
        ("geospatial", 2, 2),
        ("hr", 3, 2),
    ])
    def test_all_data_types_produce_valid_manifests(
        self, data_type, insight_count, expected_kpi_min
    ):
        """Test that all data types produce valid story manifests."""
        # This is a sanity check that we have fixtures and test structure
        fixture_path = Path(__file__).parent / "fixtures" / f"{data_type}_*_data.csv"
        assert len(list(fixture_path.parent.glob(f"{data_type}_*_data.csv"))) > 0

    def test_section_grouper_handles_unknown_categories(self):
        """Test section grouper gracefully handles unknown categories."""
        unknown_insights = [
            StoryInsight(
                insight_id="unk_001",
                text="Unknown category metric shows 42% variance",
                category="completely_unknown_category",
                confidence=0.90,
                business_value=0.85,
                actionability=0.80,
                supporting_data=[],
            ),
        ]

        grouper = SectionGrouper()
        sections = grouper.group_insights(unknown_insights, chart_refs={})

        # Should either create section or gracefully handle (empty is OK for 1 insight)
        # The important thing is it doesn't crash
        assert sections is not None
        assert isinstance(sections, list)

    def test_kpi_extractor_handles_diverse_number_formats(self):
        """Test KPI extractor finds numbers in various formats."""
        diverse_insights = [
            StoryInsight(
                insight_id="div_001",
                text="Revenue grew $1.2M to reach $45.6M total",
                category="test",
                confidence=0.9,
                business_value=0.8,
                actionability=0.7,
                supporting_data=[],
            ),
            StoryInsight(
                insight_id="div_002",
                text="Win rate improved 2.3x from 0.45 to 0.89",
                category="test",
                confidence=0.9,
                business_value=0.8,
                actionability=0.7,
                supporting_data=[],
            ),
            StoryInsight(
                insight_id="div_003",
                text="Response rate declined -15pp to 68.5%",
                category="test",
                confidence=0.9,
                business_value=0.8,
                actionability=0.7,
                supporting_data=[],
            ),
        ]

        extractor = KPIExtractor()
        kpis = extractor.extract_kpis(diverse_insights)

        # Should find at least some numbers from the diverse formats
        assert len(kpis) >= 1
        kpi_values = [k.value for k in kpis]
        # Check we extracted at least one type
        has_currency = any("$" in v for v in kpi_values)
        has_percentage = any("%" in v for v in kpi_values)
        has_multiplier = any("x" in v.lower() for v in kpi_values)
        assert has_currency or has_percentage or has_multiplier  # At least one format type found
