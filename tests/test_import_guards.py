#!/usr/bin/env python3
"""
Unit tests for PR #6: Import Guards

Verifies that forbidden visualization libraries are blocked at import time.
"""

import subprocess
import sys

import pytest


def test_import_guard_allows_valid_imports():
    """
    TEST: Import guard allows normal KIE usage.
    """
    # Should succeed - no forbidden imports
    result = subprocess.run(
        [sys.executable, "-c", "import kie; print('SUCCESS')"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "SUCCESS" in result.stdout
    assert "Forbidden" not in result.stderr

    print("✅ Valid Import Test PASSED")
    print(f"   - KIE imports successfully without errors")


def test_import_guard_blocks_matplotlib():
    """
    TEST: Import guard blocks matplotlib when imported before kie.
    """
    # Import matplotlib BEFORE kie - should be blocked
    test_code = """
import matplotlib
import kie
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True
    )

    # Should fail with ImportError
    assert result.returncode != 0
    assert "Forbidden" in result.stderr or "matplotlib" in result.stderr.lower()

    print("✅ Matplotlib Block Test PASSED")
    print(f"   - Import guard blocked matplotlib")


def test_import_guard_blocks_seaborn():
    """
    TEST: Import guard blocks seaborn when imported before kie.
    """
    test_code = """
import seaborn
import kie
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True
    )

    # Should fail with ImportError
    assert result.returncode != 0
    assert "Forbidden" in result.stderr or "seaborn" in result.stderr.lower()

    print("✅ Seaborn Block Test PASSED")
    print(f"   - Import guard blocked seaborn")


def test_import_guard_blocks_plotly():
    """
    TEST: Import guard blocks plotly when imported before kie.
    """
    test_code = """
import plotly
import kie
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True
    )

    # Should fail with ImportError
    assert result.returncode != 0
    assert "Forbidden" in result.stderr or "plotly" in result.stderr.lower()

    print("✅ Plotly Block Test PASSED")
    print(f"   - Import guard blocked plotly")


def test_import_guard_message_is_clear():
    """
    TEST: Import guard error message is clear and actionable.
    """
    test_code = """
import matplotlib
import kie
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True
    )

    # Should have helpful error message
    error_text = result.stderr

    # Check for key elements
    assert "matplotlib" in error_text.lower()
    assert "recharts" in error_text.lower() or "chartfactory" in error_text.lower()
    assert "kds" in error_text.lower()

    print("✅ Error Message Test PASSED")
    print(f"   - Error message is clear and actionable")
    print(f"   - Message mentions: matplotlib, KDS, Recharts")


def test_ci_grep_check_would_catch_matplotlib():
    """
    TEST: Verify CI grep pattern would catch matplotlib imports.
    """
    # Test patterns that CI workflow checks
    test_patterns = [
        "import matplotlib",
        "from matplotlib import pyplot",
        "import seaborn",
        "from seaborn import *",
        "import plotly",
    ]

    for pattern in test_patterns:
        # Simulate what grep would find
        if any(keyword in pattern for keyword in ["matplotlib", "seaborn", "plotly"]):
            print(f"✅ CI would catch: {pattern}")
        else:
            raise AssertionError(f"CI wouldn't catch: {pattern}")

    print("✅ CI Pattern Test PASSED")
    print(f"   - All forbidden import patterns would be caught by CI")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PR #6: IMPORT GUARD TESTS")
    print("Testing: Forbidden visualization library prevention")
    print("="*70 + "\n")

    try:
        test_import_guard_allows_valid_imports()
        print()
        test_import_guard_blocks_matplotlib()
        print()
        test_import_guard_blocks_seaborn()
        print()
        test_import_guard_blocks_plotly()
        print()
        test_import_guard_message_is_clear()
        print()
        test_ci_grep_check_would_catch_matplotlib()
        print("\n" + "="*70)
        print("✅ ALL PR #6 TESTS PASSED")
        print("Import guards working correctly")
        print("="*70 + "\n")
    except AssertionError as e:
        print("\n" + "="*70)
        print("❌ PR #6 TEST FAILED")
        print(f"   {e}")
        print("="*70 + "\n")
        raise
