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


def test_build_auto_creates_spec():
    """Test that /build auto-creates spec.yaml if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Bootstrap workspace
        from kie.commands.handler import CommandHandler
        handler = CommandHandler(project_root=project_root)
        handler.handle_startkie()

        # Ensure spec does NOT exist
        spec_path = project_root / "project_state" / "spec.yaml"
        if spec_path.exists():
            spec_path.unlink()

        # Run /build (should auto-create spec)
        result = handler.handle_build(target="presentation")

        # Verify spec was created
        assert spec_path.exists(), "build did not create spec.yaml"

        # Verify build succeeded (or failed gracefully)
        # It's OK if build fails due to missing data, but NOT due to missing spec
        if not result["success"]:
            assert "No spec.yaml found" not in result["message"], \
                "build blocked on missing spec - spec should have been auto-created"


def test_build_without_interview():
    """Test that /build works without running /interview first."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Bootstrap workspace
        from kie.commands.handler import CommandHandler
        handler = CommandHandler(project_root=project_root)
        handler.handle_startkie()

        # Copy sample data
        import shutil
        from kie import __file__ as kie_init
        kie_package_dir = Path(kie_init).parent
        source_fixture = kie_package_dir / "templates" / "fixture_data.csv"

        # Use sample_data.csv that was copied during bootstrap
        data_dir = project_root / "data"
        assert (data_dir / "sample_data.csv").exists(), "Bootstrap did not copy fixture data"

        # Run /build WITHOUT running /interview
        result = handler.handle_build(target="presentation")

        # Should succeed or fail gracefully (but NOT block on missing spec)
        if not result["success"]:
            assert "No spec.yaml found" not in result["message"], \
                "build blocked on missing spec - should auto-create"
            assert "Run /interview first" not in result["message"], \
                "build requires interview - violates rails requirement"


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


def test_build_auto_repairs_stale_data_source():
    """Test that /build auto-repairs stale data_source before building."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        from kie.commands.handler import CommandHandler
        handler = CommandHandler(project_root=project_root)
        handler.handle_startkie()

        # Remove bootstrap's sample data to isolate test
        sample_data = project_root / "data" / "sample_data.csv"
        if sample_data.exists():
            sample_data.unlink()

        # Create spec with stale data_source
        import yaml
        spec_path = project_root / "project_state" / "spec.yaml"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        with open(spec_path, "w") as f:
            yaml.dump({
                "project_name": "Test",
                "objective": "Analysis",
                "project_type": "analytics",
                "data_source": "missing.csv",  # Stale
            }, f)

        # Create actual data file
        data_dir = project_root / "data"
        actual_data = data_dir / "actual_data.csv"
        actual_data.write_text("region,revenue\nNorth,1000\nSouth,2000\n")

        # Run build (should auto-repair spec)
        result = handler.handle_build(target="presentation")

        # Verify spec was auto-repaired
        with open(spec_path) as f:
            spec = yaml.safe_load(f)
        assert spec["data_source"] == "actual_data.csv", \
            f"build did not auto-repair data_source: {spec.get('data_source')}"


def test_rails_end_to_end():
    """Test full Rails workflow: bootstrap -> eda -> analyze -> build (no interview)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        from kie.commands.handler import CommandHandler
        handler = CommandHandler(project_root=project_root)

        # 1. Bootstrap
        result = handler.handle_startkie()
        assert result["success"], f"Bootstrap failed: {result}"

        # Verify sample_data.csv exists
        sample_data = project_root / "data" / "sample_data.csv"
        assert sample_data.exists(), "Bootstrap did not copy fixture data"

        # 2. Run EDA
        result = handler.handle_eda()
        assert result["success"], f"EDA failed: {result}"

        # 3. Run analyze
        result = handler.handle_analyze()
        assert result["success"], f"Analyze failed: {result}"

        # 4. Run build WITHOUT interview
        result = handler.handle_build(target="presentation")

        # Verify spec was auto-created
        spec_path = project_root / "project_state" / "spec.yaml"
        assert spec_path.exists(), "build did not auto-create spec.yaml"

        # Build should succeed or fail gracefully (not block on spec)
        if not result["success"]:
            assert "No spec.yaml found" not in result["message"], \
                "build blocked on missing spec"
            assert "Run /interview first" not in result["message"], \
                "build requires interview"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
