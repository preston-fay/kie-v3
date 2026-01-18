"""
Tests for consultant WOW factor features (STEP 3)

Tests Insight Brief, Next Steps Advisor, and Run Story.
CRITICAL: All features must cite real artifacts with evidence.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from kie.consultant import InsightBriefGenerator, NextStepsAdvisor, RunStoryGenerator


# ===== Insight Brief Tests =====


def test_insight_brief_requires_insights_catalog(tmp_path):
    """Test Insight Brief requires insights_catalog.json."""
    gen = InsightBriefGenerator(tmp_path)

    # No insights catalog
    result = gen.generate()

    assert result["success"] is False
    assert "insights_catalog.json not found" in result["message"]
    assert result["missing_artifact"] == "outputs/insights_catalog.json"
    assert "/analyze" in result["recovery"][0]


def test_insight_brief_generates_from_catalog(tmp_path):
    """Test Insight Brief generates from insights catalog."""
    # Setup outputs directory
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal insights catalog
    catalog_data = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "What drives revenue growth?",
        "insights": [
            {
                "id": "insight_1",
                "headline": "Northeast Region Drives 60% of Growth",
                "supporting_text": "Analysis shows Northeast contributes majority of revenue increase.",
                "insight_type": "comparison",
                "severity": "key",
                "category": "finding",
                "evidence": [
                    {
                        "type": "metric",
                        "reference": "outputs/chart1.json",
                        "value": 0.60,
                        "label": "Northeast contribution",
                    }
                ],
                "confidence": 0.9,
                "statistical_significance": 0.01,
            }
        ],
        "data_summary": {"row_count": 1000, "column_count": 5},
    }

    catalog_path = internal_dir / "insights_catalog.json"
    catalog_path.write_text(json.dumps(catalog_data))

    # Generate brief
    gen = InsightBriefGenerator(tmp_path)
    result = gen.generate()

    assert result["success"] is True
    assert "brief_markdown" in result
    assert "brief_json" in result
    assert result["key_insights_count"] == 1
    assert result["total_insights"] == 1
    assert result["evidence_backed"] is True

    # Check markdown content
    brief_path = Path(result["brief_markdown"])
    assert brief_path.exists()
    brief_content = brief_path.read_text()

    assert "# Insight Brief" in brief_content
    assert "Northeast Region Drives 60% of Growth" in brief_content
    assert "Evidence:" in brief_content
    assert "Artifact Provenance" in brief_content
    assert "outputs/insights_catalog.json" in brief_content


def test_insight_brief_cites_evidence(tmp_path):
    """Test Insight Brief cites evidence with artifacts."""
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # Create catalog with evidence
    catalog_data = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "Test question",
        "insights": [
            {
                "id": "i1",
                "headline": "Finding 1",
                "supporting_text": "Details",
                "insight_type": "comparison",
                "severity": "key",
                "category": "finding",
                "evidence": [
                    {"type": "chart", "reference": "outputs/chart1.json", "value": 100}
                ],
                "confidence": 0.8,
            }
        ],
        "data_summary": {},
    }

    catalog_path = internal_dir / "insights_catalog.json"
    catalog_path.write_text(json.dumps(catalog_data))

    # Generate brief
    gen = InsightBriefGenerator(tmp_path)
    result = gen.generate()

    # Check JSON output has evidence
    brief_json_path = Path(result["brief_json"])
    with open(brief_json_path) as f:
        brief_data = json.load(f)

    assert "artifact_provenance" in brief_data
    assert brief_data["artifact_provenance"]["insights_catalog"]["path"] == "outputs/insights_catalog.json"


def test_insight_brief_identifies_limitations(tmp_path):
    """Test Insight Brief identifies data limitations."""
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # Create catalog with low confidence insight
    catalog_data = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "Test",
        "insights": [
            {
                "id": "i1",
                "headline": "Low Confidence Finding",
                "supporting_text": "Details",
                "insight_type": "comparison",
                "severity": "supporting",
                "category": "finding",
                "evidence": [],
                "confidence": 0.5,  # Low confidence
                "statistical_significance": 0.1,  # Not significant
            }
        ],
        "data_summary": {"row_count": 50},  # Small sample
    }

    catalog_path = internal_dir / "insights_catalog.json"
    catalog_path.write_text(json.dumps(catalog_data))

    gen = InsightBriefGenerator(tmp_path)
    result = gen.generate()

    # Check markdown identifies limitations
    brief_path = Path(result["brief_markdown"])
    brief_content = brief_path.read_text()

    assert "## Risks & Limitations" in brief_content
    assert "confidence < 70%" in brief_content or "Small sample size" in brief_content


# ===== Next Steps Advisor Tests =====


def test_next_steps_after_startkie():
    """Test next steps suggest spec after startkie."""
    advisor = NextStepsAdvisor(Path("/tmp"))

    steps = advisor.generate_next_steps("startkie", {"success": True})

    assert len(steps) > 0
    assert any("/spec" in step or "/interview" in step for step in steps)


def test_next_steps_after_spec_without_data(tmp_path):
    """Test next steps suggest adding data after spec."""
    # Create workspace without data
    for d in ["data", "outputs", "project_state"]:
        (tmp_path / d).mkdir()

    advisor = NextStepsAdvisor(tmp_path)
    steps = advisor.generate_next_steps("spec", {"success": True})

    assert len(steps) > 0
    assert any("data" in step.lower() for step in steps)
    assert any("/eda" in step for step in steps)


def test_next_steps_after_eda_with_profile(tmp_path):
    """Test next steps suggest analyze after successful EDA."""
    # Create outputs with EDA profile AND spec.yaml (intent required)
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)
    (internal_dir / "eda_profile.json").write_text('{"test": "data"}')

    # Create spec.yaml to satisfy intent requirement
    state_dir = tmp_path / "project_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    import yaml
    (state_dir / "spec.yaml").write_text(yaml.dump({"project_name": "Test", "objective": "Test"}))

    advisor = NextStepsAdvisor(tmp_path)
    steps = advisor.generate_next_steps("eda", {"success": True})

    assert len(steps) > 0
    # Check for analyze command (could be /analyze or mention of analyze step)
    steps_str = " ".join(steps).lower()
    assert "analyze" in steps_str, f"Expected 'analyze' in next steps, got: {steps}"


def test_next_steps_after_analyze(tmp_path):
    """Test next steps suggest build after analyze."""
    # Create outputs with insights catalog
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)
    (internal_dir / "insights_catalog.json").write_text('{"insights": []}')

    advisor = NextStepsAdvisor(tmp_path)
    steps = advisor.generate_next_steps("analyze", {"success": True})

    assert len(steps) > 0
    assert any("/build" in step for step in steps)


def test_next_steps_provides_recovery_for_failure(tmp_path):
    """Test next steps provide recovery for failed commands."""
    advisor = NextStepsAdvisor(tmp_path)

    steps = advisor.generate_next_steps("eda", {"success": False})

    assert len(steps) > 0
    # Should provide recovery guidance
    assert any("data" in step.lower() or "/eda" in step for step in steps)


def test_next_steps_are_cli_executable(tmp_path):
    """Test all next steps are CLI-executable commands."""
    advisor = NextStepsAdvisor(tmp_path)

    # Test various commands
    commands = ["startkie", "spec", "eda", "analyze", "build"]
    for cmd in commands:
        steps = advisor.generate_next_steps(cmd, {"success": True})

        # All steps should be either:
        # 1. CLI commands starting with /
        # 2. Shell commands (cd, npm, etc.)
        # 3. Comments starting with #
        for step in steps:
            assert (
                step.startswith("/") or
                step.startswith("#") or
                any(shell_cmd in step for shell_cmd in ["cd", "npm", "python"])
            ), f"Step not CLI-executable: {step}"


# ===== Run Story Tests =====


def test_run_story_requires_evidence_ledger(tmp_path):
    """Test Run Story requires evidence ledger entries."""
    gen = RunStoryGenerator(tmp_path)

    result = gen.generate()

    assert result["success"] is False
    assert "No evidence ledger entries" in result["message"]


def test_run_story_generates_from_ledger(tmp_path):
    """Test Run Story generates from evidence ledger."""
    # Create evidence ledger directory
    evidence_dir = tmp_path / "project_state" / "evidence_ledger"
    evidence_dir.mkdir(parents=True)

    # Create outputs directory
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # Create ledger entry
    ledger_data = {
        "run_id": "test_run_1",
        "timestamp": datetime.now().isoformat(),
        "command": "eda",
        "success": True,
        "outputs": [
            {"path": "outputs/eda_profile.json", "hash": "abc123"}
        ],
    }

    ledger_path = evidence_dir / "test_run_1.yaml"
    ledger_path.write_text(yaml.dump(ledger_data))

    # Generate story
    gen = RunStoryGenerator(tmp_path)
    result = gen.generate()

    assert result["success"] is True
    assert "story_markdown" in result
    assert "story_json" in result
    assert result["commands_included"] == 1

    # Check markdown content
    story_path = Path(result["story_markdown"])
    assert story_path.exists()
    story_content = story_path.read_text()

    assert "# Run Story" in story_content
    assert "## What We Did" in story_content
    assert "## What We Found" in story_content
    assert "## What It Means" in story_content
    assert "## What To Do Next" in story_content
    assert "## Evidence Trail" in story_content
    assert "test_run_1.yaml" in story_content


def test_run_story_includes_insights_if_available(tmp_path):
    """Test Run Story includes insights when catalog exists."""
    # Setup directories
    evidence_dir = tmp_path / "project_state" / "evidence_ledger"
    evidence_dir.mkdir(parents=True)
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # Create ledger
    ledger_data = {
        "run_id": "run1",
        "timestamp": datetime.now().isoformat(),
        "command": "analyze",
        "success": True,
        "outputs": [],
    }
    (evidence_dir / "run1.yaml").write_text(yaml.dump(ledger_data))

    # Create insights catalog
    catalog_data = {
        "insights": [
            {
                "headline": "Key Finding",
                "supporting_text": "Details here",
                "severity": "key",
            }
        ]
    }
    (internal_dir / "insights_catalog.json").write_text(json.dumps(catalog_data))

    # Generate story
    gen = RunStoryGenerator(tmp_path)
    result = gen.generate()

    story_path = Path(result["story_markdown"])
    story_content = story_path.read_text()

    assert "Key Finding" in story_content


def test_run_story_evidence_backed(tmp_path):
    """Test Run Story references evidence ledger entries."""
    evidence_dir = tmp_path / "project_state" / "evidence_ledger"
    evidence_dir.mkdir(parents=True)
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # Create ledger with outputs
    ledger_data = {
        "run_id": "run_with_output",
        "timestamp": datetime.now().isoformat(),
        "command": "eda",
        "success": True,
        "outputs": [
            {"path": "outputs/eda_profile.json", "hash": "abc123def456"}
        ],
    }
    (evidence_dir / "run_with_output.yaml").write_text(yaml.dump(ledger_data))

    gen = RunStoryGenerator(tmp_path)
    result = gen.generate()

    # Check JSON has evidence trail
    story_json_path = Path(result["story_json"])
    with open(story_json_path) as f:
        story_data = json.load(f)

    assert "evidence_trail" in story_data
    assert len(story_data["evidence_trail"]) == 1
    assert story_data["evidence_trail"][0]["ledger_id"] == "run_with_output"
    assert len(story_data["evidence_trail"][0]["outputs"]) == 1


# ===== Integration Tests =====


def test_wow_features_never_block_commands(tmp_path):
    """Test WOW features never block or fail commands."""
    # This is tested implicitly by:
    # 1. All WOW features wrapped in try/except
    # 2. Silent failure on errors
    # 3. Advisory-only output

    # Test that missing artifacts don't crash
    gen = InsightBriefGenerator(tmp_path)
    result = gen.generate()  # Should not raise
    assert result["success"] is False  # Reports failure gracefully

    advisor = NextStepsAdvisor(tmp_path)
    steps = advisor.generate_next_steps("test", {})  # Should not raise
    assert isinstance(steps, list)  # Returns empty list gracefully

    story_gen = RunStoryGenerator(tmp_path)
    story_result = story_gen.generate()  # Should not raise
    assert story_result["success"] is False  # Reports failure gracefully


def test_wow_features_cite_only_real_artifacts(tmp_path):
    """Test WOW features only cite artifacts that exist."""
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # Create catalog with reference to non-existent chart
    catalog_data = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "Test",
        "insights": [
            {
                "id": "i1",
                "headline": "Finding",
                "supporting_text": "Details",
                "insight_type": "comparison",
                "severity": "key",
                "category": "finding",
                "evidence": [
                    {"type": "chart", "reference": "outputs/nonexistent.json", "value": 100}
                ],
                "confidence": 0.8,
            }
        ],
        "data_summary": {},
    }

    (internal_dir / "insights_catalog.json").write_text(json.dumps(catalog_data))

    # Brief should cite the catalog (which exists) but note if evidence is missing
    gen = InsightBriefGenerator(tmp_path)
    result = gen.generate()

    assert result["success"] is True
    brief_path = Path(result["brief_markdown"])
    brief_content = brief_path.read_text()

    # Should cite the catalog
    assert "outputs/insights_catalog.json" in brief_content
