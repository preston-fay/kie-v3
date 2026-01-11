"""
Tests for Theme Gate System

Verifies that theme selection is non-interactive and blocks when theme is not set.
"""

import tempfile
from pathlib import Path

import pytest

from kie.commands.handler import CommandHandler
from kie.preferences import OutputPreferences


@pytest.fixture
def temp_project():
    """Create temporary project directory with KIE structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir(parents=True)
        (project_root / "data").mkdir(parents=True)
        (project_root / "outputs").mkdir(parents=True)

        # Add sample data
        data_file = project_root / "data" / "test_data.csv"
        data_file.write_text("region,revenue\nNorth,1000\nSouth,2000\n")

        # Set intent (required for build)
        from kie.state import IntentStorage
        storage = IntentStorage(project_root)
        storage.capture_intent("Test deliverable", captured_via="test")

        yield project_root


def test_build_blocks_without_theme(temp_project):
    """Test that /build blocks when theme is not set (no stdin attempt)."""
    handler = CommandHandler(temp_project)

    # Verify theme is not set
    prefs = OutputPreferences(temp_project)
    assert prefs.get_theme() is None

    # Run build - should block
    result = handler.handle_build(target="all")

    # Verify blocked
    assert not result["success"]
    assert result.get("blocked") is True
    assert "theme" in result["message"].lower()
    assert "/theme" in result["message"].lower()


def test_build_succeeds_with_theme_set(temp_project):
    """Test that /build succeeds when theme is set."""
    handler = CommandHandler(temp_project)

    # Create minimal spec
    import yaml
    spec = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics",
    }
    spec_path = temp_project / "project_state" / "spec.yaml"
    with open(spec_path, "w") as f:
        yaml.dump(spec, f)

    # Set theme
    prefs = OutputPreferences(temp_project)
    prefs.set_theme("dark", source="test")

    # Verify theme is set
    assert prefs.get_theme() == "dark"

    # Run build - should succeed (or at least not block on theme)
    result = handler.handle_build(target="all")

    # Verify it didn't block on theme
    # (might fail for other reasons like missing data, but shouldn't be theme-blocked)
    assert not result.get("blocked") or "theme" not in result.get("message", "").lower()


def test_go_full_blocks_at_build_without_theme(temp_project):
    """Test that /go --full blocks at build stage when theme is not set."""
    handler = CommandHandler(temp_project)

    # Create minimal spec
    import yaml
    spec = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics",
    }
    spec_path = temp_project / "project_state" / "spec.yaml"
    with open(spec_path, "w") as f:
        yaml.dump(spec, f)

    # Create rails_state with completed stages
    rails_state_path = temp_project / "project_state" / "rails_state.json"
    import json
    rails_state = {
        "completed_stages": ["startkie", "spec", "eda", "analyze"],
        "workflow_started": True
    }
    with open(rails_state_path, "w") as f:
        json.dump(rails_state, f)

    # Verify theme is not set
    prefs = OutputPreferences(temp_project)
    assert prefs.get_theme() is None

    # Execute full mode - should try to execute build stage next
    result = handler._execute_full_mode(
        completed=["startkie", "spec", "eda", "analyze"],
        workflow_started=True
    )

    # Should block at build stage
    assert result["executed_command"] == "full"
    assert result.get("blocked_at") == "build"
    assert "theme" in result["message"].lower()


def test_go_single_step_blocks_at_build_without_theme(temp_project):
    """Test that /go (single step) blocks at build when theme is not set."""
    handler = CommandHandler(temp_project)

    # Complete stages up to analyze
    handler.handle_startkie()
    handler.handle_spec(init=True)
    handler.handle_eda()
    handler.handle_analyze()

    # Verify theme is not set
    prefs = OutputPreferences(temp_project)
    assert prefs.get_theme() is None

    # Next step should be build - should block
    from kie.state import load_rails_state
    rails_state = load_rails_state(temp_project)
    completed = rails_state.get("completed_stages", [])

    result = handler._execute_single_step(completed, workflow_started=True)

    # Should block (build will return blocked result)
    assert not result["success"]
    assert result.get("blocked") is True


def test_theme_gate_message_has_clear_instructions(temp_project, capsys):
    """Test that theme gate block message has clear instructions."""
    handler = CommandHandler(temp_project)

    # Run build without theme
    result = handler.handle_build(target="all")

    # Capture printed output
    captured = capsys.readouterr()

    # Verify clear instructions are printed
    assert "OUTPUT THEME REQUIRED" in captured.out
    assert "/theme light" in captured.out
    assert "/theme dark" in captured.out


def test_no_stdin_attempt_in_build(temp_project, monkeypatch):
    """Test that /build never attempts to call input() (no stdin)."""
    # Mock input() to raise error if called
    def mock_input(*args, **kwargs):
        raise AssertionError("input() was called - theme gate should block instead!")

    monkeypatch.setattr("builtins.input", mock_input)

    handler = CommandHandler(temp_project)

    # Run build - should block cleanly without calling input()
    result = handler.handle_build(target="all")

    # Verify blocked (not crashed)
    assert not result["success"]
    assert result.get("blocked") is True
