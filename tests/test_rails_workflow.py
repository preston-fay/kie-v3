"""
Test Rails workflow - verify deterministic command execution.

This test creates a temporary workspace, runs startkie, and verifies that:
1. The workspace is properly initialized
2. railscheck passes
3. Core commands (eda, analyze) execute successfully
"""

import subprocess
import tempfile
from pathlib import Path


def test_rails_workflow():
    """Test complete Rails workflow from scratch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"\n{'='*60}")
        print(f"Testing Rails workflow in: {workspace}")
        print(f"{'='*60}\n")

        # Step 1: Run startkie
        print("Step 1: Running startkie...")
        result = subprocess.run(
            ["python3", "-m", "kie.cli", "startkie"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        assert result.returncode == 0, f"startkie failed with code {result.returncode}"
        assert (workspace / ".claude" / "commands").exists(), ".claude/commands/ not created"
        assert (workspace / "data" / "sample_data.csv").exists(), "sample_data.csv not created"

        # Step 2: Verify command wrappers exist
        print("\nStep 2: Verifying command wrappers...")
        required_commands = [
            "startkie.md",
            "eda.md",
            "analyze.md",
            "interview.md",
            "map.md",
            "build.md",
            "status.md",
            "spec.md",
            "preview.md",
            "validate.md",
        ]
        commands_dir = workspace / ".claude" / "commands"
        for cmd in required_commands:
            cmd_path = commands_dir / cmd
            assert cmd_path.exists(), f"Command wrapper {cmd} not found"
            # Verify it contains CLI invocation
            content = cmd_path.read_text()
            assert "python3 -m kie.cli" in content, f"{cmd} doesn't contain CLI invocation"
        print(f"✓ All {len(required_commands)} command wrappers present and valid")

        # Step 3: Run railscheck
        print("\nStep 3: Running railscheck...")
        result = subprocess.run(
            ["python3", "-m", "kie.cli", "railscheck"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        assert result.returncode == 0, f"railscheck failed with code {result.returncode}"
        assert "✓ PASS" in result.stdout, "railscheck did not pass"

        # Step 4: Run /eda
        print("\nStep 4: Running /eda...")
        result = subprocess.run(
            ["python3", "-m", "kie.cli", "eda"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        assert result.returncode == 0, f"/eda failed with code {result.returncode}"
        assert (workspace / "outputs" / "eda_profile.yaml").exists(), "EDA output not created"

        # Step 5: Run /analyze
        print("\nStep 5: Running /analyze...")
        result = subprocess.run(
            ["python3", "-m", "kie.cli", "analyze"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        assert result.returncode == 0, f"/analyze failed with code {result.returncode}"
        assert (workspace / "outputs" / "insights.yaml").exists(), "Analyze output not created"

        print(f"\n{'='*60}")
        print("✓ ALL RAILS WORKFLOW TESTS PASSED")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    test_rails_workflow()
