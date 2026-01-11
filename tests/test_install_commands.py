"""
Unit tests for install_commands functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_install_commands_creates_directory(monkeypatch):
    """Test that install_commands creates ~/.claude/commands if missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        fake_home = temp_path / "fake_home"
        fake_home.mkdir()

        # Monkeypatch Path.home() to return our fake home
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Import and run install_commands
        from kie.cli import install_commands

        with patch("sys.exit"):
            install_commands()

        # Verify directory was created
        user_commands_dir = fake_home / ".claude" / "commands"
        assert user_commands_dir.exists()
        assert user_commands_dir.is_dir()


def test_install_commands_copies_files(monkeypatch):
    """Test that install_commands copies command files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        fake_home = temp_path / "fake_home"
        fake_home.mkdir()

        # Monkeypatch Path.home()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Import and run install_commands
        from kie.cli import install_commands

        with patch("sys.exit"):
            install_commands()

        # Verify files were copied
        user_commands_dir = fake_home / ".claude" / "commands"

        expected_commands = [
            "eda.md", "rails.md", "go.md", "spec.md", "intent.md",
            "status.md", "interview.md", "analyze.md",
            "build.md", "preview.md", "validate.md",
            "map.md", "doctor.md", "sampledata.md"
        ]

        for cmd_file in expected_commands:
            cmd_path = user_commands_dir / cmd_file
            assert cmd_path.exists(), f"Command file {cmd_file} not installed"
            assert cmd_path.is_file()


def test_install_commands_adds_header(monkeypatch):
    """Test that install_commands adds metadata header to files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        fake_home = temp_path / "fake_home"
        fake_home.mkdir()

        # Monkeypatch Path.home()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Import and run install_commands
        from kie.cli import install_commands

        with patch("sys.exit"):
            install_commands()

        # Verify header was added
        user_commands_dir = fake_home / ".claude" / "commands"
        eda_file = user_commands_dir / "eda.md"

        content = eda_file.read_text()
        assert "installed_from_repo: preston-fay/kie-v3" in content
        assert "installed_at:" in content
        assert "source_commit:" in content


def test_install_commands_preserves_startkie(monkeypatch):
    """Test that install_commands doesn't overwrite existing startkie.md."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        fake_home = temp_path / "fake_home"
        fake_home.mkdir()

        # Monkeypatch Path.home()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create .claude/commands directory with existing startkie.md
        user_commands_dir = fake_home / ".claude" / "commands"
        user_commands_dir.mkdir(parents=True)

        startkie_path = user_commands_dir / "startkie.md"
        original_content = "USER CUSTOMIZED STARTKIE"
        startkie_path.write_text(original_content)

        # Import and run install_commands
        from kie.cli import install_commands

        with patch("sys.exit"):
            install_commands()

        # Verify startkie.md was NOT overwritten
        assert startkie_path.read_text() == original_content


def test_install_commands_workspace_detection(monkeypatch):
    """Test that installed commands include workspace detection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        fake_home = temp_path / "fake_home"
        fake_home.mkdir()

        # Monkeypatch Path.home()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Import and run install_commands
        from kie.cli import install_commands

        with patch("sys.exit"):
            install_commands()

        # Verify workspace detection in installed files
        user_commands_dir = fake_home / ".claude" / "commands"
        eda_file = user_commands_dir / "eda.md"

        content = eda_file.read_text()
        assert '.kie/src' in content
        assert 'Not in a KIE workspace' in content
        assert 'Run /startkie' in content
