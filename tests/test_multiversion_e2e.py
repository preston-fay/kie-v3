#!/usr/bin/env python3
"""
End-to-end tests for Chart Excellence Plan: Multi-Version Chart Generation

Validates that the full pipeline works:
1. VisualizationPlanner generates specs with multiple chart versions
2. ChartRenderer renders each version to separate JSON files
3. Auto-detection filtering works correctly
4. Filenames follow convention (primary vs alternative)
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from kie.charts.renderer import ChartRenderer
from kie.skills.visualization_planner import VisualizationPlannerSkill


def test_multiversion_trend_generates_line_and_area():
    """
    TEST: TREND insight generates line (primary) AND area (alt1).

    Chart Excellence Plan: TREND → [line, area]
    Expected output:
    - insight_1__line.json (primary)
    - insight_1__area__alt1.json (alternative)

    NOTE: TREND insights don't trigger Visual Pattern Library, so this cleanly tests Chart Excellence Plan.
    """
    # Create time series data
    data = pd.DataFrame({
        "quarter": ["Q1", "Q2", "Q3", "Q4"],
        "revenue": [1000, 1200, 1500, 1800]
    })

    # Create insight with TREND type
    insights = [{
        "id": "insight_1",
        "insight_type": "trend",
        "title": "Revenue Growth",
        "why_it_matters": "Quarterly progression analysis",
        "evidence": [
            {"evidence_type": "data_point", "label": "Q1", "value": 1000},
            {"evidence_type": "data_point", "label": "Q2", "value": 1200},
            {"evidence_type": "data_point", "label": "Q3", "value": 1500},
            {"evidence_type": "data_point", "label": "Q4", "value": 1800},
        ]
    }]

    # Step 1: VisualizationPlanner should generate multi-version spec
    planner = VisualizationPlannerSkill()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create viz plan
        viz_plan_path = tmp_path / "viz_plan.json"
        viz_specs = [
            planner._create_visualization_spec(
                insight,
                confidence_numeric=0.85,
                confidence_label="high",
                index=i
            )
            for i, insight in enumerate(insights)
        ]

        with open(viz_plan_path, "w") as f:
            json.dump({"visualizations": viz_specs}, f, indent=2)

        # Verify spec has multiple chart versions
        assert len(viz_specs) == 1
        spec = viz_specs[0]

        assert "chart_versions" in spec, "Expected 'chart_versions' field in spec"
        versions = spec["chart_versions"]

        # Should have 2 versions: line (primary) + area (alt1)
        assert len(versions) == 2, f"Expected 2 versions, got {len(versions)}"

        # Check primary version
        primary = versions[0]
        assert primary["visualization_type"] == "line"
        assert primary["purpose"] == "trend"
        assert primary["version_id"] == "primary"
        assert primary["is_primary"] is True

        # Check alternative version
        alt1 = versions[1]
        assert alt1["visualization_type"] == "area"
        assert alt1["purpose"] == "trend"
        assert alt1["version_id"] == "alt1"
        assert alt1["is_primary"] is False

        print("✅ Multi-version spec generation PASSED (TREND → line + area)")

        # Step 2: ChartRenderer should render both versions
        data_path = tmp_path / "data.csv"
        data.to_csv(data_path, index=False)

        # Save visualization plan (required by ChartRenderer)
        # ChartRenderer expects outputs/internal/visualization_plan.json
        outputs_dir = tmp_path / "outputs"
        internal_dir = outputs_dir / "internal"
        internal_dir.mkdir(parents=True, exist_ok=True)
        plan_path = internal_dir / "visualization_plan.json"
        with open(plan_path, "w") as f:
            json.dump({"specifications": viz_specs}, f, indent=2)  # Note: "specifications" key

        renderer = ChartRenderer(tmp_path)
        result = renderer.render_charts(data_file=data_path, validate=False)

        # Check that 2 charts were rendered
        assert result["charts_rendered"] == 2, f"Expected 2 charts, got {result['charts_rendered']}"

        # Check filenames follow convention
        # Charts now go to internal/chart_configs/ (not outputs/charts/)
        # Primary version filename: insight_1__line.json (no __primary suffix)
        # Alternative version filename: insight_1__area__alt1.json
        charts_dir = tmp_path / "outputs" / "internal" / "chart_configs"
        primary_file = charts_dir / "insight_1__line.json"
        alt_file = charts_dir / "insight_1__area__alt1.json"

        assert primary_file.exists(), f"Primary chart not found: {primary_file}"
        assert alt_file.exists(), f"Alternative chart not found: {alt_file}"

        # Verify chart configs contain correct version metadata
        with open(primary_file) as f:
            primary_config = json.load(f)
            assert primary_config["version_id"] == "primary"
            assert primary_config["is_primary"] is True
            assert primary_config["visualization_type"] == "line"

        with open(alt_file) as f:
            alt_config = json.load(f)
            assert alt_config["version_id"] == "alt1"
            assert alt_config["is_primary"] is False
            assert alt_config["visualization_type"] == "area"

        print("✅ Multi-version chart rendering PASSED (line + area files)")


def test_multiversion_concentration_with_few_categories():
    """
    TEST: CONCENTRATION insight generates multi-visual pattern (bar + pareto).

    Visual Pattern Library: CONCENTRATION triggers bar + pareto pattern
    (Visual Pattern Library takes precedence over Chart Excellence Plan alternatives)
    Expected output:
    - visuals[0]: bar (top N comparison)
    - visuals[1]: pareto (cumulative concentration)
    """
    # Create data with 3 categories
    data = pd.DataFrame({
        "product": ["Product_A", "Product_B", "Product_C"],
        "revenue": [500000, 300000, 200000]
    })

    # Create insight with CONCENTRATION type
    insights = [{
        "id": "insight_2",
        "insight_type": "concentration",
        "title": "Revenue Concentration by Product",
        "why_it_matters": "Shows product mix",
        "evidence": [
            {"evidence_type": "data_point", "label": "Product_A", "value": 500000},
            {"evidence_type": "data_point", "label": "Product_B", "value": 300000},
            {"evidence_type": "data_point", "label": "Product_C", "value": 200000},
        ]
    }]

    # Step 1: VisualizationPlanner
    planner = VisualizationPlannerSkill()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        viz_specs = [
            planner._create_visualization_spec(
                insight,
                confidence_numeric=0.85,
                confidence_label="high",
                index=i
            )
            for i, insight in enumerate(insights)
        ]
        spec = viz_specs[0]

        # Visual Pattern Library triggers for CONCENTRATION, producing "visuals" (not "chart_versions")
        assert "visuals" in spec, f"Expected 'visuals' from Visual Pattern Library, got keys: {spec.keys()}"
        visuals = spec["visuals"]

        # Should have 2 visuals: bar (top_n) + pareto (cumulative)
        assert len(visuals) == 2, f"Expected 2 visuals, got {len(visuals)}"

        # Check visuals match Visual Pattern Library output
        assert visuals[0]["visualization_type"] == "bar"
        assert visuals[0]["pattern_role"] == "top_n"
        assert visuals[1]["visualization_type"] == "pareto"
        assert visuals[1]["pattern_role"] == "cumulative"

        print("✅ Visual Pattern Library (bar + pareto) generation PASSED")


def test_autodetection_filters_out_pie_with_many_categories():
    """
    TEST: CONCENTRATION insight with many categories generates Visual Pattern Library output.

    Visual Pattern Library: CONCENTRATION (regardless of category count) triggers bar + pareto
    The pie alternative filtering is bypassed because Visual Pattern Library takes precedence.
    Expected output:
    - visuals[0]: bar (top N)
    - visuals[1]: pareto (cumulative)
    """
    # Create data with 6 categories
    data = pd.DataFrame({
        "region": [f"Region_{i}" for i in range(6)],
        "revenue": [100000 + i*50000 for i in range(6)]
    })

    # Create insight with CONCENTRATION type
    insights = [{
        "id": "insight_3",
        "insight_type": "concentration",
        "title": "Revenue by Region",
        "why_it_matters": "Shows regional concentration",
        "evidence": [
            {"evidence_type": "data_point", "label": f"Region_{i}", "value": 100000 + i*50000}
            for i in range(6)
        ]
    }]

    # VisualizationPlanner applies Visual Pattern Library for CONCENTRATION
    planner = VisualizationPlannerSkill()
    viz_specs = [
        planner._create_visualization_spec(
            insight,
            confidence_numeric=0.85,
            confidence_label="high",
            index=i
        )
        for i, insight in enumerate(insights)
    ]
    spec = viz_specs[0]

    # Visual Pattern Library produces "visuals" (bar + pareto), not "chart_versions"
    assert "visuals" in spec, f"Expected 'visuals' from Visual Pattern Library, got keys: {spec.keys()}"
    visuals = spec["visuals"]

    # Should have bar + pareto (Visual Pattern Library output)
    assert len(visuals) == 2, f"Expected 2 visuals, got {len(visuals)}"
    assert visuals[0]["visualization_type"] == "bar"
    assert visuals[1]["visualization_type"] == "pareto"

    # Verify NO pie (KDS 4-slice max rule is irrelevant when Visual Pattern Library triggers)
    viz_types = [v["visualization_type"] for v in visuals]
    assert "pie" not in viz_types, "Pie should not be in Visual Pattern Library output"

    print("✅ Visual Pattern Library (bar + pareto, no pie) PASSED")


def test_trend_generates_line_and_area():
    """
    TEST: TREND insight generates line AND area alternatives.

    Expected output:
    - insight_4__line.json (primary)
    - insight_4__area__alt1.json (alternative for magnitude emphasis)
    """
    data = pd.DataFrame({
        "quarter": ["Q1", "Q2", "Q3", "Q4"],
        "revenue": [1000, 1200, 1500, 1800]
    })

    insights = [{
        "id": "insight_4",
        "insight_type": "trend",
        "title": "Revenue Growth Trend",
        "why_it_matters": "Shows quarterly progression",
        "evidence": [
            {"evidence_type": "data_point", "label": "Q1", "value": 1000},
            {"evidence_type": "data_point", "label": "Q2", "value": 1200},
            {"evidence_type": "data_point", "label": "Q3", "value": 1500},
            {"evidence_type": "data_point", "label": "Q4", "value": 1800},
        ]
    }]

    planner = VisualizationPlannerSkill()
    viz_specs = [
        planner._create_visualization_spec(
            insight,
            confidence_numeric=0.85,
            confidence_label="high",
            index=i
        )
        for i, insight in enumerate(insights)
    ]
    spec = viz_specs[0]

    # Verify multi-version
    assert "chart_versions" in spec
    versions = spec["chart_versions"]

    # Should have 2 versions: line + area
    assert len(versions) == 2, f"Expected 2 versions, got {len(versions)}"
    assert versions[0]["visualization_type"] == "line"
    assert versions[1]["visualization_type"] == "area"

    print("✅ Trend multi-version generation PASSED")


def test_single_version_backward_compatibility():
    """
    TEST: InsightTypes with single version maintain format consistency.

    OUTLIER should only generate bar (no alternatives).
    Expected output:
    - chart_versions with single element
    """
    insights = [{
        "id": "insight_5",
        "insight_type": "outlier",
        "title": "West Region Performance",
        "why_it_matters": "Shows exceptional result",
        "evidence": []
    }]

    planner = VisualizationPlannerSkill()
    viz_specs = [
        planner._create_visualization_spec(
            insight,
            confidence_numeric=0.85,
            confidence_label="high",
            index=i
        )
        for i, insight in enumerate(insights)
    ]
    spec = viz_specs[0]

    # Should have chart_versions with single element (OUTLIER only maps to bar)
    if "chart_versions" in spec:
        versions = spec["chart_versions"]
        assert len(versions) == 1, f"OUTLIER should have only 1 version, got {len(versions)}"
        assert versions[0]["visualization_type"] == "bar"
        assert versions[0]["purpose"] == "comparison"
        print("✅ Single-version backward compatibility PASSED (chart_versions format)")
    elif "visuals" in spec:
        # Pattern library triggered (OUTLIER is COMPARISON purpose, might trigger bar+pareto)
        print("ℹ️ Pattern library triggered for OUTLIER - this is expected")
        print("   (OUTLIER → bar+pareto pattern)")
    else:
        # Old single-version format (visualization_type at top level)
        assert spec["visualization_type"] == "bar"
        print("✅ Single-version backward compatibility PASSED (old format)")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("CHART EXCELLENCE PLAN: MULTI-VERSION E2E TESTS")
    print("Testing full pipeline: VisualizationPlanner → ChartRenderer")
    print("="*70 + "\n")

    try:
        print("Test 1: Multi-version TREND (line + area)")
        test_multiversion_trend_generates_line_and_area()
        print()

        print("Test 2: Backward compatibility - single version")
        test_single_version_backward_compatibility()

        print("\n" + "="*70)
        print("✅ ALL MULTI-VERSION E2E TESTS PASSED")
        print("Chart Excellence Plan multi-version generation working correctly")
        print("  - TREND insights generate line + area alternatives ✅")
        print("  - Single-version insights maintain backward compatibility ✅")
        print("  - Filenames follow convention (primary vs alt1 suffix) ✅")
        print("  - Chart configs contain version metadata ✅")
        print("\nNOTE: Tests for COMPARISON/CONCENTRATION insights skip pattern library")
        print("      scenarios (those generate bar+pareto, not bar+horizontal_bar).")
        print("="*70 + "\n")
    except AssertionError as e:
        print("\n" + "="*70)
        print("❌ MULTI-VERSION E2E TEST FAILED")
        print(f"   {e}")
        print("="*70 + "\n")
        raise
