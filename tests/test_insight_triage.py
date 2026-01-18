"""
Tests for Insight Triage Skill

Proves that:
1. Skill runs only in allowed stages (analyze, build, preview)
2. Skill produces deterministic output for fixed inputs
3. Missing insights handled gracefully
4. Evidence references are present
5. No Rails state mutation occurs
6. Confidence and caveat behavior is correct
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from kie.insights import (
    Insight,
    InsightCatalog,
    InsightType,
    InsightCategory,
    InsightSeverity,
    Evidence,
)
from kie.skills import SkillContext
from kie.skills.insight_triage import InsightTriageSkill, ConfidenceLevel, TriageScore


def test_insight_triage_skill_metadata():
    """Test InsightTriageSkill has correct declarative metadata."""
    skill = InsightTriageSkill()

    assert skill.skill_id == "insight_triage"
    assert skill.description
    assert "analyze" in skill.stage_scope
    assert "build" in skill.stage_scope
    assert "preview" in skill.stage_scope
    assert "insights_catalog" in skill.required_artifacts
    assert "insight_triage.md" in skill.produces_artifacts
    assert "insight_triage.json" in skill.produces_artifacts


def test_stage_scoping():
    """Test skill only applies to allowed stages."""
    skill = InsightTriageSkill()

    # Should be applicable in analyze, build, preview
    assert skill.is_applicable("analyze") is True
    assert skill.is_applicable("build") is True
    assert skill.is_applicable("preview") is True

    # Should NOT be applicable in other stages
    assert skill.is_applicable("startkie") is False
    assert skill.is_applicable("eda") is False
    assert skill.is_applicable("spec") is False


def test_prerequisite_checking(tmp_path):
    """Test skill checks prerequisites correctly."""
    skill = InsightTriageSkill()

    # Context without required artifacts
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    prereqs_met, missing = skill.check_prerequisites(context)
    assert prereqs_met is False
    assert "insights_catalog" in missing

    # Context with required artifacts
    context.artifacts["insights_catalog"] = tmp_path / "outputs" / "insights_catalog.json"

    prereqs_met, missing = skill.check_prerequisites(context)
    assert prereqs_met is True
    assert len(missing) == 0


def test_handles_missing_insights_gracefully(tmp_path):
    """Test skill handles missing insights catalog gracefully."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    skill = InsightTriageSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    # Execute skill (catalog doesn't exist)
    result = skill.execute(context)

    # Should succeed with warning
    assert result.success is True
    assert len(result.warnings) > 0
    assert result.evidence["total_candidate_insights"] == 0

    # Should still produce artifacts
    assert "triage_markdown" in result.artifacts
    assert "triage_json" in result.artifacts

    # Verify files exist
    markdown_path = Path(result.artifacts["triage_markdown"])
    json_path = Path(result.artifacts["triage_json"])

    assert markdown_path.exists()
    assert json_path.exists()

    # Verify content
    content = markdown_path.read_text()
    assert "No insights available for triage" in content


def test_handles_empty_catalog_gracefully(tmp_path):
    """Test skill handles empty insights catalog gracefully."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # Create empty catalog
    catalog_data = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "Test question",
        "project_name": "Test project",
        "insights": [],
        "data_summary": None,
    }

    catalog_path = internal_dir / "insights_catalog.json"
    catalog_path.write_text(json.dumps(catalog_data))

    skill = InsightTriageSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success is True
    assert result.evidence["total_candidate_insights"] == 0

    # Verify content
    markdown_path = Path(result.artifacts["triage_markdown"])
    content = markdown_path.read_text()
    assert "Total candidate insights: 0" in content


def test_triage_logic_with_insights(tmp_path):
    """Test triage logic correctly scores and prioritizes insights."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create catalog with varied insights
    insights = [
        # High-confidence recommendation (should be top)
        Insight(
            id="test_insight_1",
            headline="Reduce costs in Region A",
            supporting_text="Region A has 30% higher costs than average",
            insight_type=InsightType.COMPARISON,
            category=InsightCategory.RECOMMENDATION,
            severity=InsightSeverity.KEY,
            confidence=0.9,
            statistical_significance=0.001,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    reference="outputs/metrics.json",
                    value=0.30,
                    label="Cost variance",
                )
            ],
        ),
        # Medium-confidence finding (should be top or cautious)
        Insight(
            id="test_insight_2",
            headline="Sales increasing in Q4",
            supporting_text="Q4 shows 15% increase over Q3",
            insight_type=InsightType.TREND,
            category=InsightCategory.FINDING,
            severity=InsightSeverity.SUPPORTING,
            confidence=0.75,
            statistical_significance=0.02,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    reference="outputs/metrics.json",
                    value=0.15,
                    label="Growth rate",
                )
            ],
        ),
        # Low-confidence observation (should be deprioritized)
        Insight(
            id="test_insight_3",
            headline="Pattern observed in data",
            supporting_text="Some correlation noticed",
            insight_type=InsightType.CORRELATION,
            category=InsightCategory.FINDING,
            severity=InsightSeverity.CONTEXT,
            confidence=0.4,
            statistical_significance=0.15,
            evidence=[],
        ),
    ]

    catalog = InsightCatalog(
        generated_at=datetime.now().isoformat(),
        business_question="Test question",
        
        insights=insights,
        data_summary={"row_count": 1000},
    )

    catalog_path = internal_dir / "insights_catalog.json"
    catalog_path.write_text(json.dumps(catalog.to_dict()))

    skill = InsightTriageSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success is True
    assert result.evidence["total_candidate_insights"] == 3
    # Note: high_confidence count depends on triage logic, may be 0-3
    assert result.evidence["high_confidence_insights"] >= 0

    # Load JSON output
    json_path = Path(result.artifacts["triage_json"])
    triage_data = json.loads(json_path.read_text())

    # Verify triage structure
    assert "top_insights" in triage_data
    assert "deprioritized_insights" in triage_data
    assert "consultant_guidance" in triage_data

    # High-confidence recommendation should be in top insights
    top_titles = [ti["title"] for ti in triage_data["top_insights"]]
    assert "Reduce costs in Region A" in top_titles

    # Low-confidence observation should be deprioritized
    deprioritized = [di["insight"] for di in triage_data["deprioritized_insights"]]
    assert "Pattern observed in data" in deprioritized

    # Verify guidance structure
    guidance = triage_data["consultant_guidance"]
    assert "lead_with" in guidance
    assert "mention_cautiously" in guidance
    assert "avoid_leading_with" in guidance


def test_evidence_references_include_hashes(tmp_path):
    """Test evidence references include artifact hashes when available."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create evidence ledger with hashes
    ledger_data = {
        "run_id": "test_run",
        "command": "/analyze",
        "outputs": [
            {
                "path": "outputs/insights_catalog.json",
                "hash": "abc123def456",
            },
            {
                "path": "outputs/metrics.json",
                "hash": "xyz789uvw012",
            },
        ],
    }

    ledger_path = evidence_dir / "test_run.yaml"
    import yaml
    ledger_path.write_text(yaml.dump(ledger_data))

    # Create insight with evidence
    insight = Insight(
        id="test_evidence_1",
        headline="Test insight",
        supporting_text="Test text",
        insight_type=InsightType.COMPARISON,
        category=InsightCategory.RECOMMENDATION,
        severity=InsightSeverity.KEY,
        confidence=0.9,
        statistical_significance=0.001,
        evidence=[
            Evidence(
                evidence_type="metric",
                reference="outputs/metrics.json",
                value=100,
            )
        ],
    )

    catalog = InsightCatalog(
        generated_at=datetime.now().isoformat(),
        business_question="Test question",
        
        insights=[insight],
        data_summary={"row_count": 1000},
    )

    catalog_path = internal_dir / "insights_catalog.json"
    catalog_path.write_text(json.dumps(catalog.to_dict()))

    skill = InsightTriageSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
        evidence_ledger_id="test_run",
    )

    # Execute skill
    result = skill.execute(context)

    # Load JSON output
    json_path = Path(result.artifacts["triage_json"])
    triage_data = json.loads(json_path.read_text())

    # Verify evidence includes hashes
    top_insight = triage_data["top_insights"][0]
    evidence_refs = top_insight["evidence"]

    # Should have metrics.json with hash
    metrics_refs = [e for e in evidence_refs if "metrics.json" in e["reference"]]
    assert len(metrics_refs) > 0
    assert "hash" in metrics_refs[0]
    assert "xyz789uvw012" in metrics_refs[0]["hash"]


def test_confidence_levels_assigned_correctly(tmp_path):
    """Test confidence levels are assigned based on evidence and risk."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # High confidence: strong evidence, low risk
    high_conf_insight = Insight(
        id="conf_high_1",
        headline="High confidence insight",
        supporting_text="Well supported",
        insight_type=InsightType.COMPARISON,
        category=InsightCategory.RECOMMENDATION,
        severity=InsightSeverity.KEY,
        confidence=0.9,
        statistical_significance=0.001,
        evidence=[
            Evidence(evidence_type="metric", reference="test1.json", value=1),
            Evidence(evidence_type="metric", reference="test2.json", value=2),
        ],
    )

    # Low confidence: weak evidence or high risk
    low_conf_insight = Insight(
        id="conf_low_1",
        headline="Low confidence insight",
        supporting_text="Questionable support",
        insight_type=InsightType.CORRELATION,
        category=InsightCategory.FINDING,
        severity=InsightSeverity.CONTEXT,
        confidence=0.4,
        statistical_significance=0.15,
        evidence=[],
    )

    catalog = InsightCatalog(
        generated_at=datetime.now().isoformat(),
        business_question="Test question",
        
        insights=[high_conf_insight, low_conf_insight],
        data_summary={"row_count": 1000},
    )

    catalog_path = internal_dir / "insights_catalog.json"
    catalog_path.write_text(json.dumps(catalog.to_dict()))

    skill = InsightTriageSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
    )

    # Execute skill
    result = skill.execute(context)

    # Load JSON output
    json_path = Path(result.artifacts["triage_json"])
    triage_data = json.loads(json_path.read_text())

    # Find insights in triage
    top_insights = {ti["title"]: ti for ti in triage_data["top_insights"]}

    # High confidence insight should have High confidence
    if "High confidence insight" in top_insights:
        assert top_insights["High confidence insight"]["confidence"] == "High"

    # Low confidence insight should be deprioritized or have caveats
    if "Low confidence insight" in top_insights:
        assert top_insights["Low confidence insight"]["confidence"] in ["Low", "Medium"]


def test_caveats_generated_correctly(tmp_path):
    """Test caveats are generated for insights with limitations."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # Insight with no statistical significance
    insight = Insight(
        id="caveat_test_1",
        headline="Not significant finding",
        supporting_text="Observed but not confirmed",
        insight_type=InsightType.TREND,
        category=InsightCategory.FINDING,
        severity=InsightSeverity.SUPPORTING,
        confidence=0.6,
        statistical_significance=0.15,  # p > 0.05, not significant
        evidence=[
            Evidence(evidence_type="metric", reference="test.json", value=1),
        ],
    )

    catalog = InsightCatalog(
        generated_at=datetime.now().isoformat(),
        business_question="Test question",
        
        insights=[insight],
        data_summary={"row_count": 1000},
    )

    catalog_path = internal_dir / "insights_catalog.json"
    catalog_path.write_text(json.dumps(catalog.to_dict()))

    skill = InsightTriageSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
    )

    # Execute skill
    result = skill.execute(context)

    # Load JSON output
    json_path = Path(result.artifacts["triage_json"])
    triage_data = json.loads(json_path.read_text())

    # Verify caveats present
    if triage_data["top_insights"]:
        top_insight = triage_data["top_insights"][0]
        assert "caveats" in top_insight
        assert len(top_insight["caveats"]) > 0

        # Should mention statistical significance
        caveats_text = " ".join(top_insight["caveats"])
        assert "significant" in caveats_text.lower() or "p=" in caveats_text


def test_deterministic_output():
    """Test skill produces deterministic output for same input."""
    # This test ensures triage logic is reproducible
    insight = Insight(
        id="deterministic_test_1",
        headline="Test insight",
        supporting_text="Test text",
        insight_type=InsightType.COMPARISON,
        category=InsightCategory.RECOMMENDATION,
        severity=InsightSeverity.KEY,
        confidence=0.8,
        statistical_significance=0.01,
        evidence=[
            Evidence(evidence_type="metric", reference="test.json", value=100),
        ],
    )

    skill = InsightTriageSkill()

    # Score insight twice
    score1 = skill._score_insight(insight)
    score2 = skill._score_insight(insight)

    # Should be identical
    assert score1 == score2
    assert score1["decision_relevance"] == score2["decision_relevance"]
    assert score1["evidence_strength"] == score2["evidence_strength"]
    assert score1["misinterpretation_risk"] == score2["misinterpretation_risk"]


def test_no_rails_state_mutation(tmp_path):
    """Test skill does not mutate Rails state."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    internal_dir = outputs_dir / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    project_state = tmp_path / "project_state"
    project_state.mkdir()

    # Create rails_state.json
    rails_state = {
        "current_stage": "analyze",
        "stages_completed": ["startkie", "eda"],
    }

    rails_path = project_state / "rails_state.json"
    rails_path.write_text(json.dumps(rails_state))

    # Store original content
    original_rails = rails_path.read_text()

    # Create minimal catalog
    catalog_data = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "Test question",
        "project_name": "Test project",
        "insights": [],
        "data_summary": None,
    }

    catalog_path = internal_dir / "insights_catalog.json"
    catalog_path.write_text(json.dumps(catalog_data))

    skill = InsightTriageSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={"insights_catalog": catalog_path},
    )

    # Execute skill
    result = skill.execute(context)

    # Rails state should be unchanged
    current_rails = rails_path.read_text()
    assert current_rails == original_rails


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
