#!/usr/bin/env python3
"""
Proof script: Fresh workspace commands work correctly.

This script:
1. Creates a fresh temp workspace using bootstrap
2. Runs status, rails, and doctor commands
3. Reports PASS/FAIL with reasons
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd: list[str], cwd: Path, env: dict | None = None) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def main():
    print("=" * 60)
    print("PROOF: Fresh Workspace Commands")
    print("=" * 60)
    print()

    # Get repo root
    repo_root = Path(__file__).resolve().parents[1]
    bootstrap_script = repo_root / "tools" / "bootstrap" / "startkie.sh"

    if not bootstrap_script.exists():
        print(f"❌ FAIL: Bootstrap script not found at {bootstrap_script}")
        return 1

    # Create temp workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"📁 Created temp workspace: {workspace}")
        print()

        # Set up environment
        env = os.environ.copy()
        env["KIE_BOOTSTRAP_SRC_DIR"] = str(repo_root)

        # Run bootstrap
        print("🚀 Running bootstrap...")
        exit_code, stdout, stderr = run_command(
            ["bash", str(bootstrap_script)],
            cwd=workspace,
            env=env
        )

        if exit_code != 0:
            print(f"❌ FAIL: Bootstrap failed with exit code {exit_code}")
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            return 1

        print("✓ Bootstrap succeeded")
        print()

        # Check that mandatory wrappers exist
        cmd_dir = workspace / ".claude" / "commands"
        mandatory_files = ["doctor.md", "rails.md", "status.md", "sampledata.md"]

        print("📋 Checking command wrappers...")
        for cmd_file in mandatory_files:
            cmd_path = cmd_dir / cmd_file
            if not cmd_path.exists():
                print(f"❌ FAIL: {cmd_file} missing")
                return 1
            print(f"✓ {cmd_file} present")

        print()

        # Test CLI commands
        tests = [
            ("status", ["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli status']),
            ("rails", ["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli rails']),
            ("doctor", ["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli doctor']),
        ]

        print("🧪 Testing CLI commands...")
        all_passed = True

        for test_name, cmd in tests:
            exit_code, stdout, stderr = run_command(cmd, cwd=workspace, env=env)

            if exit_code == 0:
                print(f"✓ PASS: {test_name}")
            else:
                print(f"❌ FAIL: {test_name} (exit code {exit_code})")
                print(f"  STDOUT: {stdout[:200]}")
                print(f"  STDERR: {stderr[:200]}")
                all_passed = False

                # Special check for the "rails directory bug"
                if test_name == "rails" and "Directory does not exist" in stderr:
                    print(f"  REASON: Rails command tried to open a directory named 'rails'")
                    print(f"  This is the bug we're fixing - rails should be an alias for status")

        print()
        print("=" * 60)
        if all_passed:
            print("✅ ALL TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            print("=" * 60)
            return 1


if __name__ == "__main__":
    sys.exit(main())
