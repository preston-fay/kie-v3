"""
Tests for InsightTriageSkill

Verifies:
- Skill runs only when insights_catalog exists (JSON or YAML)
- Deterministic ranking based on severity and confidence
- Suppression logic works correctly
- No rails_state mutation
- Truth Gate passes (artifacts exist)
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from kie.insights.schema import (
    Insight,
    InsightCatalog,
    InsightCategory,
    InsightSeverity,
    InsightType,
)
from kie.skills import SkillContext
from kie.skills.insight_triage import InsightTriageSkill


@pytest.fixture
def temp_project():
    """Create temporary project structure."""
    tmpdir = tempfile.mkdtemp()
    project_root = Path(tmpdir)

    # Create directory structure
    (project_root / "outputs").mkdir(parents=True)
    (project_root / "project_state").mkdir(parents=True)
    (project_root / "project_state" / "evidence_ledger").mkdir(parents=True)

    return project_root


@pytest.fixture
def sample_insights():
    """Create sample insights with varying quality."""
    from datetime import datetime
    from kie.insights.schema import Evidence

    insights = [
        Insight(
            id="insight_1",
            headline="High confidence key insight",
            supporting_text="This is a critical finding with strong evidence.",
            insight_type=InsightType.COMPARISON,
            severity=InsightSeverity.KEY,
            confidence=0.92,
            statistical_significance=0.001,
            evidence=[
                Evidence(evidence_type="metric", reference="test1", value=100),
                Evidence(evidence_type="chart", reference="test2", value=200),
            ],
        ),
        Insight(
            id="insight_2",
            headline="Medium confidence supporting insight",
            supporting_text="This is a supporting finding with moderate evidence.",
            insight_type=InsightType.TREND,
            severity=InsightSeverity.SUPPORTING,
            confidence=0.75,
            statistical_significance=0.03,
            evidence=[
                Evidence(evidence_type="metric", reference="test3", value=150),
            ],
        ),
        Insight(
            id="insight_3",
            headline="Low confidence insight",
            supporting_text="This finding has weak evidence.",
            insight_type=InsightType.DISTRIBUTION,
            severity=InsightSeverity.CONTEXT,
            confidence=0.45,
            statistical_significance=0.15,
            evidence=[],
        ),
        Insight(
            id="insight_4",
            headline="High confidence recommendation",
            supporting_text="Actionable recommendation with strong backing.",
            insight_type=InsightType.BENCHMARK,
            severity=InsightSeverity.KEY,
            category=InsightCategory.RECOMMENDATION,
            confidence=0.88,
            statistical_significance=0.002,
            evidence=[
                Evidence(evidence_type="metric", reference="test4", value=300),
                Evidence(evidence_type="metric", reference="test5", value=400),
            ],
        ),
        Insight(
            id="insight_5",
            headline="Not statistically significant",
            supporting_text="This insight lacks statistical support.",
            insight_type=InsightType.CORRELATION,
            severity=InsightSeverity.SUPPORTING,
            confidence=0.70,
            statistical_significance=0.12,
            evidence=[],
        ),
    ]

    catalog = InsightCatalog(
        generated_at=datetime.now().isoformat(),
        business_question="What are the key findings?",
        insights=insights,
    )

    return catalog


def test_skill_requires_insights_catalog(temp_project):
    """Test that skill handles missing insights_catalog gracefully."""
    skill = InsightTriageSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill - should handle gracefully
    result = skill.execute(context)

    # Should succeed but with no insights
    assert result.success
    assert "triage_markdown" in result.artifacts
    assert "triage_json" in result.artifacts

    # Check that files were created
    markdown_path = Path(result.artifacts["triage_markdown"])
    json_path = Path(result.artifacts["triage_json"])

    assert markdown_path.exists()
    assert json_path.exists()

    # Check content mentions no insights
    content = markdown_path.read_text()
    assert "No insights available" in content or "0" in content


def test_skill_loads_yaml_format(temp_project, sample_insights):
    """Test that skill can load insights from YAML format."""
    # Save catalog as YAML
    catalog_path = temp_project / "outputs" / "insights.yaml"
    sample_insights.save(str(catalog_path))

    skill = InsightTriageSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success
    assert "triage_markdown" in result.artifacts
    assert "triage_json" in result.artifacts

    # Should also create JSON version
    json_catalog = temp_project / "outputs" / "insights_catalog.json"
    assert json_catalog.exists()


def test_skill_loads_json_format(temp_project, sample_insights):
    """Test that skill can load insights from JSON format."""
    # Save catalog as JSON
    catalog_path = temp_project / "outputs" / "insights_catalog.json"
    catalog_path.write_text(json.dumps(sample_insights.to_dict(), indent=2))

    skill = InsightTriageSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success
    assert "triage_markdown" in result.artifacts
    assert "triage_json" in result.artifacts


def test_deterministic_ranking(temp_project, sample_insights):
    """Test that ranking is deterministic based on severity and confidence."""
    # Save catalog
    catalog_path = temp_project / "outputs" / "insights.yaml"
    sample_insights.save(str(catalog_path))

    skill = InsightTriageSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill twice
    result1 = skill.execute(context)
    result2 = skill.execute(context)

    # Load JSON results
    json_path = Path(result1.artifacts["triage_json"])
    with open(json_path) as f:
        triage1 = json.load(f)

    json_path = Path(result2.artifacts["triage_json"])
    with open(json_path) as f:
        triage2 = json.load(f)

    # Top insights should be identical
    assert len(triage1["top_insights"]) == len(triage2["top_insights"])

    for i in range(len(triage1["top_insights"])):
        assert triage1["top_insights"][i]["title"] == triage2["top_insights"][i]["title"]


def test_suppression_logic(temp_project, sample_insights):
    """Test that low-quality insights are suppressed."""
    # Save catalog
    catalog_path = temp_project / "outputs" / "insights.yaml"
    sample_insights.save(str(catalog_path))

    skill = InsightTriageSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Load JSON result
    json_path = Path(result.artifacts["triage_json"])
    with open(json_path) as f:
        triage = json.load(f)

    # Should have top insights (limited to 3 or fewer)
    assert len(triage["top_insights"]) <= 3

    # Should have some deprioritized insights
    assert len(triage["deprioritized_insights"]) > 0

    # Low confidence insight should be deprioritized
    deprioritized_titles = [d["insight"] for d in triage["deprioritized_insights"]]
    assert "Low confidence insight" in deprioritized_titles


def test_no_rails_state_mutation(temp_project, sample_insights):
    """Test that skill does not mutate rails_state."""
    # Create rails_state
    rails_state_path = temp_project / "project_state" / "rails_state.json"
    original_state = {
        "completed_stages": ["startkie", "eda", "analyze"],
        "workflow_started": True,
    }
    with open(rails_state_path, "w") as f:
        json.dump(original_state, f)

    # Save catalog
    catalog_path = temp_project / "outputs" / "insights.yaml"
    sample_insights.save(str(catalog_path))

    skill = InsightTriageSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Rails state should be unchanged
    with open(rails_state_path) as f:
        final_state = json.load(f)

    assert final_state == original_state


def test_truth_gate_artifacts_exist(temp_project, sample_insights):
    """Test that all claimed artifacts actually exist (Truth Gate)."""
    # Save catalog
    catalog_path = temp_project / "outputs" / "insights.yaml"
    sample_insights.save(str(catalog_path))

    skill = InsightTriageSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
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


def test_high_confidence_insights_promoted(temp_project, sample_insights):
    """Test that high-confidence insights are marked for leading."""
    # Save catalog
    catalog_path = temp_project / "outputs" / "insights.yaml"
    sample_insights.save(str(catalog_path))

    skill = InsightTriageSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Load JSON result
    json_path = Path(result.artifacts["triage_json"])
    with open(json_path) as f:
        triage = json.load(f)

    # Should have high-confidence insights
    assert triage["high_confidence_insights"] > 0

    # Check guidance
    guidance = triage["consultant_guidance"]
    assert len(guidance["lead_with"]) > 0


def test_markdown_output_format(temp_project, sample_insights):
    """Test that markdown output has correct format."""
    # Save catalog
    catalog_path = temp_project / "outputs" / "insights.yaml"
    sample_insights.save(str(catalog_path))

    skill = InsightTriageSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read markdown
    markdown_path = Path(result.artifacts["triage_markdown"])
    content = markdown_path.read_text()

    # Check required sections
    assert "# Insight Triage" in content
    assert "## Executive Snapshot" in content
    assert "## Top Insights" in content
    assert "## Deprioritized Insights" in content
    assert "## Consultant Guidance" in content
    assert "**Lead with:**" in content
    assert "**Mention cautiously:**" in content
    assert "**Avoid leading with:**" in content
