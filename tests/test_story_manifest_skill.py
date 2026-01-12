"""
Unit tests for Story Manifest Skill.

Tests that the skill correctly creates canonical story representation
from judged artifacts.
"""

import json
from pathlib import Path
import pytest
import yaml

from kie.skills.story_manifest import StoryManifestSkill
from kie.skills.base import SkillContext


def test_story_manifest_requires_insight_triage(tmp_path):
    """Test that story manifest fails without insight_triage.json."""
    # Create project structure
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create all required inputs EXCEPT insight_triage
    (outputs_dir / "visual_storyboard.json").write_text(
        json.dumps({"elements": []})
    )
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "executive_summary.md").write_text("# Summary\n")
    (project_state_dir / "intent.yaml").write_text("objective: Test\n")

    # Run skill
    skill = StoryManifestSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    # Should fail with error
    assert not result.success
    assert any("insight_triage" in str(e).lower() for e in result.errors)


def test_story_manifest_requires_visual_storyboard(tmp_path):
    """Test that story manifest fails without visual_storyboard.json."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create all required inputs EXCEPT visual_storyboard
    (outputs_dir / "insight_triage.json").write_text(
        json.dumps({"judged_insights": []})
    )
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "executive_summary.md").write_text("# Summary\n")
    (project_state_dir / "intent.yaml").write_text("objective: Test\n")

    # Run skill
    skill = StoryManifestSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    # Should fail
    assert not result.success
    assert any("visual_storyboard" in str(e).lower() for e in result.errors)


def test_story_manifest_requires_charts_exist(tmp_path):
    """Test that story manifest fails if chart_ref doesn't exist."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create storyboard with chart_ref that doesn't exist
    storyboard = {
        "elements": [
            {
                "section": "Context & Baseline",
                "chart_ref": "missing_chart.json",
                "role": "baseline",
                "transition_text": "Test",
                "emphasis": "Test",
                "caveats": [],
                "visualization_type": "bar",
                "insight_title": "Test",
                "insight_id": "test-1",
            }
        ]
    }

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps({"judged_insights": []})
    )
    (outputs_dir / "visual_storyboard.json").write_text(json.dumps(storyboard))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "executive_summary.md").write_text("# Summary\n")
    (project_state_dir / "intent.yaml").write_text("objective: Test\n")

    # Run skill
    skill = StoryManifestSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    # Should fail with missing chart error
    assert not result.success
    assert any("missing_chart.json" in str(e) for e in result.errors)


def test_story_manifest_deterministic_output(tmp_path):
    """Test that story manifest produces deterministic output for same inputs."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create chart
    chart_file = charts_dir / "test_chart.json"
    chart_file.write_text(
        json.dumps(
            {
                "type": "bar",
                "data": [{"x": "A", "y": 10}],
                "config": {"xAxis": {"dataKey": "x"}, "bars": [{"dataKey": "y"}]},
            }
        )
    )

    # Create storyboard
    storyboard = {
        "elements": [
            {
                "section": "Context & Baseline",
                "chart_ref": "test_chart.json",
                "role": "baseline",
                "transition_text": "Test narrative",
                "emphasis": "Key point",
                "caveats": ["Caveat 1"],
                "visualization_type": "bar",
                "insight_title": "Test Insight",
                "insight_id": "test-1",
            }
        ]
    }

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(
            {
                "judged_insights": [
                    {
                        "insight_id": "test-1",
                        "headline": "Test Insight",
                        "confidence": "high",
                    }
                ]
            }
        )
    )
    (outputs_dir / "visual_storyboard.json").write_text(json.dumps(storyboard))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "executive_summary.md").write_text("# Summary\n- Bullet 1\n")
    (project_state_dir / "intent.yaml").write_text("objective: Test objective\n")

    # Run skill twice
    skill = StoryManifestSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={"project_name": "Test Project", "execution_mode": "rails"},
    )

    result1 = skill.execute(context)
    assert result1.success

    # Load first manifest
    manifest1_path = outputs_dir / "story_manifest.json"
    with open(manifest1_path) as f:
        manifest1 = json.load(f)

    # Delete manifest
    manifest1_path.unlink()
    (outputs_dir / "story_manifest.md").unlink()

    # Run again
    result2 = skill.execute(context)
    assert result2.success

    # Load second manifest
    with open(manifest1_path) as f:
        manifest2 = json.load(f)

    # Ignore story_id and generated_at (will be different)
    manifest1.pop("story_id")
    manifest1.pop("generated_at")
    manifest2.pop("story_id")
    manifest2.pop("generated_at")

    # Also ignore section_ids (UUIDs)
    for section in manifest1["sections"]:
        section.pop("section_id", None)
    for section in manifest2["sections"]:
        section.pop("section_id", None)

    # Rest should be identical
    assert manifest1 == manifest2


def test_story_manifest_section_order(tmp_path):
    """Test that story manifest maintains correct section order."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create charts
    for i in range(3):
        chart_file = charts_dir / f"chart{i}.json"
        chart_file.write_text(
            json.dumps(
                {
                    "type": "bar",
                    "data": [{"x": "A", "y": i}],
                    "config": {
                        "xAxis": {"dataKey": "x"},
                        "bars": [{"dataKey": "y"}],
                    },
                }
            )
        )

    # Create storyboard with multiple sections
    storyboard = {
        "elements": [
            {
                "section": "Context & Baseline",
                "chart_ref": "chart0.json",
                "role": "baseline",
                "transition_text": "Baseline narrative",
                "emphasis": "Key point 1",
                "caveats": [],
                "visualization_type": "bar",
                "insight_title": "Baseline Insight",
                "insight_id": "test-1",
            },
            {
                "section": "Dominance & Comparison",
                "chart_ref": "chart1.json",
                "role": "comparison",
                "transition_text": "Comparison narrative",
                "emphasis": "Key point 2",
                "caveats": [],
                "visualization_type": "bar",
                "insight_title": "Comparison Insight",
                "insight_id": "test-2",
            },
            {
                "section": "Risk, Outliers & Caveats",
                "chart_ref": "chart2.json",
                "role": "risk",
                "transition_text": "Risk narrative",
                "emphasis": "Key point 3",
                "caveats": ["Important caveat"],
                "visualization_type": "bar",
                "insight_title": "Risk Insight",
                "insight_id": "test-3",
            },
        ]
    }

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps({"judged_insights": []})
    )
    (outputs_dir / "visual_storyboard.json").write_text(json.dumps(storyboard))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "executive_summary.md").write_text("# Summary\n- Finding 1\n")
    (project_state_dir / "intent.yaml").write_text("objective: Test objective\n")

    # Run skill
    skill = StoryManifestSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={"project_name": "Test", "execution_mode": "rails"},
    )

    result = skill.execute(context)
    assert result.success

    # Load manifest
    manifest_path = outputs_dir / "story_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    # Check section order (Executive Summary first, then canonical order)
    section_titles = [s["title"] for s in manifest["sections"]]

    # Should start with Executive Summary
    assert section_titles[0] == "Executive Summary"

    # Rest should follow canonical order
    expected_order = [
        "Context & Baseline",
        "Dominance & Comparison",
        "Risk, Outliers & Caveats",
    ]

    for title in expected_order:
        assert title in section_titles

    # Check that they appear in order
    indices = [section_titles.index(title) for title in expected_order]
    assert indices == sorted(indices), "Sections not in canonical order"


def test_story_manifest_includes_actionability_annotations(tmp_path):
    """Test that story manifest includes actionability annotations from actionability_scores.json."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create chart
    chart_file = charts_dir / "test_chart.json"
    chart_file.write_text(
        json.dumps(
            {
                "type": "bar",
                "data": [{"x": "A", "y": 10}],
                "config": {"xAxis": {"dataKey": "x"}, "bars": [{"dataKey": "y"}]},
            }
        )
    )

    # Create actionability scores with decision_enabling insight
    actionability_scores = {
        "insights": [
            {
                "insight_id": "test-1",
                "title": "Critical Finding",
                "actionability": "decision_enabling",
                "confidence": 0.85,
                "severity": "Key",
            }
        ],
        "summary": {
            "decision_enabling_count": 1,
            "directional_count": 0,
            "informational_count": 0,
        },
    }
    (outputs_dir / "actionability_scores.json").write_text(
        json.dumps(actionability_scores)
    )

    # Create storyboard
    storyboard = {
        "elements": [
            {
                "section": "Context & Baseline",
                "chart_ref": "test_chart.json",
                "role": "baseline",
                "transition_text": "Test narrative",
                "emphasis": "Key point",
                "caveats": [],
                "visualization_type": "bar",
                "insight_title": "Critical Finding",
                "insight_id": "test-1",
            }
        ]
    }

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(
            {
                "judged_insights": [
                    {
                        "insight_id": "test-1",
                        "headline": "Critical Finding",
                        "confidence": "high",
                        "severity": "Key",
                    }
                ]
            }
        )
    )
    (outputs_dir / "visual_storyboard.json").write_text(json.dumps(storyboard))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps({}))
    (outputs_dir / "executive_summary.md").write_text("# Summary\\n- Finding 1\\n")
    (project_state_dir / "intent.yaml").write_text("objective: Test objective\\n")

    # Run skill
    skill = StoryManifestSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={"project_name": "Test Project", "execution_mode": "rails"},
    )

    result = skill.execute(context)
    assert result.success

    # Load manifest
    manifest_path = outputs_dir / "story_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    # Check that sections have actionability_level
    sections = manifest.get("sections", [])
    assert len(sections) > 0

    for section in sections:
        assert "actionability_level" in section
        assert section["actionability_level"] in [
            "decision_enabling",
            "directional",
            "informational",
        ]

    # Check that evidence_index includes actionability
    for section in sections:
        for evidence in section.get("evidence_index", []):
            if evidence.get("insight_id") == "test-1":
                assert "actionability" in evidence
                assert evidence["actionability"] == "decision_enabling"

    # Verify that decision_enabling section comes first (after Executive Summary)
    non_exec_sections = [s for s in sections if s["title"] != "Executive Summary"]
    if non_exec_sections:
        first_section = non_exec_sections[0]
        assert first_section["actionability_level"] == "decision_enabling"
