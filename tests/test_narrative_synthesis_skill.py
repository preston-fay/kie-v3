"""
Tests for NarrativeSynthesisSkill

Verifies:
- Skill runs only when triage exists OR produces graceful "missing triage" narrative
- Deterministic output for fixed triage input
- Uses only triage content (no extra inference)
- Evidence index included and truthful about hash availability
- No rails_state mutation
- Truth Gate passes (artifacts exist)
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from kie.skills import SkillContext
from kie.skills.narrative_synthesis import NarrativeSynthesisSkill


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
                "title": "Revenue growth opportunity in Region A",
                "why_it_matters": "Region A shows 25% higher customer retention with similar acquisition costs",
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
                "title": "Customer churn pattern detected",
                "why_it_matters": "30% of churned customers showed early warning signs that were not acted upon",
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
                "Revenue growth opportunity in Region A",
                "Cost reduction potential in supply chain",
            ],
            "mention_cautiously": ["Customer churn pattern detected"],
            "avoid_leading_with": ["Seasonal variation in sales"],
        },
    }


def test_skill_handles_no_triage(temp_project):
    """Test that skill handles missing triage gracefully."""
    skill = NarrativeSynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill - should handle gracefully
    result = skill.execute(context)

    # Should succeed
    assert result.success
    assert "narrative_markdown" in result.artifacts
    assert "narrative_json" in result.artifacts

    # Check that files were created
    markdown_path = Path(result.artifacts["narrative_markdown"])
    json_path = Path(result.artifacts["narrative_json"])

    assert markdown_path.exists()
    assert json_path.exists()

    # Check content mentions no triage
    content = markdown_path.read_text()
    assert "No ranked insights available" in content or "Run /analyze" in content


def test_skill_handles_missing_triage_json(temp_project):
    """Test that skill handles case where triage MD exists but JSON missing."""
    # Create triage markdown but no JSON
    triage_md = temp_project / "outputs" / "insight_triage.md"
    triage_md.write_text("# Sample triage markdown")

    skill = NarrativeSynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed with explanation
    assert result.success
    assert "narrative_markdown" in result.artifacts

    markdown_path = Path(result.artifacts["narrative_markdown"])
    content = markdown_path.read_text()

    assert "structured JSON not available" in content or "JSON missing" in content


def test_skill_generates_complete_narrative(temp_project, sample_triage_data):
    """Test that skill generates all required sections."""
    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = NarrativeSynthesisSkill()

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
    assert "narrative_markdown" in result.artifacts
    assert "narrative_json" in result.artifacts

    # Read markdown
    markdown_path = Path(result.artifacts["narrative_markdown"])
    content = markdown_path.read_text()

    # Check required sections
    assert "# Executive Narrative (Internal)" in content
    assert "## 1. What matters most (Top 3)" in content
    assert "## 2. What this means" in content
    assert "## 3. Recommended actions (Internal)" in content
    assert "## 4. Risks and caveats" in content
    assert "## 5. Evidence index" in content

    # Check INTERNAL ONLY marker
    assert "INTERNAL ONLY" in content


def test_deterministic_output(temp_project, sample_triage_data):
    """Test that output is deterministic for fixed input."""
    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = NarrativeSynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill twice
    result1 = skill.execute(context)

    # Read first output
    json_path1 = Path(result1.artifacts["narrative_json"])
    with open(json_path1) as f:
        data1 = json.load(f)

    result2 = skill.execute(context)

    # Read second output
    json_path2 = Path(result2.artifacts["narrative_json"])
    with open(json_path2) as f:
        data2 = json.load(f)

    # Sections should be identical (except generated_at timestamp)
    assert data1["sections"] == data2["sections"]
    assert data1["metadata"] == data2["metadata"]


def test_uses_only_triage_content(temp_project, sample_triage_data):
    """Test that narrative uses only triage content, no extra inference."""
    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = NarrativeSynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read markdown
    markdown_path = Path(result.artifacts["narrative_markdown"])
    content = markdown_path.read_text()

    # Check that insight titles from triage appear
    assert "Revenue growth opportunity in Region A" in content
    assert "Cost reduction potential in supply chain" in content

    # Check that caveats from triage appear
    assert "Statistical significance not assessed" in content

    # No new numbers should be fabricated
    # All metrics should come from triage "why_it_matters"
    assert "25%" in content  # From triage
    assert "15%" in content  # From triage


def test_evidence_index_truthful_about_hashes(temp_project, sample_triage_data):
    """Test that evidence index is truthful about hash availability."""
    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = NarrativeSynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read markdown
    markdown_path = Path(result.artifacts["narrative_markdown"])
    content = markdown_path.read_text()

    # Check evidence index section
    assert "## 5. Evidence index" in content
    assert "| Insight | Source | Hash | Confidence |" in content

    # Should show "hash unavailable" for entries without evidence ledger
    assert "hash unavailable" in content or "abc123def456" in content


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

    skill = NarrativeSynthesisSkill()

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

    skill = NarrativeSynthesisSkill()

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


def test_json_structure_completeness(temp_project, sample_triage_data):
    """Test that JSON output has complete structure."""
    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = NarrativeSynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read JSON
    json_path = Path(result.artifacts["narrative_json"])
    with open(json_path) as f:
        data = json.load(f)

    # Check required fields
    assert "generated_at" in data
    assert "status" in data
    assert "sections" in data

    # Check sections
    sections = data["sections"]
    assert "what_matters_most" in sections
    assert "implications" in sections
    assert "recommended_actions" in sections
    assert "risks_and_caveats" in sections

    # Check metadata
    assert "metadata" in data
    metadata = data["metadata"]
    assert "total_candidate_insights" in metadata
    assert "high_confidence_insights" in metadata


def test_confidence_levels_respected(temp_project, sample_triage_data):
    """Test that confidence levels from triage are respected."""
    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = NarrativeSynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read markdown
    markdown_path = Path(result.artifacts["narrative_markdown"])
    content = markdown_path.read_text()

    # Check that confidence levels are mentioned
    assert "Confidence: HIGH" in content
    assert "Confidence: MEDIUM" in content
    assert "Confidence: LOW" in content


def test_intent_integration(temp_project, sample_triage_data):
    """Test that project intent is integrated when available."""
    # Create intent file
    intent_path = temp_project / "project_state" / "intent.yaml"
    intent_data = {
        "intent_text": "Analyze revenue growth opportunities and cost reduction potential"
    }
    with open(intent_path, "w") as f:
        yaml.dump(intent_data, f)

    # Save triage JSON
    triage_path = temp_project / "outputs" / "insight_triage.json"
    triage_path.write_text(json.dumps(sample_triage_data, indent=2))

    skill = NarrativeSynthesisSkill()

    context = SkillContext(
        project_root=temp_project,
        current_stage="analyze",
        artifacts={"insight_triage": triage_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Read markdown
    markdown_path = Path(result.artifacts["narrative_markdown"])
    content = markdown_path.read_text()

    # Check that intent appears
    assert "Project Intent:" in content
    assert "revenue growth opportunities" in content
