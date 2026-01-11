#!/usr/bin/env python3
"""
Consultant Reality Gate - Standalone Runner

Run this script locally to verify the complete consultant journey works correctly.

Usage:
    python tools/verify/consultant_reality_gate.py

This script runs the same acceptance test that CI uses, providing immediate feedback
on Constitution compliance.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the consultant reality gate acceptance test."""
    print("=" * 70)
    print("CONSULTANT REALITY GATE - LOCAL VERIFICATION")
    print("=" * 70)
    print()
    print("This test simulates the complete consultant journey:")
    print("  - Bootstrap workspace")
    print("  - Handle no-data scenario")
    print("  - Install sample data")
    print("  - Run EDA with intent-awareness")
    print("  - Enforce analyze intent gate")
    print("  - Enforce build theme gate")
    print("  - Verify preview truthfulness")
    print("  - Validate audit artifacts")
    print()
    print("Any Constitution violation will cause the test to FAIL.")
    print("=" * 70)
    print()

    # Find the repo root (parent of tools/)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    # Path to acceptance test
    test_path = repo_root / "tests" / "acceptance" / "test_consultant_reality_gate.py"

    if not test_path.exists():
        print(f"❌ ERROR: Acceptance test not found at {test_path}")
        return 1

    # Run pytest
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_path),
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=repo_root)

    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ CONSULTANT REALITY GATE: PASSED")
        print("=" * 70)
        print("All Constitution requirements verified successfully.")
        print("The consultant journey works correctly end-to-end.")
    else:
        print("❌ CONSULTANT REALITY GATE: FAILED")
        print("=" * 70)
        print("Constitution violation detected or test failure occurred.")
        print("Review the output above to identify the issue.")
    print("=" * 70)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
