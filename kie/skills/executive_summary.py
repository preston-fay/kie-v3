"""
Executive Summary Skill

Produces consultant-grade executive summary from judged artifacts.
This is NOT a fixed-length bullet generator - it optimizes for correctness,
clarity, and impact, not arbitrary brevity.

This is the slide a Partner would actually read.

ENHANCED (Phase 5): Now includes formatted tables and chart embeds.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.reports.markdown_enhancer import (
    create_confidence_distribution_table,
    create_insight_distribution_table,
    embed_chart,
    format_markdown_table,
)
from kie.skills.base import Skill, SkillContext, SkillResult


class ExecutiveSummarySkill(Skill):
    """
    Synthesizes executive summary from triage, narrative, and visualization plan.

    INPUTS (read-only, required):
    - outputs/insight_triage.json
    - outputs/executive_narrative.md or .json
    - outputs/visualization_plan.json
    - project_state/intent.yaml (if present)

    OUTPUTS:
    - outputs/executive_summary.md (INTERNAL)
    - outputs/executive_summary.json (structured)

    STAGE SCOPE:
    - analyze
    - build
    - preview
    """

    @staticmethod
    def _get_confidence_numeric(insight: dict) -> float:
        """Extract numeric confidence from insight, handling multiple formats."""
        conf = insight.get("confidence")
        if isinstance(conf, dict):
            return conf.get("numeric", 0)
        elif isinstance(conf, str):
            # Map string confidence to numeric
            conf_map = {"Very High": 0.9, "High": 0.8, "Medium": 0.65, "Low": 0.4}
            return conf_map.get(conf, 0.5)
        elif isinstance(conf, (int, float)):
            return conf
        return 0

    @staticmethod
    def _get_confidence_label(insight: dict) -> str:
        """Extract confidence label from insight, handling multiple formats."""
        conf = insight.get("confidence")
        if isinstance(conf, dict):
            return conf.get("label", "UNKNOWN")
        elif isinstance(conf, str):
            return conf
        elif isinstance(conf, (int, float)):
            # Map numeric to label
            if conf >= 0.85:
                return "Very High"
            elif conf >= 0.7:
                return "High"
            elif conf >= 0.5:
                return "Medium"
            else:
                return "Low"
        return "UNKNOWN"

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill."""
        return "executive_summary"

    @property
    def stage_scope(self) -> list[str]:
        """Stages where this skill should run."""
        return ["analyze", "build", "preview"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute executive summary generation from judged artifacts.

        Args:
            context: Skill execution context with artifacts

        Returns:
            SkillResult with summary paths and metadata
        """
        outputs_dir = context.project_root / "outputs"
        internal_dir = outputs_dir / "internal"
        project_state_dir = context.project_root / "project_state"

        # Load required inputs (JSON artifacts are in internal/ directory)
        triage_json_path = internal_dir / "insight_triage.json"
        narrative_md_path = outputs_dir / "executive_narrative.md"  # MD may be in root
        narrative_json_path = internal_dir / "executive_narrative.json"
        viz_plan_path = internal_dir / "visualization_plan.json"

        # Check prerequisites
        if not triage_json_path.exists():
            return self._handle_missing_prerequisite(
                outputs_dir, "insight_triage.json"
            )

        if not narrative_md_path.exists() and not narrative_json_path.exists():
            return self._handle_missing_prerequisite(
                outputs_dir, "executive_narrative"
            )

        if not viz_plan_path.exists():
            return self._handle_missing_prerequisite(
                outputs_dir, "visualization_plan.json"
            )

        # Load data
        with open(triage_json_path) as f:
            triage_data = json.load(f)

        narrative_data = None
        if narrative_json_path.exists():
            with open(narrative_json_path) as f:
                narrative_data = json.load(f)

        with open(viz_plan_path) as f:
            viz_plan = json.load(f)

        # Load intent if available
        intent_text = self._load_intent(project_state_dir)

        # Generate executive summary
        summary_md = self._generate_summary_markdown(
            triage_data, narrative_data, viz_plan, intent_text
        )
        summary_json = self._generate_summary_json(
            triage_data, narrative_data, viz_plan, intent_text
        )

        # Save outputs (internal artifacts)
        internal_dir.mkdir(parents=True, exist_ok=True)
        summary_md_path = internal_dir / "executive_summary.md"
        summary_json_path = internal_dir / "executive_summary.json"

        summary_md_path.write_text(summary_md)
        summary_json_path.write_text(json.dumps(summary_json, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "executive_summary_markdown": str(summary_md_path),
                "executive_summary_json": str(summary_json_path),
            },
            evidence={
                "triage_input": str(triage_json_path),
                "narrative_input": str(narrative_json_path if narrative_json_path.exists() else narrative_md_path),
                "viz_plan_input": str(viz_plan_path),
                "top_insights_count": len(triage_data.get("top_insights", [])),
                "key_findings_count": len(summary_json.get("key_findings", [])),
            },
            metadata={
                "artifact_classification": "INTERNAL",
                "generated_at": datetime.now().isoformat(),
            },
        )

    def _handle_missing_prerequisite(
        self, outputs_dir: Path, missing_artifact: str
    ) -> SkillResult:
        """Handle case where required artifact is missing."""
        summary_md = (
            f"# Executive Summary (Internal)\n\n"
            f"**Status:** Missing required artifact: {missing_artifact}\n\n"
            f"The executive summary skill requires:\n"
            f"- outputs/insight_triage.json\n"
            f"- outputs/executive_narrative.md or .json\n"
            f"- outputs/visualization_plan.json\n\n"
            f"**Resolution:** Run /analyze to generate all required artifacts.\n"
        )

        summary_json = {
            "status": "missing_prerequisites",
            "missing_artifact": missing_artifact,
            "message": f"Required artifact missing: {missing_artifact}",
        }

        internal_dir = outputs_dir / "internal"
        internal_dir.mkdir(parents=True, exist_ok=True)
        summary_md_path = internal_dir / "executive_summary.md"
        summary_json_path = internal_dir / "executive_summary.json"

        summary_md_path.write_text(summary_md)
        summary_json_path.write_text(json.dumps(summary_json, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "executive_summary_markdown": str(summary_md_path),
                "executive_summary_json": str(summary_json_path),
            },
            evidence={
                "status": "missing_prerequisites",
                "missing_artifact": missing_artifact,
            },
        )

    def _load_intent(self, project_state_dir: Path) -> str:
        """Load project intent if available."""
        intent_path = project_state_dir / "intent.yaml"
        if not intent_path.exists():
            return ""

        import yaml

        with open(intent_path) as f:
            intent_data = yaml.safe_load(f)
            if intent_data:
                return intent_data.get("intent", "")
        return ""

    def _generate_summary_markdown(
        self,
        triage_data: dict[str, Any],
        narrative_data: dict[str, Any] | None,
        viz_plan: dict[str, Any],
        intent_text: str,
    ) -> str:
        """Generate executive summary markdown with enhanced formatting."""
        lines = []
        lines.append("# Executive Summary")
        lines.append("")
        lines.append("*Internal Document — Consultant-Grade Synthesis*")
        lines.append("")

        if intent_text:
            lines.append(f"**Project Objective:** {intent_text}")
            lines.append("")

        # Section 1: Insight Overview Table (NEW - shows distribution at a glance)
        top_insights = triage_data.get("top_insights", [])
        if top_insights:
            lines.append("## Insight Overview")
            lines.append("")

            # Create distribution table
            insight_table = create_insight_distribution_table(
                top_insights, strength_key="confidence", confidence_key="confidence"
            )
            lines.append(insight_table)
            lines.append("")

            # Also show confidence distribution
            lines.append("### Confidence Distribution")
            lines.append("")
            confidence_table = create_confidence_distribution_table(
                top_insights, confidence_field="confidence"
            )
            lines.append(confidence_table)
            lines.append("")

        # Section 2: Situation Overview
        lines.append("## Situation Overview")
        lines.append("")
        situation_bullets = self._generate_situation_overview(
            triage_data, narrative_data, intent_text
        )
        for bullet in situation_bullets:
            lines.append(f"- {bullet}")
        lines.append("")

        # Section 3: Key Findings
        lines.append("## Key Findings")
        lines.append("")
        for insight in top_insights:
            confidence_label = self._get_confidence_label(insight)
            finding_text = self._format_finding(insight, confidence_label)
            lines.append(f"- {finding_text}")
        lines.append("")

        # NEW: Embed chart if top insight has associated visualization
        # Check if charts are available in outputs/charts/
        if top_insights and len(top_insights) > 0:
            first_insight = top_insights[0]
            chart_id = first_insight.get("chart_id") or first_insight.get("id")

            if chart_id:
                lines.append("### Supporting Visualization")
                lines.append("")
                lines.append(embed_chart(
                    chart_id,
                    "Key Insights Visualization",
                    charts_dir="../charts"  # Relative to outputs/
                ))
                lines.append("")

        # Section 4: Why This Matters
        lines.append("## Why This Matters")
        lines.append("")
        implications = self._generate_implications(top_insights)
        for implication in implications:
            lines.append(f"- {implication}")
        lines.append("")

        # Section 5: Recommended Actions (Internal)
        lines.append("## Recommended Actions (Internal)")
        lines.append("")
        actions = self._generate_recommended_actions(top_insights, viz_plan)
        for action in actions:
            lines.append(f"- {action}")
        lines.append("")

        # Section 6: Risks & Caveats
        lines.append("## Risks & Caveats")
        lines.append("")
        caveats = self._consolidate_caveats(triage_data, viz_plan)
        if caveats:
            for caveat in caveats:
                lines.append(f"- {caveat}")
        else:
            lines.append("- No significant caveats identified")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        lines.append("*This summary synthesizes judged insights from triage, narrative, and visualization planning.*")
        lines.append("")
        lines.append("*For HTML version: Convert with `kie.reports.markdown_to_html()`*")

        return "\n".join(lines)

    def _generate_summary_json(
        self,
        triage_data: dict[str, Any],
        narrative_data: dict[str, Any] | None,
        viz_plan: dict[str, Any],
        intent_text: str,
    ) -> dict[str, Any]:
        """Generate executive summary JSON structure."""
        top_insights = triage_data.get("top_insights", [])

        return {
            "generated_at": datetime.now().isoformat(),
            "project_intent": intent_text,
            "situation_overview": self._generate_situation_overview(
                triage_data, narrative_data, intent_text
            ),
            "key_findings": [
                {
                    "insight_id": insight.get("id", ""),
                    "title": insight.get("title", ""),
                    "confidence": insight.get("confidence", {}),
                    "decision_enabling": self._get_confidence_numeric(insight) >= 0.7,
                }
                for insight in top_insights
            ],
            "implications": self._generate_implications(top_insights),
            "recommended_actions": self._generate_recommended_actions(top_insights, viz_plan),
            "caveats": self._consolidate_caveats(triage_data, viz_plan),
            "metadata": {
                "artifact_classification": "INTERNAL",
                "insights_reviewed": len(top_insights),
                "visualizations_planned": viz_plan.get("visualizations_planned", 0),
            },
        }

    def _generate_situation_overview(
        self,
        triage_data: dict[str, Any],
        narrative_data: dict[str, Any] | None,
        intent_text: str,
    ) -> list[str]:
        """
        Generate situation overview bullets.

        Must synthesize multiple insights, not restate them.
        2-4 bullets describing the business situation.
        """
        bullets = []
        top_insights = triage_data.get("top_insights", [])

        if not top_insights:
            bullets.append("No high-confidence insights available for analysis")
            return bullets

        # Count insights by category if available
        categories = {}
        for insight in top_insights:
            category = insight.get("category", "General")
            categories[category] = categories.get(category, 0) + 1

        # Synthesize overview
        total_insights = len(top_insights)

        high_conf_count = sum(
            1 for i in top_insights if self._get_confidence_numeric(i) >= 0.7
        )

        bullets.append(
            f"Analysis identified {total_insights} priority insights, "
            f"with {high_conf_count} reaching HIGH or VERY HIGH confidence"
        )

        # Add category distribution if available
        if len(categories) > 1:
            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            cat_str = ", ".join(f"{cat} ({count})" for cat, count in top_categories)
            bullets.append(f"Insights span multiple areas: {cat_str}")

        # Add data context if available
        data_context = triage_data.get("data_context", {})
        if data_context:
            data_points = data_context.get("total_records", 0)
            if data_points > 0:
                bullets.append(
                    f"Analysis based on {data_points:,} records across "
                    f"{data_context.get('columns_analyzed', 0)} dimensions"
                )

        # Add intent context if available
        if intent_text and len(bullets) < 4:
            bullets.append(
                f"Findings align with stated objective: {intent_text[:100]}"
                + ("..." if len(intent_text) > 100 else "")
            )

        return bullets[:4]  # Maximum 4 bullets

    def _format_finding(self, insight: dict[str, Any], confidence_label: str) -> str:
        """
        Format a finding with confidence and decision-enabling flag.

        Each bullet must:
        - map to one triaged insight
        - reference confidence level
        - indicate whether it is decision-enabling or directional
        """
        title = insight.get("title", "Untitled Insight")
        numeric_conf = self._get_confidence_numeric(insight)
        decision_enabling = numeric_conf >= 0.7

        suffix = (
            f" [{confidence_label} confidence, decision-enabling]"
            if decision_enabling
            else f" [{confidence_label} confidence, directional]"
        )

        return f"{title}{suffix}"

    def _generate_implications(self, top_insights: list[dict[str, Any]]) -> list[str]:
        """
        Generate implications from findings.

        Must use implication language (risk, opportunity, constraint, tradeoff).
        "X happened" is NOT allowed here.
        3-6 bullets translating findings into implications.
        """
        implications = []

        for insight in top_insights[:6]:  # Max 6 implications
            title = insight.get("title", "")
            confidence = self._get_confidence_numeric(insight)

            # Generate implication based on confidence level
            if confidence >= 0.8:
                implications.append(
                    f"High-confidence finding on {self._extract_topic(title)} "
                    "creates opportunity for immediate action"
                )
            elif confidence >= 0.7:
                implications.append(
                    f"Reliable evidence on {self._extract_topic(title)} "
                    "enables informed decision-making"
                )
            elif confidence >= 0.5:
                implications.append(
                    f"Moderate-confidence signal on {self._extract_topic(title)} "
                    "suggests further investigation warranted"
                )
            else:
                implications.append(
                    f"Low-confidence observation on {self._extract_topic(title)} "
                    "indicates data quality constraint or complexity"
                )

        # Ensure we have at least 3 implications
        if len(implications) < 3:
            implications.append(
                "Limited high-confidence findings constrain immediate decision support"
            )
            if len(implications) < 3:
                implications.append(
                    "Additional data collection or analysis may reduce uncertainty"
                )

        return implications[:6]  # Maximum 6 bullets

    def _extract_topic(self, title: str) -> str:
        """Extract topic from insight title for implication phrasing."""
        # Simple extraction - take first few meaningful words
        words = title.lower().split()
        # Remove common leading words
        stop_words = {"the", "a", "an", "this", "that", "these", "those"}
        meaningful = [w for w in words if w not in stop_words]
        return " ".join(meaningful[:3]) if meaningful else "analysis"

    def _generate_recommended_actions(
        self, top_insights: list[dict[str, Any]], viz_plan: dict[str, Any]
    ) -> list[str]:
        """
        Generate recommended actions.

        Must be phrased as:
        - decisions to consider
        - analyses to run next
        - actions to evaluate
        NO commitments, NO sales language.
        3-7 bullets.
        """
        actions = []

        # Actions based on confidence levels
        high_conf = [i for i in top_insights if self._get_confidence_numeric(i) >= 0.7]
        medium_conf = [
            i
            for i in top_insights
            if 0.5 <= self._get_confidence_numeric(i) < 0.7
        ]
        low_conf = [i for i in top_insights if self._get_confidence_numeric(i) < 0.5]

        if high_conf:
            actions.append(
                f"Consider prioritizing {len(high_conf)} high-confidence "
                "findings for immediate stakeholder discussion"
            )

        if medium_conf:
            actions.append(
                f"Evaluate feasibility of validating {len(medium_conf)} "
                "medium-confidence insights with additional data"
            )

        if low_conf:
            actions.append(
                f"Review data quality constraints affecting {len(low_conf)} "
                "low-confidence observations"
            )

        # Visualization-based actions
        viz_count = viz_plan.get("visualizations_planned", 0)
        if viz_count > 0:
            actions.append(
                f"Prepare {viz_count} recommended visualizations for "
                "executive presentation or dashboard"
            )

        # General recommendations
        if len(top_insights) > 5:
            actions.append(
                "Consider filtering insights to top 3-5 for executive "
                "communication to maintain focus"
            )

        actions.append(
            "Review caveats section below to ensure claims are not "
            "overstated in external materials"
        )

        # Ensure we have at least 3 actions
        if len(actions) < 3:
            actions.append("Schedule follow-up analysis to deepen understanding")

        return actions[:7]  # Maximum 7 bullets

    def _consolidate_caveats(
        self, triage_data: dict[str, Any], viz_plan: dict[str, Any]
    ) -> list[str]:
        """
        Consolidate caveats from triage and viz plan.

        Pull from:
        - triage caveats
        - narrative caveats
        - visualization caveats

        Must explicitly state what should NOT be overclaimed.
        """
        caveats = []

        # Collect caveats from triage
        for insight in triage_data.get("top_insights", []):
            insight_caveats = insight.get("caveats", [])
            for caveat in insight_caveats:
                if caveat and caveat not in caveats:
                    caveats.append(caveat)

        # Check for low confidence insights
        low_conf_count = sum(
            1
            for i in triage_data.get("top_insights", [])
            if self._get_confidence_numeric(i) < 0.5
        )
        if low_conf_count > 0:
            caveats.append(
                f"{low_conf_count} insights fall below medium confidence threshold "
                "and should not be presented as conclusive"
            )

        # Check for visualization caveats
        for spec in viz_plan.get("specifications", []):
            spec_caveats = spec.get("caveats", [])
            for caveat in spec_caveats:
                if caveat and caveat not in caveats:
                    caveats.append(caveat)

        # Add suppression warning if visualizations suppress categories
        suppressed_categories = set()
        for spec in viz_plan.get("specifications", []):
            if spec.get("visualization_required", False):
                suppressed_categories.update(spec.get("suppress", []))

        if suppressed_categories:
            # Filter out garbage categories
            meaningful_suppressed = [
                cat
                for cat in suppressed_categories
                if cat.upper() not in ["UNASSIGNED", "UNKNOWN", "N/A", "NULL", ""]
            ]
            if meaningful_suppressed:
                caveats.append(
                    f"Visualizations exclude certain categories for clarity: "
                    f"{', '.join(meaningful_suppressed)}"
                )

        # Add data completeness caveat if needed
        data_context = triage_data.get("data_context", {})
        if data_context.get("has_nulls", False):
            caveats.append(
                "Dataset contains null values which may affect completeness of certain insights"
            )

        return caveats
