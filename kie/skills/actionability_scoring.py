"""
Actionability Scoring Skill

WHAT THIS SKILL DOES:
Classifies insights and story sections by how decision-enabling they are.
This is the final judgment layer before presentation.

INPUTS (read-only, required):
- outputs/insight_triage.json
- outputs/executive_narrative.json (optional)
- outputs/executive_summary.json or .md (optional)
- project_state/intent.yaml

OUTPUTS:
- outputs/actionability_scores.json
- outputs/actionability_scores.md

STAGE SCOPE: analyze, build, preview

CLASSIFICATION CATEGORIES:
- decision_enabling: High confidence + clear implication → actionable decision
- directional: Medium confidence or incomplete implication → points direction
- informational: Low confidence or descriptive only → context/background

RULES:
- High confidence + clear implication → decision_enabling
- Medium confidence or incomplete implication → directional
- Low confidence or descriptive only → informational
- Never assign decision_enabling if confidence < high threshold
- Severity (Key vs Supporting) influences classification
- Alignment to stated objective matters
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.charts.formatting import format_number
from kie.skills.base import Skill, SkillContext, SkillResult


class ActionabilityScoringSkill(Skill):
    """
    Actionability Scoring Skill.

    Classifies insights by decision-enabling quality to drive emphasis
    in presentations and dashboards.
    """

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.7
    MEDIUM_CONFIDENCE_THRESHOLD = 0.4

    # Keywords that indicate actionability
    ACTION_KEYWORDS = [
        "recommend",
        "should",
        "must",
        "critical",
        "prioritize",
        "focus",
        "invest",
        "stop",
        "start",
        "continue",
        "change",
        "improve",
        "optimize",
        "reduce",
        "increase",
        "eliminate",
        "implement",
        "decision",
        "action",
    ]

    @property
    def skill_id(self) -> str:
        return "actionability_scoring"

    @property
    def description(self) -> str:
        return "Classify insights by decision-enabling quality"

    @property
    def stage_scope(self) -> list[str]:
        return ["analyze", "build", "preview"]

    @property
    def required_artifacts(self) -> list[str]:
        return ["insight_triage"]

    @property
    def produces_artifacts(self) -> list[str]:
        return ["actionability_scores_json", "actionability_scores_markdown"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute actionability scoring.

        Args:
            context: Read-only context with project state and artifacts

        Returns:
            SkillResult with scoring artifacts and status
        """
        warnings = []
        errors = []

        outputs_dir = context.project_root / "outputs"
        project_state_dir = context.project_root / "project_state"

        # Validate required inputs
        (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
        triage_path = outputs_dir / "internal" / "insight_triage.json"
        intent_path = project_state_dir / "intent.yaml"

        if not triage_path.exists():
            errors.append("insight_triage.json not found")
            return SkillResult(
                success=False,
                artifacts={},
                evidence=[],
                warnings=warnings,
                errors=errors,
            )

        # Load inputs
        with open(triage_path) as f:
            triage_data = json.load(f)

        # Load intent if available
        objective = ""
        if intent_path.exists():
            import yaml

            with open(intent_path) as f:
                intent_data = yaml.safe_load(f)
                objective = intent_data.get("objective", "")

        # Score insights
        judged_insights = triage_data.get("judged_insights", [])
        scored_insights = []

        for insight in judged_insights:
            score = self._score_insight(insight, objective)
            scored_insights.append(score)

        # Calculate summary
        summary = {
            "decision_enabling_count": sum(
                1 for s in scored_insights if s["actionability"] == "decision_enabling"
            ),
            "directional_count": sum(
                1 for s in scored_insights if s["actionability"] == "directional"
            ),
            "informational_count": sum(
                1 for s in scored_insights if s["actionability"] == "informational"
            ),
        }

        # Build output
        output = {"insights": scored_insights, "summary": summary}

        # Save JSON
        scores_json_path = outputs_dir / "internal" / "actionability_scores.json"
        with open(scores_json_path, "w") as f:
            json.dump(output, f, indent=2)

        # Save Markdown
        scores_md_path = outputs_dir / "internal" / "actionability_scores.md"
        markdown = self._generate_markdown(output)
        scores_md_path.write_text(markdown)

        evidence = [
            f"Scored {len(scored_insights)} insights",
            f"Decision-enabling: {summary['decision_enabling_count']}",
            f"Directional: {summary['directional_count']}",
            f"Informational: {summary['informational_count']}",
        ]

        return SkillResult(
            success=True,
            artifacts={
                "actionability_scores_json": scores_json_path,
                "actionability_scores_markdown": scores_md_path,
            },
            evidence=evidence,
            warnings=warnings,
            errors=errors,
        )

    def _score_insight(self, insight: dict[str, Any], objective: str) -> dict[str, Any]:
        """
        Score a single insight for actionability.

        Args:
            insight: Insight data from triage
            objective: Project objective

        Returns:
            Scored insight with actionability classification
        """
        insight_id = insight.get("insight_id", "")
        title = insight.get("headline", "")
        confidence = self._parse_confidence(insight.get("confidence", "unknown"))
        severity = insight.get("severity", "unknown")
        implications = insight.get("implications", "")
        recommendation = insight.get("recommendation", "")

        # Combine text for analysis
        full_text = f"{title} {implications} {recommendation}".lower()

        # Count action keywords
        action_keyword_count = sum(1 for kw in self.ACTION_KEYWORDS if kw in full_text)

        # Check objective alignment
        objective_aligned = False
        if objective:
            objective_words = set(objective.lower().split())
            title_words = set(title.lower().split())
            objective_aligned = len(objective_words & title_words) > 0

        # Classification logic
        actionability = "informational"  # Default
        rationale = []

        # Decision-enabling criteria
        if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            rationale.append(f"High confidence ({format_number(confidence, precision=2, abbreviate=False)})")

            if action_keyword_count >= 2:
                rationale.append(f"Strong action language ({action_keyword_count} keywords)")
                actionability = "decision_enabling"

            elif severity == "Key":
                rationale.append("Key insight severity")
                if action_keyword_count >= 1 or objective_aligned:
                    actionability = "decision_enabling"
                else:
                    actionability = "directional"

            elif action_keyword_count >= 1:
                rationale.append("Action language present")
                actionability = "directional"

            else:
                rationale.append("Lacks clear action implication")
                actionability = "directional"

        # Medium confidence
        elif confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            rationale.append(f"Medium confidence ({format_number(confidence, precision=2, abbreviate=False)})")

            if action_keyword_count >= 2 and severity == "Key":
                rationale.append("Strong action language with key severity")
                actionability = "directional"
            elif action_keyword_count >= 1:
                rationale.append("Some action language")
                actionability = "directional"
            else:
                rationale.append("Limited actionability")
                actionability = "informational"

        # Low confidence
        else:
            rationale.append(f"Low confidence ({format_number(confidence, precision=2, abbreviate=False)})")
            rationale.append("Descriptive or exploratory")
            actionability = "informational"

        # Objective alignment bonus
        if objective_aligned:
            rationale.append("Aligns with stated objective")
            # Bump up one level if not already decision_enabling
            if actionability == "informational":
                actionability = "directional"

        return {
            "insight_id": insight_id,
            "title": title,
            "actionability": actionability,
            "rationale": " | ".join(rationale),
            "confidence": confidence,
            "severity": severity,
        }

    def _parse_confidence(self, confidence_str: str) -> float:
        """Parse confidence string to numeric value."""
        confidence_map = {
            "high": 0.85,
            "medium": 0.60,
            "low": 0.35,
            "unknown": 0.30,
        }
        return confidence_map.get(confidence_str.lower(), 0.30)

    def _generate_markdown(self, output: dict[str, Any]) -> str:
        """Generate markdown report of actionability scores."""
        lines = [
            "# Actionability Scores",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Decision-Enabling**: {output['summary']['decision_enabling_count']} insights",
            f"- **Directional**: {output['summary']['directional_count']} insights",
            f"- **Informational**: {output['summary']['informational_count']} insights",
            "",
            "---",
            "",
        ]

        # Group by actionability
        by_category = {
            "decision_enabling": [],
            "directional": [],
            "informational": [],
        }

        for insight in output["insights"]:
            category = insight["actionability"]
            by_category[category].append(insight)

        # Decision-enabling insights
        if by_category["decision_enabling"]:
            lines.append("## Decision-Enabling Insights")
            lines.append("")
            lines.append("These insights have high confidence and clear action implications.")
            lines.append("")
            for insight in by_category["decision_enabling"]:
                lines.append(f"### {insight['title']}")
                lines.append("")
                lines.append(f"**Confidence**: {insight['confidence']:.2f}")
                lines.append(f"**Severity**: {insight['severity']}")
                lines.append(f"**Rationale**: {insight['rationale']}")
                lines.append("")

        # Directional insights
        if by_category["directional"]:
            lines.append("## Directional Insights")
            lines.append("")
            lines.append("These insights point direction but may need additional validation.")
            lines.append("")
            for insight in by_category["directional"]:
                lines.append(f"### {insight['title']}")
                lines.append("")
                lines.append(f"**Confidence**: {insight['confidence']:.2f}")
                lines.append(f"**Severity**: {insight['severity']}")
                lines.append(f"**Rationale**: {insight['rationale']}")
                lines.append("")

        # Informational insights
        if by_category["informational"]:
            lines.append("## Informational Insights")
            lines.append("")
            lines.append("These insights provide context but lack clear action implications.")
            lines.append("")
            for insight in by_category["informational"]:
                lines.append(f"### {insight['title']}")
                lines.append("")
                lines.append(f"**Confidence**: {insight['confidence']:.2f}")
                lines.append(f"**Severity**: {insight['severity']}")
                lines.append(f"**Rationale**: {insight['rationale']}")
                lines.append("")

        return "\n".join(lines)
