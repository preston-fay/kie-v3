"""Test bootstrap refresh mode for upgrading existing workspaces."""

import hashlib
import subprocess
import tempfile
from pathlib import Path

import pytest


def compute_file_hash(filepath: Path) -> str:
    """Compute MD5 hash of a file."""
    return hashlib.md5(filepath.read_bytes()).hexdigest()


def test_bootstrap_refresh_mode():
    """Test that refresh mode upgrades existing workspace without overwriting user files."""
    # Get path to kie-v3 repo root
    repo_root = Path(__file__).parent.parent.resolve()
    bootstrap_script = repo_root / "tools" / "bootstrap" / "startkie.sh"

    assert bootstrap_script.exists(), f"Bootstrap script not found at {bootstrap_script}"

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Step 1: Create a simulated old workspace with legacy command files
        print(f"\n📁 Creating simulated old workspace at {workspace}")

        # Create basic structure
        (workspace / ".claude" / "commands").mkdir(parents=True)
        (workspace / "project_state").mkdir(parents=True)
        (workspace / "data").mkdir(parents=True)

        # Add CLAUDE.md with KIE marker (simulates existing project)
        claude_md_content = "# KIE Project\n\nThis is an existing workspace.\n"
        (workspace / "CLAUDE.md").write_text(claude_md_content)
        original_claude_hash = compute_file_hash(workspace / "CLAUDE.md")

        # Add README with user content
        readme_content = "# My Custom README\n\nUser wrote this.\n"
        (workspace / "README.md").write_text(readme_content)
        original_readme_hash = compute_file_hash(workspace / "README.md")

        # Add legacy command files (simulate old workspace)
        legacy_files = ["interview_v3.md", "status_v3.md", "validate_v3.md", "help.md"]
        for legacy_file in legacy_files:
            (workspace / ".claude" / "commands" / legacy_file).write_text(
                f"---\nname: {legacy_file.replace('.md', '')}\n---\nOld command\n"
            )

        # Verify setup
        assert (workspace / "CLAUDE.md").exists()
        assert (workspace / ".claude" / "commands" / "interview_v3.md").exists()
        assert not (workspace / ".claude" / "commands" / "rails.md").exists()
        assert not (workspace / "project_state" / "rails_state.json").exists()

        print("✓ Old workspace created with legacy files")

        # Step 2: Run bootstrap script in REFRESH mode
        print(f"\n🔄 Running bootstrap refresh mode...")
        result = subprocess.run(
            ["bash", str(bootstrap_script)],
            cwd=workspace,
            env={
                "KIE_BOOTSTRAP_REFRESH": "1",
                "KIE_BOOTSTRAP_SRC_DIR": str(repo_root),
                "PATH": subprocess.os.environ.get("PATH", ""),
            },
            capture_output=True,
            text=True,
        )

        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        assert result.returncode == 0, f"Bootstrap refresh failed: {result.stderr}"
        assert "REFRESH MODE" in result.stdout
        assert "Workspace upgraded successfully" in result.stdout

        # Step 3: Verify upgrade results
        print("\n✅ Verifying upgrade results...")

        # Check that vendored runtime exists
        assert (workspace / ".kie" / "src" / "kie").exists(), "Vendored runtime missing"
        print("✓ Vendored runtime present")

        # Check that rails.md now exists in workspace
        rails_md = workspace / ".claude" / "commands" / "rails.md"
        assert rails_md.exists(), "rails.md not copied to workspace"
        print("✓ rails.md exists")

        # Verify rails.md has PYTHONPATH prefix
        rails_content = rails_md.read_text()
        assert 'PYTHONPATH=".kie/src"' in rails_content, "rails.md not configured for vendored runtime"
        print("✓ rails.md configured for vendored runtime")

        # Check that legacy files were removed
        for legacy_file in legacy_files:
            legacy_path = workspace / ".claude" / "commands" / legacy_file
            assert not legacy_path.exists(), f"Legacy file {legacy_file} not removed"
        print("✓ All legacy *_v3.md files removed")

        # Check that rails_state.json exists
        rails_state = workspace / "project_state" / "rails_state.json"
        assert rails_state.exists(), "rails_state.json not created"
        print("✓ rails_state.json exists")

        # Check that user files were NOT overwritten
        current_claude_hash = compute_file_hash(workspace / "CLAUDE.md")
        current_readme_hash = compute_file_hash(workspace / "README.md")

        assert current_claude_hash == original_claude_hash, "CLAUDE.md was overwritten (should be preserved)"
        assert current_readme_hash == original_readme_hash, "README.md was overwritten (should be preserved)"
        print("✓ User files (CLAUDE.md, README.md) not overwritten")

        # Verify other expected commands exist
        expected_commands = ["interview.md", "eda.md", "status.md", "spec.md"]
        for cmd in expected_commands:
            cmd_path = workspace / ".claude" / "commands" / cmd
            assert cmd_path.exists(), f"Expected command {cmd} missing"
        print(f"✓ All expected commands present: {expected_commands}")

        print("\n✅ Bootstrap refresh mode test PASSED")


def test_bootstrap_refresh_without_flag():
    """Test that without KIE_BOOTSTRAP_REFRESH, existing workspace exits early."""
    repo_root = Path(__file__).parent.parent.resolve()
    bootstrap_script = repo_root / "tools" / "bootstrap" / "startkie.sh"

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create basic KIE marker
        (workspace / "CLAUDE.md").write_text("# KIE Project\n")

        # Run without refresh flag
        result = subprocess.run(
            ["bash", str(bootstrap_script)],
            cwd=workspace,
            env={
                "PATH": subprocess.os.environ.get("PATH", ""),
            },
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "already a KIE project" in result.stdout
        assert "REFRESH MODE" not in result.stdout
        assert "Use KIE_BOOTSTRAP_REFRESH=1" in result.stdout
        print("\n✓ Without flag: exits early with hint about refresh mode")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
