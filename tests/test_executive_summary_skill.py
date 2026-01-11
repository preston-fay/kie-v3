"""
Tests for ExecutiveSummarySkill

Verifies:
- Summary exists when triage + narrative + viz plan exist
- Length is variable (not hard-coded)
- Each finding maps to a triaged insight
- Each implication is not a restatement
- Caveats section present when any insight < confidence threshold
- No rails_state mutation
- Truth Gate passes (artifacts exist)
"""

import json
import tempfile
from pathlib import Path

import pytest

from kie.skills import SkillContext
from kie.skills.executive_summary import ExecutiveSummarySkill


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
def sample_triage_data():
    """Create sample triage data with varied confidence levels."""
    return {
        "total_candidate_insights": 5,
        "high_confidence_insights": 2,
        "use_with_caution_insights": 1,
        "top_insights": [
            {
                "id": "insight_1",
                "title": "Revenue growth opportunity in Region A",
                "why_it_matters": "Region A shows 25% higher retention",
                "confidence": {"numeric": 0.85, "label": "HIGH"},
                "caveats": [],
                "category": "Revenue",
            },
            {
                "id": "insight_2",
                "title": "Cost reduction potential in supply chain",
                "why_it_matters": "15% overhead reduction opportunity",
                "confidence": {"numeric": 0.65, "label": "MEDIUM"},
                "caveats": ["Statistical significance not assessed"],
                "category": "Cost",
            },
            {
                "id": "insight_3",
                "title": "Customer churn pattern detected",
                "why_it_matters": "30% of churned customers showed early warnings",
                "confidence": {"numeric": 0.45, "label": "LOW"},
                "caveats": ["Limited supporting evidence", "Moderate confidence (45%)"],
                "category": "Customer",
            },
        ],
        "data_context": {
            "total_records": 1500,
            "columns_analyzed": 8,
            "has_nulls": True,
        },
    }


@pytest.fixture
def sample_viz_plan():
    """Create sample visualization plan."""
    return {
        "generated_at": "2026-01-11T12:00:00",
        "project_intent": "Analyze efficiency opportunities",
        "total_insights_reviewed": 3,
        "visualizations_planned": 2,
        "specifications": [
            {
                "insight_id": "insight_1",
                "visualization_required": True,
                "visualization_type": "bar",
                "suppress": ["UNASSIGNED", "Unknown"],
                "caveats": [],
            },
            {
                "insight_id": "insight_2",
                "visualization_required": True,
                "visualization_type": "line",
                "suppress": [],
                "caveats": ["Time series limited to 6 months"],
            },
            {
                "insight_id": "insight_3",
                "visualization_required": False,
                "reason": "Confidence too low",
                "caveats": [],
            },
        ],
    }


@pytest.fixture
def sample_narrative_json():
    """Create sample narrative JSON."""
    return {
        "generated_at": "2026-01-11T12:00:00",
        "sections": {
            "executive_summary": "Analysis reveals revenue growth opportunities.",
            "key_findings": ["Revenue growth in Region A", "Cost reduction potential"],
        },
    }


def test_skill_requires_all_prerequisites(temp_project):
    """Test that skill fails gracefully when prerequisites missing."""
    skill = ExecutiveSummarySkill()

    context = SkillContext(project_root=temp_project, current_stage="analyze")

    # No files exist - should fail gracefully
    result = skill.execute(context)

    assert result.success
    assert "executive_summary_markdown" in result.artifacts
    assert "missing_prerequisites" in result.evidence.get("status", "")


def test_skill_generates_summary_with_all_inputs(
    temp_project, sample_triage_data, sample_viz_plan, sample_narrative_json
):
    """Test that skill generates summary when all inputs available."""
    # Save required inputs
    outputs_dir = temp_project / "outputs"

    triage_path = outputs_dir / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    narrative_json_path = outputs_dir / "executive_narrative.json"
    narrative_json_path.write_text(json.dumps(sample_narrative_json, indent=2))

    viz_plan_path = outputs_dir / "visualization_plan.json"
    viz_plan_path.write_text(json.dumps(sample_viz_plan, indent=2))

    # Execute skill
    skill = ExecutiveSummarySkill()
    context = SkillContext(project_root=temp_project, current_stage="analyze")

    result = skill.execute(context)

    # Verify success
    assert result.success
    assert "executive_summary_markdown" in result.artifacts
    assert "executive_summary_json" in result.artifacts

    # Verify files exist
    summary_md_path = Path(result.artifacts["executive_summary_markdown"])
    summary_json_path = Path(result.artifacts["executive_summary_json"])

    assert summary_md_path.exists()
    assert summary_json_path.exists()


def test_summary_has_required_sections(
    temp_project, sample_triage_data, sample_viz_plan, sample_narrative_json
):
    """Test that summary contains all required sections."""
    # Save required inputs
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(sample_triage_data, indent=2)
    )
    (outputs_dir / "executive_narrative.json").write_text(
        json.dumps(sample_narrative_json, indent=2)
    )
    (outputs_dir / "visualization_plan.json").write_text(
        json.dumps(sample_viz_plan, indent=2)
    )

    # Execute skill
    skill = ExecutiveSummarySkill()
    context = SkillContext(project_root=temp_project, current_stage="analyze")
    result = skill.execute(context)

    # Load markdown
    summary_md = Path(result.artifacts["executive_summary_markdown"]).read_text()

    # Verify all required sections
    assert "# Executive Summary" in summary_md
    assert "## Situation Overview" in summary_md
    assert "## Key Findings" in summary_md
    assert "## Why This Matters" in summary_md
    assert "## Recommended Actions (Internal)" in summary_md
    assert "## Risks & Caveats" in summary_md


def test_key_findings_map_to_triage_insights(
    temp_project, sample_triage_data, sample_viz_plan, sample_narrative_json
):
    """Test that each finding maps to a triaged insight."""
    # Save required inputs
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(sample_triage_data, indent=2)
    )
    (outputs_dir / "executive_narrative.json").write_text(
        json.dumps(sample_narrative_json, indent=2)
    )
    (outputs_dir / "visualization_plan.json").write_text(
        json.dumps(sample_viz_plan, indent=2)
    )

    # Execute skill
    skill = ExecutiveSummarySkill()
    context = SkillContext(project_root=temp_project, current_stage="analyze")
    result = skill.execute(context)

    # Load JSON
    summary_json_path = Path(result.artifacts["executive_summary_json"])
    with open(summary_json_path) as f:
        summary_json = json.load(f)

    # Verify key findings map to insights
    key_findings = summary_json["key_findings"]
    assert len(key_findings) == len(sample_triage_data["top_insights"])

    for finding in key_findings:
        # Each finding must have insight_id
        assert "insight_id" in finding
        assert "confidence" in finding
        assert "decision_enabling" in finding

        # Verify insight_id exists in triage
        insight_ids = [i["id"] for i in sample_triage_data["top_insights"]]
        assert finding["insight_id"] in insight_ids


def test_implications_are_not_restatements(
    temp_project, sample_triage_data, sample_viz_plan, sample_narrative_json
):
    """Test that implications use implication language, not restatements."""
    # Save required inputs
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(sample_triage_data, indent=2)
    )
    (outputs_dir / "executive_narrative.json").write_text(
        json.dumps(sample_narrative_json, indent=2)
    )
    (outputs_dir / "visualization_plan.json").write_text(
        json.dumps(sample_viz_plan, indent=2)
    )

    # Execute skill
    skill = ExecutiveSummarySkill()
    context = SkillContext(project_root=temp_project, current_stage="analyze")
    result = skill.execute(context)

    # Load JSON
    summary_json_path = Path(result.artifacts["executive_summary_json"])
    with open(summary_json_path) as f:
        summary_json = json.load(f)

    # Verify implications use implication language
    implications = summary_json["implications"]
    assert len(implications) >= 3

    # Check for implication keywords (not just facts)
    implication_keywords = [
        "opportunity",
        "risk",
        "constraint",
        "tradeoff",
        "enables",
        "creates",
        "suggests",
        "indicates",
        "warranted",
    ]

    for implication in implications:
        # At least one implication keyword should be present
        has_implication_language = any(
            keyword in implication.lower() for keyword in implication_keywords
        )
        assert has_implication_language, f"Implication lacks implication language: {implication}"


def test_caveats_present_for_low_confidence(
    temp_project, sample_triage_data, sample_viz_plan, sample_narrative_json
):
    """Test that caveats section includes warnings for low confidence insights."""
    # Save required inputs
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(sample_triage_data, indent=2)
    )
    (outputs_dir / "executive_narrative.json").write_text(
        json.dumps(sample_narrative_json, indent=2)
    )
    (outputs_dir / "visualization_plan.json").write_text(
        json.dumps(sample_viz_plan, indent=2)
    )

    # Execute skill
    skill = ExecutiveSummarySkill()
    context = SkillContext(project_root=temp_project, current_stage="analyze")
    result = skill.execute(context)

    # Load JSON
    summary_json_path = Path(result.artifacts["executive_summary_json"])
    with open(summary_json_path) as f:
        summary_json = json.load(f)

    # Verify caveats present
    caveats = summary_json["caveats"]
    assert len(caveats) > 0

    # Check for low confidence warning
    low_conf_warning = any(
        "below medium confidence" in caveat.lower() for caveat in caveats
    )
    assert low_conf_warning


def test_summary_length_is_variable(
    temp_project, sample_triage_data, sample_viz_plan, sample_narrative_json
):
    """Test that summary length varies based on input, not fixed."""
    # Save required inputs
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(sample_triage_data, indent=2)
    )
    (outputs_dir / "executive_narrative.json").write_text(
        json.dumps(sample_narrative_json, indent=2)
    )
    (outputs_dir / "visualization_plan.json").write_text(
        json.dumps(sample_viz_plan, indent=2)
    )

    # Execute skill
    skill = ExecutiveSummarySkill()
    context = SkillContext(project_root=temp_project, current_stage="analyze")
    result1 = skill.execute(context)

    # Load first summary
    summary1_json = json.loads(
        Path(result1.artifacts["executive_summary_json"]).read_text()
    )
    findings_count_1 = len(summary1_json["key_findings"])

    # Now modify triage to have more insights
    sample_triage_data["top_insights"].extend(
        [
            {
                "id": "insight_4",
                "title": "Another finding",
                "why_it_matters": "Additional analysis",
                "confidence": {"numeric": 0.75, "label": "HIGH"},
                "caveats": [],
                "category": "Other",
            },
            {
                "id": "insight_5",
                "title": "Yet another finding",
                "why_it_matters": "More analysis",
                "confidence": {"numeric": 0.80, "label": "HIGH"},
                "caveats": [],
                "category": "Other",
            },
        ]
    )

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(sample_triage_data, indent=2)
    )

    result2 = skill.execute(context)

    # Verify findings count increased
    summary2_json = json.loads(
        Path(result2.artifacts["executive_summary_json"]).read_text()
    )
    findings_count_2 = len(summary2_json["key_findings"])

    assert findings_count_2 > findings_count_1, \
        f"Expected findings to increase from {findings_count_1} to more, got {findings_count_2}"


def test_no_rails_state_mutation(
    temp_project, sample_triage_data, sample_viz_plan, sample_narrative_json
):
    """Test that skill does not mutate rails state."""
    # Save required inputs
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(sample_triage_data, indent=2)
    )
    (outputs_dir / "executive_narrative.json").write_text(
        json.dumps(sample_narrative_json, indent=2)
    )
    (outputs_dir / "visualization_plan.json").write_text(
        json.dumps(sample_viz_plan, indent=2)
    )

    # Create rails state
    rails_state_path = temp_project / "project_state" / "rails_state.json"
    rails_state_path.parent.mkdir(parents=True, exist_ok=True)
    initial_rails_state = {"current_stage": "analyze", "last_updated": "2026-01-11"}
    rails_state_path.write_text(json.dumps(initial_rails_state, indent=2))

    # Execute skill
    skill = ExecutiveSummarySkill()
    context = SkillContext(project_root=temp_project, current_stage="analyze")
    result = skill.execute(context)

    # Verify rails state unchanged
    final_rails_state = json.loads(rails_state_path.read_text())
    assert final_rails_state == initial_rails_state


def test_truth_gate_artifacts_exist(
    temp_project, sample_triage_data, sample_viz_plan, sample_narrative_json
):
    """Test that all claimed artifacts actually exist (Truth Gate)."""
    # Save required inputs
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(sample_triage_data, indent=2)
    )
    (outputs_dir / "executive_narrative.json").write_text(
        json.dumps(sample_narrative_json, indent=2)
    )
    (outputs_dir / "visualization_plan.json").write_text(
        json.dumps(sample_viz_plan, indent=2)
    )

    # Execute skill
    skill = ExecutiveSummarySkill()
    context = SkillContext(project_root=temp_project, current_stage="analyze")
    result = skill.execute(context)

    # Verify all claimed artifacts exist
    for artifact_name, artifact_path in result.artifacts.items():
        path = Path(artifact_path)
        assert path.exists(), f"Artifact {artifact_name} does not exist at {artifact_path}"


def test_artifact_classification_internal(
    temp_project, sample_triage_data, sample_viz_plan, sample_narrative_json
):
    """Test that artifacts are marked as INTERNAL."""
    # Save required inputs
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(sample_triage_data, indent=2)
    )
    (outputs_dir / "executive_narrative.json").write_text(
        json.dumps(sample_narrative_json, indent=2)
    )
    (outputs_dir / "visualization_plan.json").write_text(
        json.dumps(sample_viz_plan, indent=2)
    )

    # Execute skill
    skill = ExecutiveSummarySkill()
    context = SkillContext(project_root=temp_project, current_stage="analyze")
    result = skill.execute(context)

    # Verify metadata classification
    assert result.metadata.get("artifact_classification") == "INTERNAL"

    # Verify JSON includes classification
    summary_json_path = Path(result.artifacts["executive_summary_json"])
    with open(summary_json_path) as f:
        summary_json = json.load(f)

    assert summary_json["metadata"]["artifact_classification"] == "INTERNAL"


def test_no_garbage_categories_in_summary(
    temp_project, sample_triage_data, sample_viz_plan, sample_narrative_json
):
    """Test that garbage categories are filtered from meaningful suppression warnings."""
    # Add meaningful suppressed category to viz plan
    sample_viz_plan["specifications"][0]["suppress"] = ["UNASSIGNED", "Unknown", "TBD", "Pending"]

    # Save required inputs
    outputs_dir = temp_project / "outputs"

    (outputs_dir / "insight_triage.json").write_text(
        json.dumps(sample_triage_data, indent=2)
    )
    (outputs_dir / "executive_narrative.json").write_text(
        json.dumps(sample_narrative_json, indent=2)
    )
    (outputs_dir / "visualization_plan.json").write_text(
        json.dumps(sample_viz_plan, indent=2)
    )

    # Execute skill
    skill = ExecutiveSummarySkill()
    context = SkillContext(project_root=temp_project, current_stage="analyze")
    result = skill.execute(context)

    # Load JSON to check caveats
    summary_json = json.loads(
        Path(result.artifacts["executive_summary_json"]).read_text()
    )

    # Check if suppression caveat exists
    suppression_caveats = [
        caveat for caveat in summary_json["caveats"]
        if "exclude certain categories" in caveat.lower() or "visualizations exclude" in caveat.lower()
    ]

    # If suppression caveat exists, verify it doesn't list garbage categories
    if suppression_caveats:
        for caveat in suppression_caveats:
            # Should mention meaningful categories like "TBD", "Pending"
            # Should NOT mention garbage like "UNASSIGNED", "Unknown"
            assert "TBD" in caveat or "Pending" in caveat, \
                f"Suppression caveat should mention meaningful categories: {caveat}"
            # Verify garbage categories are filtered out
            assert "UNASSIGNED" not in caveat and "Unknown" not in caveat, \
                f"Garbage categories should be filtered from caveat: {caveat}"
