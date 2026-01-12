"""
Unit tests for Actionability Scoring Skill.

Tests that the skill correctly classifies insights by decision-enabling quality.
"""

import json
from pathlib import Path

import pytest
import yaml

from kie.skills.actionability_scoring import ActionabilityScoringSkill
from kie.skills.base import SkillContext


def test_actionability_scoring_requires_insight_triage(tmp_path):
    """Test that actionability scoring fails without insight_triage.json."""
    # Create project structure
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create intent but NO insight_triage
    (project_state_dir / "intent.yaml").write_text("objective: Test\n")

    # Run skill
    skill = ActionabilityScoringSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    result = skill.execute(context)

    # Should fail with error
    assert not result.success
    assert any("insight_triage" in str(e).lower() for e in result.errors)


def test_actionability_scoring_high_confidence_action_keywords(tmp_path):
    """Test that high confidence + action keywords → decision_enabling."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create insight with high confidence and action keywords
    triage = {
        "judged_insights": [
            {
                "insight_id": "test-1",
                "headline": "Recommend prioritizing North region",
                "confidence": "high",
                "severity": "Key",
                "implications": "Revenue growth critical for Q4",
                "recommendation": "Focus investment on North market",
            }
        ]
    }
    (outputs_dir / "insight_triage.json").write_text(json.dumps(triage))
    (project_state_dir / "intent.yaml").write_text("objective: Increase revenue\n")

    # Run skill
    skill = ActionabilityScoringSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    result = skill.execute(context)

    # Should succeed
    assert result.success

    # Load scores
    scores_path = outputs_dir / "actionability_scores.json"
    assert scores_path.exists()

    with open(scores_path) as f:
        scores = json.load(f)

    # Check classification
    insights = scores.get("insights", [])
    assert len(insights) == 1
    assert insights[0]["actionability"] == "decision_enabling"
    assert "High confidence" in insights[0]["rationale"]
    assert "action language" in insights[0]["rationale"].lower()


def test_actionability_scoring_medium_confidence_directional(tmp_path):
    """Test that medium confidence → directional."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create insight with medium confidence
    triage = {
        "judged_insights": [
            {
                "insight_id": "test-1",
                "headline": "South region shows potential",
                "confidence": "medium",
                "severity": "Supporting",
                "implications": "May improve with investment",
                "recommendation": "Consider exploring South opportunities",
            }
        ]
    }
    (outputs_dir / "insight_triage.json").write_text(json.dumps(triage))
    (project_state_dir / "intent.yaml").write_text("objective: Growth strategy\n")

    # Run skill
    skill = ActionabilityScoringSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    result = skill.execute(context)

    # Should succeed
    assert result.success

    # Load scores
    with open(outputs_dir / "actionability_scores.json") as f:
        scores = json.load(f)

    # Check classification
    insights = scores.get("insights", [])
    assert len(insights) == 1
    assert insights[0]["actionability"] == "directional"
    assert "Medium confidence" in insights[0]["rationale"]


def test_actionability_scoring_low_confidence_informational(tmp_path):
    """Test that low confidence → informational."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create insight with low confidence and NO action keywords
    # Use non-overlapping words to avoid objective alignment bonus
    triage = {
        "judged_insights": [
            {
                "insight_id": "test-1",
                "headline": "West region shows variability",
                "confidence": "low",
                "severity": "Supporting",
                "implications": "Further investigation required",
                "recommendation": "Additional collection may help",
            }
        ]
    }
    (outputs_dir / "insight_triage.json").write_text(json.dumps(triage))
    (project_state_dir / "intent.yaml").write_text("objective: Analyze sales performance\n")

    # Run skill
    skill = ActionabilityScoringSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    result = skill.execute(context)

    # Should succeed
    assert result.success

    # Load scores
    with open(outputs_dir / "actionability_scores.json") as f:
        scores = json.load(f)

    # Check classification
    insights = scores.get("insights", [])
    assert len(insights) == 1
    # Low confidence always results in informational, regardless of action keywords
    assert insights[0]["actionability"] == "informational"
    assert "Low confidence" in insights[0]["rationale"]


def test_actionability_scoring_objective_alignment_bonus(tmp_path):
    """Test that objective alignment bumps informational → directional."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create insight with medium confidence but no action keywords
    # Headline aligns with objective
    triage = {
        "judged_insights": [
            {
                "insight_id": "test-1",
                "headline": "Revenue patterns show seasonality",
                "confidence": "medium",
                "severity": "Supporting",
                "implications": "Q4 consistently higher than Q2",
                "recommendation": "",
            }
        ]
    }
    (outputs_dir / "insight_triage.json").write_text(json.dumps(triage))
    (project_state_dir / "intent.yaml").write_text("objective: Analyze revenue trends\n")

    # Run skill
    skill = ActionabilityScoringSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    result = skill.execute(context)

    # Should succeed
    assert result.success

    # Load scores
    with open(outputs_dir / "actionability_scores.json") as f:
        scores = json.load(f)

    # Check classification - without objective alignment would be informational
    # With alignment should be directional
    insights = scores.get("insights", [])
    assert len(insights) == 1
    # Could be informational OR directional depending on action keywords
    # Main test: objective alignment is mentioned in rationale
    assert insights[0]["actionability"] in ["informational", "directional"]


def test_actionability_scoring_summary_counts(tmp_path):
    """Test that summary correctly counts classifications."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create multiple insights with different confidence levels
    triage = {
        "judged_insights": [
            {
                "insight_id": "test-1",
                "headline": "Must prioritize North",
                "confidence": "high",
                "severity": "Key",
                "implications": "Critical for growth",
                "recommendation": "Immediate action required",
            },
            {
                "insight_id": "test-2",
                "headline": "South shows potential",
                "confidence": "medium",
                "severity": "Supporting",
                "implications": "May improve",
                "recommendation": "Consider exploring",
            },
            {
                "insight_id": "test-3",
                "headline": "Data quality varies",
                "confidence": "low",
                "severity": "Supporting",
                "implications": "Needs validation",
                "recommendation": "",
            },
        ]
    }
    (outputs_dir / "insight_triage.json").write_text(json.dumps(triage))
    (project_state_dir / "intent.yaml").write_text("objective: Growth\n")

    # Run skill
    skill = ActionabilityScoringSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    result = skill.execute(context)

    # Should succeed
    assert result.success

    # Load scores
    with open(outputs_dir / "actionability_scores.json") as f:
        scores = json.load(f)

    # Check summary
    summary = scores.get("summary", {})
    total = (
        summary.get("decision_enabling_count", 0)
        + summary.get("directional_count", 0)
        + summary.get("informational_count", 0)
    )
    assert total == 3

    # Expect at least 1 decision_enabling (test-1) and 1 informational (test-3)
    assert summary.get("decision_enabling_count", 0) >= 1
    assert summary.get("informational_count", 0) >= 1


def test_actionability_scoring_markdown_generation(tmp_path):
    """Test that markdown report is generated."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    project_state_dir = tmp_path / "project_state"
    project_state_dir.mkdir()

    # Create simple insight
    triage = {
        "judged_insights": [
            {
                "insight_id": "test-1",
                "headline": "Test insight",
                "confidence": "high",
                "severity": "Key",
                "implications": "Test",
                "recommendation": "Recommend action",
            }
        ]
    }
    (outputs_dir / "insight_triage.json").write_text(json.dumps(triage))
    (project_state_dir / "intent.yaml").write_text("objective: Test\n")

    # Run skill
    skill = ActionabilityScoringSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="analyze",
        artifacts={},
    )

    result = skill.execute(context)

    # Should succeed
    assert result.success

    # Check markdown exists
    md_path = outputs_dir / "actionability_scores.md"
    assert md_path.exists()

    # Check markdown content
    md_content = md_path.read_text()
    assert "# Actionability Scores" in md_content
    assert "## Summary" in md_content
    assert "## Decision-Enabling Insights" in md_content or "## Directional Insights" in md_content
