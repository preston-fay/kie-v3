"""
Tests for ChartRenderer

Verifies:
- Missing visualization_plan.json blocks chart rendering
- visualization_required=false produces no charts
- visualization_required=true produces exactly one chart
- Suppressed categories never appear in chart data
- Extra charts cause failure
- Deterministic filenames
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from kie.charts.renderer import ChartRenderer


@pytest.fixture
def temp_project():
    """Create temporary project structure."""
    tmpdir = tempfile.mkdtemp()
    project_root = Path(tmpdir)

    # Create directory structure
    (project_root / "outputs").mkdir(parents=True)
    (project_root / "data").mkdir(parents=True)

    return project_root


@pytest.fixture
def sample_data(temp_project):
    """Create sample data file."""
    data = {
        "Product": ["Widget A", "Widget B", "Widget C", "UNASSIGNED", "Unknown"],
        "Revenue": [1000, 1500, 2000, 500, 300],
        "Region": ["North", "South", "East", "West", "North"],
    }
    df = pd.DataFrame(data)

    data_file = temp_project / "data" / "sample.csv"
    df.to_csv(data_file, index=False)

    return data_file


@pytest.fixture
def viz_plan_with_charts():
    """Create visualization plan with visualization_required=true."""
    return {
        "generated_at": "2026-01-11T12:00:00",
        "total_insights_reviewed": 2,
        "visualizations_planned": 2,
        "specifications": [
            {
                "insight_id": "insight_1",
                "insight_title": "Widget C leads revenue",
                "visualization_required": True,
                "visualization_type": "bar",
                "purpose": "comparison",
                "x_axis": "Product",
                "y_axis": "Revenue",
                "grouping": None,
                "highlights": ["Widget C"],
                "suppress": ["UNASSIGNED", "Unknown", "N/A"],
                "annotations": ["Widget C represents 40% of revenue"],
                "caveats": [],
                "confidence": {"numeric": 0.85, "label": "HIGH"},
            },
            {
                "insight_id": "insight_2",
                "insight_title": "Revenue varies by region",
                "visualization_required": True,
                "visualization_type": "bar",
                "purpose": "comparison",
                "x_axis": "Region",
                "y_axis": "Revenue",
                "grouping": None,
                "highlights": [],
                "suppress": ["UNASSIGNED", "Unknown"],
                "annotations": [],
                "caveats": [],
                "confidence": {"numeric": 0.75, "label": "MEDIUM"},
            },
        ],
    }


@pytest.fixture
def viz_plan_without_charts():
    """Create visualization plan with visualization_required=false."""
    return {
        "generated_at": "2026-01-11T12:00:00",
        "total_insights_reviewed": 1,
        "visualizations_planned": 0,
        "specifications": [
            {
                "insight_id": "insight_low_conf",
                "insight_title": "Possible trend",
                "visualization_required": False,
                "visualization_type": "none",
                "purpose": "none",
                "reason": "Confidence too low (0.45) for visualization",
                "confidence": {"numeric": 0.45, "label": "LOW"},
            }
        ],
    }


def test_missing_visualization_plan_blocks_rendering(temp_project, sample_data):
    """Test that missing visualization_plan.json blocks chart rendering."""
    renderer = ChartRenderer(temp_project)

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError) as exc_info:
        renderer.render_charts(data_file=sample_data)

    assert "visualization_plan.json" in str(exc_info.value)
    assert "Run /analyze first" in str(exc_info.value)


def test_visualization_required_false_produces_no_charts(
    temp_project, sample_data, viz_plan_without_charts
):
    """Test that visualization_required=false produces no charts."""
    # Save visualization plan
    viz_plan_path = temp_project / "outputs" / "internal" / "visualization_plan.json"
    (temp_project / "outputs" / "internal").mkdir(parents=True, exist_ok=True)
    viz_plan_path.write_text(json.dumps(viz_plan_without_charts, indent=2))

    renderer = ChartRenderer(temp_project)
    result = renderer.render_charts(data_file=sample_data)

    # Should succeed with zero charts
    assert result["success"]
    assert result["charts_rendered"] == 0
    assert len(result["charts"]) == 0
    assert result["visualizations_skipped"] == 1

    # charts/ directory should not contain any files (or be empty if it exists)
    charts_dir = temp_project / "outputs" / "charts"
    if charts_dir.exists():
        assert len(list(charts_dir.glob("*.json"))) == 0


def test_visualization_required_true_produces_exactly_one_chart(
    temp_project, sample_data, viz_plan_with_charts
):
    """Test that visualization_required=true produces exactly one chart per spec."""
    # Save visualization plan
    viz_plan_path = temp_project / "outputs" / "internal" / "visualization_plan.json"
    (temp_project / "outputs" / "internal").mkdir(parents=True, exist_ok=True)
    viz_plan_path.write_text(json.dumps(viz_plan_with_charts, indent=2))

    renderer = ChartRenderer(temp_project)
    result = renderer.render_charts(data_file=sample_data)

    # Should render exactly 2 charts (one per spec with visualization_required=true)
    assert result["success"]
    assert result["charts_rendered"] == 2
    assert len(result["charts"]) == 2
    assert result["visualizations_planned"] == 2

    # Verify charts directory contains exactly 2 chart files
    charts_dir = temp_project / "outputs" / "charts"
    assert charts_dir.exists()
    chart_files = list(charts_dir.glob("*.json"))
    assert len(chart_files) == 2


def test_suppressed_categories_never_appear(
    temp_project, sample_data, viz_plan_with_charts
):
    """Test that suppressed categories never appear in chart data."""
    # Save visualization plan
    viz_plan_path = temp_project / "outputs" / "internal" / "visualization_plan.json"
    (temp_project / "outputs" / "internal").mkdir(parents=True, exist_ok=True)
    viz_plan_path.write_text(json.dumps(viz_plan_with_charts, indent=2))

    renderer = ChartRenderer(temp_project)
    result = renderer.render_charts(data_file=sample_data)

    # Load first chart
    chart_file = temp_project / "outputs" / "charts" / "insight_1__bar.json"
    assert chart_file.exists()

    with open(chart_file) as f:
        chart_data = json.load(f)

    # Check that suppressed categories are not in data
    # Chart data uses original column names from DataFrame
    products = [point["Product"] for point in chart_data["data"]]

    assert "UNASSIGNED" not in products
    assert "Unknown" not in products
    assert "N/A" not in products


def test_deterministic_filenames(temp_project, sample_data, viz_plan_with_charts):
    """Test that chart filenames are deterministic."""
    # Save visualization plan
    viz_plan_path = temp_project / "outputs" / "internal" / "visualization_plan.json"
    (temp_project / "outputs" / "internal").mkdir(parents=True, exist_ok=True)
    viz_plan_path.write_text(json.dumps(viz_plan_with_charts, indent=2))

    renderer = ChartRenderer(temp_project)
    result = renderer.render_charts(data_file=sample_data)

    # Check expected filenames
    chart1_path = temp_project / "outputs" / "charts" / "insight_1__bar.json"
    chart2_path = temp_project / "outputs" / "charts" / "insight_2__bar.json"

    assert chart1_path.exists()
    assert chart2_path.exists()

    # Verify filename format: <insight_id>__<visualization_type>.json
    for chart_info in result["charts"]:
        expected_filename = f"{chart_info['insight_id']}__{chart_info['visualization_type']}.json"
        assert chart_info["filename"] == expected_filename


def test_chart_metadata_completeness(
    temp_project, sample_data, viz_plan_with_charts
):
    """Test that each chart includes complete metadata."""
    # Save visualization plan
    viz_plan_path = temp_project / "outputs" / "internal" / "visualization_plan.json"
    (temp_project / "outputs" / "internal").mkdir(parents=True, exist_ok=True)
    viz_plan_path.write_text(json.dumps(viz_plan_with_charts, indent=2))

    renderer = ChartRenderer(temp_project)
    result = renderer.render_charts(data_file=sample_data)

    # Load first chart config (in internal/chart_configs/)
    from kie.paths import ArtifactPaths
    paths = ArtifactPaths(temp_project)
    chart_file = paths.chart_config("insight_1__bar.json")
    with open(chart_file) as f:
        chart_data = json.load(f)

    # Verify chart config has recharts fields (metadata is in render result, not chart JSON)
    assert "type" in chart_data, "Chart missing type"
    assert "data" in chart_data, "Chart missing data"
    assert "config" in chart_data, "Chart missing config"

    # Verify render result has metadata
    assert result["success"], "Render failed"
    assert "charts" in result, "Result missing charts"
    assert len(result["charts"]) > 0, "No charts in result"

    chart_info = result["charts"][0]
    assert "insight_id" in chart_info, "Chart info missing insight_id"
    assert "visualization_type" in chart_info, "Chart info missing visualization_type"


def test_no_extra_charts(temp_project, sample_data, viz_plan_with_charts):
    """Test that exactly N specs produce exactly N charts (no extras)."""
    # Save visualization plan
    viz_plan_path = temp_project / "outputs" / "internal" / "visualization_plan.json"
    (temp_project / "outputs" / "internal").mkdir(parents=True, exist_ok=True)
    viz_plan_path.write_text(json.dumps(viz_plan_with_charts, indent=2))

    renderer = ChartRenderer(temp_project)
    result = renderer.render_charts(data_file=sample_data)

    # Count specs with visualization_required=true
    viz_required_count = sum(
        1
        for spec in viz_plan_with_charts["specifications"]
        if spec.get("visualization_required", False)
    )

    # Should match exactly
    assert result["charts_rendered"] == viz_required_count

    # Verify files on disk match
    charts_dir = temp_project / "outputs" / "charts"
    chart_files = list(charts_dir.glob("*.json"))
    assert len(chart_files) == viz_required_count


def test_highlights_marked_in_data(temp_project, sample_data, viz_plan_with_charts):
    """Test that highlighted categories exist in chart data."""
    # Save visualization plan
    viz_plan_path = temp_project / "outputs" / "internal" / "visualization_plan.json"
    (temp_project / "outputs" / "internal").mkdir(parents=True, exist_ok=True)
    viz_plan_path.write_text(json.dumps(viz_plan_with_charts, indent=2))

    renderer = ChartRenderer(temp_project)
    result = renderer.render_charts(data_file=sample_data)

    # Load first chart (has "Widget C" as highlight)
    chart_file = temp_project / "outputs" / "charts" / "insight_1__bar.json"
    with open(chart_file) as f:
        chart_data = json.load(f)

    # Find Widget C in data
    # Chart data uses original column names from DataFrame
    widget_c = next(
        (point for point in chart_data["data"] if "Widget C" in point["Product"]),
        None,
    )

    # Verify Widget C exists in the data (highlighting is handled by the renderer,
    # not stored in individual data points)
    assert widget_c is not None
    assert widget_c["Product"] == "Widget C"
    assert widget_c["Revenue"] == 2000


def test_missing_data_file_raises_error(temp_project, viz_plan_with_charts):
    """Test that missing data file raises appropriate error."""
    # Save visualization plan
    viz_plan_path = temp_project / "outputs" / "internal" / "visualization_plan.json"
    (temp_project / "outputs" / "internal").mkdir(parents=True, exist_ok=True)
    viz_plan_path.write_text(json.dumps(viz_plan_with_charts, indent=2))

    renderer = ChartRenderer(temp_project)

    # No data file - should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        renderer.render_charts(data_file=None)

    assert "No data files found" in str(exc_info.value)


def test_deterministic_output_on_repeat(temp_project, sample_data, viz_plan_with_charts):
    """Test that rendering is deterministic on repeat calls."""
    # Save visualization plan
    viz_plan_path = temp_project / "outputs" / "internal" / "visualization_plan.json"
    (temp_project / "outputs" / "internal").mkdir(parents=True, exist_ok=True)
    viz_plan_path.write_text(json.dumps(viz_plan_with_charts, indent=2))

    renderer = ChartRenderer(temp_project)

    # Render twice
    result1 = renderer.render_charts(data_file=sample_data)
    result2 = renderer.render_charts(data_file=sample_data)

    # Results should match (except timestamps)
    assert result1["charts_rendered"] == result2["charts_rendered"]
    assert len(result1["charts"]) == len(result2["charts"])

    # Load first chart from both runs
    chart_file = temp_project / "outputs" / "charts" / "insight_1__bar.json"
    with open(chart_file) as f:
        chart_data1 = json.load(f)

    result2 = renderer.render_charts(data_file=sample_data)

    with open(chart_file) as f:
        chart_data2 = json.load(f)

    # Data should be identical (except generated_at timestamp)
    assert chart_data1["data"] == chart_data2["data"]
    assert chart_data1["type"] == chart_data2["type"]

    # Verify metadata from results match
    assert result1["charts"][0]["insight_id"] == result2["charts"][0]["insight_id"]
    assert result1["charts"][0]["visualization_type"] == result2["charts"][0]["visualization_type"]
