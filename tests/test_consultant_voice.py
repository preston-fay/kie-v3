"""
Unit tests for ConsultantVoiceSkill.

Tests deterministic text polishing into crisp consulting language.
"""

from pathlib import Path

import pytest

from kie.skills.consultant_voice import ConsultantVoiceSkill
from kie.skills.base import SkillContext


def test_consultant_voice_removes_filler_words(tmp_path):
    """Test that filler words are removed deterministically."""
    skill = ConsultantVoiceSkill()

    original = "The data is very interesting and really shows that sales are quite strong."
    polished = skill._polish_text(original)

    # Filler words should be removed
    assert "very" not in polished
    assert "really" not in polished
    assert "quite" not in polished
    assert "interesting" in polished  # Content word preserved
    assert "sales" in polished
    assert "strong" in polished


def test_consultant_voice_strengthens_weak_verbs(tmp_path):
    """Test that weak verbs are strengthened."""
    skill = ConsultantVoiceSkill()

    original = "The analysis shows revenue growth. Data seems to show margin decline."
    polished = skill._polish_text(original)

    # Weak verbs should be strengthened
    assert "indicates" in polished
    assert "suggests" in polished
    assert "shows" not in polished or polished.count("shows") < original.count("shows")


def test_consultant_voice_removes_hedging_phrases(tmp_path):
    """Test that hedging phrases are removed."""
    skill = ConsultantVoiceSkill()

    original = "It is interesting to note that revenue increased. It appears that costs declined."
    polished = skill._polish_text(original)

    # Hedging phrases should be removed
    assert "it is interesting to note that" not in polished.lower()
    assert "it appears that" not in polished.lower()
    # But content should remain
    assert "revenue increased" in polished.lower()
    assert "costs declined" in polished.lower()


def test_consultant_voice_preserves_meaning(tmp_path):
    """Test that meaning and key terms are preserved."""
    skill = ConsultantVoiceSkill()

    original = "Revenue reached $1.2M in Q3. North region shows 25% margin."
    polished = skill._polish_text(original)

    # Numbers must be preserved exactly
    assert "$1.2M" in polished
    assert "25%" in polished
    # Key terms preserved
    assert "Revenue" in polished
    assert "Q3" in polished
    assert "North region" in polished
    assert "margin" in polished


def test_consultant_voice_deterministic_output(tmp_path):
    """Test that output is deterministic for same input."""
    skill = ConsultantVoiceSkill()

    original = "The data really shows that very strong performance."

    polished1 = skill._polish_text(original)
    polished2 = skill._polish_text(original)
    polished3 = skill._polish_text(original)

    # All outputs must be identical
    assert polished1 == polished2
    assert polished2 == polished3


def test_consultant_voice_processes_executive_summary(tmp_path):
    """Test that consultant voice processes executive_summary.md."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    # Create executive summary with filler and weak verbs
    summary = """# Executive Summary

It is interesting to note that revenue really shows strong growth.

- Sales are very high in Q3
- Margins seem to show improvement

## Risks

- Data is quite limited
"""
    (outputs_dir / "executive_summary.md").write_text(summary)

    # Execute skill
    skill = ConsultantVoiceSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={}
    )

    result = skill.execute(context)

    assert result.success
    assert (outputs_dir / "executive_summary_consultant.md").exists()

    # Check polished version
    polished = (outputs_dir / "executive_summary_consultant.md").read_text()

    # Filler removed
    assert "very" not in polished
    assert "really" not in polished
    assert "quite" not in polished
    assert "it is interesting to note that" not in polished.lower()

    # Weak verbs strengthened
    assert "indicates" in polished or "suggests" in polished

    # Content preserved
    assert "revenue" in polished.lower()
    assert "Q3" in polished
    assert "Margins" in polished


def test_consultant_voice_generates_diff_summary(tmp_path):
    """Test that diff summary is generated."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    summary = "The data is very interesting and really shows growth."
    (outputs_dir / "executive_summary.md").write_text(summary)

    skill = ConsultantVoiceSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={}
    )

    result = skill.execute(context)

    assert result.success
    assert (outputs_dir / "consultant_voice.md").exists()

    diff = (outputs_dir / "consultant_voice.md").read_text()

    # Should contain diff info
    assert "executive_summary.md" in diff
    assert "Before:" in diff or "After:" in diff or "Line" in diff


def test_consultant_voice_handles_missing_files_gracefully(tmp_path):
    """Test that missing input files are handled gracefully."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    # No executive_summary.md, no executive_narrative.md

    skill = ConsultantVoiceSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={}
    )

    result = skill.execute(context)

    # Should succeed with warnings
    assert result.success
    assert len(result.warnings) > 0
    assert any("not found" in w for w in result.warnings)


def test_consultant_voice_no_changes_if_already_clean(tmp_path):
    """Test that already-clean text generates no unnecessary changes."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    # Already consultant-grade text
    clean_summary = """# Executive Summary

Revenue indicates strong Q3 performance.

- Sales increased 25% year-over-year
- Margins expanded to 30%
"""
    (outputs_dir / "executive_summary.md").write_text(clean_summary)

    skill = ConsultantVoiceSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={}
    )

    result = skill.execute(context)

    assert result.success

    # Check if polished version is similar (may have minor whitespace changes)
    polished = (outputs_dir / "executive_summary_consultant.md").read_text()
    assert "Revenue indicates strong Q3 performance" in polished
    assert "25%" in polished
    assert "30%" in polished


def test_consultant_voice_preserves_all_insight_references(tmp_path):
    """Test that all insight IDs and references are preserved."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    summary = """# Executive Summary

It really shows that insight-1 indicates revenue growth.
The data very clearly suggests insight-2 implies cost reduction.
"""
    (outputs_dir / "executive_summary.md").write_text(summary)

    skill = ConsultantVoiceSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={}
    )

    result = skill.execute(context)

    polished = (outputs_dir / "executive_summary_consultant.md").read_text()

    # Insight references must be preserved
    assert "insight-1" in polished
    assert "insight-2" in polished


def test_consultant_voice_cleans_whitespace(tmp_path):
    """Test that excessive whitespace is cleaned up."""
    skill = ConsultantVoiceSkill()

    original = "Revenue  increased    by  25%  in   Q3."
    polished = skill._polish_text(original)

    # Should have single spaces
    assert "  " not in polished
    assert "Revenue increased by 25% in Q3" in polished
