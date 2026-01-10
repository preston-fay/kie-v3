#!/usr/bin/env python3
"""
Proof script for first-run consultant experience fixes.

Tests the complete flow: startkie → eda → analyze → build → preview

All commands must succeed without errors in a fresh workspace.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd: list[str], cwd: Path, env: dict | None = None) -> tuple[int, str, str]:
    """
    Run a command and capture output.

    Args:
        cmd: Command list
        cwd: Working directory
        env: Environment variables

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def test_first_run_experience() -> int:
    """
    Test complete first-run experience.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("=" * 70)
    print("KIE First-Run Consultant Experience Proof")
    print("=" * 70)
    print()

    # Find repo root
    repo_root = Path(__file__).parent.parent
    kie_src = repo_root

    # Create temp workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "test_workspace"
        workspace.mkdir()

        print(f"Test workspace: {workspace}")
        print()

        # Step 1: Bootstrap workspace
        print("=" * 70)
        print("STEP 1: Bootstrap Workspace")
        print("=" * 70)

        bootstrap_script = repo_root / "tools" / "bootstrap" / "startkie.sh"

        env = {
            "PATH": subprocess.os.environ.get("PATH", ""),
            "KIE_BOOTSTRAP_SRC_DIR": str(kie_src),
            "KIE_BOOTSTRAP_REFRESH": "1",
        }

        returncode, stdout, stderr = run_command(
            ["bash", str(bootstrap_script)],
            cwd=workspace,
            env=env,
        )

        print(stdout)
        if stderr:
            print("STDERR:", stderr)

        if returncode != 0:
            print(f"❌ FAIL: Bootstrap failed with exit code {returncode}")
            return 1

        # Verify .kie/src exists
        if not (workspace / ".kie" / "src").exists():
            print("❌ FAIL: .kie/src not created")
            return 1

        # Verify sample data exists and is non-empty
        sample_data = workspace / "data" / "sample_data.csv"
        if not sample_data.exists():
            print("❌ FAIL: sample_data.csv not created")
            return 1

        sample_data_content = sample_data.read_text()
        if len(sample_data_content) < 100:  # Should have headers + multiple rows
            print(f"❌ FAIL: sample_data.csv is too small ({len(sample_data_content)} bytes)")
            return 1

        print(f"✅ PASS: Bootstrap created workspace with sample data ({len(sample_data_content)} bytes)")
        print()

        # Step 2: Run /eda
        print("=" * 70)
        print("STEP 2: Run EDA")
        print("=" * 70)

        returncode, stdout, stderr = run_command(
            ["python3", "-m", "kie.cli", "eda"],
            cwd=workspace,
            env={"PYTHONPATH": str(workspace / ".kie" / "src")},
        )

        print(stdout)
        if stderr:
            print("STDERR:", stderr)

        if returncode != 0:
            print(f"❌ FAIL: EDA failed with exit code {returncode}")
            return 1

        # Verify EDA created profile
        profile_path = workspace / "outputs" / "profile.json"
        if not profile_path.exists():
            print("❌ FAIL: EDA did not create profile.json")
            return 1

        print("✅ PASS: EDA succeeded and created profile.json")
        print()

        # Step 3: Run /analyze
        print("=" * 70)
        print("STEP 3: Run Analyze")
        print("=" * 70)

        returncode, stdout, stderr = run_command(
            ["python3", "-m", "kie.cli", "analyze"],
            cwd=workspace,
            env={"PYTHONPATH": str(workspace / ".kie" / "src")},
        )

        print(stdout)
        if stderr:
            print("STDERR:", stderr)

        if returncode != 0:
            print(f"❌ FAIL: Analyze failed with exit code {returncode}")
            return 1

        # Verify insights created
        insights_path = workspace / "outputs" / "insights.yaml"
        if not insights_path.exists():
            print("❌ FAIL: Analyze did not create insights.yaml")
            return 1

        print("✅ PASS: Analyze succeeded and created insights.yaml")
        print()

        # Step 4: Run /build (presentation only, skip dashboard for CI)
        print("=" * 70)
        print("STEP 4: Run Build (Presentation)")
        print("=" * 70)

        returncode, stdout, stderr = run_command(
            ["python3", "-m", "kie.cli", "build", "presentation"],
            cwd=workspace,
            env={"PYTHONPATH": str(workspace / ".kie" / "src")},
        )

        print(stdout)
        if stderr:
            print("STDERR:", stderr)

        if returncode != 0:
            print(f"❌ FAIL: Build failed with exit code {returncode}")
            return 1

        # Verify presentation created
        ppt_files = list((workspace / "outputs").glob("*.pptx"))
        if not ppt_files:
            print("❌ FAIL: Build did not create PowerPoint presentation")
            return 1

        print(f"✅ PASS: Build succeeded and created {ppt_files[0].name}")
        print()

        # Step 5: Run /preview
        print("=" * 70)
        print("STEP 5: Run Preview")
        print("=" * 70)

        returncode, stdout, stderr = run_command(
            ["python3", "-m", "kie.cli", "preview"],
            cwd=workspace,
            env={"PYTHONPATH": str(workspace / ".kie" / "src")},
        )

        print(stdout)
        if stderr:
            print("STDERR:", stderr)

        if returncode != 0:
            print(f"❌ FAIL: Preview failed with exit code {returncode}")
            return 1

        print("✅ PASS: Preview succeeded")
        print()

        # Final verification
        print("=" * 70)
        print("FINAL VERIFICATION")
        print("=" * 70)

        # Verify all critical artifacts exist
        critical_artifacts = [
            workspace / "data" / "sample_data.csv",
            workspace / "outputs" / "profile.json",
            workspace / "outputs" / "insights.yaml",
            ppt_files[0],
        ]

        all_exist = True
        for artifact in critical_artifacts:
            rel_path = artifact.relative_to(workspace)
            if artifact.exists():
                print(f"✓ {rel_path}")
            else:
                print(f"✗ {rel_path} (MISSING)")
                all_exist = False

        print()

        if not all_exist:
            print("❌ FAIL: Some critical artifacts missing")
            return 1

        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("First-run consultant experience is working correctly:")
        print("- Bootstrap creates non-empty sample data")
        print("- EDA succeeds on fresh workspace")
        print("- Analyze succeeds on sample data")
        print("- Build creates PowerPoint presentation")
        print("- Preview shows real outputs")

        return 0


if __name__ == "__main__":
    sys.exit(test_first_run_experience())
