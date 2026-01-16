"""
Test Suite: LLM-Powered Story Components with Universal Data Types

Validates that the story-first architecture works for ANY data domain:
- Healthcare (clinical trials, patient outcomes)
- IoT (sensor telemetry, system metrics)
- Manufacturing (quality control, throughput)
- Financial (trading, portfolio performance)
- Business (supply chain, procurement, sales, customer experience)

This ensures KIE can handle "literally any sort of data someone may ever want to use for an analysis."
"""

import pytest
from kie.story.models import StoryInsight, NarrativeMode
from kie.story.llm_grouper import LLMSectionGrouper
from kie.story.llm_chart_selector import LLMChartSelector
from kie.story.llm_narrative_synthesizer import LLMNarrativeSynthesizer
from kie.story.llm_story_builder import LLMStoryBuilder


# ============================================================================
# Healthcare Data Tests
# ============================================================================

def test_llm_grouper_healthcare():
    """LLM grouper should learn medical topics from clinical data"""
    insights = [
        StoryInsight(
            insight_id="med_001",
            text="Patient survival rate improved 23% with new protocol (p<0.01)",
            category="outcome",
            confidence=0.95,
            business_value=0.92,
            actionability=0.88
        ),
        StoryInsight(
            insight_id="med_002",
            text="Symptom reduction observed in 89% of cohort (n=412)",
            category="treatment",
            confidence=0.90,
            business_value=0.85,
            actionability=0.80
        ),
        StoryInsight(
            insight_id="med_003",
            text="Adverse events decreased 34% compared to standard treatment",
            category="safety",
            confidence=0.88,
            business_value=0.82,
            actionability=0.75
        ),
        StoryInsight(
            insight_id="med_004",
            text="Patient compliance reached 94%, up from 78% baseline",
            category="outcome",
            confidence=0.85,
            business_value=0.80,
            actionability=0.85
        )
    ]

    grouper = LLMSectionGrouper()
    sections = grouper.group_insights(insights, {}, min_section_size=2)

    # Should detect medical themes (not business themes like "satisfaction" or "price")
    section_titles = [sec.title.lower() for sec in sections]

    # Check for medical-relevant themes (or fallback section)
    medical_keywords = ["treatment", "outcome", "patient", "symptom", "safety", "protocol", "clinical", "key findings"]
    has_medical_theme = any(
        any(keyword in title for keyword in medical_keywords)
        for title in section_titles
    )

    assert has_medical_theme, f"Should detect medical themes or create fallback, got: {section_titles}"
    assert len(sections) >= 1, "Should create at least 1 section"


def test_llm_chart_selector_healthcare():
    """LLM chart selector should pick appropriate charts for medical data"""
    insight = StoryInsight(
        insight_id="med_001",
        text="Patient survival rate distribution shows strong correlation with treatment duration (p<0.01)",
        category="outcome",
        confidence=0.95,
        business_value=0.92,
        actionability=0.88
    )

    selector = LLMChartSelector()
    chart_type, params = selector.select_chart_type(insight)

    # Should pick statistical charts for medical data
    statistical_charts = ["scatter", "box_plot", "histogram", "violin", "heatmap", "correlation_matrix"]
    assert chart_type in statistical_charts, f"Expected statistical chart for correlation, got {chart_type}"


def test_end_to_end_healthcare():
    """Full pipeline should work for healthcare data"""
    insights = [
        StoryInsight(
            insight_id="med_001",
            text="Patient survival rate improved 23% with new protocol (p<0.01)",
            category="outcome",
            confidence=0.95,
            business_value=0.92,
            actionability=0.88
        ),
        StoryInsight(
            insight_id="med_002",
            text="Symptom reduction observed in 89% of cohort (n=412)",
            category="treatment",
            confidence=0.90,
            business_value=0.85,
            actionability=0.80
        )
    ]

    builder = LLMStoryBuilder(narrative_mode=NarrativeMode.TECHNICAL)
    story = builder.build_story(
        insights,
        project_name="Clinical Trial Q4 2025",
        objective="Evaluate treatment efficacy"
    )

    # Validate story structure
    assert story.thesis.title is not None
    assert len(story.top_kpis) >= 2
    assert len(story.sections) >= 1
    assert story.executive_summary is not None

    # Should detect medical KPIs (23%, 89%, p<0.01)
    kpi_values = [kpi.value for kpi in story.top_kpis]
    assert any("23" in str(val) or "89" in str(val) for val in kpi_values), \
        f"Should extract medical KPIs, got: {kpi_values}"


# ============================================================================
# IoT/Telemetry Data Tests
# ============================================================================

def test_llm_grouper_iot():
    """LLM grouper should learn technical themes from IoT data"""
    insights = [
        StoryInsight(
            insight_id="iot_001",
            text="System latency reduced 34ms (99th percentile) after optimization",
            category="performance",
            confidence=0.88,
            business_value=0.90,
            actionability=0.95
        ),
        StoryInsight(
            insight_id="iot_002",
            text="Network uptime reached 99.97%, up from 99.2% baseline",
            category="reliability",
            confidence=0.92,
            business_value=0.88,
            actionability=0.85
        ),
        StoryInsight(
            insight_id="iot_003",
            text="Packet loss decreased to 0.02%, 85% improvement",
            category="reliability",
            confidence=0.90,
            business_value=0.85,
            actionability=0.80
        ),
        StoryInsight(
            insight_id="iot_004",
            text="CPU utilization optimized to 45% average (from 72%)",
            category="performance",
            confidence=0.85,
            business_value=0.82,
            actionability=0.88
        )
    ]

    grouper = LLMSectionGrouper()
    sections = grouper.group_insights(insights, {}, min_section_size=2)

    # Should detect technical themes (or fallback)
    section_titles = [sec.title.lower() for sec in sections]
    technical_keywords = ["performance", "reliability", "latency", "uptime", "system", "network", "key findings"]
    has_technical_theme = any(
        any(keyword in title for keyword in technical_keywords)
        for title in section_titles
    )

    assert has_technical_theme, f"Should detect technical themes or create fallback, got: {section_titles}"


def test_llm_chart_selector_iot():
    """LLM chart selector should pick time series charts for IoT data"""
    insight = StoryInsight(
        insight_id="iot_001",
        text="System latency shows clear downward trend over time, with 34ms reduction since optimization",
        category="performance",
        confidence=0.88,
        business_value=0.90,
        actionability=0.95
    )

    selector = LLMChartSelector()
    chart_type, params = selector.select_chart_type(insight)

    # Should pick time series charts for trend data
    time_series_charts = ["line", "area", "stacked_area"]
    assert chart_type in time_series_charts, f"Expected time series chart for trend, got {chart_type}"


def test_end_to_end_iot():
    """Full pipeline should work for IoT data"""
    insights = [
        StoryInsight(
            insight_id="iot_001",
            text="System latency reduced 34ms (99th percentile) after optimization",
            category="performance",
            confidence=0.88,
            business_value=0.90,
            actionability=0.95
        ),
        StoryInsight(
            insight_id="iot_002",
            text="Network uptime reached 99.97%, up from 99.2% baseline",
            category="reliability",
            confidence=0.92,
            business_value=0.88,
            actionability=0.85
        )
    ]

    builder = LLMStoryBuilder(narrative_mode=NarrativeMode.ANALYST)
    story = builder.build_story(
        insights,
        project_name="Network Performance Analysis",
        objective="Assess infrastructure optimization"
    )

    assert story.thesis.title is not None
    assert len(story.top_kpis) >= 2
    assert len(story.sections) >= 1

    # Should detect technical KPIs (34ms, 99.97%)
    kpi_values = [kpi.value for kpi in story.top_kpis]
    assert any("34" in str(val) or "99" in str(val) for val in kpi_values), \
        f"Should extract technical KPIs, got: {kpi_values}"


# ============================================================================
# Manufacturing Data Tests
# ============================================================================

def test_llm_grouper_manufacturing():
    """LLM grouper should learn operations themes from manufacturing data"""
    insights = [
        StoryInsight(
            insight_id="mfg_001",
            text="Defect rate dropped to 0.3%, 47% below target threshold",
            category="quality",
            confidence=0.90,
            business_value=0.95,
            actionability=0.92
        ),
        StoryInsight(
            insight_id="mfg_002",
            text="Production line efficiency increased 18%, throughput at 1,240 units/hour",
            category="efficiency",
            confidence=0.88,
            business_value=0.90,
            actionability=0.88
        ),
        StoryInsight(
            insight_id="mfg_003",
            text="Machine downtime reduced 42%, preventive maintenance working",
            category="reliability",
            confidence=0.85,
            business_value=0.88,
            actionability=0.90
        ),
        StoryInsight(
            insight_id="mfg_004",
            text="First-pass yield improved to 94.2%, up from 87.5%",
            category="quality",
            confidence=0.92,
            business_value=0.90,
            actionability=0.85
        )
    ]

    grouper = LLMSectionGrouper()
    sections = grouper.group_insights(insights, {}, min_section_size=2)

    # Should detect operations themes (or fallback)
    section_titles = [sec.title.lower() for sec in sections]
    ops_keywords = ["quality", "efficiency", "production", "defect", "throughput", "yield", "key findings"]
    has_ops_theme = any(
        any(keyword in title for keyword in ops_keywords)
        for title in section_titles
    )

    assert has_ops_theme, f"Should detect operations themes or create fallback, got: {section_titles}"


def test_llm_chart_selector_manufacturing():
    """LLM chart selector should pick comparison charts for manufacturing data"""
    insight = StoryInsight(
        insight_id="mfg_001",
        text="Defect rate comparison shows Line 3 performs 47% better than target",
        category="quality",
        confidence=0.90,
        business_value=0.95,
        actionability=0.92
    )

    selector = LLMChartSelector()
    chart_type, params = selector.select_chart_type(insight)

    # Should pick comparison charts
    comparison_charts = ["bar", "horizontal_bar", "grouped_bar", "waterfall"]
    assert chart_type in comparison_charts, f"Expected comparison chart, got {chart_type}"


def test_end_to_end_manufacturing():
    """Full pipeline should work for manufacturing data"""
    insights = [
        StoryInsight(
            insight_id="mfg_001",
            text="Defect rate dropped to 0.3%, 47% below target threshold",
            category="quality",
            confidence=0.90,
            business_value=0.95,
            actionability=0.92
        ),
        StoryInsight(
            insight_id="mfg_002",
            text="Production line efficiency increased 18%, throughput at 1,240 units/hour",
            category="efficiency",
            confidence=0.88,
            business_value=0.90,
            actionability=0.88
        )
    ]

    builder = LLMStoryBuilder(narrative_mode=NarrativeMode.EXECUTIVE)
    story = builder.build_story(
        insights,
        project_name="Line 3 Process Improvement",
        objective="Reduce defects and increase throughput"
    )

    assert story.thesis.title is not None
    assert len(story.top_kpis) >= 2
    assert len(story.sections) >= 1

    # Should detect manufacturing KPIs (0.3%, 47%, 18%, 1,240)
    kpi_values = [kpi.value for kpi in story.top_kpis]
    assert len(kpi_values) >= 2, f"Should extract manufacturing KPIs, got: {kpi_values}"


# ============================================================================
# Financial Data Tests
# ============================================================================

def test_llm_grouper_financial():
    """LLM grouper should learn financial themes from trading data"""
    insights = [
        StoryInsight(
            insight_id="fin_001",
            text="Sharpe ratio improved to 1.82, up from 1.45 baseline",
            category="performance",
            confidence=0.92,
            business_value=0.90,
            actionability=0.85
        ),
        StoryInsight(
            insight_id="fin_002",
            text="Portfolio volatility decreased 12%, risk-adjusted returns exceed benchmark",
            category="risk",
            confidence=0.88,
            business_value=0.88,
            actionability=0.80
        ),
        StoryInsight(
            insight_id="fin_003",
            text="Maximum drawdown limited to 8.2%, well within risk tolerance",
            category="risk",
            confidence=0.90,
            business_value=0.85,
            actionability=0.75
        ),
        StoryInsight(
            insight_id="fin_004",
            text="Alpha generation at 3.4% annually, outperforming S&P 500",
            category="performance",
            confidence=0.85,
            business_value=0.92,
            actionability=0.88
        )
    ]

    grouper = LLMSectionGrouper()
    sections = grouper.group_insights(insights, {}, min_section_size=2)

    # Should detect financial themes
    section_titles = [sec.title.lower() for sec in sections]
    finance_keywords = ["risk", "performance", "return", "portfolio", "volatility", "sharpe"]
    has_finance_theme = any(
        any(keyword in title for keyword in finance_keywords)
        for title in section_titles
    )

    assert has_finance_theme, f"Should detect financial themes, got: {section_titles}"


def test_llm_chart_selector_financial():
    """LLM chart selector should pick candlestick for trading data"""
    insight = StoryInsight(
        insight_id="fin_001",
        text="Trading pattern shows strong correlation between volume and price movement over time",
        category="performance",
        confidence=0.92,
        business_value=0.90,
        actionability=0.85
    )

    selector = LLMChartSelector()
    chart_type, params = selector.select_chart_type(insight)

    # Should pick financial or correlation charts
    financial_charts = ["candlestick", "line", "scatter", "heatmap", "correlation_matrix"]
    assert chart_type in financial_charts, f"Expected financial chart, got {chart_type}"


def test_end_to_end_financial():
    """Full pipeline should work for financial data"""
    insights = [
        StoryInsight(
            insight_id="fin_001",
            text="Sharpe ratio improved to 1.82, up from 1.45 baseline",
            category="performance",
            confidence=0.92,
            business_value=0.90,
            actionability=0.85
        ),
        StoryInsight(
            insight_id="fin_002",
            text="Portfolio volatility decreased 12%, risk-adjusted returns exceed benchmark",
            category="risk",
            confidence=0.88,
            business_value=0.88,
            actionability=0.80
        )
    ]

    builder = LLMStoryBuilder(narrative_mode=NarrativeMode.ANALYST)
    story = builder.build_story(
        insights,
        project_name="Portfolio Risk Analysis",
        objective="Optimize risk-adjusted returns"
    )

    assert story.thesis.title is not None
    assert len(story.top_kpis) >= 1  # At least 1 KPI extracted
    assert len(story.sections) >= 1

    # Should detect financial KPIs
    kpi_values = [kpi.value for kpi in story.top_kpis]
    assert len(kpi_values) >= 1, f"Should extract financial KPIs, got: {kpi_values}"


# ============================================================================
# Business Data Tests (Supply Chain, Sales, Customer Experience)
# ============================================================================

def test_llm_grouper_business():
    """LLM grouper should learn business themes from operational data"""
    insights = [
        StoryInsight(
            insight_id="biz_001",
            text="Supply chain lead time reduced 23% across all vendors",
            category="operations",
            confidence=0.88,
            business_value=0.90,
            actionability=0.92
        ),
        StoryInsight(
            insight_id="biz_002",
            text="Customer satisfaction score increased to 4.7/5.0, up from 4.2",
            category="customer",
            confidence=0.90,
            business_value=0.85,
            actionability=0.80
        ),
        StoryInsight(
            insight_id="biz_003",
            text="Sales conversion rate improved 15% with new targeting approach",
            category="sales",
            confidence=0.92,
            business_value=0.95,
            actionability=0.88
        ),
        StoryInsight(
            insight_id="biz_004",
            text="Procurement costs decreased 8.2% through vendor consolidation",
            category="operations",
            confidence=0.85,
            business_value=0.88,
            actionability=0.85
        )
    ]

    grouper = LLMSectionGrouper()
    sections = grouper.group_insights(insights, {}, min_section_size=2)

    # Should detect business themes (or fallback)
    section_titles = [sec.title.lower() for sec in sections]
    business_keywords = ["supply", "customer", "sales", "procurement", "operations", "satisfaction", "key findings"]
    has_business_theme = any(
        any(keyword in title for keyword in business_keywords)
        for title in section_titles
    )

    assert has_business_theme, f"Should detect business themes or create fallback, got: {section_titles}"
    assert len(sections) >= 1


def test_end_to_end_business():
    """Full pipeline should work for business data"""
    insights = [
        StoryInsight(
            insight_id="biz_001",
            text="Supply chain lead time reduced 23% across all vendors",
            category="operations",
            confidence=0.88,
            business_value=0.90,
            actionability=0.92
        ),
        StoryInsight(
            insight_id="biz_002",
            text="Customer satisfaction score increased to 4.7/5.0, up from 4.2",
            category="customer",
            confidence=0.90,
            business_value=0.85,
            actionability=0.80
        ),
        StoryInsight(
            insight_id="biz_003",
            text="Sales conversion rate improved 15% with new targeting approach",
            category="sales",
            confidence=0.92,
            business_value=0.95,
            actionability=0.88
        )
    ]

    builder = LLMStoryBuilder(narrative_mode=NarrativeMode.EXECUTIVE)
    story = builder.build_story(
        insights,
        project_name="Operational Excellence Initiative",
        objective="Improve end-to-end operational metrics"
    )

    assert story.thesis.title is not None
    assert len(story.top_kpis) >= 2  # At least 2 KPIs from 3 insights
    assert len(story.sections) >= 1
    assert story.executive_summary is not None


# ============================================================================
# Backward Compatibility Tests
# ============================================================================

def test_backward_compatibility_rule_based():
    """Ensure rule-based components still work"""
    insights = [
        StoryInsight(
            insight_id="test_001",
            text="Revenue increased 25% compared to prior quarter",
            category="performance",
            confidence=0.90,
            business_value=0.95,
            actionability=0.85
        ),
        StoryInsight(
            insight_id="test_002",
            text="Customer satisfaction improved significantly",
            category="satisfaction",
            confidence=0.85,
            business_value=0.80,
            actionability=0.75
        )
    ]

    # Use rule-based components
    builder = LLMStoryBuilder(
        use_llm_grouping=False,
        use_llm_narrative=False,
        use_llm_charts=False
    )

    story = builder.build_story(
        insights,
        project_name="Q4 Business Review",
        objective="Analyze quarterly performance"
    )

    # Should still work
    assert story.thesis.title is not None
    assert len(story.top_kpis) >= 1
    assert len(story.sections) >= 1


def test_hybrid_mode():
    """Test hybrid mode (LLM grouping + rule-based narrative)"""
    insights = [
        StoryInsight(
            insight_id="test_001",
            text="Revenue increased 25% compared to prior quarter",
            category="performance",
            confidence=0.90,
            business_value=0.95,
            actionability=0.85
        ),
        StoryInsight(
            insight_id="test_002",
            text="Cost optimization saved $2.3M annually",
            category="cost",
            confidence=0.88,
            business_value=0.92,
            actionability=0.90
        )
    ]

    # Hybrid: LLM grouping, rule-based narrative
    builder = LLMStoryBuilder(
        use_llm_grouping=True,
        use_llm_narrative=False,
        use_llm_charts=True
    )

    story = builder.build_story(
        insights,
        project_name="Hybrid Test",
        objective="Test mixed mode"
    )

    assert story.thesis.title is not None
    assert len(story.sections) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
