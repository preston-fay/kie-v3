"""
Tests for enforcement system (STEP 2: ENFORCEMENT)

Tests policy engine, stage preconditions, evidence completeness.
CRITICAL: Enforcement blocks INVALID actions only, preserves valid failures.
"""

import json
import tempfile
from pathlib import Path

import pytest

from kie.observability import (
    PolicyDecision,
    PolicyEngine,
    PolicyResult,
    generate_recovery_message,
)


# ===== Policy Engine Tests =====


def test_policy_engine_init(tmp_path):
    """Test PolicyEngine initializes."""
    engine = PolicyEngine(tmp_path)
    assert engine.project_root == tmp_path


def test_evaluate_preconditions_allows_commands_without_checks(tmp_path):
    """Test commands without preconditions are always allowed."""
    engine = PolicyEngine(tmp_path)

    # Commands without precondition checks
    result = engine.evaluate_preconditions("interview", None, {})
    assert result.decision == PolicyDecision.ALLOW

    result = engine.evaluate_preconditions("status", None, {})
    assert result.decision == PolicyDecision.ALLOW


# ===== Stage Precondition Tests =====


def test_spec_requires_startkie(tmp_path):
    """Test /spec requires workspace initialization."""
    engine = PolicyEngine(tmp_path)

    # No Rails state = invalid stage
    result = engine.evaluate_preconditions("spec", None, {})

    assert result.is_blocked
    assert "Cannot initialize spec without workspace" in result.message
    assert result.violated_invariant == "Stage Preconditions (Invariant 2)"
    assert result.missing_prerequisite == "Workspace initialization (/startkie)"
    assert "/startkie" in result.recovery_steps[0]


def test_spec_allows_after_startkie(tmp_path):
    """Test /spec allowed after workspace initialization."""
    engine = PolicyEngine(tmp_path)

    # Valid stage after startkie
    result = engine.evaluate_preconditions("spec", "startkie", {})

    assert result.decision == PolicyDecision.ALLOW


def test_eda_requires_spec(tmp_path):
    """Test /eda requires spec.yaml."""
    engine = PolicyEngine(tmp_path)

    # No spec
    result = engine.evaluate_preconditions("eda", "startkie", {"has_spec": False, "has_data": True})

    assert result.is_blocked
    assert "Cannot run EDA without project spec" in result.message
    assert result.missing_prerequisite == "spec.yaml"
    assert "/spec --init" in result.recovery_steps[0]


def test_eda_requires_data(tmp_path):
    """Test /eda requires data files."""
    engine = PolicyEngine(tmp_path)

    # Has spec but no data
    result = engine.evaluate_preconditions("eda", "spec", {"has_spec": True, "has_data": False})

    assert result.is_blocked
    assert "Cannot run EDA without data" in result.message
    assert result.missing_prerequisite == "Data files in data/"


def test_eda_allows_with_spec_and_data(tmp_path):
    """Test /eda allowed when spec and data present."""
    engine = PolicyEngine(tmp_path)

    # Valid preconditions
    result = engine.evaluate_preconditions("eda", "spec", {"has_spec": True, "has_data": True})

    assert result.decision == PolicyDecision.ALLOW


def test_analyze_requires_eda_profile(tmp_path):
    """Test /analyze requires EDA artifacts."""
    engine = PolicyEngine(tmp_path)

    # No EDA profile
    result = engine.evaluate_preconditions("analyze", "eda", {})

    assert result.is_blocked
    assert "Cannot analyze without EDA profile" in result.message
    assert result.missing_prerequisite == "outputs/internal/eda_profile.json or .yaml"
    assert "/eda" in result.recovery_steps[0]


def test_analyze_allows_with_eda_profile(tmp_path):
    """Test /analyze allowed when EDA profile exists."""
    engine = PolicyEngine(tmp_path)

    # Create EDA profile
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)
    (internal_dir / "eda_profile.json").write_text('{"test": "data"}')

    result = engine.evaluate_preconditions("analyze", "eda", {})

    assert result.decision == PolicyDecision.ALLOW


def test_build_requires_insights_catalog(tmp_path):
    """Test /build requires analyze artifacts."""
    engine = PolicyEngine(tmp_path)

    # No insights catalog
    result = engine.evaluate_preconditions("build", "analyze", {})

    assert result.is_blocked
    assert "Cannot build without insights" in result.message
    assert result.missing_prerequisite == "outputs/insights_catalog.json"
    assert "/analyze" in result.recovery_steps[0]


def test_build_allows_with_insights_catalog(tmp_path):
    """Test /build allowed when insights catalog exists."""
    engine = PolicyEngine(tmp_path)

    # Create insights catalog
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)
    (internal_dir / "insights_catalog.json").write_text('{"test": "data"}')

    result = engine.evaluate_preconditions("build", "analyze", {})

    assert result.decision == PolicyDecision.ALLOW


def test_preview_requires_dashboard(tmp_path):
    """Test /preview requires build artifacts."""
    engine = PolicyEngine(tmp_path)

    # No dashboard
    result = engine.evaluate_preconditions("preview", "build", {})

    assert result.is_blocked
    assert "Cannot preview without build artifacts" in result.message
    assert result.missing_prerequisite == "exports/dashboard/"
    assert "/build" in result.recovery_steps[0]


def test_preview_allows_with_dashboard(tmp_path):
    """Test /preview allowed when dashboard exists."""
    engine = PolicyEngine(tmp_path)

    # Create dashboard
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    (exports_dir / "dashboard").mkdir()

    result = engine.evaluate_preconditions("preview", "build", {})

    assert result.decision == PolicyDecision.ALLOW


# ===== Evidence Completeness Tests =====


def test_evidence_completeness_allows_failed_commands(tmp_path):
    """Test evidence completeness allows failed commands."""
    engine = PolicyEngine(tmp_path)

    # Failed command with no artifacts
    result = engine.evaluate_evidence_completeness(
        "eda",
        {"success": False},
        []
    )

    assert result.decision == PolicyDecision.ALLOW


def test_evidence_completeness_blocks_false_success(tmp_path):
    """Test evidence completeness blocks success claims without artifacts."""
    engine = PolicyEngine(tmp_path)

    # Success claimed but no artifacts
    result = engine.evaluate_evidence_completeness(
        "eda",
        {"success": True},
        []
    )

    assert result.is_blocked
    assert "claimed success but produced no artifacts" in result.message
    assert result.violated_invariant == "Artifact Existence (Invariant 5)"


def test_evidence_completeness_allows_success_with_artifacts(tmp_path):
    """Test evidence completeness allows success with artifacts."""
    engine = PolicyEngine(tmp_path)

    # Success with artifacts
    result = engine.evaluate_evidence_completeness(
        "eda",
        {"success": True},
        [{"path": "/tmp/output.txt", "hash": "abc123"}]
    )

    assert result.decision == PolicyDecision.ALLOW


def test_evidence_completeness_skips_non_artifact_commands(tmp_path):
    """Test evidence completeness skips commands that don't require artifacts."""
    engine = PolicyEngine(tmp_path)

    # /status doesn't require artifacts
    result = engine.evaluate_evidence_completeness(
        "status",
        {"success": True},
        []
    )

    assert result.decision == PolicyDecision.ALLOW


# ===== Recovery Message Tests =====


def test_generate_recovery_message_formats_block():
    """Test recovery message formats block correctly."""
    result = PolicyResult(
        decision=PolicyDecision.BLOCK,
        message="Test block message",
        violated_invariant="Test Invariant",
        missing_prerequisite="test.yaml",
        recovery_steps=[
            "/command1  # First step",
            "/command2  # Second step",
        ]
    )

    msg = generate_recovery_message(result)

    assert "❌ ACTION BLOCKED" in msg
    assert "Test block message" in msg
    assert "Violated: Test Invariant" in msg
    assert "Missing: test.yaml" in msg
    assert "/command1" in msg
    assert "/command2" in msg


def test_generate_recovery_message_empty_for_allow():
    """Test recovery message returns empty for ALLOW."""
    result = PolicyResult(decision=PolicyDecision.ALLOW)

    msg = generate_recovery_message(result)

    assert msg == ""


# ===== Integration Tests =====


def test_enforcement_preserves_valid_failures(tmp_path):
    """Test enforcement does NOT block valid failures."""
    engine = PolicyEngine(tmp_path)

    # Valid workflow that fails naturally (e.g., /eda with corrupt data)
    # Preconditions are met
    result = engine.evaluate_preconditions("eda", "spec", {"has_spec": True, "has_data": True})
    assert result.decision == PolicyDecision.ALLOW

    # Command executes and fails (valid failure)
    command_result = {"success": False, "errors": ["Data file is corrupt"]}

    # Evidence completeness allows failed commands
    evidence_result = engine.evaluate_evidence_completeness("eda", command_result, [])
    assert evidence_result.decision == PolicyDecision.ALLOW


def test_enforcement_blocks_invalid_workflow_progression(tmp_path):
    """Test enforcement blocks invalid stage transitions."""
    engine = PolicyEngine(tmp_path)

    # Try to run /build without /analyze
    result = engine.evaluate_preconditions("build", "eda", {})

    assert result.is_blocked
    assert "Cannot build without insights" in result.message


def test_enforcement_end_to_end(tmp_path):
    """Test complete enforcement flow."""
    engine = PolicyEngine(tmp_path)

    # Setup workspace
    for d in ["data", "outputs", "exports", "project_state"]:
        (tmp_path / d).mkdir()

    # Create Rails state
    rails_state = {"current_stage": "spec"}
    (tmp_path / "project_state" / "rails_state.json").write_text(json.dumps(rails_state))

    # Create spec
    (tmp_path / "project_state" / "spec.yaml").write_text("project_name: test")

    # Try /eda without data - should block
    result = engine.evaluate_preconditions("eda", "spec", {"has_spec": True, "has_data": False})
    assert result.is_blocked

    # Add data file
    (tmp_path / "data" / "test.csv").write_text("col1,col2\n1,2\n")

    # Try /eda again - should allow
    result = engine.evaluate_preconditions("eda", "spec", {"has_spec": True, "has_data": True})
    assert result.decision == PolicyDecision.ALLOW

    # Simulate successful /eda with artifacts
    command_result = {"success": True}
    artifacts = [{"path": str(tmp_path / "outputs" / "eda_profile.json"), "hash": "abc"}]

    evidence_result = engine.evaluate_evidence_completeness("eda", command_result, artifacts)
    assert evidence_result.decision == PolicyDecision.ALLOW
