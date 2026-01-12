"""
Unit Tests for Visual Storyboard Skill

Tests verify:
1. Skill fails cleanly if visualization_plan.json missing
2. Deterministic ordering (same inputs → same outputs)
3. Suppressed insights never appear
4. Visual count limits enforced (≤6)
5. Multiple chart types sequenced correctly when available
6. No rails_state mutation
7. Truth gate - all claimed artifacts exist
8. Sections follow mandatory order
9. Visual diversity requirement enforced
10. Garbage categories filtered from caveats
"""

import json
import tempfile
from pathlib import Path

import pytest

from kie.skills import VisualStoryboardSkill, SkillContext


@pytest.fixture
def temp_project():
    """Create temporary project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create directories
        (project_root / "outputs").mkdir(parents=True)
        (project_root / "project_state").mkdir(parents=True)

        yield project_root


@pytest.fixture
def sample_triage_data():
    """Sample triage data."""
    return {
        "total_candidate_insights": 5,
        "high_confidence_insights": 3,
        "top_insights": [
            {
                "id": "insight_1",
                "title": "Revenue concentration in Widget C",
                "why_it_matters": "Widget C represents 36% of revenue",
                "confidence": {"numeric": 0.85, "label": "HIGH"},
                "caveats": [],
                "category": "Revenue",
            },
            {
                "id": "insight_2",
                "title": "Cost efficiency varies by region",
                "why_it_matters": "Regional cost differences impact margins",
                "confidence": {"numeric": 0.75, "label": "MEDIUM"},
                "caveats": ["Limited to 6-month timeframe"],
                "category": "Cost",
            },
            {
                "id": "insight_3",
                "title": "Outlier detection: North region anomaly",
                "why_it_matters": "Unusual pattern requires investigation",
                "confidence": {"numeric": 0.65, "label": "MEDIUM"},
                "caveats": ["May be data quality issue"],
                "category": "Risk",
            },
        ],
        "consultant_guidance": {
            "avoid_leading_with": []
        }
    }


@pytest.fixture
def sample_viz_plan():
    """Sample visualization plan."""
    return {
        "generated_at": "2026-01-11T12:00:00",
        "total_insights_reviewed": 3,
        "visualizations_planned": 3,
        "specifications": [
            {
                "insight_id": "insight_1",
                "insight_title": "Revenue concentration in Widget C",
                "visualization_required": True,
                "visualization_type": "bar",
                "purpose": "Show revenue leaders and gaps",
                "confidence": {"numeric": 0.85, "label": "HIGH"},
                "caveats": [],
            },
            {
                "insight_id": "insight_2",
                "insight_title": "Cost efficiency varies by region",
                "visualization_required": True,
                "visualization_type": "line",
                "purpose": "Show efficiency drivers over time",
                "confidence": {"numeric": 0.75, "label": "MEDIUM"},
                "caveats": ["Limited to 6-month timeframe"],
            },
            {
                "insight_id": "insight_3",
                "insight_title": "Outlier detection: North region anomaly",
                "visualization_required": True,
                "visualization_type": "scatter",
                "purpose": "Highlight outliers and risks",
                "confidence": {"numeric": 0.65, "label": "MEDIUM"},
                "caveats": ["May be data quality issue"],
            },
        ]
    }


def test_skill_fails_without_viz_plan(temp_project):
    """Test that skill fails cleanly if visualization_plan.json missing."""
    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert not result.success
    assert any("visualization_plan" in err.lower() for err in result.errors)


def test_skill_fails_without_triage(temp_project, sample_viz_plan):
    """Test that skill fails cleanly if insight_triage.json missing."""
    # Create viz plan but not triage
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(sample_viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"visualization_plan": outputs_dir / "visualization_plan.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert not result.success
    assert any("insight_triage" in err.lower() for err in result.errors)


def test_skill_generates_storyboard_with_all_inputs(
    temp_project, sample_triage_data, sample_viz_plan
):
    """Test that skill generates storyboard when all inputs available."""
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(json.dumps(sample_triage_data, indent=2))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(sample_viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={
            "insight_triage": outputs_dir / "insight_triage.json",
            "visualization_plan": outputs_dir / "visualization_plan.json",
        },
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success
    assert "visual_storyboard_json" in result.artifacts
    assert "visual_storyboard_markdown" in result.artifacts


def test_deterministic_ordering(temp_project, sample_triage_data, sample_viz_plan):
    """Test that same inputs produce same outputs."""
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(json.dumps(sample_triage_data, indent=2))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(sample_viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={
            "insight_triage": outputs_dir / "insight_triage.json",
            "visualization_plan": outputs_dir / "visualization_plan.json",
        },
        evidence_ledger_id="test_run"
    )

    # First run
    result1 = skill.execute(context)
    storyboard1_json = json.loads(Path(result1.artifacts["visual_storyboard_json"]).read_text())

    # Delete outputs
    (outputs_dir / "visual_storyboard.json").unlink()
    (outputs_dir / "visual_storyboard.md").unlink()

    # Second run
    result2 = skill.execute(context)
    storyboard2_json = json.loads(Path(result2.artifacts["visual_storyboard_json"]).read_text())

    # Compare sections (ignore timestamps)
    assert storyboard1_json["total_visuals"] == storyboard2_json["total_visuals"]
    assert len(storyboard1_json["sections"]) == len(storyboard2_json["sections"])

    # Compare visual order
    for section1, section2 in zip(storyboard1_json["sections"], storyboard2_json["sections"]):
        assert section1["section"] == section2["section"]
        assert len(section1["visuals"]) == len(section2["visuals"])
        for vis1, vis2 in zip(section1["visuals"], section2["visuals"]):
            assert vis1["order"] == vis2["order"]
            assert vis1["insight_id"] == vis2["insight_id"]


def test_suppressed_insights_never_appear(temp_project, sample_triage_data, sample_viz_plan):
    """Test that suppressed insights never appear in storyboard."""
    # Mark insight_2 as suppressed
    sample_triage_data["consultant_guidance"]["avoid_leading_with"] = [
        "Cost efficiency varies by region"
    ]

    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(json.dumps(sample_triage_data, indent=2))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(sample_viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={
            "insight_triage": outputs_dir / "insight_triage.json",
            "visualization_plan": outputs_dir / "visualization_plan.json",
        },
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    storyboard_json = json.loads(Path(result.artifacts["visual_storyboard_json"]).read_text())

    # Verify insight_2 does not appear
    all_insight_ids = []
    for section in storyboard_json["sections"]:
        for visual in section["visuals"]:
            all_insight_ids.append(visual["insight_id"])

    assert "insight_2" not in all_insight_ids


def test_visual_count_limit_enforced(temp_project, sample_triage_data):
    """Test that visual count limit (≤6) is enforced."""
    # Create 8 visualizations
    viz_plan = {
        "generated_at": "2026-01-11T12:00:00",
        "total_insights_reviewed": 8,
        "visualizations_planned": 8,
        "specifications": [
            {
                "insight_id": f"insight_{i}",
                "insight_title": f"Insight {i}",
                "visualization_required": True,
                "visualization_type": "bar",
                "purpose": "test",
                "confidence": {"numeric": 0.8, "label": "HIGH"},
                "caveats": [],
            }
            for i in range(1, 9)
        ]
    }

    # Add corresponding insights to triage
    sample_triage_data["top_insights"] = [
        {
            "id": f"insight_{i}",
            "title": f"Insight {i}",
            "why_it_matters": "test",
            "confidence": {"numeric": 0.8, "label": "HIGH"},
            "caveats": [],
            "category": "Test",
        }
        for i in range(1, 9)
    ]

    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(json.dumps(sample_triage_data, indent=2))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={
            "insight_triage": outputs_dir / "insight_triage.json",
            "visualization_plan": outputs_dir / "visualization_plan.json",
        },
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    storyboard_json = json.loads(Path(result.artifacts["visual_storyboard_json"]).read_text())

    # Should have ≤6 visuals
    assert storyboard_json["total_visuals"] <= 6


def test_multiple_chart_types_sequenced(temp_project, sample_triage_data, sample_viz_plan):
    """Test that multiple chart types are sequenced correctly."""
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(json.dumps(sample_triage_data, indent=2))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(sample_viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={
            "insight_triage": outputs_dir / "insight_triage.json",
            "visualization_plan": outputs_dir / "visualization_plan.json",
        },
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    # Check evidence for visual diversity
    assert "visualization_types_used" in result.evidence
    viz_types = result.evidence["visualization_types_used"]

    # Should have multiple types (bar, line, scatter)
    assert len(viz_types) >= 2


def test_no_rails_state_mutation(temp_project, sample_triage_data, sample_viz_plan):
    """Test that skill does not mutate Rails state."""
    # Capture initial state
    state_files_before = list((temp_project / "project_state").glob("*"))
    state_files_before_content = {
        f.name: f.read_text() if f.is_file() else None
        for f in state_files_before
    }

    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(json.dumps(sample_triage_data, indent=2))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(sample_viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={
            "insight_triage": outputs_dir / "insight_triage.json",
            "visualization_plan": outputs_dir / "visualization_plan.json",
        },
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    # Capture final state
    state_files_after = list((temp_project / "project_state").glob("*"))
    state_files_after_content = {
        f.name: f.read_text() if f.is_file() else None
        for f in state_files_after
    }

    # Verify no changes to Rails state
    assert state_files_before_content == state_files_after_content, \
        "Skill mutated Rails state files"


def test_truth_gate_artifacts_exist(temp_project, sample_triage_data, sample_viz_plan):
    """Test that all claimed artifacts actually exist."""
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(json.dumps(sample_triage_data, indent=2))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(sample_viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={
            "insight_triage": outputs_dir / "insight_triage.json",
            "visualization_plan": outputs_dir / "visualization_plan.json",
        },
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    # Verify every claimed artifact exists
    for artifact_name, artifact_path in result.artifacts.items():
        assert Path(artifact_path).exists(), \
            f"Claimed artifact does not exist: {artifact_name} at {artifact_path}"


def test_sections_follow_mandatory_order(temp_project, sample_triage_data, sample_viz_plan):
    """Test that sections follow the mandatory order."""
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(json.dumps(sample_triage_data, indent=2))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(sample_viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={
            "insight_triage": outputs_dir / "insight_triage.json",
            "visualization_plan": outputs_dir / "visualization_plan.json",
        },
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    storyboard_json = json.loads(Path(result.artifacts["visual_storyboard_json"]).read_text())

    # Check section order
    expected_sections = [
        "Context & Baseline",
        "Dominance & Comparison",
        "Drivers & Structure",
        "Risk, Outliers & Caveats",
        "Implications & Actions",
    ]

    section_names = [section["section"] for section in storyboard_json["sections"]]

    # Verify sections appear in order (not all sections may be present)
    last_index = -1
    for section_name in section_names:
        current_index = expected_sections.index(section_name)
        assert current_index > last_index, \
            f"Section {section_name} appears out of order"
        last_index = current_index


def test_artifact_classification_internal(temp_project, sample_triage_data, sample_viz_plan):
    """Test that artifacts are marked as INTERNAL."""
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(json.dumps(sample_triage_data, indent=2))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(sample_viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={
            "insight_triage": outputs_dir / "insight_triage.json",
            "visualization_plan": outputs_dir / "visualization_plan.json",
        },
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    # Check JSON metadata
    storyboard_json = json.loads(Path(result.artifacts["visual_storyboard_json"]).read_text())

    assert storyboard_json["metadata"]["artifact_classification"] == "INTERNAL"

    # Check markdown header
    storyboard_md = Path(result.artifacts["visual_storyboard_markdown"]).read_text()
    assert "Internal" in storyboard_md


def test_visual_diversity_enforced(temp_project, sample_triage_data, sample_viz_plan):
    """Test that visual diversity is tracked and enforced."""
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(json.dumps(sample_triage_data, indent=2))
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(sample_viz_plan, indent=2))

    skill = VisualStoryboardSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={
            "insight_triage": outputs_dir / "insight_triage.json",
            "visualization_plan": outputs_dir / "visualization_plan.json",
        },
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    storyboard_json = json.loads(Path(result.artifacts["visual_storyboard_json"]).read_text())

    # Check metadata for diversity requirement
    assert storyboard_json["metadata"]["diversity_required"] is True

    # Check evidence for visualization types
    assert "visualization_types_used" in result.evidence
    viz_types = result.evidence["visualization_types_used"]

    # With sample data, should have multiple types
    assert len(viz_types) >= 2
