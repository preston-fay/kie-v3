"""
Unit tests for Mode Gate (Constitution Section 4).

Tests execution policy management and mode enforcement.
"""

import tempfile
from pathlib import Path

import pytest

from kie.state import ExecutionMode, ExecutionPolicy


@pytest.fixture
def temp_workspace():
    """Create temporary workspace."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "project_state").mkdir(parents=True)
        yield tmp_path


def test_default_mode_is_rails(temp_workspace):
    """Test that default execution mode is Rails."""
    policy = ExecutionPolicy(temp_workspace)
    mode = policy.get_mode()

    assert mode == ExecutionMode.RAILS, "Default mode must be Rails"
    assert not policy.is_freeform_enabled(), "Freeform must not be enabled by default"


def test_enable_freeform_mode(temp_workspace):
    """Test enabling freeform mode."""
    policy = ExecutionPolicy(temp_workspace)

    # Initially rails
    assert policy.get_mode() == ExecutionMode.RAILS

    # Enable freeform
    result = policy.set_mode(ExecutionMode.FREEFORM)

    assert result["success"], "set_mode should succeed"
    assert result["mode"] == "freeform", "Result should show freeform mode"
    assert policy.get_mode() == ExecutionMode.FREEFORM, "Mode should be freeform"
    assert policy.is_freeform_enabled(), "is_freeform_enabled should be True"


def test_disable_freeform_mode(temp_workspace):
    """Test disabling freeform mode (return to rails)."""
    policy = ExecutionPolicy(temp_workspace)

    # Enable freeform
    policy.set_mode(ExecutionMode.FREEFORM)
    assert policy.get_mode() == ExecutionMode.FREEFORM

    # Disable (return to rails)
    result = policy.set_mode(ExecutionMode.RAILS)

    assert result["success"], "set_mode should succeed"
    assert result["mode"] == "rails", "Result should show rails mode"
    assert policy.get_mode() == ExecutionMode.RAILS, "Mode should be rails"
    assert not policy.is_freeform_enabled(), "is_freeform_enabled should be False"


def test_mode_persists_across_instances(temp_workspace):
    """Test that mode setting persists to disk."""
    # Set freeform with first instance
    policy1 = ExecutionPolicy(temp_workspace)
    policy1.set_mode(ExecutionMode.FREEFORM)

    # Create new instance and check mode
    policy2 = ExecutionPolicy(temp_workspace)
    assert policy2.get_mode() == ExecutionMode.FREEFORM, "Mode should persist"


def test_policy_file_created(temp_workspace):
    """Test that execution_policy.yaml is created."""
    policy = ExecutionPolicy(temp_workspace)
    policy_path = temp_workspace / "project_state" / "execution_policy.yaml"

    # Initially no policy file
    assert not policy_path.exists(), "Policy file should not exist initially"

    # Set mode
    policy.set_mode(ExecutionMode.FREEFORM)

    # Policy file should now exist
    assert policy_path.exists(), "Policy file should be created"

    # Read and verify content
    import yaml
    with open(policy_path) as f:
        data = yaml.safe_load(f)

    assert data["mode"] == "freeform", "Policy file should contain correct mode"
    assert "set_at" in data, "Policy file should contain timestamp"
    assert "set_by" in data, "Policy file should contain set_by field"


def test_get_policy_info(temp_workspace):
    """Test getting full policy information."""
    policy = ExecutionPolicy(temp_workspace)

    # Before setting mode
    info = policy.get_policy_info()
    assert info["mode"] == "rails", "Default mode info should be rails"

    # After setting mode
    policy.set_mode(ExecutionMode.FREEFORM, set_by="test_user")
    info = policy.get_policy_info()

    assert info["mode"] == "freeform", "Mode should be freeform"
    assert "set_at" in info, "Info should include set_at"
    assert info["set_by"] == "test_user", "Info should include set_by"


def test_mode_in_status_command(temp_workspace):
    """Test that execution mode appears in /status output."""
    from kie.commands.handler import CommandHandler

    handler = CommandHandler(temp_workspace)
    status = handler.handle_status()

    assert "execution_mode" in status, "/status should include execution_mode"
    assert status["execution_mode"] == "rails", "Default mode in status should be rails"

    # Enable freeform and check again
    policy = ExecutionPolicy(temp_workspace)
    policy.set_mode(ExecutionMode.FREEFORM)

    status = handler.handle_status()
    assert status["execution_mode"] == "freeform", "Status should show freeform mode"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
