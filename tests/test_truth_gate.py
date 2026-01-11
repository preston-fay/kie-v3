"""
Unit tests for Truth Gate (Constitution Section 5).

Tests that commands cannot claim non-existent outputs.
"""

import tempfile
from pathlib import Path

import pytest

from kie.observability.truth_gate import TruthGate, TruthValidation


@pytest.fixture
def temp_workspace():
    """Create temporary workspace."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "outputs").mkdir(parents=True)
        (tmp_path / "outputs" / "charts").mkdir(parents=True)
        (tmp_path / "outputs" / "maps").mkdir(parents=True)
        (tmp_path / "exports").mkdir(parents=True)
        yield tmp_path


def test_truth_gate_passes_when_outputs_exist(temp_workspace):
    """Test that truth gate passes when claimed outputs exist."""
    gate = TruthGate(temp_workspace)

    # Create a real profile file
    profile_path = temp_workspace / "outputs" / "eda_profile.yaml"
    profile_path.write_text("test: data")

    # Simulate EDA result claiming this file
    result = {
        "success": True,
        "profile_saved": str(profile_path),
    }

    validation = gate.validate_command_outputs("eda", result)

    assert validation.passed, "Truth gate should pass when outputs exist"
    assert len(validation.missing_artifacts) == 0, "Should have no missing artifacts"
    assert str(profile_path) in validation.validated_artifacts, "Should validate the file"


def test_truth_gate_fails_when_outputs_missing(temp_workspace):
    """Test that truth gate fails when claimed outputs don't exist."""
    gate = TruthGate(temp_workspace)

    # Claim a file that doesn't exist
    fake_path = temp_workspace / "outputs" / "fake_profile.yaml"

    result = {
        "success": True,
        "profile_saved": str(fake_path),
    }

    validation = gate.validate_command_outputs("eda", result)

    assert not validation.passed, "Truth gate must fail when outputs missing"
    assert len(validation.missing_artifacts) > 0, "Should report missing artifacts"
    assert str(fake_path) in validation.missing_artifacts, "Should list the missing file"


def test_truth_gate_validates_analyze_charts(temp_workspace):
    """Test truth gate validation for analyze charts."""
    gate = TruthGate(temp_workspace)

    # Create insights catalog
    catalog_path = temp_workspace / "outputs" / "insights.yaml"
    catalog_path.write_text("insights: []")

    # Claim charts were created but don't create them
    result = {
        "success": True,
        "catalog_saved": str(catalog_path),
        "charts_created": 3,  # LYING - no charts exist
    }

    validation = gate.validate_command_outputs("analyze", result)

    assert not validation.passed, "Truth gate must fail when charts claimed but missing"
    assert any("charts" in artifact.lower() for artifact in validation.missing_artifacts), \
        "Should report charts directory issue"


def test_truth_gate_passes_with_real_charts(temp_workspace):
    """Test truth gate passes when charts actually exist."""
    gate = TruthGate(temp_workspace)

    # Create real charts
    charts_dir = temp_workspace / "outputs" / "charts"
    (charts_dir / "chart1.png").write_text("fake chart 1")
    (charts_dir / "chart2.png").write_text("fake chart 2")
    (charts_dir / "chart3.png").write_text("fake chart 3")

    # Create catalog
    catalog_path = temp_workspace / "outputs" / "insights.yaml"
    catalog_path.write_text("insights: []")

    result = {
        "success": True,
        "catalog_saved": str(catalog_path),
        "charts_created": 3,
    }

    validation = gate.validate_command_outputs("analyze", result)

    assert validation.passed, "Truth gate should pass when charts exist"
    assert len(validation.missing_artifacts) == 0, "Should have no missing artifacts"


def test_truth_gate_skips_failed_commands(temp_workspace):
    """Test that truth gate doesn't double-fail already failed commands."""
    gate = TruthGate(temp_workspace)

    # Command already failed
    result = {
        "success": False,
        "error": "Something went wrong",
        "profile_saved": "/fake/path/that/doesnt/exist.yaml",
    }

    validation = gate.validate_command_outputs("eda", result)

    # Should pass validation (not double-fail)
    assert validation.passed, "Truth gate should skip validation for already-failed commands"


def test_truth_gate_validates_build_presentation(temp_workspace):
    """Test truth gate validation for build outputs."""
    gate = TruthGate(temp_workspace)

    # Claim presentation exists but don't create it
    fake_pptx = temp_workspace / "exports" / "presentation.pptx"

    result = {
        "success": True,
        "presentation_path": str(fake_pptx),
    }

    validation = gate.validate_command_outputs("build", result)

    assert not validation.passed, "Truth gate must fail when presentation claimed but missing"
    assert str(fake_pptx) in validation.missing_artifacts, "Should list missing presentation"


def test_truth_validation_to_dict(temp_workspace):
    """Test TruthValidation serialization."""
    validation = TruthValidation(
        passed=False,
        missing_artifacts=["/fake/path1.txt", "/fake/path2.txt"],
        validated_artifacts=["/real/path.txt"],
        warnings=["Warning 1"],
    )

    data = validation.to_dict()

    assert data["passed"] is False
    assert len(data["missing_artifacts"]) == 2
    assert len(data["validated_artifacts"]) == 1
    assert len(data["warnings"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
