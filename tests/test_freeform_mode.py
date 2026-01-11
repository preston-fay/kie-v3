#!/usr/bin/env python3
"""
Unit tests for Freeform Mode functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml


def test_default_mode_is_rails():
    """Test that default execution mode is 'rails'."""
    from kie.execution_policy import ExecutionPolicy

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        policy = ExecutionPolicy(project_root)

        # Default mode should be rails
        assert policy.get_mode() == "rails"
        assert policy.is_rails_mode() is True
        assert policy.is_freeform_enabled() is False


def test_mode_storage_and_retrieval():
    """Test that execution mode can be stored and retrieved."""
    from kie.execution_policy import ExecutionPolicy

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        policy = ExecutionPolicy(project_root)

        # Initially rails (default)
        assert policy.get_mode() == "rails"

        # Set to freeform
        policy.set_mode("freeform")
        assert policy.get_mode() == "freeform"
        assert policy.is_freeform_enabled() is True
        assert policy.is_rails_mode() is False

        # Create new instance - should persist
        policy2 = ExecutionPolicy(project_root)
        assert policy2.get_mode() == "freeform"

        # Change back to rails
        policy2.set_mode("rails")
        assert policy2.get_mode() == "rails"


def test_mode_validation():
    """Test that invalid modes are rejected."""
    from kie.execution_policy import ExecutionPolicy

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        policy = ExecutionPolicy(project_root)

        # Invalid mode should raise ValueError
        with pytest.raises(ValueError):
            policy.set_mode("invalid")

        with pytest.raises(ValueError):
            policy.set_mode("custom")

        # Valid modes should work
        policy.set_mode("rails")
        assert policy.get_mode() == "rails"

        policy.set_mode("freeform")
        assert policy.get_mode() == "freeform"


def test_policy_file_format():
    """Test that policy is stored in correct format."""
    from kie.execution_policy import ExecutionPolicy

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        policy = ExecutionPolicy(project_root)

        policy.set_mode("freeform", set_by="test")

        # Check file exists
        policy_file = project_root / "project_state" / "execution_policy.yaml"
        assert policy_file.exists()

        # Check file structure
        with open(policy_file) as f:
            data = yaml.safe_load(f)

        assert data["mode"] == "freeform"
        assert data["set_by"] == "test"
        assert "set_at" in data


def test_freeform_command_status():
    """Test /freeform status command."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Default mode
        result = handler.handle_freeform(action="status")
        assert result["success"] is True
        assert result["mode"] == "rails"


def test_freeform_command_enable():
    """Test /freeform enable command."""
    from kie.commands.handler import CommandHandler
    from kie.execution_policy import ExecutionPolicy

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Enable freeform
        result = handler.handle_freeform(action="enable")
        assert result["success"] is True
        assert result["mode"] == "freeform"

        # Verify persisted
        policy = ExecutionPolicy(project_root)
        assert policy.get_mode() == "freeform"


def test_freeform_command_disable():
    """Test /freeform disable command."""
    from kie.commands.handler import CommandHandler
    from kie.execution_policy import ExecutionPolicy

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Enable first
        handler.handle_freeform(action="enable")

        # Then disable
        result = handler.handle_freeform(action="disable")
        assert result["success"] is True
        assert result["mode"] == "rails"

        # Verify persisted
        policy = ExecutionPolicy(project_root)
        assert policy.get_mode() == "rails"


def test_freeform_command_invalid_action():
    """Test /freeform command rejects invalid actions."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Invalid action
        result = handler.handle_freeform(action="invalid")
        assert result["success"] is False


def test_status_shows_execution_mode():
    """Test /status includes execution_mode."""
    from kie.commands.handler import CommandHandler
    from kie.execution_policy import ExecutionPolicy

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)
        handler.handle_startkie()

        # Default mode
        status = handler.handle_status()
        assert "execution_mode" in status
        assert status["execution_mode"] == "rails"

        # Enable freeform
        policy = ExecutionPolicy(project_root)
        policy.set_mode("freeform")

        # Status should show freeform
        status = handler.handle_status()
        assert status["execution_mode"] == "freeform"


def test_no_rails_mutation():
    """Test that execution policy does NOT mutate rails_state.json."""
    from kie.commands.handler import CommandHandler
    from kie.execution_policy import ExecutionPolicy

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)
        handler.handle_startkie()

        # Record original rails state
        rails_path = project_root / "project_state" / "rails_state.json"
        if rails_path.exists():
            original_rails = rails_path.read_text()
        else:
            original_rails = None

        # Set execution mode
        policy = ExecutionPolicy(project_root)
        policy.set_mode("freeform")

        # Rails state should be unchanged
        if rails_path.exists():
            current_rails = rails_path.read_text()
            assert current_rails == original_rails
        else:
            # Rails state still doesn't exist (expected if workspace not advanced)
            assert original_rails is None

        # Verify execution mode was stored elsewhere
        policy_path = project_root / "project_state" / "execution_policy.yaml"
        assert policy_path.exists()
        assert policy.get_mode() == "freeform"


def test_guardrail_text_in_templates():
    """Test that command templates include guardrail text."""
    # Check user commands
    user_commands = Path("tools/claude_user_commands")
    for cmd_file in ["analyze.md", "build.md", "eda.md", "interview.md", "map.md"]:
        file_path = user_commands / cmd_file
        assert file_path.exists(), f"User command file {cmd_file} not found"

        content = file_path.read_text()
        assert "GUARDRAIL" in content, f"GUARDRAIL section missing in user command {cmd_file}"
        assert "Rails Mode" in content, f"Rails Mode description missing in {cmd_file}"
        assert "freeform enable" in content, f"Freeform enable instruction missing in {cmd_file}"

    # Check project template commands
    template_commands = Path("project_template/.claude/commands")
    for cmd_file in ["analyze.md", "build.md", "eda.md", "interview.md", "map.md"]:
        file_path = template_commands / cmd_file
        assert file_path.exists(), f"Template command file {cmd_file} not found"

        content = file_path.read_text()
        assert "GUARDRAIL" in content, f"GUARDRAIL section missing in template {cmd_file}"
        assert "Rails Mode" in content, f"Rails Mode description missing in {cmd_file}"
        assert "freeform enable" in content, f"Freeform enable instruction missing in {cmd_file}"


def test_policy_info():
    """Test get_policy_info returns full information."""
    from kie.execution_policy import ExecutionPolicy

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        policy = ExecutionPolicy(project_root)

        # Default info
        info = policy.get_policy_info()
        assert info["mode"] == "rails"
        assert info["set_at"] is None
        assert info["set_by"] == "default"

        # After setting mode
        policy.set_mode("freeform", set_by="user")
        info = policy.get_policy_info()
        assert info["mode"] == "freeform"
        assert info["set_at"] is not None
        assert info["set_by"] == "user"
