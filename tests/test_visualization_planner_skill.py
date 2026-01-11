"""
Tests for VisualizationPlannerSkill

Verifies:
- Skill fails cleanly if insight_triage missing
- Deterministic output for fixed input
- visualization_required false path tested
- No rails_state mutation
- Truth Gate passes (artifacts exist)
"""

import json
import tempfile
from pathlib import Path

import pytest

from kie.skills import SkillContext
from kie.skills.visualization_planner import VisualizationPlannerSkill


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
def sample_triage_data():
    """Create sample triage data."""
    return {
        "total_candidate_insights": 5,
        "high_confidence_insights": 2,
        "use_with_caution_insights": 1,
        "top_insights": [
            {
                "id": "insight_1",
                "title": "Revenue growth opportunity in Region B",
                "why_it_matters": "Region B shows 45% higher margins compared to Region A with similar overhead costs",
                "evidence": [
                    {
                        "type": "metric",
                        "reference": "outputs/eda_profile.json",
                        "hash": "abc123def456...",
                    }
                ],
                "confidence": "HIGH",
                "caveats": [],
            },
            {
                "id": "insight_2",
                "title": "Cost reduction potential in supply chain",
                "why_it_matters": "Identified 15% overhead reduction opportunity through vendor consolidation",
                "evidence": [
                    {
                        "type": "metric",
                        "reference": "outputs/insights_catalog.json",
                    }
                ],
                "confidence": "MEDIUM",
                "caveats": ["Statistical significance not assessed"],
            },
            {
                "id": "insight_3",
                "title": "Customer churn pattern detected",
                "why_it_matters": "30% of churned customers showed early warning signs",
                "evidence": [],
                "confidence": "LOW",
                "caveats": ["Limited supporting evidence", "Moderate confidence (65%)"],
            },
        ],
        "deprioritized_insights": [
            {
                "insight": "Seasonal variation in sales",
                "reason": "Weak evidence - needs validation",
            }
        ],
        "consultant_guidance": {
            "lead_with": [
                "Revenue growth opportunity in Region B",
                "Cost reduction potential in supply chain",
            ],
            "mention_cautiously": ["Customer churn pattern detected"],
            "avoid_leading_with": ["Seasonal variation in sales"],
        },
    }


def test_skill_fails_cleanly_on_missing_triage(temp_project):
    """Test that skill handles missing triage gracefully."""
    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill - should handle gracefully
    result = skill.execute(context)

    # Should succeed (graceful handling)
    assert result.success
    assert "visualization_plan_md" in result.artifacts
    assert "visualization_plan_json" in result.artifacts

    # Check that files were created
    md_path = Path(result.artifacts["visualization_plan_md"])
    json_path = Path(result.artifacts["visualization_plan_json"])

    assert md_path.exists()
    assert json_path.exists()

    # Check content mentions no triage
    content = md_path.read_text()
    assert "No insight triage available" in content or "Run /analyze" in content


def test_skill_generates_complete_plan(temp_project, sample_triage_data):
    """Test that skill generates all required fields."""
    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success
    assert "visualization_plan_md" in result.artifacts
    assert "visualization_plan_json" in result.artifacts

    # Read JSON
    json_path = Path(result.artifacts["visualization_plan_json"])
    with open(json_path) as f:
        plan_data = json.load(f)

    # Check required fields
    assert "generated_at" in plan_data
    assert "total_insights_reviewed" in plan_data
    assert "visualizations_planned" in plan_data
    assert "specifications" in plan_data

    # Check specifications
    specs = plan_data["specifications"]
    assert len(specs) > 0

    for spec in specs:
        # All specs must have these fields
        assert "insight_id" in spec
        assert "insight_title" in spec
        assert "visualization_required" in spec
        assert "visualization_type" in spec
        assert "purpose" in spec
        assert "confidence" in spec

        if spec["visualization_required"]:
            # Full specs must have all fields
            assert "x_axis" in spec
            assert "y_axis" in spec
            assert "highlights" in spec
            assert "suppress" in spec
            assert "annotations" in spec
            assert "caveats" in spec


def test_deterministic_output(temp_project, sample_triage_data):
    """Test that output is deterministic for fixed input."""
    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill twice
    result1 = skill.execute(context)
    json_path1 = Path(result1.artifacts["visualization_plan_json"])
    with open(json_path1) as f:
        data1 = json.load(f)

    result2 = skill.execute(context)
    json_path2 = Path(result2.artifacts["visualization_plan_json"])
    with open(json_path2) as f:
        data2 = json.load(f)

    # Specifications should be identical (except generated_at timestamp)
    assert data1["specifications"] == data2["specifications"]
    assert data1["total_insights_reviewed"] == data2["total_insights_reviewed"]
    assert data1["visualizations_planned"] == data2["visualizations_planned"]


def test_visualization_required_false_path(temp_project):
    """Test that visualization_required = false works correctly."""
    # Create triage with low-confidence insight
    triage_data = {
        "total_candidate_insights": 1,
        "high_confidence_insights": 0,
        "use_with_caution_insights": 1,
        "top_insights": [
            {
                "id": "insight_low_conf",
                "title": "Possible trend observed",
                "why_it_matters": "Some data suggests a pattern but evidence is weak",
                "evidence": [],
                "confidence": "LOW",
                "caveats": ["Insufficient data"],
            }
        ],
        "consultant_guidance": {
            "lead_with": [],
            "mention_cautiously": [],
            "avoid_leading_with": [],
        },
    }

    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(triage_data, indent=2))

    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read JSON
    json_path = Path(result.artifacts["visualization_plan_json"])
    with open(json_path) as f:
        plan_data = json.load(f)

    # Check that visualization_required is false
    specs = plan_data["specifications"]
    assert len(specs) > 0

    low_conf_spec = specs[0]
    assert low_conf_spec["visualization_required"] is False
    assert "reason" in low_conf_spec
    assert low_conf_spec["visualization_type"] == "none"


def test_visualization_required_false_no_evidence(temp_project):
    """Test that visualization_required = false when no evidence."""
    # Create triage with medium confidence but no evidence
    triage_data = {
        "total_candidate_insights": 1,
        "high_confidence_insights": 0,
        "use_with_caution_insights": 0,
        "top_insights": [
            {
                "id": "insight_no_evidence",
                "title": "Revenue higher in Q3 vs Q2",
                "why_it_matters": "Q3 shows 20% revenue growth compared to Q2",
                "evidence": [],  # No evidence
                "confidence": "MEDIUM",
                "caveats": [],
            }
        ],
        "consultant_guidance": {
            "lead_with": [],
            "mention_cautiously": [],
            "avoid_leading_with": [],
        },
    }

    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(triage_data, indent=2))

    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read JSON
    json_path = Path(result.artifacts["visualization_plan_json"])
    with open(json_path) as f:
        plan_data = json.load(f)

    # Check that visualization_required is false due to no evidence
    specs = plan_data["specifications"]
    assert len(specs) > 0

    no_ev_spec = specs[0]
    assert no_ev_spec["visualization_required"] is False
    assert "No numeric evidence" in no_ev_spec["reason"]


def test_no_rails_state_mutation(temp_project, sample_triage_data):
    """Test that skill does not mutate rails_state."""
    # Create rails_state
    rails_state_path = temp_project / "project_state" / "rails_state.json"
    original_state = {
        "completed_stages": ["startkie", "eda", "analyze"],
        "workflow_started": True,
    }
    with open(rails_state_path, "w") as f:
        json.dump(original_state, f)

    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Rails state should be unchanged
    with open(rails_state_path) as f:
        final_state = json.load(f)

    assert final_state == original_state


def test_truth_gate_artifacts_exist(temp_project, sample_triage_data):
    """Test that all claimed artifacts actually exist (Truth Gate)."""
    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
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


def test_markdown_structure_completeness(temp_project, sample_triage_data):
    """Test that markdown output has complete structure."""
    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read markdown
    md_path = Path(result.artifacts["visualization_plan_md"])
    content = md_path.read_text()

    # Check required sections
    assert "# Visualization Plan (Internal)" in content
    assert "**Total Insights Reviewed:**" in content
    assert "**Visualizations Planned:**" in content

    # Check that each insight has a section
    for insight in sample_triage_data["top_insights"]:
        # Skip insights that should be avoided
        if insight["title"] not in sample_triage_data["consultant_guidance"]["avoid_leading_with"]:
            assert f"## Insight" in content

    # Check INTERNAL ONLY marker
    assert "INTERNAL ONLY" in content


def test_confidence_thresholds_respected(temp_project):
    """Test that confidence thresholds are properly enforced."""
    # Create triage with mix of confidence levels
    triage_data = {
        "total_candidate_insights": 3,
        "high_confidence_insights": 1,
        "use_with_caution_insights": 2,
        "top_insights": [
            {
                "id": "high_conf",
                "title": "Revenue growth in Region A",
                "why_it_matters": "Region A shows 50% higher revenue compared to baseline",
                "evidence": [{"type": "metric", "reference": "outputs/data.json"}],
                "confidence": "HIGH",
                "caveats": [],
            },
            {
                "id": "med_conf",
                "title": "Cost trends improving",
                "why_it_matters": "Costs decreased 10% quarter over quarter",
                "evidence": [{"type": "metric", "reference": "outputs/data.json"}],
                "confidence": "MEDIUM",
                "caveats": [],
            },
            {
                "id": "low_conf",
                "title": "Possible efficiency gain",
                "why_it_matters": "Some indicators suggest improvement",
                "evidence": [],
                "confidence": "LOW",
                "caveats": [],
            },
        ],
        "consultant_guidance": {
            "lead_with": [],
            "mention_cautiously": [],
            "avoid_leading_with": [],
        },
    }

    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(triage_data, indent=2))

    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read JSON
    json_path = Path(result.artifacts["visualization_plan_json"])
    with open(json_path) as f:
        plan_data = json.load(f)

    specs = plan_data["specifications"]

    # High confidence should have viz
    high_spec = next(s for s in specs if s["insight_id"] == "high_conf")
    assert high_spec["visualization_required"] is True

    # Medium confidence should have viz
    med_spec = next(s for s in specs if s["insight_id"] == "med_conf")
    assert med_spec["visualization_required"] is True

    # Low confidence should NOT have viz
    low_spec = next(s for s in specs if s["insight_id"] == "low_conf")
    assert low_spec["visualization_required"] is False


def test_intent_integration(temp_project, sample_triage_data):
    """Test that project intent is integrated when available."""
    import yaml

    # Create intent file
    intent_path = temp_project / "project_state" / "intent.yaml"
    intent_data = {
        "intent_text": "Analyze revenue growth opportunities and operational efficiency"
    }
    with open(intent_path, "w") as f:
        yaml.dump(intent_data, f)

    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read markdown
    md_path = Path(result.artifacts["visualization_plan_md"])
    content = md_path.read_text()

    # Check that intent appears
    assert "Project Intent:" in content
    assert "revenue growth opportunities" in content

    # Read JSON
    json_path = Path(result.artifacts["visualization_plan_json"])
    with open(json_path) as f:
        plan_data = json.load(f)

    assert plan_data["project_intent"] == intent_data["intent_text"]


def test_skip_avoid_leading_with_insights(temp_project):
    """Test that insights marked 'avoid_leading_with' are skipped."""
    triage_data = {
        "total_candidate_insights": 2,
        "high_confidence_insights": 1,
        "use_with_caution_insights": 0,
        "top_insights": [
            {
                "id": "good_insight",
                "title": "Strong revenue growth",
                "why_it_matters": "Revenue increased 40% year over year",
                "evidence": [{"type": "metric", "reference": "outputs/data.json"}],
                "confidence": "HIGH",
                "caveats": [],
            },
            {
                "id": "bad_insight",
                "title": "Questionable pattern",
                "why_it_matters": "Some data suggests something",
                "evidence": [],
                "confidence": "LOW",
                "caveats": [],
            },
        ],
        "consultant_guidance": {
            "lead_with": ["Strong revenue growth"],
            "mention_cautiously": [],
            "avoid_leading_with": ["Questionable pattern"],
        },
    }

    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(triage_data, indent=2))

    skill = VisualizationPlannerSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read JSON
    json_path = Path(result.artifacts["visualization_plan_json"])
    with open(json_path) as f:
        plan_data = json.load(f)

    specs = plan_data["specifications"]

    # Should only have 1 spec (the good one)
    assert len(specs) == 1
    assert specs[0]["insight_id"] == "good_insight"
