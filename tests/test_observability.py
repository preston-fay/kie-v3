"""
Tests for observability system (STEP 1: OBSERVABILITY)

Tests evidence ledger, hooks, and run summary functionality.
CRITICAL: Observability must NEVER fail a command.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from kie.observability import (
    EvidenceLedger,
    ObservabilityHooks,
    RunSummary,
    create_ledger,
)
from kie.observability.evidence_ledger import (
    capture_environment,
    compute_file_hash,
    read_rails_stage,
    record_artifacts,
)


# ===== Evidence Ledger Tests =====


def test_create_ledger():
    """Test that create_ledger produces valid ledger."""
    ledger = create_ledger("test_command", {"arg1": "value1"})

    assert ledger.run_id
    assert ledger.timestamp
    assert ledger.command == "test_command"
    assert ledger.args == {"arg1": "value1"}
    assert ledger.success is True


def test_capture_environment():
    """Test that capture_environment records OS and Python version."""
    env = capture_environment()

    assert "os" in env
    assert "python_version" in env
    assert env["os"] in ["Darwin", "Windows", "Linux"]
    assert "." in env["python_version"]  # Should have version dots


def test_read_rails_stage_missing(tmp_path):
    """Test read_rails_stage returns None if rails_state.json missing."""
    stage = read_rails_stage(tmp_path)
    assert stage is None


def test_read_rails_stage_exists(tmp_path):
    """Test read_rails_stage reads current stage."""
    # Create rails_state.json
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    rails_state = {"current_stage": "eda", "progress": "2/6"}
    rails_state_path = project_state_dir / "rails_state.json"
    rails_state_path.write_text(json.dumps(rails_state))

    stage = read_rails_stage(tmp_path)
    assert stage == "eda"


def test_compute_file_hash(tmp_path):
    """Test compute_file_hash calculates SHA-256."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    file_hash = compute_file_hash(test_file)
    assert file_hash
    assert len(file_hash) == 64  # SHA-256 is 64 hex chars


def test_compute_file_hash_missing(tmp_path):
    """Test compute_file_hash returns None for missing files."""
    missing_file = tmp_path / "nonexistent.txt"
    file_hash = compute_file_hash(missing_file)
    assert file_hash is None


def test_record_artifacts(tmp_path):
    """Test record_artifacts adds files to ledger."""
    ledger = create_ledger("test")

    # Create test files
    file1 = tmp_path / "output1.txt"
    file2 = tmp_path / "output2.txt"
    file1.write_text("content1")
    file2.write_text("content2")

    record_artifacts(ledger, [file1, file2], artifact_type="output")

    assert len(ledger.outputs) == 2
    assert ledger.outputs[0]["path"] == str(file1)
    assert ledger.outputs[0]["hash"]  # Should have hash
    assert ledger.outputs[1]["path"] == str(file2)
    assert ledger.outputs[1]["hash"]  # Should have hash


def test_ledger_to_dict():
    """Test ledger serializes to dictionary."""
    ledger = create_ledger("test", {"key": "value"})
    ledger.warnings.append("test warning")
    ledger.errors.append("test error")

    data = ledger.to_dict()

    assert data["command"] == "test"
    assert data["args"] == {"key": "value"}
    assert "test warning" in data["warnings"]
    assert "test error" in data["errors"]


def test_ledger_save(tmp_path):
    """Test ledger saves to YAML file."""
    ledger = create_ledger("test")

    ledger_dir = tmp_path / "evidence_ledger"
    ledger_path = ledger.save(ledger_dir)

    assert ledger_path
    assert ledger_path.exists()
    assert ledger_path.name == f"{ledger.run_id}.yaml"


def test_ledger_save_never_fails(tmp_path):
    """Test ledger save never raises exception even if directory is readonly."""
    ledger = create_ledger("test")

    # Try to save to invalid location
    invalid_dir = tmp_path / "readonly" / "nested" / "invalid"

    # This should NOT raise an exception
    result = ledger.save(invalid_dir)

    # May return None but should not crash
    assert result is None or result.exists()


# ===== Observability Hooks Tests =====


def test_observability_hooks_init(tmp_path):
    """Test ObservabilityHooks initializes."""
    hooks = ObservabilityHooks(tmp_path)
    assert hooks.project_root == tmp_path


def test_pre_command_hook(tmp_path):
    """Test pre_command hook observes state."""
    # Create Rails state
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()
    rails_state = {"current_stage": "spec"}
    (project_state_dir / "rails_state.json").write_text(json.dumps(rails_state))

    # Create workspace dirs
    for d in ["data", "outputs", "exports"]:
        (tmp_path / d).mkdir()

    hooks = ObservabilityHooks(tmp_path)
    ledger = create_ledger("test")

    hooks.pre_command(ledger, "test", {})

    # Should have observed Rails stage
    assert ledger.rails_stage_before == "spec"

    # Should have observed workspace
    assert ledger.proof_references.get("workspace_valid") is True


def test_pre_command_hook_missing_data(tmp_path):
    """Test pre_command hook detects missing data."""
    # Create workspace without data
    for d in ["outputs", "exports", "project_state"]:
        (tmp_path / d).mkdir()

    hooks = ObservabilityHooks(tmp_path)
    ledger = create_ledger("test")

    hooks.pre_command(ledger, "test", {})

    # Should detect missing data dir
    assert "data" in ledger.proof_references.get("missing_workspace_dirs", [])


def test_post_command_hook(tmp_path):
    """Test post_command hook observes outputs."""
    hooks = ObservabilityHooks(tmp_path)
    ledger = create_ledger("test")

    # Simulate command result
    result = {
        "success": True,
        "warnings": ["test warning"],
        "errors": [],
    }

    hooks.post_command(ledger, result)

    # Should have recorded success
    assert ledger.success is True

    # Should have recorded warnings
    assert "test warning" in ledger.warnings


def test_post_command_hook_failure(tmp_path):
    """Test post_command hook observes failures."""
    hooks = ObservabilityHooks(tmp_path)
    ledger = create_ledger("test")

    # Simulate failure
    result = {
        "success": False,
        "errors": ["test error"],
    }

    hooks.post_command(ledger, result)

    # Should have recorded failure
    assert ledger.success is False

    # Should have recorded errors
    assert "test error" in ledger.errors


def test_hooks_never_fail(tmp_path):
    """Test hooks never raise exceptions."""
    hooks = ObservabilityHooks(tmp_path)
    ledger = create_ledger("test")

    # Try to break pre_command - should not crash
    try:
        hooks.pre_command(ledger, "test", {"invalid": object()})
        # Should complete without exception
        success = True
    except Exception:
        success = False

    assert success

    # Try to break post_command - should not crash
    try:
        hooks.post_command(ledger, {"invalid": object()})
        # Should complete without exception
        success = True
    except Exception:
        success = False

    assert success


# ===== Run Summary Tests =====


def test_run_summary_format():
    """Test RunSummary formats output."""
    ledger = create_ledger("test")
    ledger.success = True
    ledger.rails_stage_after = "eda"
    ledger.outputs.append({"path": "/tmp/output.txt", "hash": "abc123"})
    ledger.warnings.append("test warning")

    result = {"next_steps": ["/analyze"]}

    summary = RunSummary.format(ledger, result)

    assert "Command: /test" in summary
    assert "✓ SUCCESS" in summary
    assert "Current Stage: eda" in summary
    assert "/tmp/output.txt" in summary
    assert "test warning" in summary
    assert "/analyze" in summary


def test_run_summary_format_failure():
    """Test RunSummary formats failures."""
    ledger = create_ledger("test")
    ledger.success = False
    ledger.errors.append("test error")

    result = {}

    summary = RunSummary.format(ledger, result)

    assert "✗ FAILED" in summary
    assert "test error" in summary


def test_run_summary_compact():
    """Test RunSummary compact format."""
    ledger = create_ledger("test")
    ledger.success = True
    ledger.outputs.append({"path": "/tmp/out.txt", "hash": "abc"})
    ledger.warnings.append("warning")

    summary = RunSummary.format_compact(ledger)

    assert "✓ /test" in summary
    assert "1 outputs" in summary
    assert "1 warnings" in summary


# ===== Integration Tests =====


def test_observability_end_to_end(tmp_path):
    """Test complete observability flow."""
    # Setup workspace
    for d in ["data", "outputs", "exports", "project_state"]:
        (tmp_path / d).mkdir()

    # Create Rails state
    rails_state = {"current_stage": "startkie"}
    (tmp_path / "project_state" / "rails_state.json").write_text(json.dumps(rails_state))

    # Create hooks
    hooks = ObservabilityHooks(tmp_path)

    # Create ledger
    ledger = create_ledger("eda", {"data_file": "test.csv"}, tmp_path)

    # Pre-command
    hooks.pre_command(ledger, "eda", {"data_file": "test.csv"})

    # Simulate command execution
    # (normally done by CommandHandler)

    # Create output
    output_file = tmp_path / "outputs" / "eda_profile.json"
    output_file.write_text('{"test": "data"}')

    # Post-command
    result = {
        "success": True,
        "profile_saved": str(output_file),
    }
    hooks.post_command(ledger, result)

    # Save ledger
    ledger_dir = tmp_path / "project_state" / "evidence_ledger"
    ledger_path = ledger.save(ledger_dir)

    # Verify
    assert ledger_path.exists()
    assert ledger.rails_stage_before == "startkie"
    assert ledger.success is True

    # Should have recorded output
    assert len(ledger.outputs) > 0


def test_observability_disabled(tmp_path):
    """Test that observability can be disabled."""
    # This is tested by the KIE_DISABLE_OBSERVABILITY env var
    # in CommandHandler.__init__
    with patch.dict("os.environ", {"KIE_DISABLE_OBSERVABILITY": "1"}):
        # CommandHandler should initialize without observability
        from kie.commands.handler import CommandHandler

        handler = CommandHandler(tmp_path)

        # Should not crash if observability is disabled
        assert handler is not None
