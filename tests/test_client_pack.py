"""
Tests for Client Pack Skill

Proves that:
1. Skill runs only in preview stage
2. Pack is generated even when not client-ready
3. Pack includes readiness gate + next actions
4. Pack aggregates available artifacts deterministically
5. Evidence index includes hashes and ledger ID
6. No Rails state mutation
7. Deterministic output for fixed inputs
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from kie.skills import SkillContext
from kie.skills.client_pack import ClientPackSkill


def test_client_pack_skill_metadata():
    """Test ClientPackSkill has correct declarative metadata."""
    skill = ClientPackSkill()

    assert skill.skill_id == "client_pack"
    assert skill.description
    assert skill.stage_scope == ["preview"]  # ONLY preview
    assert len(skill.required_artifacts) == 0  # Graceful when missing
    assert "client_pack.md" in skill.produces_artifacts
    assert "client_pack.json" in skill.produces_artifacts


def test_stage_scoping():
    """Test skill only applies to preview stage."""
    skill = ClientPackSkill()

    # Should ONLY be applicable in preview
    assert skill.is_applicable("preview") is True

    # Should NOT be applicable in any other stage
    assert skill.is_applicable("build") is False
    assert skill.is_applicable("analyze") is False
    assert skill.is_applicable("eda") is False
    assert skill.is_applicable("startkie") is False
    assert skill.is_applicable("spec") is False


def test_pack_generated_when_not_ready(tmp_path):
    """Test pack is generated even when NOT CLIENT READY."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create recovery plan (indicates NOT READY)
    recovery_plan = project_state / "recovery_plan.md"
    recovery_plan.write_text("# Recovery Plan\n\nRecover from error...")

    # Create client_readiness output showing INTERNAL_ONLY
    client_readiness_data = {
        "generated_at": "2024-01-01T00:00:00",
        "overall_readiness": "INTERNAL_ONLY",
        "overall_reason": "Recovery plan exists",
        "next_actions": [
            "python3 -m kie.cli doctor",
            "python3 -m kie.cli validate",
        ],
    }
    (outputs_dir / "client_readiness.json").write_text(
        json.dumps(client_readiness_data)
    )

    # Create trust bundle
    trust_bundle_data = {
        "run_identity": {"run_id": "test_run_001", "command": "preview"},
    }
    (project_state / "trust_bundle.json").write_text(json.dumps(trust_bundle_data))

    skill = ClientPackSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="preview",
        artifacts={},
        evidence_ledger_id="test_run_001",
    )

    # Execute skill
    result = skill.execute(context)

    # Should succeed despite NOT READY
    assert result.success is True
    assert result.evidence["is_client_ready"] is False

    # Load pack markdown
    pack_md = Path(result.artifacts["client_pack_markdown"]).read_text()

    # Verify NOT READY title
    assert "NOT CLIENT READY" in pack_md

    # Verify readiness gate section
    assert "## 0. Readiness Gate" in pack_md
    assert "INTERNAL_ONLY" in pack_md

    # Verify next actions are present
    assert "## Next CLI Actions" in pack_md or "### Next CLI Actions" in pack_md
    assert "python3 -m kie.cli doctor" in pack_md


def test_pack_includes_readiness_gate(tmp_path):
    """Test pack includes readiness gate with proof links."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create client_readiness
    client_readiness_data = {
        "overall_readiness": "CLIENT_READY",
        "overall_reason": "All conditions satisfied",
    }
    (outputs_dir / "client_readiness.json").write_text(
        json.dumps(client_readiness_data)
    )

    # Create trust bundle
    trust_bundle_data = {
        "run_identity": {"run_id": "test_run_002", "command": "preview"},
    }
    (project_state / "trust_bundle.json").write_text(json.dumps(trust_bundle_data))

    # Create evidence ledger
    ledger_data = {
        "run_id": "test_run_002",
        "command": "/preview",
        "outputs": [],
    }
    (evidence_dir / "test_run_002.yaml").write_text(yaml.dump(ledger_data))

    skill = ClientPackSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="preview",
        artifacts={},
        evidence_ledger_id="test_run_002",
    )

    # Execute skill
    result = skill.execute(context)

    # Load pack markdown
    pack_md = Path(result.artifacts["client_pack_markdown"]).read_text()

    # Verify readiness gate
    assert "## 0. Readiness Gate" in pack_md
    assert "CLIENT_READY" in pack_md

    # Verify proof links
    assert "Evidence Ledger" in pack_md
    assert "test_run_002.yaml" in pack_md
    assert "trust_bundle.json" in pack_md


def test_pack_aggregates_artifacts_deterministically(tmp_path):
    """Test pack aggregates all available artifacts."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create all possible input artifacts
    client_readiness_data = {
        "overall_readiness": "CLIENT_READY_WITH_CAVEATS",
        "overall_reason": "Some limitations exist",
        "approved_client_narrative": [
            "Analysis complete",
            "Key insights identified",
        ],
        "do_not_say": [
            "Do not claim 100% certainty",
        ],
        "artifact_classifications": [
            {
                "artifact": "outputs/insight_brief.md",
                "caveats": ["Limited timeframe"],
            }
        ],
    }
    (outputs_dir / "client_readiness.json").write_text(
        json.dumps(client_readiness_data)
    )

    insight_triage_data = {
        "top_insights": [
            {
                "title": "Revenue concentration risk",
                "confidence": "High",
                "evidence": [{"reference": "outputs/eda.json"}],
                "caveats": [],
            }
        ],
        "consultant_guidance": {
            "lead_with": ["Revenue concentration risk"],
            "mention_cautiously": [],
        },
    }
    (outputs_dir / "insight_triage.json").write_text(json.dumps(insight_triage_data))

    (outputs_dir / "insight_brief.md").write_text("# Insight Brief\n\nBrief content")
    (outputs_dir / "run_story.md").write_text("# Run Story\n\nStory content")

    # Create trust bundle
    trust_bundle_data = {
        "run_identity": {"run_id": "test_run_003", "command": "preview"},
    }
    (project_state / "trust_bundle.json").write_text(json.dumps(trust_bundle_data))

    skill = ClientPackSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="preview",
        artifacts={},
        evidence_ledger_id="test_run_003",
    )

    # Execute skill
    result = skill.execute(context)

    # Load pack markdown
    pack_md = Path(result.artifacts["client_pack_markdown"]).read_text()

    # Verify all sections present
    assert "## 0. Readiness Gate" in pack_md
    assert "## 1. Executive Narrative" in pack_md
    assert "## 2. Top Insights" in pack_md
    assert "## 3. Client-Safe Talking Points" in pack_md
    assert "## 4. Caveats & Limitations" in pack_md
    assert "## 5. Do Not Say" in pack_md
    assert "## 6. Evidence Index" in pack_md

    # Verify content from each artifact
    assert "Revenue concentration risk" in pack_md
    assert "Analysis complete" in pack_md
    assert "Do not claim 100% certainty" in pack_md


def test_evidence_index_includes_hashes_and_ledger_id(tmp_path):
    """Test evidence index includes artifact hashes and ledger ID."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()
    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir()

    # Create client_readiness
    client_readiness_data = {
        "overall_readiness": "CLIENT_READY",
    }
    (outputs_dir / "client_readiness.json").write_text(
        json.dumps(client_readiness_data)
    )

    # Create evidence ledger with hashes
    ledger_data = {
        "run_id": "test_run_004",
        "command": "/preview",
        "outputs": [
            {"path": "outputs/insight_brief.md", "hash": "abc123def456"},
            {"path": "outputs/run_story.md", "hash": "xyz789uvw012"},
        ],
    }
    (evidence_dir / "test_run_004.yaml").write_text(yaml.dump(ledger_data))

    skill = ClientPackSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="preview",
        artifacts={},
        evidence_ledger_id="test_run_004",
    )

    # Execute skill
    result = skill.execute(context)

    # Load pack markdown
    pack_md = Path(result.artifacts["client_pack_markdown"]).read_text()

    # Verify evidence index
    assert "## 6. Evidence Index" in pack_md
    assert "insight_brief.md" in pack_md
    assert "run_story.md" in pack_md
    assert "abc123" in pack_md
    assert "xyz789" in pack_md
    assert "test_run_004" in pack_md

    # Load pack JSON
    pack_json = json.loads(Path(result.artifacts["client_pack_json"]).read_text())

    # Verify JSON evidence index
    assert "evidence_index" in pack_json
    assert len(pack_json["evidence_index"]) == 2
    assert pack_json["evidence_index"][0]["ledger_id"] == "test_run_004"


def test_no_rails_state_mutation(tmp_path):
    """Test skill does not mutate Rails state."""
    # Setup
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()

    # Create rails_state.json
    rails_state = {
        "current_stage": "preview",
        "stages_completed": ["startkie", "eda", "analyze", "build"],
    }

    rails_path = project_state / "rails_state.json"
    rails_path.write_text(json.dumps(rails_state))

    # Store original content
    original_rails = rails_path.read_text()

    # Create client_readiness
    client_readiness_data = {
        "overall_readiness": "CLIENT_READY",
    }
    (outputs_dir / "client_readiness.json").write_text(
        json.dumps(client_readiness_data)
    )

    skill = ClientPackSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="preview",
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

    # Create client_readiness
    client_readiness_data = {
        "overall_readiness": "CLIENT_READY",
        "approved_client_narrative": ["Test narrative"],
    }
    (outputs_dir / "client_readiness.json").write_text(
        json.dumps(client_readiness_data)
    )

    # Create evidence ledger
    ledger_data = {
        "run_id": "test_run_005",
        "command": "/preview",
        "outputs": [
            {"path": "outputs/insight_brief.md", "hash": "abc123"},
        ],
    }
    (evidence_dir / "test_run_005.yaml").write_text(yaml.dump(ledger_data))

    skill = ClientPackSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="preview",
        artifacts={},
        evidence_ledger_id="test_run_005",
    )

    # Execute twice
    result1 = skill.execute(context)

    # Remove outputs for second run
    (Path(result1.artifacts["client_pack_markdown"])).unlink()
    (Path(result1.artifacts["client_pack_json"])).unlink()

    result2 = skill.execute(context)

    # Load both JSON outputs
    json1 = json.loads(Path(result1.artifacts["client_pack_json"]).read_text())
    json2 = json.loads(Path(result2.artifacts["client_pack_json"]).read_text())

    # Should be identical (except timestamp)
    assert json1["overall_readiness"] == json2["overall_readiness"]
    assert json1["is_client_ready"] == json2["is_client_ready"]
    assert json1["artifacts_included"] == json2["artifacts_included"]


def test_handles_missing_artifacts_gracefully(tmp_path):
    """Test skill handles missing input artifacts gracefully."""
    # Setup with NO input artifacts
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    project_state = tmp_path / "project_state"
    project_state.mkdir()

    skill = ClientPackSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="preview",
        artifacts={},
    )

    # Execute skill (no input artifacts available)
    result = skill.execute(context)

    # Should succeed
    assert result.success is True

    # Should produce artifacts
    assert "client_pack_markdown" in result.artifacts
    assert "client_pack_json" in result.artifacts

    # Verify files exist
    pack_md = Path(result.artifacts["client_pack_markdown"])
    pack_json = Path(result.artifacts["client_pack_json"])

    assert pack_md.exists()
    assert pack_json.exists()

    # Verify content acknowledges missing artifacts
    content = pack_md.read_text()
    assert "NOT CLIENT READY" in content or "not available" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
