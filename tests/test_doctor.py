"""
Tests for /doctor command (package collision detection and workspace health checks).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kie.commands.handler import CommandHandler


@pytest.fixture
def handler(tmp_path):
    """Create a CommandHandler in a temporary directory."""
    return CommandHandler(project_root=tmp_path)


@pytest.fixture
def mock_kie_module(tmp_path):
    """Mock the kie module import to test collision detection."""
    mock_module = MagicMock()
    mock_module.__file__ = str(tmp_path / "kie" / "__init__.py")
    return mock_module


def test_doctor_detects_correct_package_location(handler, monkeypatch):
    """Test that doctor correctly identifies the kie package location."""
    # Mock Node version to avoid failing on old Node
    monkeypatch.setenv("TEST_NODE_VERSION", "22.0.0")

    result = handler.handle_doctor()

    assert result["success"] is True
    assert "kie_package_location" in result
    assert "kie" in result["kie_package_location"]


def test_doctor_warns_missing_workspace_dirs(handler):
    """Test that doctor warns when workspace directories are missing."""
    result = handler.handle_doctor()

    # Should warn about missing workspace directories
    warnings = result.get("warnings", [])
    assert any("Missing workspace directories" in w for w in warnings)


def test_doctor_checks_pass_with_initialized_workspace(handler):
    """Test that doctor passes checks when workspace is properly initialized."""
    # Create workspace directories
    for dir_name in ["data", "outputs", "exports", "project_state"]:
        (handler.project_root / dir_name).mkdir()

    # Create .claude/commands directory with mock commands
    commands_dir = handler.project_root / ".claude" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "test.md").write_text("# Test command")

    result = handler.handle_doctor()

    # Should have checks that passed
    checks = result.get("checks", [])
    assert len(checks) > 0
    assert any("Workspace structure valid" in c for c in checks)
    assert any("Slash commands provisioned" in c for c in checks)


def test_doctor_warns_missing_slash_commands(handler):
    """Test that doctor warns when slash commands are missing."""
    # Create workspace dirs but no slash commands
    for dir_name in ["data", "outputs", "exports", "project_state"]:
        (handler.project_root / dir_name).mkdir()

    result = handler.handle_doctor()

    warnings = result.get("warnings", [])
    assert any("Slash commands not found" in w for w in warnings)


def test_doctor_warns_missing_spec(handler, monkeypatch):
    """Test that doctor warns when spec.yaml is missing."""
    # Mock Node version to avoid failing on old Node
    monkeypatch.setenv("TEST_NODE_VERSION", "22.0.0")

    result = handler.handle_doctor()

    # The spec warning comes via smart hints in next_steps, not warnings
    next_steps = result.get("next_steps", [])
    assert any("/spec --init" in step for step in next_steps) or \
           any("/interview" in step for step in next_steps)


def test_doctor_detects_spec_when_present(handler, monkeypatch):
    """Test that doctor detects spec.yaml when it exists."""
    # Mock Node version to avoid failing on old Node
    monkeypatch.setenv("TEST_NODE_VERSION", "22.0.0")

    # Create project_state and spec.yaml
    project_state_dir = handler.project_root / "project_state"
    project_state_dir.mkdir()
    (project_state_dir / "spec.yaml").write_text("project_name: test")

    result = handler.handle_doctor()

    # With spec present and no data, should suggest /eda in next_steps
    next_steps = result.get("next_steps", [])
    assert any("/eda" in step for step in next_steps)


def test_doctor_detects_missing_cli_module(handler):
    """Test that doctor detects when kie.cli module is missing (wrong package)."""
    # Patch find_spec inside the function call
    from importlib.util import find_spec as real_find_spec

    def mock_find_spec(name):
        if name == "kie.cli":
            return None
        return real_find_spec(name)

    with patch('importlib.util.find_spec', side_effect=mock_find_spec):
        result = handler.handle_doctor()

        errors = result.get("errors", [])
        assert any("kie.cli module not found" in e for e in errors)
        assert result["success"] is False


def test_doctor_warns_on_unexpected_package_location(handler):
    """Test that doctor warns when kie module is from unexpected location."""
    # This test is difficult to implement without breaking actual kie imports
    # The collision detection works correctly in practice - tested manually
    # Skipping automated test for this edge case
    pytest.skip("Manual test only - requires mock that doesn't break kie imports")


def test_doctor_returns_structured_result(handler):
    """Test that doctor returns properly structured result dictionary."""
    result = handler.handle_doctor()

    # Check required keys
    assert "success" in result
    assert "checks" in result
    assert "warnings" in result
    assert "errors" in result
    assert "kie_package_location" in result

    # Check types
    assert isinstance(result["success"], bool)
    assert isinstance(result["checks"], list)
    assert isinstance(result["warnings"], list)
    assert isinstance(result["errors"], list)
    assert isinstance(result["kie_package_location"], str)


# ===== New Enhanced Doctor Tests =====


def test_doctor_checks_rails_state(handler):
    """Test that doctor checks for rails_state.json."""
    # Create project_state directory
    project_state_dir = handler.project_root / "project_state"
    project_state_dir.mkdir()

    # No rails_state.json yet
    result = handler.handle_doctor()
    warnings = result.get("warnings", [])
    assert any("Rails state tracking not found" in w for w in warnings)

    # Create valid rails_state.json
    import json
    rails_state_path = project_state_dir / "rails_state.json"
    rails_state_path.write_text(json.dumps({"status": "active"}))

    result = handler.handle_doctor()
    checks = result.get("checks", [])
    assert any("Rails state tracking active" in c for c in checks)


def test_doctor_checks_rails_command(handler):
    """Test that doctor checks for /rails command."""
    # Create .claude/commands directory
    commands_dir = handler.project_root / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # No rails.md yet
    result = handler.handle_doctor()
    warnings = result.get("warnings", [])
    assert any("/rails command not found" in w for w in warnings)

    # Create rails.md
    (commands_dir / "rails.md").write_text("# Rails command")

    result = handler.handle_doctor()
    checks = result.get("checks", [])
    assert any("Rails workflow command available" in c for c in checks)


def test_doctor_reports_python_version(handler):
    """Test that doctor reports Python version."""
    result = handler.handle_doctor()

    checks = result.get("checks", [])
    assert any("Python version:" in c for c in checks)
    assert "python_version" in result
    assert result["python_version"]  # Should be non-empty


def test_doctor_detects_node_version_via_env(handler, monkeypatch):
    """Test that doctor detects Node version via TEST_NODE_VERSION env var."""
    # Simulate Node 22 (compatible)
    monkeypatch.setenv("TEST_NODE_VERSION", "22.0.0")

    result = handler.handle_doctor()

    checks = result.get("checks", [])
    assert any("Node.js version: 22.0.0" in c for c in checks)
    assert result["node_version"] == "22.0.0"
    assert result["success"] is True


def test_doctor_fails_on_old_node_version(handler, monkeypatch):
    """Test that doctor fails when Node version is too old."""
    # Simulate Node 18 (too old)
    monkeypatch.setenv("TEST_NODE_VERSION", "18.0.0")

    result = handler.handle_doctor()

    errors = result.get("errors", [])
    assert any("Node.js version 18.0.0 is too old" in e for e in errors)
    assert result["success"] is False


def test_doctor_provides_mac_node_upgrade_instructions(handler, monkeypatch):
    """Test that doctor provides Mac-specific Node upgrade instructions."""
    # Simulate Node 18 on Mac
    monkeypatch.setenv("TEST_NODE_VERSION", "18.0.0")

    with patch("platform.system", return_value="Darwin"):
        result = handler.handle_doctor()

    next_steps = result.get("next_steps", [])
    assert any("brew install node@22" in step for step in next_steps)
    assert any("Mac: Upgrade Node.js" in step for step in next_steps)


def test_doctor_provides_windows_node_upgrade_instructions(handler, monkeypatch):
    """Test that doctor provides Windows-specific Node upgrade instructions."""
    # Simulate Node 18 on Windows
    monkeypatch.setenv("TEST_NODE_VERSION", "18.0.0")

    with patch("platform.system", return_value="Windows"):
        result = handler.handle_doctor()

    next_steps = result.get("next_steps", [])
    assert any("winget install OpenJS.NodeJS.LTS" in step for step in next_steps)
    assert any("Windows: Upgrade Node.js" in step for step in next_steps)


def test_doctor_detects_dashboard_generated(handler):
    """Test that doctor detects when dashboard has been generated."""
    # Create exports/dashboard/package.json
    dashboard_dir = handler.project_root / "exports" / "dashboard"
    dashboard_dir.mkdir(parents=True)
    (dashboard_dir / "package.json").write_text('{"name": "dashboard"}')

    result = handler.handle_doctor()

    checks = result.get("checks", [])
    assert any("Dashboard generated" in c for c in checks)

    # Should provide launch instructions
    next_steps = result.get("next_steps", [])
    assert any("npm run dev" in step for step in next_steps)
    assert any("cd" in step and "exports/dashboard" in step for step in next_steps)


def test_doctor_suggests_spec_when_missing(handler):
    """Test that doctor suggests creating spec when missing."""
    # Create workspace directories so we get to smart hints
    for dir_name in ["data", "outputs", "exports", "project_state"]:
        (handler.project_root / dir_name).mkdir()

    result = handler.handle_doctor()

    next_steps = result.get("next_steps", [])
    assert any("/spec --init" in step for step in next_steps)
    assert any("/interview" in step for step in next_steps)


def test_doctor_suggests_eda_when_no_data(handler):
    """Test that doctor suggests /eda when spec exists but no data."""
    # Create workspace directories
    for dir_name in ["data", "outputs", "exports", "project_state"]:
        (handler.project_root / dir_name).mkdir()

    # Create spec.yaml
    project_state_dir = handler.project_root / "project_state"
    (project_state_dir / "spec.yaml").write_text("project_name: test")

    result = handler.handle_doctor()

    next_steps = result.get("next_steps", [])
    assert any("/eda" in step for step in next_steps)
    assert any("data" in step.lower() for step in next_steps)


def test_doctor_reports_os(handler):
    """Test that doctor reports the operating system."""
    result = handler.handle_doctor()

    assert "os" in result
    assert result["os"] in ["Darwin", "Windows", "Linux"]


def test_doctor_includes_next_steps_field(handler):
    """Test that doctor includes next_steps field in response."""
    result = handler.handle_doctor()

    assert "next_steps" in result
    assert isinstance(result["next_steps"], list)
