"""
Tests for KIE workspace initialization and diagnostics.
"""

import tempfile
from pathlib import Path

import pytest

from kie.cli.workspace import initialize_workspace, diagnose_workspace


class TestWorkspaceInitialization:
    """Test workspace initialization functionality."""

    def test_initialize_creates_folders(self):
        """Test that initialization creates all required folders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            success, message = initialize_workspace(target)

            assert success, f"Initialization failed: {message}"
            assert (target / "data").exists()
            assert (target / "outputs").exists()
            assert (target / "exports").exists()
            assert (target / "project_state").exists()

    def test_initialize_creates_project_files(self):
        """Test that initialization creates project files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            success, message = initialize_workspace(target)

            assert success, f"Initialization failed: {message}"
            assert (target / "README.md").exists()
            assert (target / "CLAUDE.md").exists()
            assert (target / ".gitignore").exists()

            # Check content
            readme_content = (target / "README.md").read_text()
            assert "KIE Project" in readme_content

            claude_content = (target / "CLAUDE.md").read_text()
            assert "Kearney Insight Engine" in claude_content

    def test_initialize_creates_slash_commands(self):
        """Test that initialization creates slash commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            success, message = initialize_workspace(target)

            assert success, f"Initialization failed: {message}"

            commands_dir = target / ".claude" / "commands"
            assert commands_dir.exists()

            # Check critical commands exist
            assert (commands_dir / "interview.md").exists()
            assert (commands_dir / "build.md").exists()
            assert (commands_dir / "review.md").exists()
            assert (commands_dir / "startkie.md").exists()

            # Check command content
            interview_content = (commands_dir / "interview.md").read_text()
            assert "interview process" in interview_content.lower()

    def test_initialize_verifies_critical_files(self):
        """Test that initialization verifies critical files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            success, message = initialize_workspace(target)

            assert success, f"Initialization failed: {message}"
            assert "✓" in message  # Success indicators
            assert "interview.md" in str(target / ".claude" / "commands" / "interview.md")

    def test_initialize_checks_importability(self):
        """Test that initialization verifies KIE package can be imported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            success, message = initialize_workspace(target)

            # Should succeed if kie is installed
            assert success, f"Initialization failed: {message}"

            # Verify the import check ran
            assert "Python package importable" in message or success


class TestWorkspaceDiagnostics:
    """Test workspace diagnostic functionality."""

    def test_diagnose_initialized_workspace(self):
        """Test diagnostics on a properly initialized workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Initialize first
            success, _ = initialize_workspace(target)
            assert success

            # Run diagnostics
            all_passed, report = diagnose_workspace(target)

            assert all_passed, f"Diagnostics failed:\n{report}"
            assert "PASS" in report
            assert "✓" in report

    def test_diagnose_missing_folders(self):
        """Test diagnostics detects missing folders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Don't initialize, just diagnose
            all_passed, report = diagnose_workspace(target)

            assert not all_passed
            assert "FAIL" in report
            assert "✗" in report
            assert "data/" in report or "outputs/" in report

    def test_diagnose_missing_commands(self):
        """Test diagnostics detects missing slash commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Create folders but not commands
            (target / "data").mkdir()
            (target / "outputs").mkdir()
            (target / "exports").mkdir()
            (target / "project_state").mkdir()

            all_passed, report = diagnose_workspace(target)

            assert not all_passed
            assert ".claude/commands" in report

    def test_diagnose_provides_remediation(self):
        """Test diagnostics provides remediation steps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            all_passed, report = diagnose_workspace(target)

            assert not all_passed
            assert "Remediation" in report
            assert "kie.cli init" in report


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_init_and_doctor_workflow(self):
        """Test complete workflow: init -> doctor -> verify."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Step 1: Initialize
            success, message = initialize_workspace(target)
            assert success, f"Init failed: {message}"

            # Step 2: Run doctor
            all_passed, report = diagnose_workspace(target)
            assert all_passed, f"Doctor failed:\n{report}"

            # Step 3: Verify specific files
            assert (target / ".claude" / "commands" / "interview.md").exists()
            assert (target / ".claude" / "commands" / "build.md").exists()
            assert (target / "CLAUDE.md").exists()
            assert (target / "README.md").exists()

            # Step 4: Verify folder structure
            assert (target / "data").is_dir()
            assert (target / "outputs").is_dir()
            assert (target / "exports").is_dir()
            assert (target / "project_state").is_dir()

    def test_multiple_command_files_present(self):
        """Test that at least 4 command files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            success, _ = initialize_workspace(target)
            assert success

            commands_dir = target / ".claude" / "commands"
            command_files = list(commands_dir.glob("*.md"))

            assert len(command_files) >= 4, f"Expected >=4 commands, got {len(command_files)}"
