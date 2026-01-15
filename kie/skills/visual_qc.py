"""
Visual Quality Control Skill

WHAT THIS SKILL DOES:
Evaluates rendered charts for consultant-grade quality and annotates them
with readiness classification and remediation guidance.

This enforces a professional visual quality bar without blocking output.

INPUTS (read-only, required):
- outputs/charts/* (rendered chart artifacts)
- outputs/visualization_plan.json
- outputs/story_manifest.json

OUTPUTS:
- outputs/visual_qc.json
- outputs/visual_qc.md

STAGE SCOPE: build, preview

VISUAL QC CRITERIA:
1) Axis & Label Clarity: Missing labels, ambiguous units, overloaded categories
2) Scale & Perception Risk: Truncated axes, extreme skew, misleading ordering
3) Emphasis Consistency: Highlighted categories, suppressed categories, color semantics
4) Cognitive Load: Too many categories, too many annotations, dense visuals

CLASSIFICATION:
- client_ready: No issues, ready for client presentation
- client_ready_with_caveats: Minor issues, needs annotation or explanation
- internal_only: Major issues, needs rework or is exploratory only

RULES:
- NO blocking: All charts pass through with classification
- NO hiding: All visuals remain in output
- Deterministic: Same chart always gets same classification
- Actionable: Every issue includes remediation guidance
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.skills.base import Skill, SkillContext, SkillResult


class VisualQCSkill(Skill):
    """
    Visual Quality Control Skill.

    Evaluates rendered charts for consultant-grade quality.
    """

    # Quality thresholds
    MAX_CATEGORIES_CLIENT_READY = 10
    MAX_CATEGORIES_WITH_CAVEATS = 15
    MAX_ANNOTATIONS_CLIENT_READY = 5

    @property
    def skill_id(self) -> str:
        return "visual_qc"

    @property
    def description(self) -> str:
        return "Evaluate charts for consultant-grade visual quality"

    @property
    def stage_scope(self) -> list[str]:
        return ["build", "preview"]

    @property
    def required_artifacts(self) -> list[str]:
        return ["visualization_plan"]

    @property
    def produces_artifacts(self) -> list[str]:
        return ["visual_qc_json", "visual_qc_markdown"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute visual quality control.

        Args:
            context: Read-only context with project state and artifacts

        Returns:
            SkillResult with QC artifacts and status
        """
        warnings = []
        errors = []

        outputs_dir = context.project_root / "outputs"
        charts_dir = outputs_dir / "charts"

        # Validate required inputs
        (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
        viz_plan_path = outputs_dir / "internal" / "visualization_plan.json"
        manifest_path = outputs_dir / "internal" / "story_manifest.json"

        if not viz_plan_path.exists():
            errors.append("visualization_plan.json not found")
            return SkillResult(
                success=False,
                artifacts={},
                evidence=[],
                warnings=warnings,
                errors=errors,
            )

        # story_manifest is optional - used for actionability lookup if available
        manifest_data = {}
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest_data = json.load(f)
        else:
            warnings.append(
                "story_manifest.json not found - proceeding without actionability context"
            )

        # Check charts directory exists
        if not charts_dir.exists():
            warnings.append("No charts directory found, creating empty QC report")
            charts_dir.mkdir(parents=True, exist_ok=True)

        # Load inputs
        with open(viz_plan_path) as f:
            viz_plan = json.load(f)

        # Build actionability lookup from manifest (if available)
        actionability_lookup = self._build_actionability_lookup(manifest_data)

        # Evaluate all charts
        chart_evaluations = []
        chart_files = list(charts_dir.glob("*.json"))

        for chart_file in chart_files:
            evaluation = self._evaluate_chart(
                chart_file, actionability_lookup.get(chart_file.name, "informational")
            )
            chart_evaluations.append(evaluation)

        # Calculate summary
        summary = {
            "client_ready": sum(
                1 for e in chart_evaluations if e["visual_quality"] == "client_ready"
            ),
            "with_caveats": sum(
                1
                for e in chart_evaluations
                if e["visual_quality"] == "client_ready_with_caveats"
            ),
            "internal_only": sum(
                1 for e in chart_evaluations if e["visual_quality"] == "internal_only"
            ),
        }

        # Build output
        output = {"charts": chart_evaluations, "summary": summary}

        # Save JSON
        qc_json_path = outputs_dir / "internal" / "visual_qc.json"
        with open(qc_json_path, "w") as f:
            json.dump(output, f, indent=2)

        # Save Markdown
        qc_md_path = outputs_dir / "internal" / "visual_qc.md"
        markdown = self._generate_markdown(output)
        qc_md_path.write_text(markdown)

        evidence = [
            f"Evaluated {len(chart_evaluations)} charts",
            f"Client-ready: {summary['client_ready']}",
            f"With caveats: {summary['with_caveats']}",
            f"Internal-only: {summary['internal_only']}",
        ]

        return SkillResult(
            success=True,
            artifacts={
                "visual_qc_json": qc_json_path,
                "visual_qc_markdown": qc_md_path,
            },
            evidence=evidence,
            warnings=warnings,
            errors=errors,
        )

    def _build_actionability_lookup(self, manifest: dict[str, Any]) -> dict[str, str]:
        """Build lookup from chart_ref to actionability level."""
        lookup = {}
        for section in manifest.get("sections", []):
            for visual in section.get("visuals", []):
                chart_ref = visual.get("chart_ref", "")
                # Get actionability from evidence_index if available
                evidence = section.get("evidence_index", [])
                if evidence:
                    # Use first evidence actionability as proxy
                    actionability = evidence[0].get("actionability", "informational")
                else:
                    # Fall back to section-level actionability
                    actionability = section.get("actionability_level", "informational")
                if chart_ref:
                    lookup[chart_ref] = actionability
        return lookup

    def _evaluate_chart(
        self, chart_path: Path, actionability: str
    ) -> dict[str, Any]:
        """
        Evaluate a single chart for visual quality.

        Args:
            chart_path: Path to chart JSON file
            actionability: Actionability level of associated insight

        Returns:
            Evaluation dict with classification and issues
        """
        chart_ref = chart_path.name
        issues = []
        recommended_actions = []

        # Load chart data
        try:
            with open(chart_path) as f:
                chart_data = json.load(f)
        except Exception as e:
            return {
                "chart_ref": chart_ref,
                "actionability": actionability,
                "visual_quality": "internal_only",
                "issues": [f"Failed to load chart: {e}"],
                "recommended_action": "Fix chart rendering",
            }

        data = chart_data.get("data", [])
        config = chart_data.get("config", {})
        chart_type = chart_data.get("type", "unknown")

        # 1) AXIS & LABEL CLARITY
        # Check for missing axis labels
        x_axis = config.get("xAxis", {})
        y_axis = config.get("yAxis", {})

        if not x_axis.get("label") and chart_type in ["bar", "line", "area"]:
            issues.append("Missing X-axis label")
            recommended_actions.append("Add descriptive X-axis label")

        if not y_axis.get("label") and chart_type in ["bar", "line", "area"]:
            issues.append("Missing Y-axis label")
            recommended_actions.append("Add descriptive Y-axis label with units")

        # Check for overloaded categories
        num_categories = len(data)
        if num_categories > self.MAX_CATEGORIES_WITH_CAVEATS:
            issues.append(f"Too many categories ({num_categories})")
            recommended_actions.append(
                "Group bottom categories into 'Other' or create separate chart"
            )
        elif num_categories > self.MAX_CATEGORIES_CLIENT_READY:
            issues.append(f"Many categories ({num_categories})")
            recommended_actions.append(
                "Consider grouping or filtering to top categories"
            )

        # 2) SCALE & PERCEPTION RISK
        # Check for potential truncated axes (heuristic: min value much larger than 0)
        if chart_type in ["bar", "line", "area"] and data:
            # Extract numeric values
            numeric_values = []
            for item in data:
                for key, value in item.items():
                    if isinstance(value, (int, float)) and key not in [
                        "x",
                        "name",
                        "category",
                    ]:
                        numeric_values.append(value)

            if numeric_values:
                min_val = min(numeric_values)
                max_val = max(numeric_values)
                range_val = max_val - min_val

                # If min is > 50% of max, axis might be truncated
                if min_val > 0 and min_val > max_val * 0.5 and range_val > 0:
                    issues.append("Potentially truncated Y-axis")
                    recommended_actions.append(
                        "Add annotation explaining scale or start from zero"
                    )

                # Check for extreme skew (one value >> others)
                if numeric_values:
                    avg_val = sum(numeric_values) / len(numeric_values)
                    if max_val > avg_val * 10:
                        issues.append("Extreme value skew detected")
                        recommended_actions.append(
                            "Consider log scale or separate chart for outlier"
                        )

        # 3) EMPHASIS CONSISTENCY
        # Check if highlighted categories are actually present
        bars = config.get("bars", [])
        lines = config.get("lines", [])
        areas = config.get("areas", [])

        all_series = bars + lines + areas
        for series in all_series:
            if series.get("highlight") or series.get("emphasize"):
                # Verify data exists for highlighted series
                data_key = series.get("dataKey", "")
                if data and data_key:
                    has_data = any(data_key in item for item in data)
                    if not has_data:
                        issues.append(
                            f"Highlighted series '{data_key}' has no data"
                        )
                        recommended_actions.append(
                            "Remove highlight or verify data source"
                        )

        # 4) COGNITIVE LOAD
        # Count annotations (tooltips, labels, etc.)
        annotation_count = 0
        if config.get("showDataLabels"):
            annotation_count += num_categories
        if config.get("annotations"):
            annotation_count += len(config["annotations"])

        if annotation_count > self.MAX_ANNOTATIONS_CLIENT_READY:
            issues.append(f"Too many annotations ({annotation_count})")
            recommended_actions.append("Reduce annotations or use hover tooltips only")

        # CLASSIFY
        if not issues:
            visual_quality = "client_ready"
            recommended_action = "No changes needed"
        elif len(issues) <= 2 and num_categories <= self.MAX_CATEGORIES_WITH_CAVEATS:
            visual_quality = "client_ready_with_caveats"
            recommended_action = " | ".join(recommended_actions[:2])
        else:
            visual_quality = "internal_only"
            recommended_action = " | ".join(recommended_actions[:3])

        return {
            "chart_ref": chart_ref,
            "actionability": actionability,
            "visual_quality": visual_quality,
            "issues": issues,
            "recommended_action": recommended_action,
        }

    def _generate_markdown(self, output: dict[str, Any]) -> str:
        """Generate markdown report of visual QC results."""
        lines = [
            "# Visual Quality Control Report",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Client-Ready**: {output['summary']['client_ready']} charts",
            f"- **With Caveats**: {output['summary']['with_caveats']} charts",
            f"- **Internal-Only**: {output['summary']['internal_only']} charts",
            "",
            "---",
            "",
        ]

        # Group by visual quality
        by_quality = {
            "client_ready": [],
            "client_ready_with_caveats": [],
            "internal_only": [],
        }

        for chart in output["charts"]:
            quality = chart["visual_quality"]
            by_quality[quality].append(chart)

        # Client-ready charts
        if by_quality["client_ready"]:
            lines.append("## Client-Ready Charts")
            lines.append("")
            lines.append("These charts are ready for client presentation without modification.")
            lines.append("")
            for chart in by_quality["client_ready"]:
                lines.append(f"### {chart['chart_ref']}")
                lines.append("")
                lines.append(f"**Actionability**: {chart['actionability']}")
                lines.append(f"**Status**: ✅ Client-Ready")
                lines.append("")

        # Charts with caveats
        if by_quality["client_ready_with_caveats"]:
            lines.append("## Charts with Caveats")
            lines.append("")
            lines.append(
                "These charts are acceptable but have minor issues. Add annotations or explanations."
            )
            lines.append("")
            for chart in by_quality["client_ready_with_caveats"]:
                lines.append(f"### {chart['chart_ref']}")
                lines.append("")
                lines.append(f"**Actionability**: {chart['actionability']}")
                lines.append(f"**Status**: ⚠️  With Caveats")
                lines.append("")
                if chart.get("issues"):
                    lines.append("**Issues:**")
                    for issue in chart["issues"]:
                        lines.append(f"- {issue}")
                    lines.append("")
                lines.append(f"**Recommended Action**: {chart['recommended_action']}")
                lines.append("")

        # Internal-only charts
        if by_quality["internal_only"]:
            lines.append("## Internal-Only Charts")
            lines.append("")
            lines.append(
                "These charts have significant issues and should be reworked or marked as exploratory."
            )
            lines.append("")
            for chart in by_quality["internal_only"]:
                lines.append(f"### {chart['chart_ref']}")
                lines.append("")
                lines.append(f"**Actionability**: {chart['actionability']}")
                lines.append(f"**Status**: 🔴 Internal-Only")
                lines.append("")
                if chart.get("issues"):
                    lines.append("**Issues:**")
                    for issue in chart["issues"]:
                        lines.append(f"- {issue}")
                    lines.append("")
                lines.append(f"**Recommended Action**: {chart['recommended_action']}")
                lines.append("")

        return "\\n".join(lines)
