#!/usr/bin/env python3
"""
Proof script: Intent command is properly wrapped and functional.

This script:
1. Bootstraps a temp workspace
2. Verifies intent.md wrapper exists in .claude/commands
3. Runs: PYTHONPATH=".kie/src" python3 -m kie.cli intent set "test objective"
4. Verifies project_state/intent.yaml was created
5. Reports PASS/FAIL with reasons
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
    print("PROOF: Intent Command Wrapped and Functional")
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

        # Check that intent.md wrapper exists
        print("📋 Checking for intent.md wrapper...")
        intent_wrapper = workspace / ".claude" / "commands" / "intent.md"

        if not intent_wrapper.exists():
            print(f"❌ FAIL: intent.md wrapper missing at {intent_wrapper}")
            return 1

        print(f"✓ intent.md wrapper exists")

        # Verify wrapper content
        content = intent_wrapper.read_text()
        if "python3 -m kie.cli intent" not in content:
            print(f"❌ FAIL: intent.md wrapper doesn't route to CLI")
            print(f"Content: {content[:200]}")
            return 1

        print(f"✓ intent.md wrapper routes to CLI correctly")
        print()

        # Test intent status (should show NOT SET)
        print("🧪 Testing: intent status...")
        exit_code, stdout, stderr = run_command(
            ["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli intent status'],
            cwd=workspace,
            env=env
        )

        if exit_code != 0:
            print(f"❌ FAIL: intent status failed (exit code {exit_code})")
            print(f"  STDOUT: {stdout}")
            print(f"  STDERR: {stderr}")
            return 1

        if "NOT SET" not in stdout:
            print(f"❌ FAIL: Expected 'NOT SET' in output")
            print(f"  STDOUT: {stdout}")
            return 1

        print("✓ PASS: intent status shows NOT SET")
        print()

        # Test intent set
        print("🧪 Testing: intent set \"test objective\"...")
        exit_code, stdout, stderr = run_command(
            ["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli intent set "test objective"'],
            cwd=workspace,
            env=env
        )

        if exit_code != 0:
            print(f"❌ FAIL: intent set failed (exit code {exit_code})")
            print(f"  STDOUT: {stdout}")
            print(f"  STDERR: {stderr}")
            return 1

        print("✓ PASS: intent set succeeded")
        print()

        # Verify intent.yaml was created
        print("📋 Verifying project_state/intent.yaml...")
        intent_file = workspace / "project_state" / "intent.yaml"

        if not intent_file.exists():
            print(f"❌ FAIL: intent.yaml not created at {intent_file}")
            return 1

        print(f"✓ intent.yaml exists")

        # Verify content
        import yaml
        with open(intent_file) as f:
            intent_data = yaml.safe_load(f)

        if not intent_data or intent_data.get("objective") != "test objective":
            print(f"❌ FAIL: intent.yaml doesn't contain correct objective")
            print(f"  Content: {intent_data}")
            return 1

        print(f"✓ intent.yaml contains correct objective: 'test objective'")
        print()

        # Test intent status again (should show the objective)
        print("🧪 Testing: intent status (should show objective)...")
        exit_code, stdout, stderr = run_command(
            ["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli intent status'],
            cwd=workspace,
            env=env
        )

        if exit_code != 0:
            print(f"❌ FAIL: intent status failed (exit code {exit_code})")
            print(f"  STDOUT: {stdout}")
            print(f"  STDERR: {stderr}")
            return 1

        if "test objective" not in stdout:
            print(f"❌ FAIL: Expected 'test objective' in output")
            print(f"  STDOUT: {stdout}")
            return 1

        print("✓ PASS: intent status shows set objective")
        print()

        # Test intent clear
        print("🧪 Testing: intent clear...")
        exit_code, stdout, stderr = run_command(
            ["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli intent clear'],
            cwd=workspace,
            env=env
        )

        if exit_code != 0:
            print(f"❌ FAIL: intent clear failed (exit code {exit_code})")
            print(f"  STDOUT: {stdout}")
            print(f"  STDERR: {stderr}")
            return 1

        print("✓ PASS: intent clear succeeded")
        print()

        # Verify intent.yaml was removed
        if intent_file.exists():
            print(f"❌ FAIL: intent.yaml still exists after clear")
            return 1

        print(f"✓ intent.yaml removed after clear")
        print()

        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("Summary:")
        print("  ✓ intent.md wrapper installed")
        print("  ✓ intent status works")
        print("  ✓ intent set creates intent.yaml")
        print("  ✓ intent.yaml contains correct data")
        print("  ✓ intent clear removes intent.yaml")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
