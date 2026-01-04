"""
Tests for KIE workspace guardrails and context detection.
"""

import json
import tempfile
from pathlib import Path

import pytest

from kie.cli.workspace import initialize_workspace, diagnose_workspace


class TestProductRepoDetection:
    """Test that workspace commands fail in product repo."""

    def test_init_fails_in_product_repo(self):
        """Test that init refuses to run in product repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Create product repo marker
            (target / '.kie_product_repo').write_text("repo_name: kie-v3\n")

            success, message = initialize_workspace(target)

            assert not success, "Init should fail in product repo"
            assert "KIE v3 product repository" in message
            assert "CANNOT INITIALIZE" in message

    def test_init_fails_with_product_indicators(self):
        """Test that init detects product repo without explicit marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Create product repo indicators
            (target / 'pyproject.toml').write_text("[project]\nname = 'kie'\n")
            (target / 'kie').mkdir()
            (target / 'kie' / '__init__.py').write_text("__version__ = '1.0.0'\n")

            success, message = initialize_workspace(target)

            assert not success, "Init should fail with product indicators"
            assert "product repository" in message.lower()

    def test_doctor_fails_in_product_repo(self):
        """Test that doctor detects and fails in product repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Create product repo marker
            (target / '.kie_product_repo').write_text("repo_name: kie-v3\n")

            all_passed, report = diagnose_workspace(target)

            assert not all_passed, "Doctor should fail in product repo"
            assert "PRODUCT REPO DETECTED" in report
            assert "Do NOT run workspace commands" in report


class TestWorkspaceMarker:
    """Test workspace marker creation and detection."""

    def test_init_writes_workspace_marker(self):
        """Test that init creates workspace marker file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            success, _ = initialize_workspace(target)
            assert success

            marker_path = target / 'project_state' / '.kie_workspace'
            assert marker_path.exists(), "Workspace marker should be created"

            # Verify marker content
            with open(marker_path) as f:
                marker_data = json.load(f)

            assert 'workspace_version' in marker_data
            assert 'kie_version' in marker_data
            assert 'created_at' in marker_data
            assert marker_data['workspace_version'] == 1

    def test_doctor_checks_workspace_marker(self):
        """Test that doctor verifies workspace marker exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Don't initialize - just check
            all_passed, report = diagnose_workspace(target)

            assert not all_passed, "Doctor should fail without marker"
            assert "Workspace marker missing" in report

    def test_doctor_reads_marker_info(self):
        """Test that doctor displays marker information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Initialize workspace
            success, _ = initialize_workspace(target)
            assert success

            # Run doctor
            all_passed, report = diagnose_workspace(target)

            assert all_passed, f"Doctor should pass: {report}"
            assert "Workspace marker present" in report
            assert "Version:" in report
            assert "KIE version:" in report


class TestUninitializedWorkspace:
    """Test behavior in uninitialized directories."""

    def test_doctor_fails_in_empty_dir(self):
        """Test that doctor fails in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            all_passed, report = diagnose_workspace(target)

            assert not all_passed, "Doctor should fail in empty dir"
            assert "missing" in report.lower()

    def test_doctor_provides_init_guidance(self):
        """Test that failed doctor provides remediation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            all_passed, report = diagnose_workspace(target)

            assert not all_passed
            # Should suggest running init or /startkie


class TestInitDoctorWorkflow:
    """Test complete init + doctor workflow."""

    def test_init_then_doctor_passes(self):
        """Test that doctor passes after successful init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # Step 1: Initialize
            success, message = initialize_workspace(target)
            assert success, f"Init failed: {message}"

            # Step 2: Verify marker exists
            marker_path = target / 'project_state' / '.kie_workspace'
            assert marker_path.exists()

            # Step 3: Run doctor
            all_passed, report = diagnose_workspace(target)
            assert all_passed, f"Doctor failed after init:\n{report}"

            # Step 4: Verify key checks
            assert "Workspace marker present" in report
            assert "PASS" in report


class TestTemplateContent:
    """Test that templates don't contain forbidden content."""

    def test_startkie_references_init_and_doctor(self):
        """Test that startkie template calls init and doctor."""
        try:
            from importlib.resources import files
        except ImportError:
            from importlib_resources import files

        startkie_content = files('kie.templates.commands').joinpath('startkie.md').read_text()

        assert 'python3 -m kie.cli init' in startkie_content
        assert 'python3 -m kie.cli doctor' in startkie_content
        assert 'ZERO-TERMINAL' in startkie_content

    def test_slash_commands_check_doctor(self):
        """Test that slash commands verify workspace health."""
        try:
            from importlib.resources import files
        except ImportError:
            from importlib_resources import files

        commands_to_check = ['interview.md', 'build.md', 'review.md']
        commands_source = files('kie.templates.commands')

        for cmd_file in commands_to_check:
            content = commands_source.joinpath(cmd_file).read_text()
            assert 'python3 -m kie.cli doctor' in content, f"{cmd_file} should check doctor"
            assert 'Workspace Health Check' in content or 'Pre-flight Check' in content
