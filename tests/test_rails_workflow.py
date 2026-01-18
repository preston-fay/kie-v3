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

        # Install sample data (now via separate command, not bundled in startkie)
        result = subprocess.run(
            ["bash", "-c", 'PYTHONPATH=".kie/src" python3 -m kie.cli sampledata install'],
            cwd=workspace,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"sampledata install failed: {result.stderr}"
        assert (workspace / "data" / "sample_data.csv").exists(), "sample_data.csv not created by sampledata install"

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
        # EDA outputs now go to outputs/internal/
        assert (workspace / "outputs" / "internal" / "eda_profile.yaml").exists(), "EDA output not created"

        # Step 4b: Set intent (required by Intent Gate)
        print("\nStep 4b: Setting intent...")
        result = subprocess.run(
            ["bash", "-c", 'PYTHONPATH=".kie/src" python3 -m kie.cli intent set "Analyze sample data for testing"'],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"intent set failed with code {result.returncode}"

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
        # Analyze outputs now go to outputs/internal/ - canonical name is insights.yaml
        internal_dir = workspace / "outputs" / "internal"
        assert (internal_dir / "insights.yaml").exists() or (internal_dir / "insights_catalog.json").exists(), "Analyze output not created"

        print(f"\n{'='*60}")
        print("✓ ALL RAILS WORKFLOW TESTS PASSED")
        print(f"{'='*60}\n")


def test_template_parity():
    """Test that manually copying project_template produces a valid Rails workspace.

    This simulates Claude Code fallback behavior when it bootstraps by copying files
    instead of executing the CLI startkie command.
    """
    import shutil

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"\n{'='*60}")
        print(f"Testing template parity in: {workspace}")
        print(f"{'='*60}\n")

        # Step 1: Find project_template
        print("Step 1: Locating project_template...")
        # Assume we're running from repo root or tests/
        repo_root = Path(__file__).parent.parent
        project_template = repo_root / "project_template"

        assert project_template.exists(), "project_template not found in repo"
        print(f"✓ Found project_template at {project_template}")

        # Step 2: Manually copy project_template (simulates CC fallback)
        print("\nStep 2: Manually copying project_template contents...")
        for item in project_template.iterdir():
            if item.name in [".git", "__pycache__", ".DS_Store"]:
                continue
            target = workspace / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)
        print(f"✓ Copied {len(list(workspace.iterdir()))} items")

        # Step 3: Verify .claude/commands exists with wrappers
        print("\nStep 3: Verifying command wrappers...")
        commands_dir = workspace / ".claude" / "commands"
        assert commands_dir.exists(), ".claude/commands/ not created"

        required_commands = [
            "startkie.md", "eda.md", "analyze.md", "interview.md", "map.md",
            "build.md", "status.md", "spec.md", "preview.md", "validate.md",
        ]
        for cmd in required_commands:
            cmd_path = commands_dir / cmd
            assert cmd_path.exists(), f"Command wrapper {cmd} not found"
            content = cmd_path.read_text()
            assert "python3 -m kie.cli" in content, f"{cmd} doesn't contain CLI invocation"
        print(f"✓ All {len(required_commands)} command wrappers present and valid")

        # Step 4: Verify intro exists at top of both README.md and CLAUDE.md
        print("\nStep 4: Verifying intro in README.md and CLAUDE.md...")
        readme = workspace / "README.md"
        claude_md = workspace / "CLAUDE.md"

        assert readme.exists(), "README.md not found"
        assert claude_md.exists(), "CLAUDE.md not found"

        readme_content = readme.read_text()
        claude_content = claude_md.read_text()

        # Check first 30 lines contain command table header
        readme_top = "\n".join(readme_content.split("\n")[:30])
        claude_top = "\n".join(claude_content.split("\n")[:30])

        assert "Available Commands" in readme_top, "README.md missing command table in first 30 lines"
        assert "Available Commands" in claude_top, "CLAUDE.md missing command table in first 30 lines"
        assert "/eda" in readme_top and "/analyze" in readme_top, "README.md missing command examples"
        assert "/eda" in claude_top and "/analyze" in claude_top, "CLAUDE.md missing command examples"
        print("✓ Intro present at top of both files")

        # Step 5: Copy fixture data (same as CLI path does)
        print("\nStep 5: Copying fixture data...")
        kie_package = repo_root / "kie"
        source_fixture = kie_package / "templates" / "fixture_data.csv"
        if source_fixture.exists():
            target_fixture = workspace / "data" / "sample_data.csv"
            shutil.copy(source_fixture, target_fixture)
            print(f"✓ Copied sample_data.csv")

        # Step 6: Run railscheck
        print("\nStep 6: Running railscheck...")
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

        print(f"\n{'='*60}")
        print("✓ TEMPLATE PARITY TEST PASSED")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    test_rails_workflow()
    test_template_parity()
