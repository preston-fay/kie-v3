"""
Unit tests for dashboard manifest build.

Tests that the dashboard builder correctly copies story_manifest.json and charts
to the dashboard public directory.
"""

import json
from pathlib import Path

import pytest


def test_dashboard_copies_manifest_and_charts(tmp_path):
    """Test that build dashboard copies manifest and referenced charts."""
    from kie.export.react_builder import ReactDashboardBuilder

    # Setup test data
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_file = data_dir / "sample.csv"
    data_file.write_text("category,value\nA,10\nB,20\n")

    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create story manifest
    manifest = {
        "project_name": "Test Project",
        "objective": "Test objective",
        "sections": [
            {
                "title": "Section 1",
                "actionability_level": "decision_enabling",
                "narrative": {"headline": "Test headline"},
                "visuals": [
                    {
                        "chart_ref": "chart1.json",
                        "visualization_type": "bar",
                        "visual_quality": "client_ready",
                        "role": "baseline",
                        "transition_text": "Shows data",
                        "emphasis": "Key point",
                    }
                ],
            }
        ],
    }
    (outputs_dir / "story_manifest.json").write_text(json.dumps(manifest))

    # Create referenced chart
    chart1 = {
        "type": "bar",
        "data": [{"x": "A", "y": 10}, {"x": "B", "y": 20}],
        "config": {
            "xAxis": {"dataKey": "x", "label": "X"},
            "yAxis": {"label": "Y"},
            "bars": [{"dataKey": "y", "fill": "#7823DC"}],
        },
    }
    (charts_dir / "chart1.json").write_text(json.dumps(chart1))

    # Build dashboard
    dashboard_dir = tmp_path / "exports" / "dashboard"
    builder = ReactDashboardBuilder(
        project_name="Test Project",
        client_name="Test Client",
        objective="Test objective",
    )

    builder.build_dashboard(
        data_path=data_file, charts_dir=charts_dir, output_dir=dashboard_dir
    )

    # Verify manifest copied
    manifest_public = dashboard_dir / "public" / "story_manifest.json"
    assert manifest_public.exists(), "story_manifest.json not copied to public/"

    with open(manifest_public) as f:
        copied_manifest = json.load(f)
    assert copied_manifest["project_name"] == "Test Project"

    # Verify chart copied
    chart_public = dashboard_dir / "public" / "charts" / "chart1.json"
    assert chart_public.exists(), "chart1.json not copied to public/charts/"

    with open(chart_public) as f:
        copied_chart = json.load(f)
    assert copied_chart["type"] == "bar"


def test_dashboard_code_references_manifest(tmp_path):
    """Test that generated dashboard code references story_manifest.json."""
    from kie.export.react_builder import ReactDashboardBuilder

    # Setup minimal test data
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_file = data_dir / "sample.csv"
    data_file.write_text("category,value\nA,10\n")

    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Build dashboard
    dashboard_dir = tmp_path / "exports" / "dashboard"
    builder = ReactDashboardBuilder(
        project_name="Test Project",
        client_name="Test Client",
        objective="Test objective",
    )

    builder.build_dashboard(
        data_path=data_file, charts_dir=charts_dir, output_dir=dashboard_dir
    )

    # Verify Dashboard.tsx contains required strings
    dashboard_tsx = dashboard_dir / "src" / "Dashboard.tsx"
    assert dashboard_tsx.exists(), "Dashboard.tsx not created"

    dashboard_code = dashboard_tsx.read_text()

    # Check for tab strings
    assert "Main Story" in dashboard_code, "Dashboard code missing 'Main Story' tab"
    assert "Appendix" in dashboard_code, "Dashboard code missing 'Appendix' tab"

    # Check for manifest fetch
    assert (
        "story_manifest.json" in dashboard_code
    ), "Dashboard code does not reference story_manifest.json"

    # Check for classification logic
    assert (
        "actionability_level" in dashboard_code
    ), "Dashboard code missing actionability classification"
    assert (
        "visual_quality" in dashboard_code
    ), "Dashboard code missing visual quality handling"


def test_dashboard_handles_missing_manifest(tmp_path):
    """Test that dashboard build works even if manifest doesn't exist."""
    from kie.export.react_builder import ReactDashboardBuilder

    # Setup test data
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_file = data_dir / "sample.csv"
    data_file.write_text("category,value\nA,10\n")

    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # NO MANIFEST - test graceful handling

    # Build dashboard
    dashboard_dir = tmp_path / "exports" / "dashboard"
    builder = ReactDashboardBuilder(
        project_name="Test Project",
        client_name="Test Client",
        objective="Test objective",
    )

    # Should not crash
    builder.build_dashboard(
        data_path=data_file, charts_dir=charts_dir, output_dir=dashboard_dir
    )

    # Verify build completed (created basic structure)
    assert (dashboard_dir / "package.json").exists()
    assert (dashboard_dir / "src" / "Dashboard.tsx").exists()

    # Verify manifest NOT copied (since it didn't exist)
    manifest_public = dashboard_dir / "public" / "story_manifest.json"
    assert not manifest_public.exists(), "Manifest copied when it shouldn't exist"


def test_dashboard_only_copies_referenced_charts(tmp_path):
    """Test that only charts referenced in manifest are copied."""
    from kie.export.react_builder import ReactDashboardBuilder

    # Setup test data
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_file = data_dir / "sample.csv"
    data_file.write_text("category,value\nA,10\n")

    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create manifest referencing only chart1
    manifest = {
        "project_name": "Test Project",
        "objective": "Test objective",
        "sections": [
            {
                "title": "Section 1",
                "actionability_level": "decision_enabling",
                "narrative": {"headline": "Test"},
                "visuals": [
                    {
                        "chart_ref": "chart1.json",
                        "visualization_type": "bar",
                        "visual_quality": "client_ready",
                        "role": "baseline",
                        "transition_text": "Test",
                        "emphasis": "Test",
                    }
                ],
            }
        ],
    }
    (outputs_dir / "story_manifest.json").write_text(json.dumps(manifest))

    # Create multiple charts
    for chart_name in ["chart1.json", "chart2.json", "chart3.json"]:
        chart = {"type": "bar", "data": [], "config": {}}
        (charts_dir / chart_name).write_text(json.dumps(chart))

    # Build dashboard
    dashboard_dir = tmp_path / "exports" / "dashboard"
    builder = ReactDashboardBuilder(
        project_name="Test Project",
        client_name="Test Client",
        objective="Test objective",
    )

    builder.build_dashboard(
        data_path=data_file, charts_dir=charts_dir, output_dir=dashboard_dir
    )

    charts_public = dashboard_dir / "public" / "charts"

    # Only chart1 should be copied
    assert (charts_public / "chart1.json").exists(), "Referenced chart not copied"
    assert not (
        charts_public / "chart2.json"
    ).exists(), "Unreferenced chart2 was copied"
    assert not (
        charts_public / "chart3.json"
    ).exists(), "Unreferenced chart3 was copied"
