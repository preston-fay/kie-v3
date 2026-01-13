#!/usr/bin/env python3
"""
Unit tests for PR #4: VisualizationPlanner InsightType → ChartType Mapping

Verifies that intent-driven chart selection works correctly.
"""

import tempfile
from pathlib import Path

import pytest

from kie.insights.schema import InsightType
from kie.skills.visualization_planner import VisualizationPlannerSkill, INSIGHT_TYPE_TO_CHART_TYPE


def test_insight_type_mapping_table_exists():
    """
    TEST: INSIGHT_TYPE_TO_CHART_TYPE mapping table is defined.
    Chart Excellence Plan: Now has 12 InsightType values (8 core + 4 new).
    """
    assert INSIGHT_TYPE_TO_CHART_TYPE is not None
    assert len(INSIGHT_TYPE_TO_CHART_TYPE) == 12

    # Verify all InsightType values are mapped (8 core + 4 new)
    assert InsightType.COMPARISON in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.TREND in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.DISTRIBUTION in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.CORRELATION in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.CONCENTRATION in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.OUTLIER in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.VARIANCE in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.BENCHMARK in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.COMPOSITION in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.DUAL_METRIC in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.CONTRIBUTION in INSIGHT_TYPE_TO_CHART_TYPE
    assert InsightType.DRIVER in INSIGHT_TYPE_TO_CHART_TYPE

    print("✅ Mapping Table Test PASSED")
    print(f"   - All 12 InsightType values are mapped to chart types")


def test_comparison_maps_to_bar():
    """
    TEST: COMPARISON InsightType maps to bar chart.
    Chart Excellence Plan: Now returns list of alternatives.
    """
    planner = VisualizationPlannerSkill()

    insight = {
        "insight_type": "comparison",
        "title": "Revenue comparison",
        "why_it_matters": "Shows regional differences",
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    # Should return list with primary version first
    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "bar"
    assert purpose == "comparison"
    assert version_id == "primary"

    print("✅ COMPARISON → Bar Test PASSED")


def test_trend_maps_to_line():
    """
    TEST: TREND InsightType maps to line chart.
    Chart Excellence Plan: Now returns list of alternatives.
    """
    planner = VisualizationPlannerSkill()

    insight = {
        "insight_type": "trend",
        "title": "Revenue growth over time",
        "why_it_matters": "Shows quarterly progression",
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "line"
    assert purpose == "trend"
    assert version_id == "primary"

    print("✅ TREND → Line Test PASSED")


def test_distribution_maps_to_histogram():
    """
    TEST: DISTRIBUTION InsightType maps to bar (histogram-style).
    Chart Audit Fix: Changed from "histogram" to "bar" since ChartFactory doesn't have histogram type.
    """
    planner = VisualizationPlannerSkill()

    insight = {
        "insight_type": "distribution",
        "title": "Revenue distribution across deals",
        "why_it_matters": "Shows deal size spread",
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "bar"  # Fixed: now uses bar formatted as histogram
    assert purpose == "distribution"
    assert version_id == "primary"

    print("✅ DISTRIBUTION → Bar (histogram-style) Test PASSED")


def test_correlation_maps_to_scatter():
    """
    TEST: CORRELATION InsightType maps to scatter chart.
    """
    planner = VisualizationPlannerSkill()

    insight = {
        "insight_type": "correlation",
        "title": "Marketing spend vs revenue relationship",
        "why_it_matters": "Shows strong correlation",
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "scatter"
    assert purpose == "risk"
    assert version_id == "primary"

    print("✅ CORRELATION → Scatter Test PASSED")


def test_concentration_maps_to_bar():
    """
    TEST: CONCENTRATION InsightType maps to bar chart.
    """
    planner = VisualizationPlannerSkill()

    insight = {
        "insight_type": "concentration",
        "title": "Revenue concentration in top 3 clients",
        "why_it_matters": "Shows customer concentration risk",
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "bar"
    assert purpose == "concentration"
    assert version_id == "primary"

    print("✅ CONCENTRATION → Bar Test PASSED")


def test_outlier_maps_to_bar():
    """
    TEST: OUTLIER InsightType maps to bar chart (with highlighting).
    """
    planner = VisualizationPlannerSkill()

    insight = {
        "insight_type": "outlier",
        "title": "West region outperforms by 300%",
        "why_it_matters": "Shows exceptional performance",
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "bar"
    assert purpose == "comparison"
    assert version_id == "primary"

    print("✅ OUTLIER → Bar Test PASSED")


def test_variance_maps_to_distribution():
    """
    TEST: VARIANCE InsightType maps to distribution chart.
    """
    planner = VisualizationPlannerSkill()

    insight = {
        "insight_type": "variance",
        "title": "High variance in deal sizes",
        "why_it_matters": "Shows volatility",
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "bar"  # Fixed: now uses bar formatted as histogram
    assert purpose == "distribution"
    assert version_id == "primary"

    print("✅ VARIANCE → Bar (histogram-style) Test PASSED")


def test_benchmark_maps_to_bar():
    """
    TEST: BENCHMARK InsightType maps to bar chart (comparison).
    """
    planner = VisualizationPlannerSkill()

    insight = {
        "insight_type": "benchmark",
        "title": "Performance vs industry benchmark",
        "why_it_matters": "Shows competitive position",
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "bar"
    assert purpose == "comparison"
    assert version_id == "primary"

    print("✅ BENCHMARK → Bar Test PASSED")


def test_fallback_to_keyword_matching_when_no_insight_type():
    """
    TEST: Falls back to keyword matching when insight_type is missing.
    """
    planner = VisualizationPlannerSkill()

    # No insight_type field
    insight = {
        "title": "Revenue growth over time",
        "why_it_matters": "Shows quarterly trend",
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    # Should detect "over time" and "trend" keywords
    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "line"
    assert purpose == "trend"
    assert version_id == "primary"

    print("✅ Keyword Fallback Test PASSED")


def test_fallback_when_invalid_insight_type():
    """
    TEST: Falls back to keyword matching when insight_type is invalid.
    """
    planner = VisualizationPlannerSkill()

    # Invalid insight_type value
    insight = {
        "insight_type": "invalid_type",
        "title": "Regional comparison of sales",
        "why_it_matters": "Compare regions",
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    # Should fall back to keyword matching ("compare")
    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "bar"
    assert purpose == "comparison"
    assert version_id == "primary"

    print("✅ Invalid Type Fallback Test PASSED")


def test_insight_type_takes_precedence_over_keywords():
    """
    TEST: InsightType mapping takes precedence over keyword matching.
    """
    planner = VisualizationPlannerSkill()

    # insight_type says DISTRIBUTION, but keywords suggest TREND
    insight = {
        "insight_type": "distribution",
        "title": "Revenue over time shows growth",  # Keywords: "over time", "growth"
        "why_it_matters": "Trend analysis",  # Keyword: "trend"
        "evidence": []
    }

    versions = planner._infer_visualization_type(insight, insight["title"], insight["why_it_matters"])

    # Should use InsightType mapping, NOT keyword matching
    assert isinstance(versions, list)
    assert len(versions) >= 1

    viz_type, purpose, version_id = versions[0]
    assert viz_type == "bar"  # Fixed: now uses bar formatted as histogram
    assert purpose == "distribution"
    assert version_id == "primary"

    print("✅ InsightType Precedence Test PASSED")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PR #4: VISUALIZATION PLANNER TESTS")
    print("Testing: InsightType → ChartType mapping (intent-driven selection)")
    print("="*70 + "\n")

    try:
        test_insight_type_mapping_table_exists()
        print()
        test_comparison_maps_to_bar()
        print()
        test_trend_maps_to_line()
        print()
        test_distribution_maps_to_histogram()
        print()
        test_correlation_maps_to_scatter()
        print()
        test_concentration_maps_to_bar()
        print()
        test_outlier_maps_to_bar()
        print()
        test_variance_maps_to_distribution()
        print()
        test_benchmark_maps_to_bar()
        print()
        test_fallback_to_keyword_matching_when_no_insight_type()
        print()
        test_fallback_when_invalid_insight_type()
        print()
        test_insight_type_takes_precedence_over_keywords()
        print("\n" + "="*70)
        print("✅ ALL PR #4 TESTS PASSED")
        print("Intent-driven chart selection working correctly")
        print("="*70 + "\n")
    except AssertionError as e:
        print("\n" + "="*70)
        print("❌ PR #4 TEST FAILED")
        print(f"   {e}")
        print("="*70 + "\n")
        raise
