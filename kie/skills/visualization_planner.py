"""
Visualization Planner Skill

Converts judged insights (from insight_triage) into explicit visualization
specifications for consultant-grade charts.

This is the bridge between "what matters" and "how to show it."
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.skills.base import Skill, SkillContext, SkillResult


class VisualizationPlannerSkill(Skill):
    """
    Plans visualizations from ranked insights.

    INPUTS (read-only):
    - outputs/insight_triage.json (required)
    - outputs/executive_narrative.json (optional, for framing)
    - project_state/intent.yaml (optional, for alignment)

    OUTPUTS:
    - outputs/visualization_plan.json (structured specs)
    - outputs/visualization_plan.md (human-readable)

    STAGE SCOPE:
    - analyze
    - build
    - preview
    """

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill."""
        return "visualization_planner"

    @property
    def stage_scope(self) -> list[str]:
        """Stages where this skill should run."""
        return ["analyze", "build", "preview"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute visualization planning from triage.

        Args:
            context: Skill execution context with artifacts

        Returns:
            SkillResult with visualization plan paths and metadata
        """
        outputs_dir = context.project_root / "outputs"
        project_state_dir = context.project_root / "project_state"

        # Load triage data
        triage_json_path = outputs_dir / "insight_triage.json"

        if not triage_json_path.exists():
            # No triage available yet - fail cleanly
            return self._handle_no_triage(outputs_dir)

        with open(triage_json_path) as f:
            triage_data = json.load(f)

        # Load intent if available (for alignment)
        intent_text = self._load_intent(project_state_dir)

        # Load narrative if available (for framing)
        narrative_data = self._load_narrative(outputs_dir)

        # Generate visualization specs from triage
        viz_specs = self._generate_visualization_specs(triage_data)

        # Generate outputs
        viz_plan_json = {
            "generated_at": datetime.now().isoformat(),
            "project_intent": intent_text,
            "total_insights_reviewed": len(triage_data.get("top_insights", [])),
            "visualizations_planned": sum(
                1 for spec in viz_specs if spec["visualization_required"]
            ),
            "specifications": viz_specs,
        }

        viz_plan_md = self._generate_visualization_markdown(
            viz_specs, intent_text, triage_data
        )

        # Save outputs
        viz_plan_json_path = outputs_dir / "visualization_plan.json"
        viz_plan_md_path = outputs_dir / "visualization_plan.md"

        viz_plan_json_path.write_text(json.dumps(viz_plan_json, indent=2))
        viz_plan_md_path.write_text(viz_plan_md)

        return SkillResult(
            success=True,
            artifacts={
                "visualization_plan_json": str(viz_plan_json_path),
                "visualization_plan_md": str(viz_plan_md_path),
            },
            evidence={
                "triage_input": str(triage_json_path),
                "insights_reviewed": len(triage_data.get("top_insights", [])),
                "visualizations_planned": viz_plan_json["visualizations_planned"],
            },
        )

    def _handle_no_triage(self, outputs_dir: Path) -> SkillResult:
        """Handle case where no triage exists yet."""
        viz_plan_md = (
            "# Visualization Plan (Internal)\n\n"
            "**Status:** No insight triage available yet.\n\n"
            "The visualization planner requires ranked insights to generate "
            "visualization specifications. No triage data was found.\n\n"
            "**Next step:** Run `/analyze` to extract and rank insights, then "
            "visualization plans will be automatically generated.\n"
        )

        viz_plan_json = {
            "status": "no_triage_available",
            "message": "No ranked insights available yet. Run /analyze first.",
            "specifications": [],
        }

        viz_plan_md_path = outputs_dir / "visualization_plan.md"
        viz_plan_json_path = outputs_dir / "visualization_plan.json"

        viz_plan_md_path.write_text(viz_plan_md)
        viz_plan_json_path.write_text(json.dumps(viz_plan_json, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "visualization_plan_md": str(viz_plan_md_path),
                "visualization_plan_json": str(viz_plan_json_path),
            },
            evidence={
                "status": "no_triage_available",
            },
        )

    def _load_intent(self, project_state_dir: Path) -> str | None:
        """Load project intent if available."""
        intent_path = project_state_dir / "intent.yaml"
        if not intent_path.exists():
            return None

        import yaml

        try:
            with open(intent_path) as f:
                intent_data = yaml.safe_load(f)
                return intent_data.get("intent_text", intent_data.get("intent"))
        except Exception:
            return None

    def _load_narrative(self, outputs_dir: Path) -> dict[str, Any] | None:
        """Load executive narrative if available."""
        narrative_json_path = outputs_dir / "executive_narrative.json"
        if not narrative_json_path.exists():
            return None

        try:
            with open(narrative_json_path) as f:
                return json.load(f)
        except Exception:
            return None

    def _generate_visualization_specs(
        self, triage_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Generate visualization specifications from triage.

        For each insight where recommendation != "Do not lead with",
        decide if visualization is warranted.
        """
        specs = []
        top_insights = triage_data.get("top_insights", [])
        guidance = triage_data.get("consultant_guidance", {})
        avoid_leading = guidance.get("avoid_leading_with", [])

        for insight in top_insights:
            title = insight.get("title", "Untitled insight")
            confidence_label = insight.get("confidence", "UNKNOWN")
            caveats = insight.get("caveats", [])
            why_matters = insight.get("why_it_matters", "")
            evidence = insight.get("evidence", [])

            # Check if we should deprioritize this insight
            if title in avoid_leading:
                # Skip visualization planning for deprioritized insights
                continue

            # Convert confidence label to numeric
            confidence_numeric = self._confidence_to_numeric(confidence_label)

            # Determine if visualization is required
            viz_required = self._should_visualize(
                confidence_numeric, why_matters, evidence
            )

            if not viz_required:
                # Create spec with visualization_required = false
                spec = {
                    "insight_id": insight.get("id", f"insight_{top_insights.index(insight)}"),
                    "insight_title": title,
                    "visualization_required": False,
                    "visualization_type": "none",
                    "purpose": "none",
                    "reason": self._explain_no_visualization(
                        confidence_numeric, why_matters, evidence
                    ),
                    "confidence": {
                        "numeric": confidence_numeric,
                        "label": confidence_label,
                    },
                    "caveats": caveats,
                }
            else:
                # Create full visualization spec
                spec = self._create_visualization_spec(
                    insight, confidence_numeric, confidence_label, top_insights.index(insight)
                )

            specs.append(spec)

        return specs

    def _confidence_to_numeric(self, confidence_label: str) -> float:
        """Convert confidence label to numeric value."""
        mapping = {
            "HIGH": 0.85,
            "MEDIUM": 0.65,
            "LOW": 0.45,
            "UNKNOWN": 0.50,
        }
        return mapping.get(confidence_label.upper(), 0.50)

    def _should_visualize(
        self, confidence: float, why_matters: str, evidence: list[dict]
    ) -> bool:
        """
        Determine if insight warrants visualization.

        Rules for visualization_required = false:
        - confidence < 0.60 (below medium threshold)
        - insight is purely descriptive with no comparative value
        - no numeric evidence
        """
        # Rule 1: Low confidence
        if confidence < 0.60:
            return False

        # Rule 2: No evidence
        if not evidence:
            return False

        # Rule 3: Purely descriptive (check for comparison/trend keywords)
        comparative_keywords = [
            "higher",
            "lower",
            "increased",
            "decreased",
            "more",
            "less",
            "growth",
            "decline",
            "compared",
            "vs",
            "versus",
            "%",
            "percent",
        ]

        text_to_check = (why_matters or "").lower()
        has_comparative = any(kw in text_to_check for kw in comparative_keywords)

        if not has_comparative:
            return False

        return True

    def _explain_no_visualization(
        self, confidence: float, why_matters: str, evidence: list[dict]
    ) -> str:
        """Explain why visualization is not required."""
        if confidence < 0.60:
            return f"Confidence too low ({confidence:.2f}) for visualization"

        if not evidence:
            return "No numeric evidence to visualize"

        return "Insight is purely descriptive with no comparative value"

    def _create_visualization_spec(
        self,
        insight: dict[str, Any],
        confidence_numeric: float,
        confidence_label: str,
        index: int,
    ) -> dict[str, Any]:
        """
        Create full visualization specification.

        Infers visualization type from insight characteristics.
        """
        title = insight.get("title", "Untitled insight")
        why_matters = insight.get("why_it_matters", "")
        evidence = insight.get("evidence", [])
        caveats = insight.get("caveats", [])

        # Infer visualization type from content
        viz_type, purpose = self._infer_visualization_type(title, why_matters)

        # Extract axes and grouping from content
        axes = self._extract_axes(why_matters, viz_type)

        # Determine highlights from content
        highlights = self._extract_highlights(title, why_matters)

        # Determine suppressions (common low-value categories)
        suppress = ["UNASSIGNED", "Unknown", "N/A", "Other"]

        # Generate annotations (max 2 key callouts)
        annotations = self._generate_annotations(why_matters, caveats)[:2]

        return {
            "insight_id": insight.get("id", f"insight_{index}"),
            "insight_title": title,
            "visualization_required": True,
            "visualization_type": viz_type,
            "purpose": purpose,
            "x_axis": axes.get("x"),
            "y_axis": axes.get("y"),
            "grouping": axes.get("grouping"),
            "highlights": highlights,
            "suppress": suppress,
            "annotations": annotations,
            "caveats": caveats,
            "confidence": {
                "numeric": confidence_numeric,
                "label": confidence_label,
            },
        }

    def _infer_visualization_type(
        self, title: str, why_matters: str
    ) -> tuple[str, str]:
        """
        Infer visualization type and purpose from insight content.

        Returns: (visualization_type, purpose)
        """
        text = (title + " " + why_matters).lower()

        # Map patterns to visualization types
        if any(kw in text for kw in ["trend", "over time", "growth", "decline", "quarter", "year"]):
            return "line", "trend"

        if any(kw in text for kw in ["compare", "vs", "versus", "higher", "lower", "between"]):
            return "bar", "comparison"

        if any(kw in text for kw in ["distribution", "spread", "range", "variance"]):
            return "distribution", "distribution"

        if any(kw in text for kw in ["correlation", "relationship", "associated"]):
            return "scatter", "risk"

        if any(kw in text for kw in ["region", "location", "geographic", "area", "city", "state"]):
            return "map", "concentration"

        if any(kw in text for kw in ["segment", "category", "group", "type"]):
            return "bar", "segmentation"

        # Default to bar chart for comparison
        return "bar", "comparison"

    def _extract_axes(
        self, why_matters: str, viz_type: str
    ) -> dict[str, str | None]:
        """
        Extract axis labels from insight content.

        This is a simple heuristic - real implementation would use NLP.
        """
        axes = {"x": None, "y": None, "grouping": None}

        # Common patterns
        text_lower = why_matters.lower()

        # For bar charts, look for dimension vs metric
        if viz_type == "bar":
            # Try to find metric (revenue, cost, margin, etc.)
            if "revenue" in text_lower:
                axes["y"] = "Revenue"
            elif "cost" in text_lower:
                axes["y"] = "Cost"
            elif "margin" in text_lower:
                axes["y"] = "Margin"
            elif "profit" in text_lower:
                axes["y"] = "Profit"
            else:
                axes["y"] = "Value"

            # Try to find dimension (region, product, segment, etc.)
            if "region" in text_lower:
                axes["x"] = "Region"
            elif "product" in text_lower:
                axes["x"] = "Product"
            elif "segment" in text_lower or "customer" in text_lower:
                axes["x"] = "Segment"
            elif "channel" in text_lower:
                axes["x"] = "Channel"
            else:
                axes["x"] = "Category"

        # For line charts, x is typically time
        elif viz_type == "line":
            axes["x"] = "Time Period"
            if "revenue" in text_lower:
                axes["y"] = "Revenue"
            elif "cost" in text_lower:
                axes["y"] = "Cost"
            else:
                axes["y"] = "Value"

        return axes

    def _extract_highlights(self, title: str, why_matters: str) -> list[str]:
        """
        Extract key values to highlight from insight content.

        This is a simple heuristic - looks for capitalized proper nouns
        or quoted values.
        """
        highlights = []
        text = title + " " + why_matters

        # Look for quoted values
        import re

        quoted = re.findall(r'"([^"]+)"', text)
        highlights.extend(quoted)

        # Look for capitalized multi-word phrases (e.g., "Region B", "Widget C")
        capitalized = re.findall(r'\b[A-Z][a-z]+\s+[A-Z]\b', text)
        highlights.extend(capitalized)

        # Deduplicate
        highlights = list(set(highlights))

        return highlights[:3]  # Max 3 highlights

    def _generate_annotations(
        self, why_matters: str, caveats: list[str]
    ) -> list[str]:
        """
        Generate key callout annotations.

        Max 2 annotations.
        """
        annotations = []

        # Extract percentages as potential callouts
        import re

        percentages = re.findall(r'(\d+%)', why_matters)
        if percentages:
            annotations.append(f"Key metric: {percentages[0]}")

        # Add first caveat if present
        if caveats:
            annotations.append(f"Caveat: {caveats[0]}")

        return annotations[:2]

    def _generate_visualization_markdown(
        self,
        viz_specs: list[dict[str, Any]],
        intent_text: str | None,
        triage_data: dict[str, Any],
    ) -> str:
        """
        Generate human-readable markdown visualization plan.
        """
        lines = []

        # Header
        lines.append("# Visualization Plan (Internal)")
        lines.append("")
        if intent_text:
            lines.append(f"**Project Intent:** {intent_text}")
            lines.append("")

        lines.append(
            f"**Total Insights Reviewed:** {len(triage_data.get('top_insights', []))}"
        )
        lines.append(
            f"**Visualizations Planned:** {sum(1 for spec in viz_specs if spec['visualization_required'])}"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        # For each specification
        for i, spec in enumerate(viz_specs, 1):
            lines.append(f"## Insight {i}: {spec['insight_title']}")
            lines.append("")

            if not spec["visualization_required"]:
                lines.append(f"**Visualization:** Not required")
                lines.append(f"**Reason:** {spec['reason']}")
                lines.append(
                    f"**Confidence:** {spec['confidence']['label']} ({spec['confidence']['numeric']:.2f})"
                )
            else:
                # Full spec
                lines.append(
                    f"**Visualization:** {spec['visualization_type'].title()} chart ({spec['purpose'].title()})"
                )
                lines.append(f"**Purpose:** {self._format_purpose(spec['purpose'])}")

                if spec.get("x_axis") or spec.get("y_axis"):
                    axes_str = ""
                    if spec.get("x_axis"):
                        axes_str += f"{spec['x_axis']}"
                    if spec.get("y_axis"):
                        axes_str += f" → {spec['y_axis']}"
                    lines.append(f"**Axes:** {axes_str}")

                if spec.get("grouping"):
                    lines.append(f"**Grouping:** {spec['grouping']}")

                if spec.get("highlights"):
                    lines.append(f"**Highlight:** {', '.join(spec['highlights'])}")

                if spec.get("suppress"):
                    lines.append(f"**Suppress:** {', '.join(spec['suppress'])}")

                if spec.get("annotations"):
                    lines.append("**Annotations:**")
                    for annotation in spec["annotations"]:
                        lines.append(f"  - {annotation}")

                if spec.get("caveats"):
                    lines.append("**Caveats:**")
                    for caveat in spec["caveats"]:
                        lines.append(f"  - {caveat}")

                lines.append(
                    f"**Confidence:** {spec['confidence']['label']} ({spec['confidence']['numeric']:.2f})"
                )

            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        lines.append("**INTERNAL ONLY** - Visualization specifications for chart engine")
        lines.append("")

        return "\n".join(lines)

    def _format_purpose(self, purpose: str) -> str:
        """Format purpose description."""
        purpose_descriptions = {
            "comparison": "Show relative differences between categories",
            "trend": "Display changes over time",
            "distribution": "Illustrate spread and variance",
            "risk": "Highlight correlation or relationship",
            "concentration": "Show geographic or spatial patterns",
            "segmentation": "Compare across customer or product segments",
        }
        return purpose_descriptions.get(purpose, purpose)
