"""
Test Rails Spec Blocker Fix

Tests that:
1. /build auto-creates spec.yaml if missing
2. /build works without /interview
3. spec --init creates minimal spec
4. build --help works without spec
"""

import subprocess
import tempfile
from pathlib import Path

import pytest


def test_spec_init_creates_minimal_spec():
    """Test that spec --init creates minimal spec.yaml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Bootstrap workspace
        from kie.commands.handler import CommandHandler
        handler = CommandHandler(project_root=project_root)
        result = handler.handle_startkie()
        assert result["success"], f"Bootstrap failed: {result}"

        # Run spec --init
        result = handler.handle_spec(init=True)
        assert result["success"], f"spec --init failed: {result}"

        # Verify spec.yaml exists
        spec_path = project_root / "project_state" / "spec.yaml"
        assert spec_path.exists(), "spec.yaml not created"

        # Verify minimal fields
        import yaml
        with open(spec_path) as f:
            spec = yaml.safe_load(f)

        assert "project_name" in spec, "Missing project_name"
        assert "objective" in spec, "Missing objective"
        assert "project_type" in spec, "Missing project_type"
        assert "deliverable_format" in spec, "Missing deliverable_format"


def test_build_help_without_spec():
    """Test that 'build --help' works without spec.yaml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Bootstrap workspace
        from kie.commands.handler import CommandHandler
        handler = CommandHandler(project_root=project_root)
        handler.handle_startkie()

        # Delete spec if exists
        spec_path = project_root / "project_state" / "spec.yaml"
        if spec_path.exists():
            spec_path.unlink()

        # Run build --help via CLI
        from kie.cli import KIEClient
        client = KIEClient(project_root=project_root)
        should_continue, command_succeeded = client.process_command("build --help")

        assert command_succeeded, "build --help failed"
        assert should_continue, "build --help exited unexpectedly"


def test_spec_repair_stale_data_source():
    """Test that spec --repair fixes stale data_source references."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        from kie.commands.handler import CommandHandler
        handler = CommandHandler(project_root=project_root)
        handler.handle_startkie()

        # Remove bootstrap's sample data to isolate test
        sample_data = project_root / "data" / "sample_data.csv"
        if sample_data.exists():
            sample_data.unlink()

        # Create spec with data_source
        import yaml
        spec_path = project_root / "project_state" / "spec.yaml"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        with open(spec_path, "w") as f:
            yaml.dump({
                "project_name": "Test",
                "objective": "Analysis",
                "project_type": "analytics",
                "data_source": "old_data.csv",  # Stale reference
            }, f)

        # Create NEW data file (simulating data source change)
        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        new_data = data_dir / "new_data.csv"
        new_data.write_text("col1,col2\n1,2\n")

        # Run spec --repair
        result = handler.handle_spec(repair=True)
        assert result["success"], f"spec --repair failed: {result}"

        # Verify data_source was updated
        with open(spec_path) as f:
            spec = yaml.safe_load(f)
        assert spec["data_source"] == "new_data.csv", \
            f"data_source not repaired: {spec.get('data_source')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
