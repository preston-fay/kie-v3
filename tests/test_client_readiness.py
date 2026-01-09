"""
Tests for Client Readiness Skill

Proves that:
1. Skill runs only in allowed stages (build, preview)
2. Skill produces deterministic output for fixed inputs
3. INTERNAL_ONLY when recovery plan exists
4. CLIENT_READY_WITH_CAVEATS when evidence limitations exist
5. CLIENT_READY when all conditions satisfied
6. Evidence references are present
7. No Rails state mutation occurs
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from kie.insights import (
    Insight,
    InsightCatalog,
    InsightType,
    InsightCategory,
    InsightSeverity,
    Evidence,
)
from kie.skills import SkillContext
from kie.skills.client_readiness import ClientReadinessSkill, ReadinessLabel


def test_client_readiness_skill_metadata():
    """Test ClientReadinessSkill has correct declarative metadata."""
    skill = ClientReadinessSkill()

    assert skill.skill_id == "client_readiness"
    assert skill.description
    assert "build" in skill.stage_scope
    assert "preview" in skill.stage_scope
    assert len(skill.required_artifacts) == 0  # Graceful when missing
    assert "client_readiness.md" in skill.produces_artifacts
    assert "client_readiness.json" in skill.produces_artifacts


def test_stage_scoping():
    """Test skill only applies to allowed stages."""
    skill = ClientReadinessSkill()

    # Should be applicable in build, preview
    assert skill.is_applicable("build") is True
    assert skill.is_applicable("preview") is True

    # Should NOT be applicable in other stages
    assert skill.is_applicable("startkie") is False
    assert skill.is_applicable("eda") is False
    assert skill.is_applicable("analyze") is False
    assert skill.is_applicable("spec") is False


def test_internal_only_when_recovery_plan_exists(tmp_path):
    """Test skill classifies as INTERNAL_ONLY when recovery plan exists."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create recovery plan (indicates WARN/BLOCK/FAIL)
    recovery_plan = project_state / "recovery_plan.md"
    recovery_plan.write_text("# Recovery Plan\n\nRecover from error...")

    # Create trust bundle
    trust_bundle_data = {
        "run_identity": {"run_id": "test_run_001", "command": "build"},
        "workflow_state": {"stage_after": "build"},
        "artifacts_produced": [],
    }
    trust_bundle_path = project_state / "trust_bundle.json"
    trust_bundle_path.write_text(json.dumps(trust_bundle_data))

    # Create candidate artifact
    candidate = outputs_dir / "insight_brief.md"
    candidate.write_text("# Brief\nTest brief")

    skill = ClientReadinessSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run_001",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success is True
    assert result.evidence["overall_readiness"] == ReadinessLabel.INTERNAL_ONLY.value

    # Load JSON output
    json_path = Path(result.artifacts["readiness_json"])
    readiness_data = json.loads(json_path.read_text())

    # Verify INTERNAL_ONLY classification
    assert readiness_data["overall_readiness"] == ReadinessLabel.INTERNAL_ONLY.value
    assert "recovery plan" in readiness_data["overall_reason"].lower()


def test_internal_only_when_trust_bundle_missing(tmp_path):
    """Test skill classifies as INTERNAL_ONLY when trust bundle missing."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()

    # Create candidate artifact
    candidate = outputs_dir / "insight_brief.md"
    candidate.write_text("# Brief\nTest brief")

    skill = ClientReadinessSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success is True
    assert result.evidence["overall_readiness"] == ReadinessLabel.INTERNAL_ONLY.value

    # Load JSON output
    json_path = Path(result.artifacts["readiness_json"])
    readiness_data = json.loads(json_path.read_text())

    # Verify INTERNAL_ONLY due to missing trust bundle
    assert readiness_data["overall_readiness"] == ReadinessLabel.INTERNAL_ONLY.value


def test_internal_only_when_critical_prerequisites_missing(tmp_path):
    """Test skill classifies as INTERNAL_ONLY when critical items missing."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create trust bundle with critical missing items
    trust_bundle_data = {
        "run_identity": {"run_id": "test_run_002", "command": "build"},
        "workflow_state": {"stage_after": "build"},
        "whats_missing": {
            "items": [
                {"name": "data files", "severity": "critical"},
                {"name": "insights catalog", "severity": "critical"},
            ]
        },
    }
    trust_bundle_path = project_state / "trust_bundle.json"
    trust_bundle_path.write_text(json.dumps(trust_bundle_data))

    # Create evidence ledger
    ledger_data = {
        "run_id": "test_run_002",
        "command": "/build",
        "outputs": [
            {"path": "outputs/insight_brief.md", "hash": "abc123"},
        ],
    }
    ledger_path = evidence_dir / "test_run_002.yaml"
    ledger_path.write_text(yaml.dump(ledger_data))

    # Create candidate artifact
    candidate = outputs_dir / "insight_brief.md"
    candidate.write_text("# Brief\nTest brief")

    skill = ClientReadinessSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run_002",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success is True
    assert result.evidence["overall_readiness"] == ReadinessLabel.INTERNAL_ONLY.value

    # Load JSON output
    json_path = Path(result.artifacts["readiness_json"])
    readiness_data = json.loads(json_path.read_text())

    # Verify INTERNAL_ONLY due to critical missing
    assert readiness_data["overall_readiness"] == ReadinessLabel.INTERNAL_ONLY.value
    assert "critical" in readiness_data["overall_reason"].lower()


def test_client_ready_with_caveats_for_low_confidence(tmp_path):
    """Test skill classifies as CLIENT_READY_WITH_CAVEATS for low confidence insights."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create trust bundle (no critical issues)
    trust_bundle_data = {
        "run_identity": {"run_id": "test_run_003", "command": "build"},
        "workflow_state": {"stage_after": "build"},
        "whats_missing": {"items": []},
        "warnings_blocks": {"warnings": [], "blocks": []},
    }
    trust_bundle_path = project_state / "trust_bundle.json"
    trust_bundle_path.write_text(json.dumps(trust_bundle_data))

    # Create evidence ledger
    ledger_data = {
        "run_id": "test_run_003",
        "command": "/build",
        "outputs": [
            {"path": "outputs/insight_triage.md", "hash": "def456"},
            {"path": "outputs/insight_triage.json", "hash": "ghi789"},
        ],
    }
    ledger_path = evidence_dir / "test_run_003.yaml"
    ledger_path.write_text(yaml.dump(ledger_data))

    # Create insight triage with non-High confidence
    triage_data = {
        "total_candidate_insights": 3,
        "high_confidence_insights": 1,
        "use_with_caution_insights": 2,
        "top_insights": [
            {
                "title": "Revenue trend",
                "confidence": "Medium",
                "evidence": [{"type": "metric", "reference": "test.json"}],
                "caveats": ["Limited data timeframe"],
            },
            {
                "title": "Cost pattern",
                "confidence": "Low",
                "evidence": [],
                "caveats": ["Weak statistical significance"],
            },
        ],
        "deprioritized_insights": [],
        "consultant_guidance": {
            "lead_with": [],
            "mention_cautiously": ["Revenue trend"],
            "avoid_leading_with": ["Cost pattern"],
        },
    }
    triage_json = outputs_dir / "insight_triage.json"
    triage_json.write_text(json.dumps(triage_data))

    triage_md = outputs_dir / "insight_triage.md"
    triage_md.write_text("# Insight Triage\nTest triage")

    skill = ClientReadinessSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run_003",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success is True
    assert result.evidence["overall_readiness"] == ReadinessLabel.CLIENT_READY_WITH_CAVEATS.value

    # Load JSON output
    json_path = Path(result.artifacts["readiness_json"])
    readiness_data = json.loads(json_path.read_text())

    # Verify CLIENT_READY_WITH_CAVEATS
    assert readiness_data["overall_readiness"] == ReadinessLabel.CLIENT_READY_WITH_CAVEATS.value

    # Verify caveats are present
    artifact_classifications = readiness_data["artifact_classifications"]
    triage_classification = [
        c for c in artifact_classifications
        if "insight_triage" in c["artifact"]
    ][0]
    assert len(triage_classification["caveats"]) > 0


def test_client_ready_when_all_conditions_met(tmp_path):
    """Test skill classifies as CLIENT_READY when all conditions satisfied."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create trust bundle (complete, no issues)
    trust_bundle_data = {
        "run_identity": {"run_id": "test_run_004", "command": "build"},
        "workflow_state": {"stage_after": "build"},
        "whats_missing": {"items": []},
        "warnings_blocks": {"warnings": [], "blocks": []},
    }
    trust_bundle_path = project_state / "trust_bundle.json"
    trust_bundle_path.write_text(json.dumps(trust_bundle_data))

    # Create evidence ledger
    ledger_data = {
        "run_id": "test_run_004",
        "command": "/build",
        "outputs": [
            {"path": "outputs/insight_brief.md", "hash": "abc123"},
        ],
    }
    ledger_path = evidence_dir / "test_run_004.yaml"
    ledger_path.write_text(yaml.dump(ledger_data))

    # Create candidate artifact
    candidate = outputs_dir / "insight_brief.md"
    candidate.write_text("# Brief\nTest brief")

    skill = ClientReadinessSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run_004",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed
    assert result.success is True
    assert result.evidence["overall_readiness"] == ReadinessLabel.CLIENT_READY.value

    # Load JSON output
    json_path = Path(result.artifacts["readiness_json"])
    readiness_data = json.loads(json_path.read_text())

    # Verify CLIENT_READY
    assert readiness_data["overall_readiness"] == ReadinessLabel.CLIENT_READY.value
    assert "complete" in readiness_data["overall_reason"].lower()


def test_evidence_references_include_hashes(tmp_path):
    """Test evidence references include artifact hashes when available."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create trust bundle
    trust_bundle_data = {
        "run_identity": {"run_id": "test_run_005", "command": "build"},
        "workflow_state": {"stage_after": "build"},
        "whats_missing": {"items": []},
    }
    trust_bundle_path = project_state / "trust_bundle.json"
    trust_bundle_path.write_text(json.dumps(trust_bundle_data))

    # Create evidence ledger with hashes
    ledger_data = {
        "run_id": "test_run_005",
        "command": "/build",
        "outputs": [
            {"path": "outputs/insight_brief.md", "hash": "abc123def456"},
            {"path": "outputs/run_story.md", "hash": "xyz789uvw012"},
        ],
    }
    ledger_path = evidence_dir / "test_run_005.yaml"
    ledger_path.write_text(yaml.dump(ledger_data))

    # Create candidate artifacts
    (outputs_dir / "insight_brief.md").write_text("# Brief\nTest brief")
    (outputs_dir / "run_story.md").write_text("# Story\nTest story")

    skill = ClientReadinessSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run_005",
    )

    # Execute skill
    result = skill.execute(context)

    # Load JSON output
    json_path = Path(result.artifacts["readiness_json"])
    readiness_data = json.loads(json_path.read_text())

    # Verify evidence includes hashes
    classifications = readiness_data["artifact_classifications"]

    brief_classification = [
        c for c in classifications
        if "insight_brief.md" in c["artifact"]
    ][0]

    # Should have hash
    assert len(brief_classification["evidence"]) > 0
    artifact_evidence = [e for e in brief_classification["evidence"] if e["type"] == "artifact"]
    assert len(artifact_evidence) > 0
    assert "abc123def456" in artifact_evidence[0]["hash"]


def test_no_rails_state_mutation(tmp_path):
    """Test skill does not mutate Rails state."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()

    # Create rails_state.json
    rails_state = {
        "current_stage": "build",
        "stages_completed": ["startkie", "eda", "analyze"],
    }

    rails_path = project_state / "rails_state.json"
    rails_path.write_text(json.dumps(rails_state))

    # Store original content
    original_rails = rails_path.read_text()

    # Create trust bundle
    trust_bundle_data = {
        "run_identity": {"run_id": "test_run_006", "command": "build"},
    }
    trust_bundle_path = project_state / "trust_bundle.json"
    trust_bundle_path.write_text(json.dumps(trust_bundle_data))

    skill = ClientReadinessSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    # Execute skill
    result = skill.execute(context)

    # Rails state should be unchanged
    current_rails = rails_path.read_text()
    assert current_rails == original_rails


def test_deterministic_output(tmp_path):
    """Test skill produces deterministic output for same input."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create trust bundle
    trust_bundle_data = {
        "run_identity": {"run_id": "test_run_007", "command": "build"},
        "whats_missing": {"items": []},
    }
    trust_bundle_path = project_state / "trust_bundle.json"
    trust_bundle_path.write_text(json.dumps(trust_bundle_data))

    # Create evidence ledger
    ledger_data = {
        "run_id": "test_run_007",
        "command": "/build",
        "outputs": [
            {"path": "outputs/insight_brief.md", "hash": "abc123"},
        ],
    }
    ledger_path = evidence_dir / "test_run_007.yaml"
    ledger_path.write_text(yaml.dump(ledger_data))

    # Create candidate artifact
    (outputs_dir / "insight_brief.md").write_text("# Brief\nTest")

    skill = ClientReadinessSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
        evidence_ledger_id="test_run_007",
    )

    # Execute twice
    result1 = skill.execute(context)

    # Remove outputs for second run
    (Path(result1.artifacts["readiness_json"])).unlink()
    (Path(result1.artifacts["readiness_markdown"])).unlink()

    result2 = skill.execute(context)

    # Load both JSON outputs
    json1 = json.loads(Path(result1.artifacts["readiness_json"]).read_text())
    json2 = json.loads(Path(result2.artifacts["readiness_json"]).read_text())

    # Should be identical (except timestamp)
    assert json1["overall_readiness"] == json2["overall_readiness"]
    assert json1["overall_reason"] == json2["overall_reason"]
    assert len(json1["artifact_classifications"]) == len(json2["artifact_classifications"])


def test_handles_no_candidates_gracefully(tmp_path):
    """Test skill handles missing candidate artifacts gracefully."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()

    skill = ClientReadinessSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={},
    )

    # Execute skill (no candidate artifacts)
    result = skill.execute(context)

    # Should succeed with warning
    assert result.success is True
    assert result.evidence["candidate_artifacts_count"] == 0

    # Should still produce artifacts
    assert "readiness_markdown" in result.artifacts
    assert "readiness_json" in result.artifacts

    # Verify files exist
    markdown_path = Path(result.artifacts["readiness_markdown"])
    json_path = Path(result.artifacts["readiness_json"])

    assert markdown_path.exists()
    assert json_path.exists()

    # Verify content
    content = markdown_path.read_text()
    assert "No candidate deliverables available" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
