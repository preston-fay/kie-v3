"""
Unit Tests for EDA Synthesis Skill

Tests verify:
1. Skill requires all prerequisites (eda_profile, data file)
2. Skill generates synthesis with all required artifacts
3. All required tables are created (top_contributors, distribution_summary, missingness_summary, column_reduction)
4. All required charts are created (distribution, contribution, missingness)
5. Markdown has required sections in correct order
6. JSON structure is complete
7. Column reduction logic produces non-empty results
8. Deterministic outputs (same inputs → same outputs)
9. No rails_state mutation
10. Truth gate - all claimed artifacts exist
11. Artifact classification is INTERNAL
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest
import yaml

from kie.skills import EDASynthesisSkill, SkillContext


@pytest.fixture
def temp_project():
    """Create temporary project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create directories
        (project_root / "outputs" / "internal").mkdir(parents=True)
        (project_root / "project_state").mkdir(parents=True)
        (project_root / "data").mkdir(parents=True)

        # Create sample data
        sample_data = pd.DataFrame({
            "product": ["Widget A", "Widget B", "Widget C", "Widget A", "Widget B", "Widget C"] * 2,
            "region": ["North", "South", "East", "West"] * 3,
            "revenue": [100, 200, 300, 150, 250, 350, 120, 220, 320, 170, 270, 370],
            "cost": [60, 120, 180, 90, 150, 210, 72, 132, 192, 102, 162, 222],
            "units": [10, 20, 30, 15, 25, 35, 12, 22, 32, 17, 27, 37],
            "margin": [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4],
        })
        data_file = project_root / "data" / "sample_data.csv"
        sample_data.to_csv(data_file, index=False)

        # Save data file selection
        (project_root / "project_state" / "current_data_file.txt").write_text("data/sample_data.csv")

        # Create EDA profile
        eda_profile = {
            "shape": {"rows": 12, "columns": 6},
            "memory_mb": 0.001,
            "column_types": {
                "numeric": ["revenue", "cost", "units", "margin"],
                "categorical": ["product", "region"],
                "datetime": []
            },
            "quality": {
                "null_percent": 0.0,
                "duplicate_rows": 0,
                "duplicate_percent": 0.0
            },
            "issues": {
                "high_null_columns": [],
                "constant_columns": [],
                "high_cardinality_columns": []
            }
        }

        eda_profile_path = project_root / "outputs" / "internal" / "eda_profile.json"
        with open(eda_profile_path, "w") as f:
            json.dump(eda_profile, f, indent=2)

        yield project_root


def test_skill_requires_all_prerequisites(temp_project):
    """Test that skill requires eda_profile and data file."""
    skill = EDASynthesisSkill()

    # Remove eda_profile
    (temp_project / "outputs" / "internal" / "eda_profile.json").unlink()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert not result.success
    assert any("eda profile" in err.lower() for err in result.errors)


def test_skill_requires_data_file(temp_project):
    """Test that skill requires data file selection."""
    skill = EDASynthesisSkill()

    # Remove data file selection
    (temp_project / "project_state" / "current_data_file.txt").unlink()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert not result.success
    assert any("data file" in err.lower() for err in result.errors)


def test_skill_generates_synthesis_with_all_inputs(temp_project):
    """Test that skill generates synthesis when all inputs are available."""
    skill = EDASynthesisSkill()

    # Add intent
    intent_data = {"intent_text": "Analyze revenue opportunities"}
    intent_path = temp_project / "project_state" / "intent.yaml"
    with open(intent_path, "w") as f:
        yaml.dump(intent_data, f)

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success
    assert len(result.artifacts) == 4  # md, json, tables dir, charts dir
    assert "eda_synthesis_markdown" in result.artifacts
    assert "eda_synthesis_json" in result.artifacts
    assert "eda_tables" in result.artifacts
    assert "eda_charts" in result.artifacts


def test_all_required_tables_created(temp_project):
    """Test that all 4 required tables are created."""
    skill = EDASynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    tables_dir = Path(result.artifacts["eda_tables"])
    required_tables = [
        "top_contributors.csv",
        "distribution_summary.csv",
        "missingness_summary.csv",
        "column_reduction.csv"
    ]

    for table_name in required_tables:
        table_path = tables_dir / table_name
        assert table_path.exists(), f"Missing required table: {table_name}"

        # Verify table is not empty
        df = pd.read_csv(table_path)
        assert len(df) > 0, f"Table {table_name} is empty"


def test_all_required_charts_created(temp_project):
    """Test that required charts are created."""
    skill = EDASynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    charts_dir = Path(result.artifacts["eda_charts"])

    # Check for at least one distribution chart
    distribution_charts = list(charts_dir.glob("distribution_*.json"))
    assert len(distribution_charts) > 0, "No distribution charts created"

    # Check for contribution chart
    contribution_charts = list(charts_dir.glob("contribution_*.json"))
    assert len(contribution_charts) > 0, "No contribution charts created"

    # Check for missingness heatmap
    missingness_chart = charts_dir / "missingness_heatmap.json"
    assert missingness_chart.exists(), "Missingness heatmap not created"


def test_markdown_has_required_sections(temp_project):
    """Test that markdown has all required sections in correct order."""
    skill = EDASynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    md_path = Path(result.artifacts["eda_synthesis_markdown"])
    md_content = md_path.read_text()

    required_sections = [
        "# EDA Synthesis",
        "## 1. Dataset Overview",
        "## 2. What Dominates",
        "## 3. Distributions & Shape",
        "## 4. Outliers & Anomalies",
        "## 5. Correlation Analysis",
        "## 6. Missingness & Data Quality",
        "## 7. Column Reduction (Critical)",
        "## 8. What This Means for Analysis",
    ]

    for section in required_sections:
        assert section in md_content, f"Missing required section: {section}"

    # Verify order
    positions = [md_content.index(section) for section in required_sections]
    assert positions == sorted(positions), "Sections are not in correct order"


def test_json_structure_is_complete(temp_project):
    """Test that JSON has all required fields."""
    skill = EDASynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    json_path = Path(result.artifacts["eda_synthesis_json"])
    with open(json_path) as f:
        synthesis_json = json.load(f)

    required_fields = [
        "generated_at",
        "dataset_overview",
        "dominance_analysis",
        "distribution_analysis",
        "outlier_analysis",
        "quality_analysis",
        "column_reduction",
        "actionable_insights",
        "metadata",
    ]

    for field in required_fields:
        assert field in synthesis_json, f"Missing required field: {field}"

    # Verify metadata
    assert synthesis_json["metadata"]["artifact_classification"] == "INTERNAL"
    assert synthesis_json["metadata"]["skill_id"] == "eda_synthesis"


def test_column_reduction_produces_decisions(temp_project):
    """Test that column reduction produces keep/ignore/investigate decisions."""
    skill = EDASynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    json_path = Path(result.artifacts["eda_synthesis_json"])
    with open(json_path) as f:
        synthesis_json = json.load(f)

    column_reduction = synthesis_json["column_reduction"]

    # Should have at least one decision category with columns
    total_columns = (
        len(column_reduction["keep"]) +
        len(column_reduction["ignore"]) +
        len(column_reduction["investigate"])
    )

    assert total_columns > 0, "No column reduction decisions made"

    # Verify reasons are provided
    assert len(column_reduction["reasons"]) > 0, "No reasons provided for decisions"


def test_deterministic_outputs(temp_project):
    """Test that same inputs produce same outputs."""
    skill = EDASynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    # First run
    result1 = skill.execute(context)
    assert result1.success

    json_path1 = Path(result1.artifacts["eda_synthesis_json"])
    with open(json_path1) as f:
        synthesis1 = json.load(f)

    # Delete outputs
    (temp_project / "outputs" / "internal" / "eda_synthesis.md").unlink()
    (temp_project / "outputs" / "internal" / "eda_synthesis.json").unlink()

    # Second run
    result2 = skill.execute(context)
    assert result2.success

    json_path2 = Path(result2.artifacts["eda_synthesis_json"])
    with open(json_path2) as f:
        synthesis2 = json.load(f)

    # Compare key sections (ignore timestamps)
    assert synthesis1["dataset_overview"] == synthesis2["dataset_overview"]
    assert synthesis1["dominance_analysis"] == synthesis2["dominance_analysis"]
    assert synthesis1["column_reduction"] == synthesis2["column_reduction"]


def test_no_rails_state_mutation(temp_project):
    """Test that skill does not mutate Rails state."""
    skill = EDASynthesisSkill()

    # Capture initial state
    state_files_before = list((temp_project / "project_state").glob("*"))
    state_files_before_content = {
        f.name: f.read_text() if f.is_file() else None
        for f in state_files_before
    }

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    # Capture final state
    state_files_after = list((temp_project / "project_state").glob("*"))
    state_files_after_content = {
        f.name: f.read_text() if f.is_file() else None
        for f in state_files_after
    }

    # Verify no changes to Rails state
    assert state_files_before_content == state_files_after_content, \
        "Skill mutated Rails state files"


def test_truth_gate_artifacts_exist(temp_project):
    """Test that all claimed artifacts actually exist."""
    skill = EDASynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    # Verify every claimed artifact exists
    for artifact_name, artifact_path in result.artifacts.items():
        assert Path(artifact_path).exists(), \
            f"Claimed artifact does not exist: {artifact_name} at {artifact_path}"


def test_artifact_classification_internal(temp_project):
    """Test that artifacts are marked as INTERNAL."""
    skill = EDASynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    # Check JSON metadata
    json_path = Path(result.artifacts["eda_synthesis_json"])
    with open(json_path) as f:
        synthesis_json = json.load(f)

    assert synthesis_json["metadata"]["artifact_classification"] == "INTERNAL"

    # Check markdown header
    md_path = Path(result.artifacts["eda_synthesis_markdown"])
    md_content = md_path.read_text()
    assert "Internal Analysis" in md_content or "Not Client-Ready" in md_content


def test_actionable_insights_generated(temp_project):
    """Test that actionable insights are generated."""
    skill = EDASynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    json_path = Path(result.artifacts["eda_synthesis_json"])
    with open(json_path) as f:
        synthesis_json = json.load(f)

    insights = synthesis_json["actionable_insights"]

    assert len(insights) > 0, "No actionable insights generated"

    # Verify insights are not empty strings
    assert all(len(insight.strip()) > 0 for insight in insights), \
        "Some insights are empty"


def test_handles_constant_columns(temp_project):
    """Test that constant columns are identified and flagged for removal."""
    # Add a constant column to data
    data_file = temp_project / "data" / "sample_data.csv"
    df = pd.read_csv(data_file)
    df["constant_col"] = 42
    df.to_csv(data_file, index=False)

    # Update EDA profile (now in internal/ directory)
    eda_profile_path = temp_project / "outputs" / "internal" / "eda_profile.json"
    with open(eda_profile_path) as f:
        eda_profile = json.load(f)

    eda_profile["column_types"]["numeric"].append("constant_col")
    eda_profile["issues"]["constant_columns"].append("constant_col")

    with open(eda_profile_path, "w") as f:
        json.dump(eda_profile, f, indent=2)

    skill = EDASynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="eda",
        artifacts={"eda_profile": temp_project / "outputs" / "internal" / "eda_profile.json"},
        evidence_ledger_id="test_run"
    )

    result = skill.execute(context)

    assert result.success

    json_path = Path(result.artifacts["eda_synthesis_json"])
    with open(json_path) as f:
        synthesis_json = json.load(f)

    # Verify constant column is flagged for removal
    assert "constant_col" in synthesis_json["column_reduction"]["ignore"]
    assert "constant" in synthesis_json["column_reduction"]["reasons"]["constant_col"].lower()
