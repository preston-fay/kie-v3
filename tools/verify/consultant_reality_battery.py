#!/usr/bin/env python3
"""
Consultant Reality Battery Harness

Runs the full battery of adversarial acceptance tests and reports results.
This script is designed to be run locally or in CI to catch Constitution
violations before they reach production.

Usage:
    python tools/verify/consultant_reality_battery.py

Exit codes:
    0 - All journeys passed
    1 - One or more journeys failed
"""

import subprocess
import sys
from pathlib import Path


def print_section(title: str):
    """Print section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def run_battery():
    """Run consultant reality battery and report results."""
    print_section("CONSULTANT REALITY BATTERY")
    print("Running adversarial acceptance tests...")
    print()

    # Get project root
    project_root = Path(__file__).parent.parent.parent

    # Run pytest on battery test file
    test_file = project_root / "tests" / "acceptance" / "test_consultant_reality_battery.py"

    if not test_file.exists():
        print(f"❌ Battery test file not found: {test_file}")
        return 1

    # Run pytest with verbose output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        "-v",
        "--tb=short",
        "--color=yes",
    ]

    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=project_root)

    print()

    if result.returncode == 0:
        print_section("✅ CONSULTANT REALITY BATTERY: PASSED")
        print("All journeys verified:")
        print("  ✓ Journey A: Fresh workspace, no data")
        print("  ✓ Journey B: Demo data opt-in")
        print("  ✓ Journey C: Theme gate")
        print("  ✓ Journey D: /go path")
        print("  ✓ Journey E: Corrupted Excel")
        print("  ✓ Journey F: Large CSV (~5k rows)")
        print("  ✓ Journey G: Freeform guard")
        print()
        print("All Constitution requirements verified:")
        print("  ✓ No stdin prompts (non-interactive)")
        print("  ✓ Truth Gate (artifacts exist)")
        print("  ✓ Mode Gate (freeform blocked in Rails mode)")
        print("  ✓ Intent-aware messaging (no gated recommendations)")
        print("  ✓ Graceful error handling")
        print()
        return 0
    else:
        print_section("❌ CONSULTANT REALITY BATTERY: FAILED")
        print("One or more journeys failed. Review output above for details.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(run_battery())
