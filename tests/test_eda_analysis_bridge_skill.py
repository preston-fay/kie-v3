"""
Tests for EDAAnalysisBridgeSkill

Verifies:
- Skill creates eda_analysis_bridge.md/json when synthesis exists
- Deterministic output for fixed input
- Contains required sections (6 sections)
- Uses column_reduction categories correctly
- No rails_state mutation
- Fails cleanly when eda_synthesis.json missing
"""

import json
import tempfile
from pathlib import Path

import pytest

from kie.skills import SkillContext
from kie.skills.eda_analysis_bridge import EDAAnalysisBridgeSkill


@pytest.fixture
def temp_project():
    """Create temporary project structure."""
    tmpdir = tempfile.mkdtemp()
    project_root = Path(tmpdir)

    # Create directory structure
    (project_root / "outputs").mkdir(parents=True)
    (project_root / "project_state").mkdir(parents=True)

    return project_root


@pytest.fixture
def sample_synthesis():
    """Create sample EDA synthesis."""
    return {
        "dataset_overview": {
            "row_count": 1000,
            "column_count": 8,
            "column_types": {
                "numeric": ["revenue", "cost", "margin"],
                "categorical": ["region", "product"],
            },
        },
        "dominance_analysis": {
            "top_contributors": {
                "revenue": [
                    {"category": "North", "value": 450000},
                    {"category": "South", "value": 350000},
                ]
            }
        },
        "distribution_analysis": {
            "skewed_columns": ["revenue"],
        },
        "outlier_analysis": {
            "outlier_columns": ["margin"],
        },
        "quality_analysis": {
            "columns_with_nulls": ["cost"],
        },
        "column_reduction": {
            "keep": ["revenue", "margin", "region"],
            "investigate": ["product"],
            "ignore": ["id", "timestamp"],
            "reasons": {
                "revenue": "Good variation (CV=0.45)",
                "margin": "Good variation (CV=0.32)",
                "region": "Good cardinality (4 unique values)",
                "product": "High cardinality (250 unique values)",
                "id": "High cardinality - likely identifier",
                "timestamp": "Constant value - no variation",
            },
        },
        "actionable_insights": [
            "North region shows highest revenue concentration",
            "Margin variation suggests optimization opportunities",
        ],
        "warnings": ["Outliers detected in margin column"],
    }


def test_skill_fails_cleanly_on_missing_synthesis(temp_project):
    """Test that skill handles missing synthesis gracefully."""
    skill = EDAAnalysisBridgeSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill - should fail cleanly
    result = skill.execute(context)

    assert not result.success
    assert "eda_synthesis.json not found" in result.errors[0]


def test_skill_generates_complete_bridge(temp_project, sample_synthesis):
    """Test that skill generates all required sections."""
    # Save synthesis
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
    (outputs_dir / "internal" / "eda_synthesis.json").write_text(json.dumps(sample_synthesis, indent=2))

    skill = EDAAnalysisBridgeSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_synthesis_json": outputs_dir / "internal" / "eda_synthesis.json"},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success
    assert "eda_analysis_bridge_markdown" in result.artifacts
    assert "eda_analysis_bridge_json" in result.artifacts

    # Read markdown
    md_path = Path(result.artifacts["eda_analysis_bridge_markdown"])
    content = md_path.read_text()

    # Check required sections
    assert "# EDA → Analysis Bridge (Internal)" in content
    assert "## 1) Primary Focus Areas" in content
    assert "## 2) Secondary / Exploratory Areas" in content
    assert "## 3) Deprioritized / Ignore" in content
    assert "## 4) Risks & Analytical Traps" in content
    assert "## 5) Recommended Analysis Types" in content
    assert "## 6) What This Analysis Will Enable" in content

    # Check INTERNAL ONLY marker
    assert "INTERNAL ONLY" in content


def test_bridge_uses_column_reduction_correctly(temp_project, sample_synthesis):
    """Test that bridge uses column_reduction categories correctly."""
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
    (outputs_dir / "internal" / "eda_synthesis.json").write_text(json.dumps(sample_synthesis, indent=2))

    skill = EDAAnalysisBridgeSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    result = skill.execute(context)
    assert result.success

    # Read JSON
    json_path = Path(result.artifacts["eda_analysis_bridge_json"])
    with open(json_path) as f:
        bridge_data = json.load(f)

    # Verify primary focus uses "keep" columns
    primary_focus = bridge_data["primary_focus"]
    assert len(primary_focus) == 3
    assert all(item["column"] in ["revenue", "margin", "region"] for item in primary_focus)

    # Verify secondary uses "investigate" columns
    secondary = bridge_data["secondary"]
    assert len(secondary) == 1
    assert secondary[0]["column"] == "product"

    # Verify deprioritized uses "ignore" columns
    deprioritized = bridge_data["deprioritized"]
    assert len(deprioritized) == 2
    assert all(item["column"] in ["id", "timestamp"] for item in deprioritized)


def test_bridge_contains_decisive_language(temp_project, sample_synthesis):
    """Test that bridge uses decisive language, not speculative."""
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
    (outputs_dir / "internal" / "eda_synthesis.json").write_text(json.dumps(sample_synthesis, indent=2))

    skill = EDAAnalysisBridgeSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    result = skill.execute(context)
    md_path = Path(result.artifacts["eda_analysis_bridge_markdown"])
    content = md_path.read_text()

    # Check for decisive language
    assert "Focus analysis on" in content or "Do not analyze" in content

    # Check NO speculative language
    speculative_words = ["could", "might", "potential", "possibly", "perhaps"]
    for word in speculative_words:
        assert word not in content.lower(), f"Found speculative word: {word}"


def test_deterministic_output(temp_project, sample_synthesis):
    """Test that output is deterministic for fixed input."""
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
    (outputs_dir / "internal" / "eda_synthesis.json").write_text(json.dumps(sample_synthesis, indent=2))

    skill = EDAAnalysisBridgeSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill twice
    result1 = skill.execute(context)
    json_path1 = Path(result1.artifacts["eda_analysis_bridge_json"])
    with open(json_path1) as f:
        data1 = json.load(f)

    result2 = skill.execute(context)
    json_path2 = Path(result2.artifacts["eda_analysis_bridge_json"])
    with open(json_path2) as f:
        data2 = json.load(f)

    # Key sections should be identical (except generated_at timestamp)
    assert data1["primary_focus"] == data2["primary_focus"]
    assert data1["secondary"] == data2["secondary"]
    assert data1["deprioritized"] == data2["deprioritized"]
    assert data1["risks"] == data2["risks"]
    assert data1["recommended_analysis_types"] == data2["recommended_analysis_types"]


def test_no_rails_state_mutation(temp_project, sample_synthesis):
    """Test that skill does not mutate rails_state."""
    # Create rails_state
    rails_state_path = temp_project / "project_state" / "rails_state.json"
    original_state = {
        "completed_stages": ["startkie", "eda"],
        "workflow_started": True,
    }
    with open(rails_state_path, "w") as f:
        json.dump(original_state, f)

    # Save synthesis
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
    (outputs_dir / "internal" / "eda_synthesis.json").write_text(json.dumps(sample_synthesis, indent=2))

    skill = EDAAnalysisBridgeSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Rails state should be unchanged
    with open(rails_state_path) as f:
        final_state = json.load(f)

    assert final_state == original_state


def test_truth_gate_artifacts_exist(temp_project, sample_synthesis):
    """Test that all claimed artifacts actually exist (Truth Gate)."""
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
    (outputs_dir / "internal" / "eda_synthesis.json").write_text(json.dumps(sample_synthesis, indent=2))

    skill = EDAAnalysisBridgeSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Verify all artifacts exist
    for artifact_name, artifact_path in result.artifacts.items():
        path = Path(artifact_path)
        assert path.exists(), f"Artifact {artifact_name} does not exist at {artifact_path}"

        # Verify files are not empty
        assert path.stat().st_size > 0, f"Artifact {artifact_name} is empty"


def test_bridge_recommends_analysis_types(temp_project, sample_synthesis):
    """Test that bridge recommends appropriate analysis types."""
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
    (outputs_dir / "internal" / "eda_synthesis.json").write_text(json.dumps(sample_synthesis, indent=2))

    skill = EDAAnalysisBridgeSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    result = skill.execute(context)

    # Read JSON
    json_path = Path(result.artifacts["eda_analysis_bridge_json"])
    with open(json_path) as f:
        bridge_data = json.load(f)

    # Should recommend at least one analysis type
    analysis_types = bridge_data["recommended_analysis_types"]
    assert len(analysis_types) > 0

    # Each recommendation should have type and reason
    for rec in analysis_types:
        assert "type" in rec
        assert "reason" in rec
        assert len(rec["type"]) > 0
        assert len(rec["reason"]) > 0


def test_bridge_aligns_to_intent(temp_project, sample_synthesis):
    """Test that bridge aligns outcomes to project intent when present."""
    # Create intent
    intent_path = temp_project / "project_state" / "intent.yaml"
    intent_path.write_text("text: Analyze efficiency and cost reduction opportunities\n")

    # Save synthesis
    outputs_dir = temp_project / "outputs"
    (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
    (outputs_dir / "internal" / "eda_synthesis.json").write_text(json.dumps(sample_synthesis, indent=2))

    skill = EDAAnalysisBridgeSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    result = skill.execute(context)

    # Read JSON
    json_path = Path(result.artifacts["eda_analysis_bridge_json"])
    with open(json_path) as f:
        bridge_data = json.load(f)

    # Should reference intent in outcomes
    outcomes = bridge_data["expected_outcomes"]
    outcomes_text = " ".join(outcomes).lower()

    # Should mention efficiency or cost
    assert "efficiency" in outcomes_text or "cost" in outcomes_text
