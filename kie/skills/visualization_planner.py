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

from kie.insights.schema import InsightType
from kie.skills.base import Skill, SkillContext, SkillResult
from kie.charts.formatting import format_number


# Chart Excellence Plan: InsightType → ChartType Multi-Version Mapping
# Each InsightType returns LIST of (chart_type, purpose, version_id) tuples
# version_id: "primary" (default), "alt1", "alt2"
# Auto-detection logic filters alternatives based on data characteristics
INSIGHT_TYPE_TO_CHART_TYPE = {
    # Core insight types (8 existing) - now with alternatives
    InsightType.COMPARISON: [
        ("bar", "comparison", "primary"),           # Default
        ("horizontal_bar", "comparison", "alt1"),   # If >8 categories or long labels
    ],
    InsightType.TREND: [
        ("line", "trend", "primary"),               # Default
        ("area", "trend", "alt1"),                  # Emphasis on magnitude
    ],
    InsightType.DISTRIBUTION: [
        ("bar", "distribution", "primary"),         # Histogram-style bar chart
    ],
    InsightType.CORRELATION: [
        ("scatter", "risk", "primary"),             # Default
    ],
    InsightType.CONCENTRATION: [
        ("bar", "concentration", "primary"),        # Default
        ("pie", "concentration", "alt1"),           # If 2-4 categories only (KDS max 4 slices)
    ],
    InsightType.OUTLIER: [
        ("bar", "comparison", "primary"),           # With highlighting
    ],
    InsightType.VARIANCE: [
        ("bar", "distribution", "primary"),         # Histogram-style bar chart
    ],
    InsightType.BENCHMARK: [
        ("bar", "comparison", "primary"),           # Default
    ],

    # Sophisticated chart types (4 new)
    InsightType.COMPOSITION: [
        ("stacked_bar", "composition", "primary"),  # Primary: Part-to-whole stacked
        ("bar", "comparison", "alt1"),              # Alternative: Ungrouped comparison
        ("pie", "composition", "alt2"),             # Alternative: If ≤4 categories
    ],
    InsightType.DUAL_METRIC: [
        ("combo", "dual_metric", "primary"),        # Primary: Bar + line combo
        ("bar", "comparison", "alt1"),              # Alternative: Primary metric only
    ],
    InsightType.CONTRIBUTION: [
        ("waterfall", "contribution", "primary"),   # Primary: KDS-compliant waterfall
        ("stacked_bar", "composition", "alt1"),     # Alternative: Composition view
    ],
    InsightType.DRIVER: [
        ("scatter", "risk", "primary"),             # Primary: Correlation view
        ("bar", "comparison", "alt1"),              # Alternative: Magnitude view
    ],
}


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
        triage_json_path = outputs_dir / "internal" / "insight_triage.json"

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
        internal_dir = outputs_dir / "internal"
        internal_dir.mkdir(parents=True, exist_ok=True)

        viz_plan_json_path = internal_dir / "visualization_plan.json"
        viz_plan_md_path = internal_dir / "visualization_plan.md"

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

        internal_dir = outputs_dir / "internal"
        internal_dir.mkdir(parents=True, exist_ok=True)

        viz_plan_md_path = internal_dir / "visualization_plan.md"
        viz_plan_json_path = internal_dir / "visualization_plan.json"

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
            "share",
            "lead",
            "top",
            "dominat",
            "driver",
            "impact",
            "affect",
            "influence",
            "relationship",
            "correlat",
            "concentration",
            "concentrat",
            "distribution",
            "across",
            "across",
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
            return f"Confidence too low ({format_number(confidence, precision=2, abbreviate=False)}) for visualization"

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
        May return multiple visualizations per insight based on pattern rules.
        """
        title = insight.get("title", "Untitled insight")
        why_matters = insight.get("why_it_matters", "")
        evidence = insight.get("evidence", [])
        caveats = insight.get("caveats", [])

        # Chart Excellence Plan: Get all versions (primary + alternatives)
        versions = self._infer_visualization_type(insight, title, why_matters)

        # Use primary version for pattern library and axes extraction
        viz_type, purpose, version_id = versions[0]

        # Extract axes and grouping from content
        axes = self._extract_axes(why_matters, viz_type)

        # Determine highlights from content
        highlights = self._extract_highlights(title, why_matters)

        # Determine suppressions (common low-value categories)
        suppress = ["UNASSIGNED", "Unknown", "N/A", "Other"]

        # Generate annotations (max 2 key callouts)
        annotations = self._generate_annotations(why_matters, caveats)[:2]

        # VISUAL PATTERN LIBRARY: Check if multi-visual patterns apply
        pattern_visuals = self._apply_visual_patterns(
            purpose, viz_type, title, why_matters, axes, highlights, suppress, annotations, caveats
        )

        # If pattern returned multiple visuals, use them; otherwise generate version alternatives
        if len(pattern_visuals) > 1:
            # Multi-visual pattern (Visual Pattern Library)
            base_spec = {
                "insight_id": insight.get("id", f"insight_{index}"),
                "insight_title": title,
                "visualization_required": True,
                "confidence": {
                    "numeric": confidence_numeric,
                    "label": confidence_label,
                },
                "visuals": pattern_visuals,  # Multiple visualizations
            }
            return base_spec
        else:
            # Chart Excellence Plan: Generate specs for all versions
            if len(versions) > 1:
                # Multiple versions available - generate spec for each
                version_specs = []
                for viz_type_v, purpose_v, version_id_v in versions:
                    version_specs.append({
                        "visualization_type": viz_type_v,
                        "purpose": purpose_v,
                        "version_id": version_id_v,
                        "is_primary": version_id_v == "primary",
                        "x_axis": axes.get("x"),
                        "y_axis": axes.get("y"),
                        "grouping": axes.get("grouping"),
                        "highlights": highlights,
                        "suppress": suppress,
                        "annotations": annotations,
                        "caveats": caveats,
                    })

                return {
                    "insight_id": insight.get("id", f"insight_{index}"),
                    "insight_title": title,
                    "visualization_required": True,
                    "confidence": {
                        "numeric": confidence_numeric,
                        "label": confidence_label,
                    },
                    "chart_versions": version_specs,  # Multiple chart versions
                }
            else:
                # Single version only (backward compatibility)
                return {
                    "insight_id": insight.get("id", f"insight_{index}"),
                    "insight_title": title,
                    "visualization_required": True,
                    "visualization_type": viz_type,
                    "purpose": purpose,
                    "version_id": version_id,
                    "is_primary": True,
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

    def _apply_visual_patterns(
        self,
        purpose: str,
        viz_type: str,
        title: str,
        why_matters: str,
        axes: dict[str, str | None],
        highlights: list[str],
        suppress: list[str],
        annotations: list[str],
        caveats: list[str],
    ) -> list[dict[str, Any]]:
        """
        Apply Visual Pattern Library rules to generate multiple visualizations.

        DETERMINISTIC PATTERNS:
        1. comparison + many categories (>5 implied) → bar + pareto
        2. distribution → histogram + distribution_summary
        3. drivers/relationship + numeric fields → scatter + trend_summary

        Returns:
            List of visualization specs (single item = no pattern, multiple = pattern applied)
        """
        text = (title + " " + why_matters).lower()

        # PATTERN 1: Comparison with many categories
        # Trigger when ANY:
        # - purpose is comparison OR concentration
        # - share/dominance language (share, lead, top, dominates)
        # - plural entity keywords (regions, products, segments, etc.)
        share_language = any(kw in text for kw in ["share", "lead", "top", "dominat"])
        entity_keywords = any(kw in text for kw in ["regions", "products", "segments", "categories", "channels", "customers"])

        if (purpose in ["comparison", "concentration"]) or share_language or entity_keywords:
            # Emit 2 visuals: bar (top N) + pareto (cumulative)
            return [
                {
                    "visualization_type": "bar",
                    "purpose": "comparison",
                    "x_axis": axes.get("x"),
                    "y_axis": axes.get("y"),
                    "grouping": axes.get("grouping"),
                    "highlights": highlights,
                    "suppress": suppress,
                    "annotations": annotations,
                    "caveats": caveats,
                    "pattern_role": "top_n",
                    "description": "Top contributors",
                },
                {
                    "visualization_type": "pareto",
                    "purpose": "concentration",
                    "x_axis": axes.get("x"),
                    "y_axis": axes.get("y"),
                    "grouping": None,
                    "highlights": [],
                    "suppress": suppress,
                    "annotations": ["Cumulative share analysis"],
                    "caveats": caveats,
                    "pattern_role": "cumulative",
                    "description": "Cumulative concentration",
                },
            ]

        # PATTERN 2: Distribution
        # Detect: "distribution", "spread", "range", "variance"
        if purpose == "distribution" or viz_type == "distribution":
            return [
                {
                    "visualization_type": "histogram",
                    "purpose": "distribution",
                    "x_axis": "Value Range",
                    "y_axis": "Frequency",
                    "grouping": None,
                    "highlights": [],
                    "suppress": suppress,
                    "annotations": annotations,
                    "caveats": caveats,
                    "pattern_role": "histogram",
                    "description": "Value distribution",
                },
                {
                    "visualization_type": "distribution_summary",
                    "purpose": "distribution",
                    "x_axis": axes.get("x"),
                    "y_axis": axes.get("y"),
                    "grouping": None,
                    "highlights": [],
                    "suppress": suppress,
                    "annotations": ["Min, Median, Max, IQR"],
                    "caveats": caveats,
                    "pattern_role": "summary",
                    "description": "Statistical summary",
                },
            ]

        # PATTERN 3: Drivers/Relationship
        # Trigger when ANY:
        # - purpose is risk, drivers, or relationship
        # - driver/impact/relationship keywords
        driver_keywords = any(kw in text for kw in ["driver", "impact", "affect", "influence", "relationship", "correlat"])

        if (purpose in ["risk", "drivers", "relationship"]) or driver_keywords:
            return [
                {
                    "visualization_type": "scatter",
                    "purpose": "risk",
                    "x_axis": axes.get("x"),
                    "y_axis": axes.get("y"),
                    "grouping": axes.get("grouping"),
                    "highlights": highlights,
                    "suppress": suppress,
                    "annotations": annotations,
                    "caveats": caveats,
                    "pattern_role": "scatter",
                    "description": "Relationship analysis",
                },
                {
                    "visualization_type": "trend_summary",
                    "purpose": "risk",
                    "x_axis": axes.get("x"),
                    "y_axis": axes.get("y"),
                    "grouping": None,
                    "highlights": [],
                    "suppress": suppress,
                    "annotations": ["Trend direction and strength"],
                    "caveats": caveats,
                    "pattern_role": "trend",
                    "description": "Trend analysis",
                },
            ]

        # NO PATTERN: Return single visual
        return [
            {
                "visualization_type": viz_type,
                "purpose": purpose,
                "x_axis": axes.get("x"),
                "y_axis": axes.get("y"),
                "grouping": axes.get("grouping"),
                "highlights": highlights,
                "suppress": suppress,
                "annotations": annotations,
                "caveats": caveats,
            }
        ]

    def _infer_visualization_type(
        self, insight: dict, title: str, why_matters: str
    ) -> list[tuple[str, str, str]]:
        """
        Infer visualization type(s) from insight content.

        Chart Excellence Plan: Returns LIST of (chart_type, purpose, version_id) tuples.
        Primary version is always first. Auto-detection logic filters alternatives.

        Args:
            insight: Full insight dictionary (may contain insight_type)
            title: Insight title (fallback)
            why_matters: Insight why_it_matters (fallback)

        Returns: List of (visualization_type, purpose, version_id)
        """
        # Step 1: Try InsightType mapping (primary method)
        insight_type_str = insight.get("insight_type")
        if insight_type_str:
            try:
                insight_type = InsightType(insight_type_str)
                if insight_type in INSIGHT_TYPE_TO_CHART_TYPE:
                    alternatives = INSIGHT_TYPE_TO_CHART_TYPE[insight_type]

                    # Analyze data shape for filtering
                    evidence = insight.get("evidence", [])
                    data_shape = self._analyze_data_shape(insight, evidence)

                    # Filter alternatives based on data characteristics
                    return self._filter_alternatives(alternatives, insight, data_shape)
            except (ValueError, KeyError):
                pass  # Fall back to keyword matching

        # Step 2: Keyword matching (fallback) - returns PRIMARY only
        text = (title + " " + why_matters).lower()

        if any(kw in text for kw in ["trend", "over time", "growth", "decline", "quarter", "year"]):
            return [("line", "trend", "primary")]

        if any(kw in text for kw in ["compare", "vs", "versus", "higher", "lower", "between", "share", "lead", "top", "dominat"]):
            return [("bar", "comparison", "primary")]

        if any(kw in text for kw in ["distribution", "spread", "range", "variance"]):
            return [("bar", "distribution", "primary")]

        if any(kw in text for kw in ["correlation", "relationship", "associated", "driver", "impact", "affect", "influence"]):
            return [("scatter", "risk", "primary")]

        if any(kw in text for kw in ["region", "location", "geographic", "area", "city", "state"]):
            return [("map", "concentration", "primary")]

        if any(kw in text for kw in ["concentration", "concentrat"]):
            return [("bar", "concentration", "primary")]

        if any(kw in text for kw in ["segment", "category", "group", "type"]):
            return [("bar", "segmentation", "primary")]

        # Default to bar chart for comparison
        return [("bar", "comparison", "primary")]

    def _analyze_data_shape(self, insight: dict, evidence: list) -> dict:
        """
        Analyze data characteristics to inform chart selection.

        Args:
            insight: Full insight dictionary
            evidence: List of evidence items

        Returns:
            {
                "num_categories": int,
                "max_label_length": int,
                "has_grouping": bool,
                "num_groups": int,
                "has_dual_metrics": bool,
                "is_sequential_change": bool,
            }
        """
        # Extract from evidence
        num_categories = len([e for e in evidence if e.get("evidence_type") == "data_point"])

        # Check label lengths
        labels = [e.get("label", "") for e in evidence]
        max_label_length = max(len(str(label)) for label in labels) if labels else 0

        # Detect grouping (e.g., "Region: North | Product: Widget")
        has_grouping = any("|" in str(e.get("label", "")) for e in evidence)

        # ISSUE #6 FIX: Parse num_groups from evidence labels
        # Count unique grouping dimensions from labels with "|" separator
        num_groups = 0
        if has_grouping:
            # Extract grouping dimensions (before ":" in each segment)
            grouping_dims = set()
            for e in evidence:
                label = str(e.get("label", ""))
                if "|" in label:
                    # Parse "Region: North | Product: Widget" → ["Region", "Product"]
                    segments = label.split("|")
                    for segment in segments:
                        if ":" in segment:
                            dim = segment.split(":")[0].strip()
                            grouping_dims.add(dim)
            num_groups = len(grouping_dims)

        # Detect dual metrics (two different scales)
        metric_values = [e.get("value") for e in evidence if e.get("evidence_type") == "metric" and isinstance(e.get("value"), (int, float))]
        has_dual_metrics = False
        if len(metric_values) >= 2:
            # Heuristic: One large (>1000), one small (<10) = different scales
            max_val = max(metric_values)
            min_val = min(metric_values)
            has_dual_metrics = (max_val > 1000 and min_val < 10)

        # Detect sequential change pattern (waterfall triggers)
        title_lower = insight.get("title", "").lower()
        why_matters_lower = insight.get("why_it_matters", "").lower()
        combined_text = title_lower + " " + why_matters_lower
        is_sequential_change = any(kw in combined_text for kw in [
            "budget vs actual", "variance", "bridge", "contribution",
            "starting", "ending", "what explains", "waterfall"
        ])

        return {
            "num_categories": num_categories,
            "max_label_length": max_label_length,
            "has_grouping": has_grouping,
            "num_groups": 0,  # TODO: Parse from evidence
            "has_dual_metrics": has_dual_metrics,
            "is_sequential_change": is_sequential_change,
        }

    def _filter_alternatives(
        self,
        alternatives: list[tuple[str, str, str]],
        insight: dict,
        data_shape: dict
    ) -> list[tuple[str, str, str]]:
        """
        Filter alternative chart types based on data characteristics.

        Args:
            alternatives: List of (chart_type, purpose, version_id)
            insight: Full insight dictionary
            data_shape: {"num_categories": int, "max_label_length": int, ...}

        Returns:
            Filtered list of alternatives that make sense for this data
        """
        filtered = []

        for chart_type, purpose, version_id in alternatives:
            # Rule 1: Pie charts only if 2-4 categories (KDS max 4 slices)
            if chart_type in ["pie", "donut"]:
                if 2 <= data_shape.get("num_categories", 0) <= 4:
                    filtered.append((chart_type, purpose, version_id))
                # Skip pie if outside valid range
                continue

            # Rule 2: Horizontal bar if long labels (>15 chars) or many categories (>8)
            if chart_type == "horizontal_bar":
                if (data_shape.get("max_label_length", 0) > 15 or
                    data_shape.get("num_categories", 0) > 8):
                    filtered.append((chart_type, purpose, version_id))
                # Skip horizontal if not needed
                continue

            # Rule 3: Stacked bar only if grouping detected AND ≤4 groups
            if chart_type == "stacked_bar":
                if (data_shape.get("has_grouping", False) and
                    data_shape.get("num_groups", 0) <= 4):
                    filtered.append((chart_type, purpose, version_id))
                # Skip stacked if no grouping or too many groups
                continue

            # Rule 4: Combo chart only if dual metrics detected
            if chart_type == "combo":
                if data_shape.get("has_dual_metrics", False):
                    filtered.append((chart_type, purpose, version_id))
                # Skip combo if not dual metrics
                continue

            # Rule 5: Waterfall only if sequential change pattern detected
            if chart_type == "waterfall":
                if data_shape.get("is_sequential_change", False):
                    filtered.append((chart_type, purpose, version_id))
                continue

            # Default: Include all other chart types
            filtered.append((chart_type, purpose, version_id))

        # Always return at least the primary version
        if not filtered and alternatives:
            filtered = [alternatives[0]]

        return filtered

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
                    f"**Confidence:** {spec['confidence']['label']} ({format_number(spec['confidence']['numeric'], precision=2, abbreviate=False)})"
                )
            elif "visuals" in spec:
                # Multi-visual pattern
                lines.append(f"**Pattern:** Multi-visual ({len(spec['visuals'])} visualizations)")
                lines.append("")
                for j, visual in enumerate(spec["visuals"], 1):
                    lines.append(f"### Visual {j}: {visual.get('description', 'Visualization')}")
                    lines.append(f"**Type:** {visual['visualization_type'].title()} ({visual['purpose'].title()})")
                    if visual.get("pattern_role"):
                        lines.append(f"**Role:** {visual['pattern_role']}")

                    if visual.get("x_axis") or visual.get("y_axis"):
                        axes_str = ""
                        if visual.get("x_axis"):
                            axes_str += f"{visual['x_axis']}"
                        if visual.get("y_axis"):
                            axes_str += f" → {visual['y_axis']}"
                        lines.append(f"**Axes:** {axes_str}")

                    if visual.get("annotations"):
                        lines.append("**Annotations:**")
                        for annotation in visual["annotations"]:
                            lines.append(f"  - {annotation}")
                    lines.append("")

                lines.append(
                    f"**Confidence:** {spec['confidence']['label']} ({format_number(spec['confidence']['numeric'], precision=2, abbreviate=False)})"
                )
            else:
                # Single visualization (original behavior)
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
                    f"**Confidence:** {spec['confidence']['label']} ({format_number(spec['confidence']['numeric'], precision=2, abbreviate=False)})"
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
