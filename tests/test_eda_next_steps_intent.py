"""
Regression test: EDA next steps must be intent-aware.

CRITICAL INVARIANT:
When intent is NOT clarified, EDA next steps must NEVER recommend /analyze directly.
Instead, they must guide user to set intent first via /intent set or /interview.
"""

import json
from pathlib import Path

import pytest

from kie.consultant.next_steps import NextStepsAdvisor
from kie.state.intent import IntentStorage


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace structure."""
    # Create required directories
    (tmp_path / "data").mkdir()
    (tmp_path / "outputs").mkdir()
    (tmp_path / "exports").mkdir()
    (tmp_path / "project_state").mkdir()

    # Add sample data file
    sample_data = tmp_path / "data" / "sample.csv"
    sample_data.write_text("col1,col2\n1,2\n3,4\n")

    return tmp_path


def test_eda_next_steps_without_intent_set(temp_workspace):
    """
    Test that EDA next steps do NOT recommend /analyze when intent is missing.

    Reproduces the Constitution violation:
    1. Fresh workspace
    2. Sample data installed
    3. Intent NOT set
    4. Run /eda
    5. Verify output does NOT recommend /analyze directly
    6. Verify output DOES recommend /intent set or /interview
    """
    # Create EDA profile (simulating successful /eda)
    eda_profile = temp_workspace / "outputs" / "eda_profile.json"
    eda_profile.write_text(json.dumps({
        "shape": {"rows": 100, "columns": 5},
        "memory_mb": 0.1
    }))

    # Verify intent is NOT set
    intent_storage = IntentStorage(temp_workspace)
    assert not intent_storage.is_clarified(), "Intent should not be set initially"

    # Generate next steps after EDA
    advisor = NextStepsAdvisor(temp_workspace)
    result = {"success": True}
    steps = advisor.generate_next_steps("eda", result)

    # CRITICAL ASSERTIONS
    # 1. Must NOT recommend /analyze directly
    analyze_recommendations = [s for s in steps if "/analyze" in s and "Set your objective first" not in s]
    assert len(analyze_recommendations) == 0, (
        f"EDA next steps must NOT recommend /analyze when intent is missing. "
        f"Found: {analyze_recommendations}"
    )

    # 2. MUST recommend setting intent
    intent_recommendations = [s for s in steps if "/intent set" in s or "/interview" in s]
    assert len(intent_recommendations) > 0, (
        "EDA next steps MUST recommend /intent set or /interview when intent is missing. "
        f"Steps: {steps}"
    )

    print("✓ EDA next steps are intent-aware (no premature /analyze recommendation)")


def test_eda_next_steps_with_intent_set(temp_workspace):
    """
    Test that EDA next steps DO recommend /analyze when intent IS set.
    """
    # Create EDA profile
    eda_profile = temp_workspace / "outputs" / "eda_profile.json"
    eda_profile.write_text(json.dumps({
        "shape": {"rows": 100, "columns": 5},
        "memory_mb": 0.1
    }))

    # Set intent
    intent_storage = IntentStorage(temp_workspace)
    intent_storage.capture_intent("Analyze sales trends and identify growth opportunities")
    assert intent_storage.is_clarified(), "Intent should be set"

    # Generate next steps after EDA
    advisor = NextStepsAdvisor(temp_workspace)
    result = {"success": True}
    steps = advisor.generate_next_steps("eda", result)

    # Should recommend /analyze when intent is set
    analyze_recommendations = [s for s in steps if "/analyze" in s]
    assert len(analyze_recommendations) > 0, (
        "EDA next steps SHOULD recommend /analyze when intent is set. "
        f"Steps: {steps}"
    )

    print("✓ EDA next steps recommend /analyze when intent is set")


if __name__ == "__main__":
    # Run test locally
    import tempfile
    import shutil

    temp_dir = Path(tempfile.mkdtemp())
    try:
        test_eda_next_steps_without_intent_set(temp_dir)

        # Clean up and create fresh temp for second test
        shutil.rmtree(temp_dir)
        temp_dir = Path(tempfile.mkdtemp())
        test_eda_next_steps_with_intent_set(temp_dir)

        print("\n✓ All tests passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
