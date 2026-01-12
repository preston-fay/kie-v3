"""
Unit tests for Visual Quality Control Skill.

Tests that the skill correctly evaluates rendered charts for consultant-grade quality.
"""

import json
from pathlib import Path

import pytest

from kie.skills.visual_qc import VisualQCSkill
from kie.skills.base import SkillContext


def test_visual_qc_requires_visualization_plan(tmp_path):
    """Test that visual QC fails without visualization_plan.json."""
    # Create project structure
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create story_manifest but NO visualization_plan
    (outputs_dir / "story_manifest.json").write_text(json.dumps({"sections": []}))

    # Run skill
    skill = VisualQCSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    # Should fail with error
    assert not result.success
    assert any("visualization_plan" in str(e).lower() for e in result.errors)


def test_visual_qc_requires_story_manifest(tmp_path):
    """Test that visual QC works without story_manifest.json (optional dependency)."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create visualization_plan but NO story_manifest
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))

    # Run skill
    skill = VisualQCSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    # Should succeed with warning (story_manifest is optional)
    assert result.success
    assert any("story_manifest.json not found" in str(w) for w in result.warnings)


def test_visual_qc_clean_chart_client_ready(tmp_path):
    """Test that a clean chart is classified as client_ready."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create clean chart with proper labels and good value range (no truncation)
    chart_data = {
        "type": "bar",
        "data": [
            {"region": "North", "revenue": 1200},
            {"region": "South", "revenue": 300},  # Wide range to avoid truncation
            {"region": "East", "revenue": 800},
            {"region": "West", "revenue": 500},
        ],
        "config": {
            "xAxis": {"dataKey": "region", "label": "Region"},
            "yAxis": {"label": "Revenue ($K)"},
            "bars": [{"dataKey": "revenue", "fill": "#7823DC"}],
        },
    }
    (charts_dir / "clean_chart.json").write_text(json.dumps(chart_data))

    # Create required inputs
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "story_manifest.json").write_text(json.dumps({"sections": []}))

    # Run skill
    skill = VisualQCSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    # Should succeed
    assert result.success

    # Load QC report
    qc_path = outputs_dir / "visual_qc.json"
    assert qc_path.exists()

    with open(qc_path) as f:
        qc_data = json.load(f)

    # Check classification
    charts = qc_data.get("charts", [])
    assert len(charts) == 1
    assert charts[0]["visual_quality"] == "client_ready"
    assert len(charts[0]["issues"]) == 0


def test_visual_qc_missing_labels_with_caveats(tmp_path):
    """Test that missing axis labels → client_ready_with_caveats."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create chart WITHOUT axis labels
    chart_data = {
        "type": "bar",
        "data": [
            {"x": "A", "y": 10},
            {"x": "B", "y": 20},
        ],
        "config": {
            "xAxis": {"dataKey": "x"},  # No label
            "yAxis": {},  # No label
            "bars": [{"dataKey": "y"}],
        },
    }
    (charts_dir / "missing_labels.json").write_text(json.dumps(chart_data))

    # Create required inputs
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "story_manifest.json").write_text(json.dumps({"sections": []}))

    # Run skill
    skill = VisualQCSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    assert result.success

    # Check classification
    qc_path = outputs_dir / "visual_qc.json"
    with open(qc_path) as f:
        qc_data = json.load(f)

    charts = qc_data.get("charts", [])
    assert len(charts) == 1
    assert charts[0]["visual_quality"] == "client_ready_with_caveats"
    assert "Missing X-axis label" in charts[0]["issues"]
    assert "Missing Y-axis label" in charts[0]["issues"]


def test_visual_qc_too_many_categories_internal_only(tmp_path):
    """Test that too many categories (>15) → internal_only."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create chart with 20 categories
    data = [{"category": f"Cat{i}", "value": i * 10} for i in range(20)]
    chart_data = {
        "type": "bar",
        "data": data,
        "config": {
            "xAxis": {"dataKey": "category", "label": "Category"},
            "yAxis": {"label": "Value"},
            "bars": [{"dataKey": "value"}],
        },
    }
    (charts_dir / "too_many_cats.json").write_text(json.dumps(chart_data))

    # Create required inputs
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "story_manifest.json").write_text(json.dumps({"sections": []}))

    # Run skill
    skill = VisualQCSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    assert result.success

    # Check classification
    qc_path = outputs_dir / "visual_qc.json"
    with open(qc_path) as f:
        qc_data = json.load(f)

    charts = qc_data.get("charts", [])
    assert len(charts) == 1
    assert charts[0]["visual_quality"] == "internal_only"
    assert any("Too many categories" in issue for issue in charts[0]["issues"])


def test_visual_qc_deterministic_output(tmp_path):
    """Test that visual QC produces deterministic output for same inputs."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create chart
    chart_data = {
        "type": "bar",
        "data": [
            {"x": "A", "y": 10},
            {"x": "B", "y": 20},
        ],
        "config": {
            "xAxis": {"dataKey": "x", "label": "X"},
            "yAxis": {"label": "Y"},
            "bars": [{"dataKey": "y"}],
        },
    }
    (charts_dir / "test_chart.json").write_text(json.dumps(chart_data))

    # Create required inputs
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "story_manifest.json").write_text(json.dumps({"sections": []}))

    # Run skill twice
    skill = VisualQCSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result1 = skill.execute(context)
    assert result1.success

    # Load first result
    qc_path = outputs_dir / "visual_qc.json"
    with open(qc_path) as f:
        qc_data1 = json.load(f)

    # Delete and run again
    qc_path.unlink()
    (outputs_dir / "visual_qc.md").unlink()

    result2 = skill.execute(context)
    assert result2.success

    # Load second result
    with open(qc_path) as f:
        qc_data2 = json.load(f)

    # Compare (should be identical)
    assert qc_data1["charts"] == qc_data2["charts"]
    assert qc_data1["summary"] == qc_data2["summary"]


def test_visual_qc_truncated_axis_detection(tmp_path):
    """Test that truncated axes are detected."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create chart with truncated axis (min > 50% of max)
    chart_data = {
        "type": "bar",
        "data": [
            {"category": "A", "value": 90},
            {"category": "B", "value": 95},
            {"category": "C", "value": 100},
        ],
        "config": {
            "xAxis": {"dataKey": "category", "label": "Category"},
            "yAxis": {"label": "Value"},
            "bars": [{"dataKey": "value"}],
        },
    }
    (charts_dir / "truncated.json").write_text(json.dumps(chart_data))

    # Create required inputs
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "story_manifest.json").write_text(json.dumps({"sections": []}))

    # Run skill
    skill = VisualQCSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    assert result.success

    # Check that truncated axis is detected
    qc_path = outputs_dir / "visual_qc.json"
    with open(qc_path) as f:
        qc_data = json.load(f)

    charts = qc_data.get("charts", [])
    assert len(charts) == 1
    assert any("truncated" in issue.lower() for issue in charts[0]["issues"])


def test_visual_qc_extreme_skew_detection(tmp_path):
    """Test that extreme value skew is detected."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create chart with extreme outlier (one value >> others)
    # Need many small values so outlier doesn't dominate the average
    # With 10 values of 10 and 1 value of 2000:
    # avg = (100 + 2000)/11 = 190.9, need max > 1909, so 2000 > 1909 ✓
    data = [{"category": f"Cat{i}", "value": 10} for i in range(10)]
    data.append({"category": "Outlier", "value": 2000})  # Extreme outlier
    chart_data = {
        "type": "bar",
        "data": data,
        "config": {
            "xAxis": {"dataKey": "category", "label": "Category"},
            "yAxis": {"label": "Value"},
            "bars": [{"dataKey": "value"}],
        },
    }
    (charts_dir / "skewed.json").write_text(json.dumps(chart_data))

    # Create required inputs
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "story_manifest.json").write_text(json.dumps({"sections": []}))

    # Run skill
    skill = VisualQCSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    assert result.success

    # Check that skew is detected
    qc_path = outputs_dir / "visual_qc.json"
    with open(qc_path) as f:
        qc_data = json.load(f)

    charts = qc_data.get("charts", [])
    assert len(charts) == 1
    assert any("skew" in issue.lower() for issue in charts[0]["issues"])


def test_visual_qc_summary_counts(tmp_path):
    """Test that summary counts are correct."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()

    # Create three charts with different quality levels
    # 1. Client ready
    (charts_dir / "chart1.json").write_text(
        json.dumps(
            {
                "type": "bar",
                "data": [{"x": "A", "y": 10}],
                "config": {
                    "xAxis": {"dataKey": "x", "label": "X"},
                    "yAxis": {"label": "Y"},
                    "bars": [{"dataKey": "y"}],
                },
            }
        )
    )

    # 2. With caveats (missing label)
    (charts_dir / "chart2.json").write_text(
        json.dumps(
            {
                "type": "bar",
                "data": [{"x": "A", "y": 10}],
                "config": {
                    "xAxis": {"dataKey": "x"},  # No label
                    "yAxis": {"label": "Y"},
                    "bars": [{"dataKey": "y"}],
                },
            }
        )
    )

    # 3. Internal only (too many categories)
    data = [{"x": f"Cat{i}", "y": i} for i in range(20)]
    (charts_dir / "chart3.json").write_text(
        json.dumps(
            {
                "type": "bar",
                "data": data,
                "config": {
                    "xAxis": {"dataKey": "x", "label": "X"},
                    "yAxis": {"label": "Y"},
                    "bars": [{"dataKey": "y"}],
                },
            }
        )
    )

    # Create required inputs
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "story_manifest.json").write_text(json.dumps({"sections": []}))

    # Run skill
    skill = VisualQCSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    assert result.success

    # Check summary counts
    qc_path = outputs_dir / "visual_qc.json"
    with open(qc_path) as f:
        qc_data = json.load(f)

    summary = qc_data.get("summary", {})
    assert summary["client_ready"] == 1
    assert summary["with_caveats"] == 1
    assert summary["internal_only"] == 1
