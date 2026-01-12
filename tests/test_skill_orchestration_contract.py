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


def test_deterministic_skill_execution(temp_workspace):
    """Test that running /eda twice produces deterministic results."""
    handler = CommandHandler(temp_workspace)

    # Run /eda first time
    result1 = handler.handle_eda()
    assert result1["success"], "First /eda run failed"

    # Capture first run artifacts
    outputs1 = temp_workspace / "outputs"
    artifacts1 = {
        "eda_synthesis": (outputs1 / "eda_synthesis.json").exists(),
        "eda_analysis_bridge_md": (outputs1 / "eda_analysis_bridge.md").exists(),
        "eda_analysis_bridge_json": (outputs1 / "eda_analysis_bridge.json").exists(),
    }

    # Read first run data
    with open(outputs1 / "eda_synthesis.json") as f:
        synthesis1 = json.load(f)
    with open(outputs1 / "eda_analysis_bridge.json") as f:
        bridge1 = json.load(f)

    # Run /eda second time
    result2 = handler.handle_eda()
    assert result2["success"], "Second /eda run failed"

    # Capture second run artifacts
    artifacts2 = {
        "eda_synthesis": (outputs1 / "eda_synthesis.json").exists(),
        "eda_analysis_bridge_md": (outputs1 / "eda_analysis_bridge.md").exists(),
        "eda_analysis_bridge_json": (outputs1 / "eda_analysis_bridge.json").exists(),
    }

    # Read second run data
    with open(outputs1 / "eda_synthesis.json") as f:
        synthesis2 = json.load(f)
    with open(outputs1 / "eda_analysis_bridge.json") as f:
        bridge2 = json.load(f)

    # Assert artifacts exist in both runs
    assert artifacts1 == artifacts2, "Artifacts differ between runs"
    assert all(artifacts1.values()), "Not all artifacts created"

    # Assert synthesis structure is deterministic (ignore timestamps)
    assert synthesis1["dataset_overview"] == synthesis2["dataset_overview"]
    assert synthesis1["column_reduction"] == synthesis2["column_reduction"]
    assert synthesis1["dominance_analysis"] == synthesis2["dominance_analysis"]

    # Assert bridge structure is deterministic (ignore timestamps)
    assert bridge1["primary_focus"] == bridge2["primary_focus"]
    assert bridge1["secondary"] == bridge2["secondary"]
    assert bridge1["deprioritized"] == bridge2["deprioritized"]
    assert bridge1["recommended_analysis_types"] == bridge2["recommended_analysis_types"]


def test_no_duplicate_skill_execution(temp_workspace):
    """Test that each skill runs exactly once per command."""
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

    # Assert expected EDA skills ran
    executed_ids = [s["skill_id"] for s in skills_executed]
    assert "eda_synthesis" in executed_ids, "eda_synthesis did not execute"
    assert "eda_analysis_bridge" in executed_ids, "eda_analysis_bridge did not execute"


def test_artifact_chaining_works(temp_workspace):
    """Test that eda_analysis_bridge only runs after eda_synthesis completes."""
    handler = CommandHandler(temp_workspace)

    # Run /eda
    result = handler.handle_eda()
    assert result["success"], "/eda failed"

    skill_results = result.get("skill_results", {})
    skills_executed = skill_results.get("skills_executed", [])

    # Find execution order
    synthesis_index = None
    bridge_index = None

    for i, skill_info in enumerate(skills_executed):
        skill_id = skill_info.get("skill_id")
        if skill_id == "eda_synthesis":
            synthesis_index = i
        elif skill_id == "eda_analysis_bridge":
            bridge_index = i

    # Assert both skills executed
    assert synthesis_index is not None, "eda_synthesis did not execute"
    assert bridge_index is not None, "eda_analysis_bridge did not execute"

    # Assert bridge ran AFTER synthesis
    assert bridge_index > synthesis_index, (
        f"eda_analysis_bridge (index {bridge_index}) ran before "
        f"eda_synthesis (index {synthesis_index})"
    )

    # Verify bridge has required artifacts from synthesis
    bridge_info = skills_executed[bridge_index]
    assert bridge_info["success"], "eda_analysis_bridge failed"

    # Verify synthesis produced its artifacts before bridge ran
    synthesis_info = skills_executed[synthesis_index]
    assert synthesis_info["success"], "eda_synthesis failed"
    assert "eda_synthesis_json" in synthesis_info["artifacts"], (
        "eda_synthesis did not produce required artifact"
    )


def test_each_skill_produces_exactly_one_artifact_set(temp_workspace):
    """Test that each skill produces exactly one set of artifacts."""
    handler = CommandHandler(temp_workspace)

    # Run /eda
    result = handler.handle_eda()
    assert result["success"], "/eda failed"

    outputs = temp_workspace / "outputs"

    # Check synthesis artifacts (should be exactly 1 of each)
    synthesis_json_files = list(outputs.glob("eda_synthesis.json"))
    assert len(synthesis_json_files) == 1, (
        f"Expected 1 eda_synthesis.json, found {len(synthesis_json_files)}"
    )

    synthesis_md_files = list(outputs.glob("eda_synthesis.md"))
    assert len(synthesis_md_files) == 1, (
        f"Expected 1 eda_synthesis.md, found {len(synthesis_md_files)}"
    )

    # Check bridge artifacts (should be exactly 1 of each)
    bridge_json_files = list(outputs.glob("eda_analysis_bridge.json"))
    assert len(bridge_json_files) == 1, (
        f"Expected 1 eda_analysis_bridge.json, found {len(bridge_json_files)}"
    )

    bridge_md_files = list(outputs.glob("eda_analysis_bridge.md"))
    assert len(bridge_md_files) == 1, (
        f"Expected 1 eda_analysis_bridge.md, found {len(bridge_md_files)}"
    )


def test_multi_pass_does_not_rerun_completed_skills(temp_workspace):
    """Test that multi-pass execution doesn't re-run already completed skills."""
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


def test_dependency_resolution_order(temp_workspace):
    """Test that skills execute in correct dependency order."""
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

    # Assert eda_synthesis ran before eda_analysis_bridge
    assert "eda_synthesis" in execution_order
    assert "eda_analysis_bridge" in execution_order
    assert execution_order["eda_synthesis"] < execution_order["eda_analysis_bridge"]

    # Verify eda_review (no deps beyond eda_profile) ran before or with synthesis
    if "eda_review" in execution_order:
        # eda_review can run in any order relative to synthesis (both depend on eda_profile)
        pass


def test_artifact_chaining_context_updates(temp_workspace):
    """Test that artifacts are properly added to context for downstream skills."""
    handler = CommandHandler(temp_workspace)

    # Run /eda
    result = handler.handle_eda()
    assert result["success"], "/eda failed"

    # Check that bridge artifacts reference synthesis correctly
    outputs = temp_workspace / "outputs"

    with open(outputs / "eda_synthesis.json") as f:
        synthesis_data = json.load(f)

    with open(outputs / "eda_analysis_bridge.json") as f:
        bridge_data = json.load(f)

    # Bridge should use column_reduction from synthesis
    synthesis_columns = set(synthesis_data["column_reduction"]["keep"])
    bridge_columns = {item["column"] for item in bridge_data["primary_focus"]}

    # Bridge primary focus should be subset of synthesis keep columns
    assert bridge_columns.issubset(synthesis_columns), (
        f"Bridge primary focus {bridge_columns} not subset of "
        f"synthesis keep {synthesis_columns}"
    )
