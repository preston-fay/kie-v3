"""
Test Story-First Pipeline End-to-End

Validates that the new story architecture transforms insights into
consultant-grade story manifests with thesis, KPIs, sections, and narratives.
"""

import json
from pathlib import Path

import pytest

from kie.story.models import StoryInsight as Insight
from kie.story import (
    StoryBuilder,
    NarrativeMode,
    KPIType,
)


@pytest.fixture
def sample_insights():
    """Create sample insights for testing."""
    return [
        Insight(
            insight_id="ins_001",
            text="68.7% of growers report being very or extremely satisfied with their current agricultural retailer.",
            category="satisfaction",
            confidence=0.92,
            business_value=0.88,
            actionability=0.75,
            supporting_data={"sample_size": 511, "percentage": 68.7}
        ),
        Insight(
            insight_id="ins_002",
            text="82% of growers indicate high price sensitivity, with over 60% stating they would switch retailers for a 5-10% price difference.",
            category="price",
            confidence=0.89,
            business_value=0.95,
            actionability=0.92,
            supporting_data={"price_sensitivity": 82, "switching_intent": 60}
        ),
        Insight(
            insight_id="ins_003",
            text="Trust in the retailer's expertise ranks as the top factor in satisfaction, cited by 78% of respondents.",
            category="trust",
            confidence=0.87,
            business_value=0.80,
            actionability=0.70,
            supporting_data={"trust_percentage": 78}
        ),
        Insight(
            insight_id="ins_004",
            text="Growers aged 45-65 demonstrate 15% higher loyalty scores compared to younger demographics.",
            category="demographics",
            confidence=0.85,
            business_value=0.65,
            actionability=0.55,
            supporting_data={"loyalty_delta": 15}
        ),
        Insight(
            insight_id="ins_005",
            text="Despite high satisfaction, 45% of growers have actively explored alternative retailers in the past 12 months.",
            category="loyalty",
            confidence=0.90,
            business_value=0.92,
            actionability=0.88,
            supporting_data={"exploration_rate": 45}
        ),
    ]


class TestThesisExtraction:
    """Test thesis extraction from insights."""

    def test_paradox_detection(self, sample_insights):
        """Should detect satisfaction-vulnerability paradox."""
        from kie.story.thesis_extractor import ThesisExtractor

        extractor = ThesisExtractor()
        thesis = extractor.extract_thesis(
            insights=sample_insights,
            project_name="Agricultural Retail Analysis",
            objective="Analyze customer satisfaction and retention drivers"
        )

        # Should detect paradox pattern
        assert thesis is not None
        assert "paradox" in thesis.title.lower() or "satisfaction" in thesis.title.lower()
        assert thesis.confidence > 0.7
        assert len(thesis.supporting_insight_ids) >= 2

        # Should have meaningful content
        assert len(thesis.hook) > 10
        assert len(thesis.summary) > 50
        assert len(thesis.implication) > 50


class TestKPIExtraction:
    """Test KPI extraction and ranking."""

    def test_kpi_extraction(self, sample_insights):
        """Should extract and rank KPIs from insights."""
        from kie.story.kpi_extractor import KPIExtractor

        extractor = KPIExtractor()
        kpis = extractor.extract_kpis(
            insights=sample_insights,
            max_kpis=5,
            context_str="n=511 growers"
        )

        # Should extract multiple KPIs
        assert len(kpis) >= 3

        # Should have properly formatted values
        assert any("%" in kpi.value for kpi in kpis)

        # Should have rankings
        assert kpis[0].rank == 1
        assert kpis[1].rank == 2

        # Should have labels
        for kpi in kpis:
            assert len(kpi.label) > 5
            assert kpi.kpi_type in [KPIType.HEADLINE, KPIType.SUPPORTING, KPIType.DELTA, KPIType.COUNT]

    def test_kpi_ranking_logic(self, sample_insights):
        """Should rank high-value insights higher."""
        from kie.story.kpi_extractor import KPIExtractor

        extractor = KPIExtractor()
        kpis = extractor.extract_kpis(
            insights=sample_insights,
            max_kpis=10
        )

        # Top KPI should be from high business_value insight
        # (82% price sensitivity has business_value=0.95)
        top_kpi = kpis[0]
        assert top_kpi.insight_id in ["ins_002", "ins_001", "ins_005"]  # High-value insights


class TestSectionGrouping:
    """Test insight grouping into sections."""

    def test_section_creation(self, sample_insights):
        """Should group insights into narrative sections."""
        from kie.story.section_grouper import SectionGrouper

        grouper = SectionGrouper()
        sections = grouper.group_insights(
            insights=sample_insights,
            chart_refs={},
            min_section_size=2
        )

        # Should create sections
        assert len(sections) >= 1

        # Sections should have required fields
        for section in sections:
            assert section.section_id
            assert section.title
            assert len(section.insight_ids) >= 2
            assert section.thesis
            assert section.order >= 0

    def test_section_ordering(self, sample_insights):
        """Should order sections by importance."""
        from kie.story.section_grouper import SectionGrouper

        grouper = SectionGrouper()
        sections = grouper.group_insights(
            insights=sample_insights,
            chart_refs={},
            min_section_size=1
        )

        # Should be ordered (order values should be sequential)
        orders = [s.order for s in sections]
        assert orders == sorted(orders)

        # Most important section should be first
        assert sections[0].order == 0


class TestNarrativeSynthesis:
    """Test narrative generation in multiple modes."""

    def test_executive_mode(self, sample_insights):
        """Should generate executive-focused narrative."""
        from kie.story.narrative_synthesizer import NarrativeSynthesizer
        from kie.story.thesis_extractor import ThesisExtractor

        thesis_extractor = ThesisExtractor()
        thesis = thesis_extractor.extract_thesis(
            insights=sample_insights,
            project_name="Test Project"
        )

        synthesizer = NarrativeSynthesizer(mode=NarrativeMode.EXECUTIVE)
        summary = synthesizer.synthesize_executive_summary(
            thesis=thesis,
            top_kpis=[],
            sections=[],
            insights=sample_insights
        )

        # Should focus on business implications
        assert len(summary) > 100
        assert any(word in summary.lower() for word in ["business", "impact", "action", "recommend", "strategic"])

    def test_analyst_mode(self, sample_insights):
        """Should generate analyst-focused narrative."""
        from kie.story.narrative_synthesizer import NarrativeSynthesizer
        from kie.story.thesis_extractor import ThesisExtractor

        thesis_extractor = ThesisExtractor()
        thesis = thesis_extractor.extract_thesis(
            insights=sample_insights,
            project_name="Test Project"
        )

        synthesizer = NarrativeSynthesizer(mode=NarrativeMode.ANALYST)
        summary = synthesizer.synthesize_executive_summary(
            thesis=thesis,
            top_kpis=[],
            sections=[],
            insights=sample_insights
        )

        # Should focus on patterns and analysis
        assert len(summary) > 100
        assert any(word in summary.lower() for word in ["pattern", "analysis", "finding", "correlation"])

    def test_technical_mode(self, sample_insights):
        """Should generate technical-focused narrative."""
        from kie.story.narrative_synthesizer import NarrativeSynthesizer
        from kie.story.thesis_extractor import ThesisExtractor

        thesis_extractor = ThesisExtractor()
        thesis = thesis_extractor.extract_thesis(
            insights=sample_insights,
            project_name="Test Project"
        )

        synthesizer = NarrativeSynthesizer(mode=NarrativeMode.TECHNICAL)
        summary = synthesizer.synthesize_executive_summary(
            thesis=thesis,
            top_kpis=[],
            sections=[],
            insights=sample_insights
        )

        # Should focus on methodology and confidence
        assert len(summary) > 100
        assert any(word in summary.lower() for word in ["confidence", "methodology", "statistical", "rigor"])


class TestStoryBuilder:
    """Test end-to-end story building."""

    def test_story_manifest_creation(self, sample_insights):
        """Should build complete story manifest."""
        builder = StoryBuilder(narrative_mode=NarrativeMode.EXECUTIVE)

        manifest = builder.build_story(
            insights=sample_insights,
            project_name="Agricultural Retail Analysis",
            objective="Analyze customer satisfaction and retention",
            chart_refs={},
            context_str="n=511 growers"
        )

        # Should have all required components
        assert manifest.story_id
        assert manifest.project_name == "Agricultural Retail Analysis"
        assert manifest.thesis is not None
        assert len(manifest.top_kpis) >= 3
        assert len(manifest.sections) >= 1
        assert manifest.narrative_mode == NarrativeMode.EXECUTIVE
        assert manifest.executive_summary
        assert len(manifest.key_findings) >= 3

    def test_multi_mode_generation(self, sample_insights):
        """Should generate manifests in all three modes."""
        modes = [NarrativeMode.EXECUTIVE, NarrativeMode.ANALYST, NarrativeMode.TECHNICAL]
        manifests = []

        for mode in modes:
            builder = StoryBuilder(narrative_mode=mode)
            manifest = builder.build_story(
                insights=sample_insights,
                project_name="Test Project",
                objective="Test objective",
                chart_refs={},
                context_str=""
            )
            manifests.append(manifest)

        # All should succeed
        assert len(manifests) == 3

        # Should have different narratives
        summaries = [m.executive_summary for m in manifests]
        assert len(set(summaries)) == 3  # All different

    def test_manifest_serialization(self, sample_insights, tmp_path):
        """Should serialize manifest to JSON."""
        builder = StoryBuilder(narrative_mode=NarrativeMode.EXECUTIVE)

        manifest = builder.build_story(
            insights=sample_insights,
            project_name="Test Project",
            objective="Test objective",
            chart_refs={},
            context_str=""
        )

        # Save to JSON
        output_path = tmp_path / "story_manifest.json"
        manifest.save(output_path)

        # Should create file
        assert output_path.exists()

        # Should be valid JSON
        with open(output_path) as f:
            data = json.load(f)

        # Should have all required fields
        assert data["story_id"]
        assert data["project_name"]
        assert "thesis" in data
        assert "top_kpis" in data
        assert "sections" in data
        assert data["narrative_mode"]


class TestChartSelector:
    """Test smart chart type selection."""

    def test_timeseries_detection(self):
        """Should detect time-series data and suggest line/area."""
        import pandas as pd
        from kie.story.chart_selector import ChartSelector

        data = pd.DataFrame({
            "quarter": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],
            "revenue": [1000, 1200, 1450, 1300]
        })

        insight = Insight(
            insight_id="test",
            text="Revenue trends over time show seasonal patterns",
            category="trend",
            confidence=0.85,
            business_value=0.80,
            actionability=0.70,
            supporting_data={}
        )

        selector = ChartSelector()
        chart_type, params = selector.select_chart_type(
            insight=insight,
            data=data,
            x_column="quarter",
            y_columns=["revenue"]
        )

        # Should suggest time-series chart
        assert chart_type in ["line", "area"]

    def test_comparison_detection(self):
        """Should detect comparison data and suggest bar chart."""
        import pandas as pd
        from kie.story.chart_selector import ChartSelector

        data = pd.DataFrame({
            "region": ["North", "South", "East", "West"],
            "revenue": [1200, 980, 1450, 1100]
        })

        insight = Insight(
            insight_id="test",
            text="East region shows higher revenue than other regions",
            category="comparison",
            confidence=0.90,
            business_value=0.85,
            actionability=0.75,
            supporting_data={}
        )

        selector = ChartSelector()
        chart_type, params = selector.select_chart_type(
            insight=insight,
            data=data,
            x_column="region",
            y_columns=["revenue"]
        )

        # Should suggest bar chart
        assert chart_type in ["bar", "horizontal_bar"]

    def test_composition_detection(self):
        """Should detect composition data and suggest pie/donut."""
        import pandas as pd
        from kie.story.chart_selector import ChartSelector

        data = pd.DataFrame({
            "category": ["A", "B", "C", "D"],
            "share": [40, 30, 20, 10]
        })

        insight = Insight(
            insight_id="test",
            text="Category A accounts for 40% of the total market share",
            category="composition",
            confidence=0.88,
            business_value=0.75,
            actionability=0.65,
            supporting_data={}
        )

        selector = ChartSelector()
        chart_type, params = selector.select_chart_type(
            insight=insight,
            data=data,
            x_column="category",
            y_columns=["share"]
        )

        # Should suggest pie/donut
        assert chart_type in ["pie", "donut"]


class TestIntegration:
    """Test full integration with real-world scenarios."""

    def test_agricultural_retail_scenario(self, sample_insights):
        """Should handle agricultural retail analysis scenario."""
        builder = StoryBuilder(narrative_mode=NarrativeMode.EXECUTIVE)

        manifest = builder.build_story(
            insights=sample_insights,
            project_name="Agricultural Retail Survey",
            objective="Understand satisfaction drivers and retention risks",
            chart_refs={},
            context_str="n=511 agricultural retailers"
        )

        # Should detect the paradox
        assert "satisfaction" in manifest.thesis.title.lower() or "paradox" in manifest.thesis.title.lower()

        # Should extract key percentages
        kpi_values = [kpi.value for kpi in manifest.top_kpis]
        assert any("68.7" in val or "82" in val or "60" in val for val in kpi_values)

        # Should group insights logically
        section_titles = [s.title for s in manifest.sections]
        assert any("satisfaction" in title.lower() or "price" in title.lower() for title in section_titles)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
