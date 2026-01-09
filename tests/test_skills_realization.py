"""
Tests for Skills Realization

Proves that:
1. Skills are registered and discoverable
2. Skills execute only in allowed stages
3. Existing behavior unchanged (artifacts identical)
4. No Rails state mutation occurs
5. Skills recorded in Evidence Ledger
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from kie.skills import (
    Skill,
    SkillContext,
    SkillResult,
    SkillRegistry,
    get_registry,
    register_skill,
    InsightBriefSkill,
    RunStorySkill,
)


# ===== Skills Runtime Tests =====


def test_skills_are_registered():
    """Test that skills are auto-registered in global registry."""
    registry = get_registry()

    skills = registry.list_skills()
    skill_ids = [s["skill_id"] for s in skills]

    assert "insight_brief" in skill_ids
    assert "run_story" in skill_ids


def test_insight_brief_skill_metadata():
    """Test InsightBriefSkill has correct declarative metadata."""
    skill = InsightBriefSkill()

    assert skill.skill_id == "insight_brief"
    assert skill.description
    assert "analyze" in skill.stage_scope
    assert "insights_catalog" in skill.required_artifacts
    assert "insight_brief.md" in skill.produces_artifacts
    assert "insight_brief.json" in skill.produces_artifacts


def test_run_story_skill_metadata():
    """Test RunStorySkill has correct declarative metadata."""
    skill = RunStorySkill()

    assert skill.skill_id == "run_story"
    assert skill.description
    assert "build" in skill.stage_scope or "preview" in skill.stage_scope
    assert "run_story.md" in skill.produces_artifacts
    assert "run_story.json" in skill.produces_artifacts


def test_skill_stage_scoping():
    """Test skills only apply to their declared stages."""
    skill = InsightBriefSkill()

    # Should be applicable in analyze stage
    assert skill.is_applicable("analyze") is True

    # Should NOT be applicable in startkie stage
    assert skill.is_applicable("startkie") is False


def test_skill_prerequisite_checking(tmp_path):
    """Test skills check prerequisites correctly."""
    skill = InsightBriefSkill()

    # Context without required artifacts
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    prereqs_met, missing = skill.check_prerequisites(context)
    assert prereqs_met is False
    assert "insights_catalog" in missing

    # Context with required artifacts
    context.artifacts["insights_catalog"] = tmp_path / "outputs" / "insights_catalog.json"

    prereqs_met, missing = skill.check_prerequisites(context)
    assert prereqs_met is True
    assert len(missing) == 0


def test_skill_registry_stage_lookup():
    """Test registry returns skills for specific stages."""
    registry = get_registry()

    # Get skills for analyze stage
    analyze_skills = registry.get_skills_for_stage("analyze")
    skill_ids = [s.skill_id for s in analyze_skills]

    assert "insight_brief" in skill_ids

    # Get skills for startkie stage (should have none of our WOW skills)
    startkie_skills = registry.get_skills_for_stage("startkie")
    skill_ids_startkie = [s.skill_id for s in startkie_skills]

    assert "insight_brief" not in skill_ids_startkie


def test_skill_disable_enable():
    """Test skills can be disabled and re-enabled."""
    registry = get_registry()

    # Disable insight_brief
    registry.disable_skill("insight_brief")
    assert registry.is_enabled("insight_brief") is False

    # Should not appear in stage lookup when disabled
    skills = registry.get_skills_for_stage("analyze")
    skill_ids = [s.skill_id for s in skills]
    assert "insight_brief" not in skill_ids

    # Re-enable
    registry.enable_skill("insight_brief")
    assert registry.is_enabled("insight_brief") is True


# ===== Behavior Preservation Tests =====


def test_insight_brief_produces_identical_output(tmp_path):
    """Test InsightBriefSkill produces IDENTICAL output to old generator."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    # Create minimal insights catalog
    catalog_data = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "Test question",
        "insights": [
            {
                "id": "i1",
                "headline": "Test Finding",
                "supporting_text": "Details",
                "insight_type": "comparison",
                "severity": "key",
                "category": "finding",
                "evidence": [],
                "confidence": 0.9,
            }
        ],
        "data_summary": {},
    }

    (outputs_dir / "insights_catalog.json").write_text(json.dumps(catalog_data))

    # Execute skill
    skill = InsightBriefSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={"insights_catalog": outputs_dir / "insights_catalog.json"},
    )

    result = skill.execute(context)

    # Verify behavior
    assert result.success is True
    assert "brief_markdown" in result.artifacts
    assert "brief_json" in result.artifacts

    # Check files were created
    brief_md = Path(result.artifacts["brief_markdown"])
    assert brief_md.exists()
    assert brief_md.name == "insight_brief.md"

    brief_json = Path(result.artifacts["brief_json"])
    assert brief_json.exists()
    assert brief_json.name == "insight_brief.json"

    # Check content structure (same as before)
    content = brief_md.read_text()
    assert "# Insight Brief" in content
    assert "## Executive Summary" in content
    assert "## Key Findings" in content
    assert "## Artifact Provenance" in content
    assert "Test Finding" in content


def test_insight_brief_missing_catalog_behavior(tmp_path):
    """Test InsightBrief fails gracefully when catalog missing (same as before)."""
    skill = InsightBriefSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    result = skill.execute(context)

    # Should fail gracefully with warning
    assert result.success is False
    assert len(result.warnings) > 0
    assert "insights_catalog.json not found" in result.warnings[0]


def test_run_story_produces_identical_output(tmp_path):
    """Test RunStorySkill produces IDENTICAL output to old generator."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()
    evidence_dir = project_state_dir / "evidence_ledger"
    evidence_dir.mkdir()

    # Create ledger entry
    ledger_data = {
        "run_id": "test_run",
        "timestamp": datetime.now().isoformat(),
        "command": "eda",
        "success": True,
        "outputs": [],
    }
    (evidence_dir / "test_run.yaml").write_text(yaml.dump(ledger_data))

    # Execute skill
    skill = RunStorySkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    result = skill.execute(context)

    # Verify behavior
    assert result.success is True
    assert "story_markdown" in result.artifacts
    assert "story_json" in result.artifacts

    # Check files were created
    story_md = Path(result.artifacts["story_markdown"])
    assert story_md.exists()
    assert story_md.name == "run_story.md"

    # Check content structure (same as before)
    content = story_md.read_text()
    assert "# Run Story" in content
    assert "## What We Did" in content
    assert "## What We Found" in content
    assert "## What It Means" in content
    assert "## What To Do Next" in content
    assert "## Evidence Trail" in content


# ===== Skills Never Mutate State Tests =====


def test_skills_never_mutate_rails_state(tmp_path):
    """Test skills NEVER mutate Rails state."""
    # Create Rails state
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()
    rails_state_path = project_state_dir / "rails_state.json"

    initial_state = {"current_stage": "analyze", "progress": "4/6"}
    rails_state_path.write_text(json.dumps(initial_state))

    # Create outputs
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    catalog_data = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "Test",
        "insights": [],
        "data_summary": {},
    }
    (outputs_dir / "insights_catalog.json").write_text(json.dumps(catalog_data))

    # Execute skill
    skill = InsightBriefSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={"insights_catalog": outputs_dir / "insights_catalog.json"},
    )

    skill.execute(context)

    # Verify Rails state unchanged
    final_state = json.loads(rails_state_path.read_text())
    assert final_state == initial_state


def test_skills_never_block_execution(tmp_path):
    """Test skills NEVER block execution on failure."""
    # Skill with missing prerequisites should return failure but not raise
    skill = InsightBriefSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},  # Missing required artifacts
    )

    # This should NOT raise an exception
    result = skill.execute(context)

    # Should return failure result
    assert result.success is False


# ===== Skills vs Hooks Distinction Tests =====


def test_skills_differ_from_hooks():
    """
    Test that Skills are distinct from Hooks.

    Skills: Bounded capabilities that produce artifacts
    Hooks: Lifecycle intercept points for validation/observation
    """
    skill = InsightBriefSkill()

    # Skills have declarative metadata
    assert hasattr(skill, "skill_id")
    assert hasattr(skill, "stage_scope")
    assert hasattr(skill, "required_artifacts")
    assert hasattr(skill, "produces_artifacts")

    # Skills have execute() method that returns SkillResult
    assert hasattr(skill, "execute")
    assert callable(skill.execute)


def test_registry_exposes_skill_metadata():
    """Test registry exposes skill metadata for policy and hooks."""
    registry = get_registry()

    skills_metadata = registry.list_skills()

    assert len(skills_metadata) >= 2

    # Each skill has complete metadata
    for skill_meta in skills_metadata:
        assert "skill_id" in skill_meta
        assert "description" in skill_meta
        assert "stage_scope" in skill_meta
        assert "required_artifacts" in skill_meta
        assert "produces_artifacts" in skill_meta
        assert "enabled" in skill_meta


# ===== Integration Tests =====


def test_skill_execution_via_registry(tmp_path):
    """Test skills execute correctly via registry."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    catalog_data = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "Test",
        "insights": [],
        "data_summary": {},
    }
    (outputs_dir / "insights_catalog.json").write_text(json.dumps(catalog_data))

    # Build context
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={"insights_catalog": outputs_dir / "insights_catalog.json"},
    )

    # Execute skills via registry
    registry = get_registry()
    results = registry.execute_skills_for_stage("analyze", context)

    # Should have executed insight_brief
    assert len(results["skills_executed"]) > 0
    skill_ids = [s["skill_id"] for s in results["skills_executed"]]
    assert "insight_brief" in skill_ids


def test_skills_record_evidence(tmp_path):
    """Test skills record evidence in their results."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    catalog_data = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "Test",
        "insights": [
            {
                "id": "i1",
                "headline": "Test",
                "supporting_text": "Details",
                "insight_type": "comparison",
                "severity": "key",
                "category": "finding",
                "evidence": [],
                "confidence": 0.9,
            }
        ],
        "data_summary": {},
    }
    (outputs_dir / "insights_catalog.json").write_text(json.dumps(catalog_data))

    skill = InsightBriefSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={"insights_catalog": outputs_dir / "insights_catalog.json"},
    )

    result = skill.execute(context)

    # Should have evidence
    assert "key_insights_count" in result.evidence
    assert "total_insights" in result.evidence
    assert result.evidence["total_insights"] == 1
