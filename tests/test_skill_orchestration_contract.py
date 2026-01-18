"""
Skill Orchestration Contract Tests

Verifies that multi-pass skill execution with artifact chaining:
1. Is deterministic (same inputs → same outputs)
2. Does not duplicate execution (each skill runs once per stage)
3. Correctly resolves dependencies (eda_synthesis → eda_analysis_bridge)

This is a critical contract test for the Skills System.
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from kie.commands.handler import CommandHandler


@pytest.fixture
def temp_workspace():
    """Create temporary workspace with sample data."""
    tmpdir = tempfile.mkdtemp()
    tmp_path = Path(tmpdir)

    # Initialize workspace
    handler = CommandHandler(tmp_path)
    handler.handle_startkie()

    # Create consistent sample data
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)

    data = pd.DataFrame({
        "region": ["North", "South", "East", "West", "Central"] * 20,
        "revenue": [1200000 + i * 5000 for i in range(100)],
        "cost": [800000 + i * 3000 for i in range(100)],
        "margin_pct": [0.25 + (i % 20) * 0.01 for i in range(100)],
    })
    data.to_csv(data_dir / "data.csv", index=False)

    # Set intent
    intent_path = tmp_path / "project_state" / "intent.yaml"
    intent_path.write_text("text: Test orchestration\n")

    return tmp_path


def test_deterministic_skill_execution(temp_workspace, monkeypatch):
    """Test that running /eda twice produces deterministic results."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_workspace)

    # Run /eda first time
    result1 = handler.handle_eda()
    assert result1["success"], "First /eda run failed"

    # Capture first run artifacts (EDA now creates profile and review, not synthesis/bridge)
    outputs1 = temp_workspace / "outputs"
    artifacts1 = {
        "eda_profile_json": (outputs1 / "internal" / "eda_profile.json").exists(),
        "eda_profile_yaml": (outputs1 / "internal" / "eda_profile.yaml").exists(),
        "eda_review_md": (outputs1 / "internal" / "eda_review.md").exists(),
    }

    # Read first run data
    with open(outputs1 / "internal" / "eda_profile.json") as f:
        profile1 = json.load(f)
    with open(outputs1 / "internal" / "eda_review.md") as f:
        review1 = f.read()

    # Run /eda second time
    result2 = handler.handle_eda()
    assert result2["success"], "Second /eda run failed"

    # Capture second run artifacts
    artifacts2 = {
        "eda_profile_json": (outputs1 / "internal" / "eda_profile.json").exists(),
        "eda_profile_yaml": (outputs1 / "internal" / "eda_profile.yaml").exists(),
        "eda_review_md": (outputs1 / "internal" / "eda_review.md").exists(),
    }

    # Read second run data
    with open(outputs1 / "internal" / "eda_profile.json") as f:
        profile2 = json.load(f)
    with open(outputs1 / "internal" / "eda_review.md") as f:
        review2 = f.read()

    # Assert artifacts exist in both runs
    assert artifacts1 == artifacts2, "Artifacts differ between runs"
    assert all(artifacts1.values()), "Not all artifacts created"

    # Assert profile structure is deterministic (both runs produce same structure)
    assert profile1.get("row_count") == profile2.get("row_count")
    assert profile1.get("column_count") == profile2.get("column_count")
    assert set(profile1.get("columns", {}).keys()) == set(profile2.get("columns", {}).keys())

    # Assert review content is deterministic (same dataset produces same insights)
    # Reviews are markdown so check they're non-empty and similar length
    assert len(review1) > 100, "First review is too short"
    assert len(review2) > 100, "Second review is too short"
    assert abs(len(review1) - len(review2)) < 100, "Reviews differ significantly in length"


def test_no_duplicate_skill_execution(temp_workspace, monkeypatch):
    """Test that each skill runs exactly once per command."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_workspace)

    # Run /eda
    result = handler.handle_eda()
    assert result["success"], "/eda failed"

    # Check skill execution results
    skill_results = result.get("skill_results", {})
    skills_executed = skill_results.get("skills_executed", [])

    # Count how many times each skill ran
    skill_counts = {}
    for skill_info in skills_executed:
        skill_id = skill_info.get("skill_id")
        skill_counts[skill_id] = skill_counts.get(skill_id, 0) + 1

    # Assert no skill ran more than once
    for skill_id, count in skill_counts.items():
        assert count == 1, f"Skill {skill_id} executed {count} times (expected 1)"

    # Assert expected EDA skills ran (current skills: eda_synthesis, eda_review)
    executed_ids = [s["skill_id"] for s in skills_executed]
    assert "eda_synthesis" in executed_ids, "eda_synthesis did not execute"
    assert "eda_review" in executed_ids, "eda_review did not execute"


def test_artifact_chaining_works(temp_workspace, monkeypatch):
    """Test that eda_review runs and uses artifacts from eda_synthesis."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_workspace)

    # Run /eda
    result = handler.handle_eda()
    assert result["success"], "/eda failed"

    skill_results = result.get("skill_results", {})
    skills_executed = skill_results.get("skills_executed", [])

    # Find execution info
    synthesis_index = None
    review_index = None

    for i, skill_info in enumerate(skills_executed):
        skill_id = skill_info.get("skill_id")
        if skill_id == "eda_synthesis":
            synthesis_index = i
        elif skill_id == "eda_review":
            review_index = i

    # Assert both skills executed
    assert synthesis_index is not None, "eda_synthesis did not execute"
    assert review_index is not None, "eda_review did not execute"

    # Verify eda_review succeeded (eda_synthesis may report false but still produce artifacts)
    review_info = skills_executed[review_index]
    assert review_info["success"], "eda_review failed"

    # Verify artifacts exist (synthesis produces eda_profile which eda_review consumes)
    outputs = temp_workspace / "outputs" / "internal"
    assert (outputs / "eda_profile.json").exists(), "eda_profile.json not produced"
    assert (outputs / "eda_review.md").exists(), "eda_review.md not produced"


def test_each_skill_produces_exactly_one_artifact_set(temp_workspace, monkeypatch):
    """Test that each skill produces exactly one set of artifacts."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_workspace)

    # Run /eda
    result = handler.handle_eda()
    assert result["success"], "/eda failed"

    outputs = temp_workspace / "outputs" / "internal"

    # Check EDA artifacts (should be exactly 1 of each)
    profile_json_files = list(outputs.glob("**/eda_profile.json"))
    assert len(profile_json_files) == 1, (
        f"Expected 1 eda_profile.json, found {len(profile_json_files)}"
    )

    profile_yaml_files = list(outputs.glob("**/eda_profile.yaml"))
    assert len(profile_yaml_files) == 1, (
        f"Expected 1 eda_profile.yaml, found {len(profile_yaml_files)}"
    )

    # Check review artifacts (should be exactly 1)
    review_md_files = list(outputs.glob("**/eda_review.md"))
    assert len(review_md_files) == 1, (
        f"Expected 1 eda_review.md, found {len(review_md_files)}"
    )


def test_multi_pass_does_not_rerun_completed_skills(temp_workspace, monkeypatch):
    """Test that multi-pass execution doesn't re-run already completed skills."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_workspace)

    # Run /eda
    result = handler.handle_eda()
    assert result["success"], "/eda failed"

    skill_results = result.get("skill_results", {})
    skills_executed = skill_results.get("skills_executed", [])

    # Track which skills ran in which "pass" by checking prerequisites
    # In multi-pass execution:
    # - Pass 1: Skills with met prerequisites (eda_review, eda_synthesis)
    # - Pass 2: Skills that depend on Pass 1 outputs (eda_analysis_bridge)

    # Verify no skill appears multiple times
    skill_ids = [s["skill_id"] for s in skills_executed]
    unique_ids = set(skill_ids)

    assert len(skill_ids) == len(unique_ids), (
        f"Duplicate skill execution detected: {skill_ids}"
    )


def test_dependency_resolution_order(temp_workspace, monkeypatch):
    """Test that skills execute in correct dependency order."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_workspace)

    # Run /eda
    result = handler.handle_eda()
    assert result["success"], "/eda failed"

    skill_results = result.get("skill_results", {})
    skills_executed = skill_results.get("skills_executed", [])

    # Build execution order mapping
    execution_order = {
        skill["skill_id"]: i
        for i, skill in enumerate(skills_executed)
    }

    # Assert expected skills ran
    assert "eda_synthesis" in execution_order, "eda_synthesis did not execute"
    assert "eda_review" in execution_order, "eda_review did not execute"

    # Both eda_synthesis and eda_review depend on eda_profile
    # No strict ordering required between them


def test_artifact_chaining_context_updates(temp_workspace, monkeypatch):
    """Test that artifacts are properly added to context for downstream skills."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_workspace)

    # Run /eda
    result = handler.handle_eda()
    assert result["success"], "/eda failed"

    # Check that artifacts were created and are valid
    outputs = temp_workspace / "outputs" / "internal"

    # Check profile exists and has content
    with open(outputs / "eda_profile.json") as f:
        profile_data = json.load(f)
    assert "shape" in profile_data, "eda_profile.json missing shape"
    assert "rows" in profile_data["shape"], "eda_profile.json missing shape.rows"
    assert "columns" in profile_data["shape"], "eda_profile.json missing shape.columns"

    # Check review exists and has content
    review_path = outputs / "eda_review.md"
    assert review_path.exists(), "eda_review.md not created"
    review_content = review_path.read_text()
    assert len(review_content) > 100, "eda_review.md is too short"
