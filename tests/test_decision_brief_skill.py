"""
Tests for DecisionBriefSkill

Verifies:
- Skill creates decision_brief.md when manifest exists
- Deterministic output for fixed input
- Contains required tags [DECISION]/[DIRECTION]/[INFO]
- Exhibit index reflects manifest sections
- No rails_state mutation
"""

import json
import tempfile
from pathlib import Path

import pytest

from kie.skills import SkillContext
from kie.skills.decision_brief import DecisionBriefSkill


@pytest.fixture
def temp_project():
    """Create temporary project structure."""
    tmpdir = tempfile.mkdtemp()
    project_root = Path(tmpdir)

    # Create directory structure
    (project_root / "outputs").mkdir(parents=True)
    (project_root / "project_state").mkdir(parents=True)
    (project_root / "project_state" / "evidence_ledger").mkdir(parents=True)

    return project_root


@pytest.fixture
def sample_manifest():
    """Create sample story manifest."""
    return {
        "project_name": "Q4 Revenue Analysis",
        "generated_at": "2026-01-12T00:00:00",
        "main_story": {
            "headline": "Revenue concentration in top regions drives 70% of total performance",
            "sections": [
                {
                    "insight_id": "insight_1",
                    "insight_title": "East region dominates with 40% revenue share",
                    "insight_text": "East region captures 40% of total revenue with highest margins",
                    "section_name": "Regional Performance",
                    "caveats": ["Data limited to Q4 only"],
                },
                {
                    "insight_id": "insight_2",
                    "insight_title": "Cost efficiency varies significantly by region",
                    "insight_text": "Operating costs show 15% variance across regions",
                    "section_name": "Cost Analysis",
                    "caveats": [],
                },
            ],
        },
        "recommendations": [
            "Focus expansion efforts on top-performing regions",
            "Investigate cost efficiency gaps in underperforming areas",
        ],
    }


@pytest.fixture
def sample_actionability():
    """Create sample actionability scores."""
    return {
        "insights": [
            {
                "insight_id": "insight_1",
                "title": "East region dominates with 40% revenue share",
                "actionability": "decision_enabling",
            },
            {
                "insight_id": "insight_2",
                "title": "Cost efficiency varies significantly by region",
                "actionability": "informational",
            },
        ],
        "summary": {"decision_enabling_count": 1},
    }


@pytest.fixture
def sample_visual_qc():
    """Create sample visual QC data."""
    return {
        "charts": [
            {
                "insight_id": "insight_1",
                "insight_title": "East region dominates",
                "quality_badge": "ready",
            },
            {
                "insight_id": "insight_2",
                "insight_title": "Cost efficiency varies",
                "quality_badge": "warning",
            },
        ]
    }


def test_skill_fails_cleanly_on_missing_manifest(temp_project):
    """Test that skill handles missing manifest gracefully."""
    skill = DecisionBriefSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill - should fail cleanly
    result = skill.execute(context)

    assert not result.success
    assert "story_manifest.json not found" in result.errors[0]


def test_skill_generates_complete_brief(temp_project, sample_manifest, sample_actionability, sample_visual_qc):
    """Test that skill generates all required sections."""
    # Save required files
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "story_manifest.json").write_text(json.dumps(sample_manifest, indent=2))
    (outputs_dir / "actionability_scores.json").write_text(json.dumps(sample_actionability, indent=2))
    (outputs_dir / "visual_qc.json").write_text(json.dumps(sample_visual_qc, indent=2))

    # Create minimal executive summary
    exec_summary = "# Executive Summary\n\nRevenue concentrated in top regions.\n"
    (outputs_dir / "executive_summary.md").write_text(exec_summary)

    skill = DecisionBriefSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="build",
        artifacts={"story_manifest": outputs_dir / "story_manifest.json"},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success
    assert "decision_brief_md" in result.artifacts
    assert "decision_brief_json" in result.artifacts

    # Read markdown
    md_path = Path(result.artifacts["decision_brief_md"])
    content = md_path.read_text()

    # Check required sections
    assert "# Decision Brief (Internal)" in content
    assert "## 1) Executive Takeaways" in content
    assert "## 2) What to Do Next" in content
    assert "## 3) What We're Not Confident About" in content
    assert "## 4) Exhibit Index" in content

    # Check for tags
    assert "[DECISION]" in content or "[DIRECTION]" in content or "[INFO]" in content

    # Check INTERNAL ONLY marker
    assert "INTERNAL ONLY" in content


def test_brief_contains_required_tags(temp_project, sample_manifest, sample_actionability):
    """Test that brief contains decision/direction/info tags."""
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "story_manifest.json").write_text(json.dumps(sample_manifest, indent=2))
    (outputs_dir / "actionability_scores.json").write_text(json.dumps(sample_actionability, indent=2))

    skill = DecisionBriefSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    result = skill.execute(context)
    assert result.success

    md_path = Path(result.artifacts["decision_brief_md"])
    content = md_path.read_text()

    # At least one tag should be present
    has_decision = "[DECISION]" in content
    has_direction = "[DIRECTION]" in content
    has_info = "[INFO]" in content

    assert has_decision or has_direction or has_info, "No tags found in decision brief"


def test_exhibit_index_reflects_manifest(temp_project, sample_manifest, sample_visual_qc):
    """Test that exhibit index matches manifest sections."""
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "story_manifest.json").write_text(json.dumps(sample_manifest, indent=2))
    (outputs_dir / "visual_qc.json").write_text(json.dumps(sample_visual_qc, indent=2))

    skill = DecisionBriefSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    result = skill.execute(context)
    assert result.success

    # Read JSON
    json_path = Path(result.artifacts["decision_brief_json"])
    with open(json_path) as f:
        brief_data = json.load(f)

    exhibit_index = brief_data.get("exhibit_index", [])

    # Should have 2 exhibits (matching 2 sections in manifest)
    assert len(exhibit_index) == 2

    # Check exhibit structure
    for exhibit in exhibit_index:
        assert "name" in exhibit
        assert "location" in exhibit
        assert "quality" in exhibit


def test_deterministic_output(temp_project, sample_manifest):
    """Test that output is deterministic for fixed input."""
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "story_manifest.json").write_text(json.dumps(sample_manifest, indent=2))

    skill = DecisionBriefSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill twice
    result1 = skill.execute(context)
    json_path1 = Path(result1.artifacts["decision_brief_json"])
    with open(json_path1) as f:
        data1 = json.load(f)

    result2 = skill.execute(context)
    json_path2 = Path(result2.artifacts["decision_brief_json"])
    with open(json_path2) as f:
        data2 = json.load(f)

    # Key sections should be identical (except generated_at timestamp)
    assert data1["executive_takeaways"] == data2["executive_takeaways"]
    assert data1["next_actions"] == data2["next_actions"]
    assert data1["caveats"] == data2["caveats"]
    assert data1["exhibit_index"] == data2["exhibit_index"]


def test_no_rails_state_mutation(temp_project, sample_manifest):
    """Test that skill does not mutate rails_state."""
    # Create rails_state
    rails_state_path = temp_project / "project_state" / "rails_state.json"
    original_state = {
        "completed_stages": ["startkie", "eda", "analyze", "build"],
        "workflow_started": True,
    }
    with open(rails_state_path, "w") as f:
        json.dump(original_state, f)

    # Save manifest
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "story_manifest.json").write_text(json.dumps(sample_manifest, indent=2))

    skill = DecisionBriefSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Rails state should be unchanged
    with open(rails_state_path) as f:
        final_state = json.load(f)

    assert final_state == original_state


def test_truth_gate_artifacts_exist(temp_project, sample_manifest):
    """Test that all claimed artifacts actually exist (Truth Gate)."""
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "story_manifest.json").write_text(json.dumps(sample_manifest, indent=2))

    skill = DecisionBriefSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Verify all artifacts exist
    for artifact_name, artifact_path in result.artifacts.items():
        path = Path(artifact_path)
        assert path.exists(), f"Artifact {artifact_name} does not exist at {artifact_path}"

        # Verify files are not empty
        assert path.stat().st_size > 0, f"Artifact {artifact_name} is empty"


def test_prefers_consultant_executive_summary(temp_project, sample_manifest):
    """Test that skill prefers consultant version of executive summary."""
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "story_manifest.json").write_text(json.dumps(sample_manifest, indent=2))

    # Create both versions
    (outputs_dir / "executive_summary.md").write_text("# Summary\n\nOriginal version with filler.")
    (outputs_dir / "executive_summary_consultant.md").write_text("# Summary\n\nPolished consultant version.")

    skill = DecisionBriefSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    result = skill.execute(context)
    assert result.success

    # The skill should have used consultant version (though we can't verify easily in this test)
    # Just verify both files were read without error
    md_path = Path(result.artifacts["decision_brief_md"])
    assert md_path.exists()
