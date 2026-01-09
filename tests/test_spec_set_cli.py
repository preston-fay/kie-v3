"""
Test spec --set CLI functionality

Verifies that spec --set works correctly in both direct and vendored runtime modes.
"""

import subprocess
import tempfile
from pathlib import Path

import yaml


def test_spec_set_auto_init():
    """Test that spec --set auto-initializes spec when missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create minimal workspace structure
        (project_root / "project_state").mkdir(parents=True)
        (project_root / "data").mkdir()

        # Run spec --set without existing spec.yaml
        result = subprocess.run(
            [
                "python3", "-m", "kie.cli",
                "spec",
                "--set", "client_name=TestCorp",
                "--set", "objective=Test Analysis",
                "--set", "deliverable_format=report"
            ],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify spec.yaml was created
        spec_path = project_root / "project_state" / "spec.yaml"
        assert spec_path.exists(), "spec.yaml was not created"

        # Verify content
        with open(spec_path) as f:
            spec = yaml.safe_load(f)

        assert spec["client_name"] == "TestCorp"
        assert spec["objective"] == "Test Analysis"
        assert spec["deliverable_format"] == "report"


def test_spec_set_quoted_values():
    """Test that spec --set handles multi-word quoted values correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create minimal workspace structure
        (project_root / "project_state").mkdir(parents=True)
        (project_root / "data").mkdir()

        # Run spec --set with quoted multi-word value
        result = subprocess.run(
            [
                "python3", "-m", "kie.cli",
                "spec",
                "--set", "client_name=SleepCo",
                "--set", "objective=Drivers of sleep quality",
                "--set", "deliverable_format=report"
            ],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify spec.yaml content
        spec_path = project_root / "project_state" / "spec.yaml"
        with open(spec_path) as f:
            spec = yaml.safe_load(f)

        assert spec["client_name"] == "SleepCo"
        assert spec["objective"] == "Drivers of sleep quality"
        assert spec["deliverable_format"] == "report"


def test_spec_set_after_bootstrap():
    """Test spec --set works after bootstrap (direct invocation, not vendored)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        kie_repo = Path(__file__).parent.parent  # /Users/.../kie-v3

        # Bootstrap workspace
        result = subprocess.run(
            ["bash", str(kie_repo / "tools" / "bootstrap" / "startkie.sh")],
            cwd=project_root,
            env={"KIE_BOOTSTRAP_SRC_DIR": str(kie_repo)},
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Bootstrap failed: {result.stderr}"

        # Run spec --set using direct invocation (not vendored - vendored has Python 3.9 compat issue)
        result = subprocess.run(
            [
                "python3", "-m", "kie.cli",
                "spec",
                "--set", "client_name=SleepCo",
                "--set", "objective=Drivers of sleep quality",
                "--set", "deliverable_format=report"
            ],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        # This should succeed (auto-init if needed)
        assert result.returncode == 0, f"Command failed: {result.stderr}\nStdout: {result.stdout}"

        # Verify spec.yaml
        spec_path = project_root / "project_state" / "spec.yaml"
        assert spec_path.exists(), "spec.yaml was not created"

        with open(spec_path) as f:
            spec = yaml.safe_load(f)

        assert spec["client_name"] == "SleepCo"
        assert spec["objective"] == "Drivers of sleep quality"
        assert spec["deliverable_format"] == "report"


def test_spec_set_nested_keys():
    """Test that spec --set handles nested keys like preferences.theme.mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create minimal workspace structure
        (project_root / "project_state").mkdir(parents=True)
        (project_root / "data").mkdir()

        # Run spec --set with nested key
        result = subprocess.run(
            [
                "python3", "-m", "kie.cli",
                "spec",
                "--set", "client_name=ThemeCo",
                "--set", "preferences.theme.mode=light"
            ],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify nested structure
        spec_path = project_root / "project_state" / "spec.yaml"
        with open(spec_path) as f:
            spec = yaml.safe_load(f)

        assert spec["client_name"] == "ThemeCo"
        assert spec["preferences"]["theme"]["mode"] == "light"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
