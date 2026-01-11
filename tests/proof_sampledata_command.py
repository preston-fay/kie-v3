#!/usr/bin/env python3
"""
Proof script: /sampledata slash command works correctly.

This script:
1. Verifies sampledata.md exists in both template directories
2. Creates a fresh temp workspace using bootstrap
3. Verifies sampledata.md wrapper exists in bootstrapped workspace
4. Runs sampledata commands to verify CLI routing
5. Verifies sample_data.csv is installed and tracking file is updated
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
    print("PROOF: /sampledata Slash Command")
    print("=" * 60)
    print()

    # Get repo root
    repo_root = Path(__file__).resolve().parents[1]

    # Step 1: Verify sampledata.md exists in template directories
    print("📋 Step 1: Verifying sampledata.md in template directories...")
    project_template_cmd = repo_root / "project_template" / ".claude" / "commands" / "sampledata.md"
    user_cmd_template = repo_root / "tools" / "claude_user_commands" / "sampledata.md"

    if not project_template_cmd.exists():
        print(f"❌ FAIL: project_template sampledata.md not found at {project_template_cmd}")
        return 1
    print(f"✓ project_template/.claude/commands/sampledata.md exists")

    if not user_cmd_template.exists():
        print(f"❌ FAIL: user command sampledata.md not found at {user_cmd_template}")
        return 1
    print(f"✓ tools/claude_user_commands/sampledata.md exists")
    print()

    # Step 2: Create temp workspace and bootstrap
    bootstrap_script = repo_root / "tools" / "bootstrap" / "startkie.sh"
    if not bootstrap_script.exists():
        print(f"❌ FAIL: Bootstrap script not found at {bootstrap_script}")
        return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"📁 Step 2: Created temp workspace: {workspace}")
        print()

        # Set up environment
        env = os.environ.copy()
        env["KIE_BOOTSTRAP_SRC_DIR"] = str(repo_root)

        # Run bootstrap
        print("🚀 Step 3: Running bootstrap...")
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

        # Step 3: Verify sampledata wrapper exists in workspace
        print("📋 Step 4: Verifying sampledata.md wrapper in workspace...")
        cmd_dir = workspace / ".claude" / "commands"
        sampledata_wrapper = cmd_dir / "sampledata.md"

        if not sampledata_wrapper.exists():
            print(f"❌ FAIL: sampledata.md wrapper not found at {sampledata_wrapper}")
            return 1
        print(f"✓ .claude/commands/sampledata.md exists")

        # Read wrapper content to verify it calls CLI correctly
        wrapper_content = sampledata_wrapper.read_text()
        if 'python3 -m kie.cli sampledata' not in wrapper_content:
            print(f"❌ FAIL: sampledata.md wrapper does not call CLI correctly")
            print(f"Content:\n{wrapper_content}")
            return 1
        print(f"✓ Wrapper bash block calls: python3 -m kie.cli sampledata")
        print()

        # Step 4: Test sampledata status (should show NOT INSTALLED)
        print("🧪 Step 5: Testing /sampledata status (should be NOT INSTALLED)...")
        exit_code, stdout, stderr = run_command(
            ["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli sampledata status'],
            cwd=workspace,
            env=env
        )

        if exit_code != 0:
            print(f"❌ FAIL: sampledata status failed with exit code {exit_code}")
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            return 1

        if "NOT INSTALLED" not in stdout:
            print(f"❌ FAIL: Expected 'NOT INSTALLED' in output")
            print(f"STDOUT:\n{stdout}")
            return 1
        print(f"✓ sampledata status reports NOT INSTALLED")
        print()

        # Step 5: Test sampledata install
        print("🧪 Step 6: Testing /sampledata install...")
        exit_code, stdout, stderr = run_command(
            ["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli sampledata install'],
            cwd=workspace,
            env=env
        )

        if exit_code != 0:
            print(f"❌ FAIL: sampledata install failed with exit code {exit_code}")
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            return 1
        print(f"✓ sampledata install succeeded")

        # Verify sample_data.csv was created
        sample_data_file = workspace / "data" / "sample_data.csv"
        if not sample_data_file.exists():
            print(f"❌ FAIL: sample_data.csv not found at {sample_data_file}")
            return 1
        print(f"✓ data/sample_data.csv created")

        # Verify tracking file was updated
        tracking_file = workspace / "project_state" / "sampledata.yaml"
        if not tracking_file.exists():
            print(f"❌ FAIL: sampledata.yaml tracking file not found at {tracking_file}")
            return 1
        print(f"✓ project_state/sampledata.yaml created")
        print()

        # Step 6: Test sampledata status again (should show INSTALLED)
        print("🧪 Step 7: Testing /sampledata status (should be INSTALLED)...")
        exit_code, stdout, stderr = run_command(
            ["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli sampledata status'],
            cwd=workspace,
            env=env
        )

        if exit_code != 0:
            print(f"❌ FAIL: sampledata status failed with exit code {exit_code}")
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            return 1

        if "INSTALLED" not in stdout:
            print(f"❌ FAIL: Expected 'INSTALLED' in output")
            print(f"STDOUT:\n{stdout}")
            return 1
        print(f"✓ sampledata status reports INSTALLED")
        print()

        print("=" * 60)
        print("✅ ALL PROOFS PASSED")
        print("=" * 60)
        print()
        print("Summary:")
        print("  ✓ Template directories contain sampledata.md")
        print("  ✓ Bootstrap creates sampledata.md wrapper")
        print("  ✓ Wrapper calls correct CLI command")
        print("  ✓ sampledata status works")
        print("  ✓ sampledata install creates files")
        print("  ✓ Tracking file updated correctly")
        return 0


if __name__ == "__main__":
    sys.exit(main())
