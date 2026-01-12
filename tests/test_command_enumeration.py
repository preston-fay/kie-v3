"""
Test command enumeration - verify dynamic command discovery.

This test ensures that:
1. Bootstrap script enumerates all commands without hardcoding
2. railscheck enumerates all commands without hardcoding
3. Adding a new command file makes it appear in the enumerated list
"""

import subprocess
import tempfile
from pathlib import Path
import shutil


def test_bootstrap_enumerates_all_commands():
    """Test that bootstrap script discovers all commands dynamically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"\n{'='*60}")
        print(f"Testing bootstrap command enumeration in: {workspace}")
        print(f"{'='*60}\n")

        # Get repo root
        repo_root = Path(__file__).parent.parent

        # Run bootstrap script with local source override
        print("Step 1: Running bootstrap script...")
        result = subprocess.run(
            ["bash", str(repo_root / "tools" / "bootstrap" / "startkie.sh")],
            cwd=workspace,
            env={"KIE_BOOTSTRAP_SRC_DIR": str(repo_root)},
            capture_output=True,
            text=True,
        )

        print(result.stdout[:2000])

        assert result.returncode == 0, f"Bootstrap failed with code {result.returncode}"
        assert "AVAILABLE SLASH COMMANDS" in result.stdout, "No command enumeration in output"

        # CRITICAL: Assert all template directories exist after bootstrap
        print("\nStep 1a: Verifying critical directories exist...")
        critical_dirs = ["data", "outputs", "exports", "project_state", ".claude/commands"]
        for dir_name in critical_dirs:
            dir_path = workspace / dir_name
            assert dir_path.exists(), f"Critical directory missing after bootstrap: {dir_name}"
            assert dir_path.is_dir(), f"Path exists but is not a directory: {dir_name}"
        print(f"✓ All {len(critical_dirs)} critical directories present")

        # Verify well-known commands appear
        assert "/startkie" in result.stdout, "/startkie not enumerated"
        assert "/eda" in result.stdout, "/eda not enumerated"
        assert "/analyze" in result.stdout, "/analyze not enumerated"
        assert "/build" in result.stdout, "/build not enumerated"

        # Count commands (should be 12 from project_template - includes /go)
        command_lines = [line for line in result.stdout.split("\n") if line.strip().startswith("/")]
        assert len(command_lines) >= 12, f"Expected at least 12 commands, found {len(command_lines)}"

        print(f"✓ Bootstrap enumerated {len(command_lines)} commands")

        # Step 2: Add a dummy command and verify it appears in railscheck
        print("\nStep 2: Adding dummy command...")
        commands_dir = workspace / ".claude" / "commands"
        dummy_cmd = commands_dir / "zz_dummy.md"
        dummy_cmd.write_text("""---
name: zz_dummy
description: Dummy command for testing enumeration
---

```bash
PYTHONPATH=".kie/src" python3 -m kie.cli doctor
```
""")
        print(f"✓ Created {dummy_cmd.name}")

        # Step 3: Run railscheck and verify dummy command appears
        print("\nStep 3: Running railscheck...")
        result = subprocess.run(
            ["bash", "-c", 'PYTHONPATH=".kie/src" python3 -m kie.cli railscheck'],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

        print(result.stdout)

        assert result.returncode == 0, f"railscheck failed with code {result.returncode}"
        assert "/zz_dummy" in result.stdout, "/zz_dummy not enumerated after adding"
        assert "Dummy command for testing enumeration" in result.stdout, "Dummy description not shown"

        # Verify original commands still there
        assert "/eda" in result.stdout, "/eda disappeared after adding dummy"
        assert "/analyze" in result.stdout, "/analyze disappeared after adding dummy"

        # Count commands again (should be at least 16 now - 15 base commands + dummy)
        # Base commands include: analyze, build, doctor, eda, go, intent, interview, map,
        # preview, rails, sampledata, spec, startkie, status, validate
        command_lines = [line for line in result.stdout.split("\n") if line.strip().startswith("/")]
        assert len(command_lines) >= 16, f"Expected ≥16 commands after adding dummy, found {len(command_lines)}"

        # Verify all critical commands are present
        critical_commands = ["/eda", "/analyze", "/build", "/interview", "/go", "/spec", "/status"]
        for cmd in critical_commands:
            assert cmd in result.stdout, f"Critical command {cmd} missing from enumeration"

        print(f"\n{'='*60}")
        print("✓ COMMAND ENUMERATION TEST PASSED")
        print(f"{'='*60}\n")


def test_railscheck_empty_data():
    """Test that railscheck PASSES when data/ exists but is empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"\n{'='*60}")
        print(f"Testing railscheck with empty data/ in: {workspace}")
        print(f"{'='*60}\n")

        # Get repo root
        repo_root = Path(__file__).parent.parent

        # Run bootstrap script to create workspace structure
        print("Step 1: Bootstrapping workspace...")
        result = subprocess.run(
            ["bash", str(repo_root / "tools" / "bootstrap" / "startkie.sh")],
            cwd=workspace,
            env={"KIE_BOOTSTRAP_SRC_DIR": str(repo_root)},
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Bootstrap failed with code {result.returncode}"

        # Verify data/ exists but is empty
        data_dir = workspace / "data"
        assert data_dir.exists(), "data/ directory should exist after bootstrap"
        assert data_dir.is_dir(), "data/ should be a directory"

        # Remove any sample data files (data/ should be empty)
        for data_file in data_dir.glob("*"):
            if data_file.is_file():
                data_file.unlink()

        print(f"✓ data/ directory exists and is empty")

        # Step 2: Run railscheck and verify it PASSES
        print("\nStep 2: Running railscheck on workspace with empty data/...")
        result = subprocess.run(
            ["bash", "-c", 'PYTHONPATH=".kie/src" python3 -m kie.cli railscheck'],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

        print(result.stdout)

        # CRITICAL: railscheck should PASS (exit code 0) even with empty data/
        assert result.returncode == 0, f"railscheck should PASS with empty data/, got exit code {result.returncode}"

        # Verify output contains the helpful note about empty data
        assert "Data directory exists" in result.stdout, "Should check for data directory existence"
        assert ("No data files found" in result.stdout or "NOTE:" in result.stdout), \
            "Should contain NOTE about no data files"

        # Should see PASS status (not FAIL)
        assert "✓ PASS" in result.stdout, "Should show PASS status overall"

        print(f"\n{'='*60}")
        print("✓ RAILSCHECK EMPTY DATA TEST PASSED")
        print(f"{'='*60}\n")


def test_bootstrap_allows_preexisting_claude_dir():
    """Test that bootstrap succeeds when only .claude/ pre-exists (Claude Code creates this)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"\n{'='*60}")
        print(f"Testing bootstrap with pre-existing .claude/ in: {workspace}")
        print(f"{'='*60}\n")

        # Pre-create .claude directory (simulating Claude Code behavior)
        claude_dir = workspace / ".claude"
        claude_dir.mkdir()
        print(f"✓ Pre-created .claude/ directory")

        # Also add .DS_Store to test it's ignored
        (workspace / ".DS_Store").write_text("")
        print(f"✓ Pre-created .DS_Store file")

        # Get repo root
        repo_root = Path(__file__).parent.parent

        # Run bootstrap script - should succeed despite .claude existing
        print("\nStep 1: Running bootstrap with pre-existing .claude/...")
        result = subprocess.run(
            ["bash", str(repo_root / "tools" / "bootstrap" / "startkie.sh")],
            cwd=workspace,
            env={"KIE_BOOTSTRAP_SRC_DIR": str(repo_root)},
            capture_output=True,
            text=True,
        )

        print(result.stdout)

        # CRITICAL: Bootstrap should succeed (not fail due to .claude existing)
        assert result.returncode == 0, f"Bootstrap should succeed with pre-existing .claude/, got exit code {result.returncode}"

        # Verify all critical directories exist
        critical_dirs = ["data", "outputs", "exports", "project_state", ".claude/commands"]
        for dir_name in critical_dirs:
            dir_path = workspace / dir_name
            assert dir_path.exists(), f"Critical directory missing after bootstrap: {dir_name}"

        # Verify railscheck passes
        print("\nStep 2: Running railscheck...")
        result = subprocess.run(
            ["bash", "-c", 'PYTHONPATH=".kie/src" python3 -m kie.cli railscheck'],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"railscheck should PASS after bootstrap with pre-existing .claude/"

        print(f"\n{'='*60}")
        print("✓ BOOTSTRAP WITH PRE-EXISTING .CLAUDE/ TEST PASSED")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    test_bootstrap_enumerates_all_commands()
    test_railscheck_empty_data()
    test_bootstrap_allows_preexisting_claude_dir()
