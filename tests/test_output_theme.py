#!/usr/bin/env python3
"""
Unit tests for output theme preference functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_theme_storage_and_retrieval():
    """Test that theme preference can be stored and retrieved."""
    from kie.preferences import OutputPreferences

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        prefs = OutputPreferences(project_root)

        # Initially no theme set
        assert prefs.get_theme() is None
        assert not prefs.is_theme_set()

        # Set light theme
        prefs.set_theme("light")
        assert prefs.get_theme() == "light"
        assert prefs.is_theme_set()

        # Create new instance - should persist
        prefs2 = OutputPreferences(project_root)
        assert prefs2.get_theme() == "light"

        # Change to dark theme
        prefs2.set_theme("dark")
        assert prefs2.get_theme() == "dark"


def test_theme_validation():
    """Test that invalid themes are rejected."""
    from kie.preferences import OutputPreferences

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        prefs = OutputPreferences(project_root)

        # Invalid theme should raise ValueError
        with pytest.raises(ValueError):
            prefs.set_theme("invalid")

        with pytest.raises(ValueError):
            prefs.set_theme("green")

        # Valid themes should work
        prefs.set_theme("light")
        assert prefs.get_theme() == "light"

        prefs.set_theme("dark")
        assert prefs.get_theme() == "dark"


def test_preferences_file_format():
    """Test that preferences are stored in correct format."""
    from kie.preferences import OutputPreferences
    import yaml

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        prefs = OutputPreferences(project_root)

        prefs.set_theme("dark", source="test")

        # Check file exists
        prefs_file = project_root / "project_state" / "output_preferences.yaml"
        assert prefs_file.exists()

        # Check file structure
        with open(prefs_file) as f:
            data = yaml.safe_load(f)

        assert data["output_theme"] == "dark"
        assert data["source"] == "test"
        assert "set_at" in data


def test_build_prompts_for_theme_when_missing():
    """Test that /build prompts for theme when not set."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Bootstrap workspace
        handler.handle_startkie()

        # Mock user input to select dark theme
        with patch("builtins.input", return_value="2"):
            # Attempt build - should prompt for theme
            # This will fail due to missing data, but should set theme first
            try:
                result = handler.handle_build(target="presentation")
            except Exception:
                pass

        # Check theme was set
        from kie.preferences import OutputPreferences
        prefs = OutputPreferences(project_root)
        assert prefs.get_theme() == "dark"


def test_build_skips_prompt_when_theme_set():
    """Test that /build proceeds without prompt when theme already set."""
    from kie.commands.handler import CommandHandler
    from kie.preferences import OutputPreferences

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Bootstrap workspace
        handler.handle_startkie()

        # Set theme first
        prefs = OutputPreferences(project_root)
        prefs.set_theme("light")

        # Mock input - should NOT be called since theme is set
        with patch("builtins.input") as mock_input:
            # Attempt build
            try:
                result = handler.handle_build(target="presentation")
            except Exception:
                pass

            # Input should not have been called (no prompt)
            mock_input.assert_not_called()


def test_theme_command_set_theme():
    """Test /theme command to set theme."""
    from kie.commands.handler import CommandHandler
    from kie.preferences import OutputPreferences

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Set theme via command
        result = handler.handle_theme(set_theme="dark")
        assert result["success"] is True
        assert result["theme"] == "dark"

        # Verify persisted
        prefs = OutputPreferences(project_root)
        assert prefs.get_theme() == "dark"

        # Change theme
        result = handler.handle_theme(set_theme="light")
        assert result["success"] is True
        assert result["theme"] == "light"

        prefs2 = OutputPreferences(project_root)
        assert prefs2.get_theme() == "light"


def test_theme_command_show_current():
    """Test /theme command to show current theme."""
    from kie.commands.handler import CommandHandler
    from kie.preferences import OutputPreferences

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # No theme set
        result = handler.handle_theme()
        assert result["success"] is True
        assert result["theme"] is None

        # Set theme
        prefs = OutputPreferences(project_root)
        prefs.set_theme("dark")

        # Show theme
        result = handler.handle_theme()
        assert result["success"] is True
        assert result["theme"] == "dark"


def test_theme_command_rejects_invalid():
    """Test /theme command rejects invalid themes."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Invalid theme
        result = handler.handle_theme(set_theme="invalid")
        assert result["success"] is False


def test_status_shows_theme():
    """Test /status includes output_theme."""
    from kie.commands.handler import CommandHandler
    from kie.preferences import OutputPreferences

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)
        handler.handle_startkie()

        # No theme set
        status = handler.handle_status()
        assert "output_theme" in status
        assert status["output_theme"] is None

        # Set theme
        prefs = OutputPreferences(project_root)
        prefs.set_theme("light")

        # Status should show theme
        status = handler.handle_status()
        assert status["output_theme"] == "light"


def test_no_rails_mutation():
    """Test that preference storage does NOT mutate rails_state.json."""
    from kie.commands.handler import CommandHandler
    from kie.preferences import OutputPreferences
    import json

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)
        handler.handle_startkie()

        # Record original rails state
        rails_path = project_root / "project_state" / "rails_state.json"
        original_rails = rails_path.read_text()

        # Set theme preference
        prefs = OutputPreferences(project_root)
        prefs.set_theme("dark")

        # Rails state should be unchanged
        current_rails = rails_path.read_text()
        assert current_rails == original_rails

        # Verify theme was stored elsewhere
        prefs_path = project_root / "project_state" / "output_preferences.yaml"
        assert prefs_path.exists()
        assert prefs.get_theme() == "dark"
