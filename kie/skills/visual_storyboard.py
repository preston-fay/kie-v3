"""
Visual Storyboard Skill

WHAT THIS SKILL DOES:
Composes multiple judged visuals into a coherent, consultant-grade visual narrative.
This is the creative layer that turns charts into a story.

Charts are not standalone. They exist as PARTS of a story.

INPUTS (read-only, required):
- outputs/insight_triage.json
- outputs/executive_narrative.json (or .md)
- outputs/visualization_plan.json

OUTPUTS (required):
- outputs/visual_storyboard.json
- outputs/visual_storyboard.md

STAGE SCOPE: analyze, build, preview

STRUCTURE (MANDATORY ORDER):
1. Context & Baseline
2. Dominance & Comparison
3. Drivers & Structure
4. Risk, Outliers & Caveats
5. Implications & Actions

VISUAL SELECTION RULES (STRICT):
- Only visuals with visualization_required=true may be used
- Suppressed insights MUST NEVER appear
- No more than 6 total visuals unless explicitly justified
- Visual diversity required: at least 2 different visualization_types if available
- If only bar charts exist, group and sequence them to avoid repetition
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.skills.base import Skill, SkillContext, SkillResult


@dataclass
class StoryboardElement:
    """A single visual element in the storyboard."""

    section: str
    order: int
    insight_id: str
    chart_ref: str
    role: str
    transition_text: str
    emphasis: str
    caveats: list[str]
    visualization_type: str
    insight_title: str


class VisualStoryboardSkill(Skill):
    """
    Visual Storyboard Skill.

    Composes judged visuals into a coherent consultant-grade visual narrative.
    """

    # Mandatory section sequence
    SECTIONS = [
        "Context & Baseline",
        "Dominance & Comparison",
        "Drivers & Structure",
        "Risk, Outliers & Caveats",
        "Implications & Actions",
    ]

    # Garbage categories to filter from suppression lists
    GARBAGE_CATEGORIES = ["unassigned", "unknown", "n/a", "null", "none", "other"]

    def _get_max_visuals(self, context: str) -> int:
        """Get max visuals based on deliverable type."""
        limits = {
            "dashboard": 25,      # Rich, exploratory
            "presentation": 8,    # Focused slides
            "executive": 5,       # Brief exec summary
        }
        return limits.get(context, 8)

    @property
    def skill_id(self) -> str:
        return "visual_storyboard"

    @property
    def description(self) -> str:
        return "Compose judged visuals into coherent visual narrative"

    @property
    def stage_scope(self) -> list[str]:
        return ["analyze", "build", "preview"]

    @property
    def required_artifacts(self) -> list[str]:
        return ["insight_triage", "visualization_plan"]

    @property
    def produces_artifacts(self) -> list[str]:
        return ["visual_storyboard_json", "visual_storyboard_markdown"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute visual storyboard generation.

        Args:
            context: Read-only context with project state and artifacts

        Returns:
            SkillResult with storyboard artifacts, evidence, and status
        """
        warnings = []
        errors = []

        outputs_dir = context.project_root / "outputs"
        internal_dir = outputs_dir / "internal"

        # Load required inputs (from internal/ directory)
        triage_path = internal_dir / "insight_triage.json"
        viz_plan_path = internal_dir / "visualization_plan.json"

        if not viz_plan_path.exists():
            return SkillResult(
                success=False,
                errors=["visualization_plan.json not found - run /analyze first"]
            )

        if not triage_path.exists():
            return SkillResult(
                success=False,
                errors=["insight_triage.json not found - run /analyze first"]
            )

        # Load data
        with open(triage_path) as f:
            triage_data = json.load(f)

        with open(viz_plan_path) as f:
            viz_plan = json.load(f)

        # Load narrative (optional)
        narrative_data = self._load_narrative(outputs_dir)

        # Get build context before generating storyboard
        build_context = context.metadata.get("build_context", "presentation")

        # Generate storyboard
        try:
            storyboard_elements = self._generate_storyboard(
                triage_data, viz_plan, narrative_data, build_context
            )
        except Exception as e:
            return SkillResult(
                success=False,
                errors=[f"Storyboard generation failed: {e}"]
            )

        # NOTE: max_visuals warnings REMOVED per user request - ALL insights should be included

        # Generate outputs to organized directories
        internal_dir = outputs_dir / "internal"
        internal_dir.mkdir(parents=True, exist_ok=True)
        deliverables_dir = outputs_dir / "deliverables"
        deliverables_dir.mkdir(parents=True, exist_ok=True)

        storyboard_json_path = internal_dir / "visual_storyboard.json"
        storyboard_md_path = deliverables_dir / "visual_storyboard.md"

        self._generate_json(storyboard_elements, storyboard_json_path, viz_plan, build_context)
        self._generate_markdown(storyboard_elements, storyboard_md_path, viz_plan, build_context)

        return SkillResult(
            success=True,
            artifacts={
                "visual_storyboard_json": str(storyboard_json_path),
                "visual_storyboard_markdown": str(storyboard_md_path),
            },
            evidence={
                "total_visuals": len(storyboard_elements),
                "sections_used": list({elem.section for elem in storyboard_elements}),
                "visualization_types_used": list(
                    {elem.visualization_type for elem in storyboard_elements}
                ),
            },
            warnings=warnings,
            metadata={
                "artifact_classification": "INTERNAL",
            }
        )

    def _load_narrative(self, outputs_dir: Path) -> dict[str, Any] | None:
        """Load narrative data if available."""
        narrative_json_path = outputs_dir / "executive_narrative.json"
        narrative_md_path = outputs_dir / "executive_narrative.md"

        if narrative_json_path.exists():
            with open(narrative_json_path) as f:
                return json.load(f)
        elif narrative_md_path.exists():
            # If only markdown exists, return minimal structure
            return {"sections": {"executive_summary": narrative_md_path.read_text()}}

        return None

    def _generate_storyboard(
        self,
        triage_data: dict[str, Any],
        viz_plan: dict[str, Any],
        narrative_data: dict[str, Any] | None,
        build_context: str = "presentation"
    ) -> list[StoryboardElement]:
        """Generate storyboard elements from visualization plan."""
        elements = []

        # Filter to only visualization_required=true specs
        viz_specs = [
            spec for spec in viz_plan.get("specifications", [])
            if spec.get("visualization_required", False)
        ]

        if not viz_specs:
            return elements

        # Get suppressed insights to filter out
        suppressed_insights = self._get_suppressed_insights(triage_data)

        # Filter out suppressed insights
        viz_specs = [
            spec for spec in viz_specs
            if spec.get("insight_id") not in suppressed_insights
        ]

        # NOTE: max_visuals limit REMOVED per user request - ALL insights should be included

        # Categorize specs by their purpose
        context_specs = []
        dominance_specs = []
        drivers_specs = []
        risk_specs = []
        implications_specs = []

        for spec in viz_specs:
            # Extract purpose and viz_type from first visual in visuals array
            visuals = spec.get("visuals", [])
            if visuals and isinstance(visuals, list):
                first_visual = visuals[0]
                purpose = first_visual.get("purpose", "").lower()
                viz_type = first_visual.get("visualization_type", "").lower()
            else:
                # Fallback to top-level fields (legacy support)
                purpose = spec.get("purpose", "").lower()
                viz_type = spec.get("visualization_type", "").lower()

            insight_title = spec.get("insight_title", "").lower()

            if "baseline" in purpose or "distribution" in purpose or "aggregate" in purpose:
                context_specs.append(spec)
            elif "leader" in purpose or "comparison" in purpose or "contrast" in purpose or "gap" in purpose:
                dominance_specs.append(spec)
            elif "driver" in purpose or "breakdown" in purpose or "structure" in purpose or "relationship" in purpose:
                drivers_specs.append(spec)
            elif "risk" in purpose or "outlier" in purpose or "caveat" in insight_title or "anomaly" in purpose:
                risk_specs.append(spec)
            elif "implication" in purpose or "action" in purpose or "summary" in purpose:
                implications_specs.append(spec)
            else:
                # Default categorization based on visualization type
                if viz_type in ["bar", "column"]:
                    dominance_specs.append(spec)
                elif viz_type in ["line", "area"]:
                    drivers_specs.append(spec)
                elif viz_type in ["scatter", "bubble"]:
                    risk_specs.append(spec)
                else:
                    context_specs.append(spec)

        # Build storyboard sections
        order = 0

        # Section 1: Context & Baseline (ALL context visuals)
        for spec in context_specs:
            # CRITICAL FIX: Create elements for ALL visuals in spec, not just first one
            visuals = spec.get("visuals", [])
            if visuals and isinstance(visuals, list):
                for visual in visuals:
                    order += 1
                    elements.append(self._create_element_from_visual(
                        section="Context & Baseline",
                        order=order,
                        spec=spec,
                        visual=visual,
                        role="set baseline and scale",
                        is_first=(order == 1)
                    ))
            else:
                # Fallback for old format (single viz at spec level)
                order += 1
                elements.append(self._create_element(
                    section="Context & Baseline",
                    order=order,
                    spec=spec,
                    role="set baseline and scale",
                    is_first=(order == 1)
                ))

        # Section 2: Dominance & Comparison (ALL comparison visuals)
        for spec in dominance_specs:
            # CRITICAL FIX: Create elements for ALL visuals in spec, not just first one
            visuals = spec.get("visuals", [])
            if visuals and isinstance(visuals, list):
                for visual in visuals:
                    order += 1
                    elements.append(self._create_element_from_visual(
                        section="Dominance & Comparison",
                        order=order,
                        spec=spec,
                        visual=visual,
                        role="highlight leaders and gaps",
                        is_first=(order == 1)
                    ))
            else:
                # Fallback for old format (single viz at spec level)
                order += 1
                elements.append(self._create_element(
                    section="Dominance & Comparison",
                    order=order,
                    spec=spec,
                    role="highlight leaders and gaps",
                    is_first=(order == 1)
                ))

        # Section 3: Drivers & Structure (ALL driver visuals)
        for spec in drivers_specs:
            # CRITICAL FIX: Create elements for ALL visuals in spec, not just first one
            visuals = spec.get("visuals", [])
            if visuals and isinstance(visuals, list):
                for visual in visuals:
                    order += 1
                    elements.append(self._create_element_from_visual(
                        section="Drivers & Structure",
                        order=order,
                        spec=spec,
                        visual=visual,
                        role="explain what drives outcomes",
                        is_first=(order == 1)
                    ))
            else:
                # Fallback for old format (single viz at spec level)
                order += 1
                elements.append(self._create_element(
                    section="Drivers & Structure",
                    order=order,
                    spec=spec,
                    role="explain what drives outcomes",
                    is_first=(order == 1)
                ))

        # Section 4: Risk, Outliers & Caveats (ALL risk visuals)
        for spec in risk_specs:
            # CRITICAL FIX: Create elements for ALL visuals in spec, not just first one
            visuals = spec.get("visuals", [])
            if visuals and isinstance(visuals, list):
                for visual in visuals:
                    order += 1
                    elements.append(self._create_element_from_visual(
                        section="Risk, Outliers & Caveats",
                        order=order,
                        spec=spec,
                        visual=visual,
                        role="stress-test the story",
                        is_first=(order == 1)
                    ))
            else:
                # Fallback for old format (single viz at spec level)
                order += 1
                elements.append(self._create_element(
                    section="Risk, Outliers & Caveats",
                    order=order,
                    spec=spec,
                    role="stress-test the story",
                    is_first=(order == 1)
                ))

        # Section 5: Implications & Actions (ALL implication visuals)
        for spec in implications_specs:
            # CRITICAL FIX: Create elements for ALL visuals in spec, not just first one
            visuals = spec.get("visuals", [])
            if visuals and isinstance(visuals, list):
                for visual in visuals:
                    order += 1
                    elements.append(self._create_element_from_visual(
                        section="Implications & Actions",
                        order=order,
                        spec=spec,
                        visual=visual,
                        role="land the story",
                        is_first=(order == 1)
                    ))
            else:
                # Fallback for old format (single viz at spec level)
                order += 1
                elements.append(self._create_element(
                    section="Implications & Actions",
                    order=order,
                    spec=spec,
                    role="land the story",
                    is_first=(order == 1)
                ))

        return elements

    def _get_suppressed_insights(self, triage_data: dict[str, Any]) -> set[str]:
        """Get set of suppressed insight IDs."""
        suppressed = set()
        guidance = triage_data.get("consultant_guidance", {})
        avoid_leading = guidance.get("avoid_leading_with", [])

        # Map titles to insight IDs
        for insight in triage_data.get("top_insights", []):
            if insight.get("title") in avoid_leading:
                suppressed.add(insight.get("id", ""))

        return suppressed

    def _create_element_from_visual(
        self,
        section: str,
        order: int,
        spec: dict[str, Any],
        visual: dict[str, Any],
        role: str,
        is_first: bool
    ) -> StoryboardElement:
        """Create a storyboard element from a specific visual in the visuals array."""
        insight_id = spec.get("insight_id", "unknown")
        viz_type = visual.get("visualization_type", "unknown")
        pattern_role = visual.get("pattern_role", "")

        # Build chart_ref matching actual filename pattern
        if pattern_role:
            chart_ref = f"{insight_id}__{viz_type}__{pattern_role}.json"
        else:
            chart_ref = f"{insight_id}__{viz_type}.json"

        # Generate transition text
        if is_first:
            transition_text = "Starting the visual narrative."
        else:
            transition_text = self._generate_transition(section, order, spec, role)

        # Generate emphasis
        emphasis = self._generate_emphasis(spec)

        # Filter meaningful caveats
        caveats = self._filter_caveats(spec.get("caveats", []))

        return StoryboardElement(
            section=section,
            order=order,
            insight_id=insight_id,
            chart_ref=chart_ref,
            role=role,
            transition_text=transition_text,
            emphasis=emphasis,
            caveats=caveats,
            visualization_type=viz_type,
            insight_title=spec.get("insight_title", "Untitled")
        )

    def _create_element(
        self,
        section: str,
        order: int,
        spec: dict[str, Any],
        role: str,
        is_first: bool
    ) -> StoryboardElement:
        """Create a storyboard element from a visualization spec (legacy fallback)."""
        insight_id = spec.get("insight_id", "unknown")

        # CRITICAL FIX: Handle multi-version charts (spec.visuals array)
        # Pick the first visual from the alternatives array
        visuals = spec.get("visuals", [])
        if visuals and isinstance(visuals, list):
            # Use first visual (primary chart)
            first_visual = visuals[0]
            viz_type = first_visual.get("visualization_type", "unknown")
            pattern_role = first_visual.get("pattern_role", "")

            # Build chart_ref matching actual filename pattern
            if pattern_role:
                chart_ref = f"{insight_id}__{viz_type}__{pattern_role}.json"
            else:
                chart_ref = f"{insight_id}__{viz_type}.json"
        else:
            # Fallback for old format (single viz_type at spec level)
            viz_type = spec.get("visualization_type", "unknown")
            chart_ref = f"{insight_id}__{viz_type}.json"

        # Generate transition text
        if is_first:
            transition_text = "Starting the visual narrative."
        else:
            transition_text = self._generate_transition(section, order, spec, role)

        # Generate emphasis
        emphasis = self._generate_emphasis(spec)

        # Filter meaningful caveats
        caveats = self._filter_caveats(spec.get("caveats", []))

        return StoryboardElement(
            section=section,
            order=order,
            insight_id=insight_id,
            chart_ref=chart_ref,
            role=role,
            transition_text=transition_text,
            emphasis=emphasis,
            caveats=caveats,
            visualization_type=viz_type,
            insight_title=spec.get("insight_title", "Untitled")
        )

    def _generate_transition(
        self,
        section: str,
        order: int,
        spec: dict[str, Any],
        role: str
    ) -> str:
        """Generate transition text between visuals."""
        purpose = spec.get("purpose", "").lower()

        if section == "Context & Baseline":
            return "This establishes the scale and starting point for analysis."
        elif section == "Dominance & Comparison":
            return "This reveals who leads and where gaps exist."
        elif section == "Drivers & Structure":
            return "This explains what drives the patterns we see."
        elif section == "Risk, Outliers & Caveats":
            return "This stress-tests our findings with edge cases and limitations."
        elif section == "Implications & Actions":
            return "This synthesizes implications and next steps."
        else:
            return f"This visual {role}."

    def _generate_emphasis(self, spec: dict[str, Any]) -> str:
        """Generate emphasis guidance for the visual."""
        highlights = spec.get("highlight", [])
        purpose = spec.get("purpose", "")

        if highlights:
            return f"Notice: {', '.join(highlights[:2])}"
        elif purpose:
            return f"Focus on: {purpose}"
        else:
            return "Look for patterns and outliers"

    def _filter_caveats(self, caveats: list[str]) -> list[str]:
        """Filter out garbage categories from caveats."""
        filtered = []
        for caveat in caveats:
            caveat_lower = caveat.lower()
            # Skip if it's just mentioning garbage categories
            if any(garbage in caveat_lower for garbage in self.GARBAGE_CATEGORIES):
                # Only skip if it ONLY mentions garbage categories
                has_meaningful = False
                words = caveat_lower.split()
                for word in words:
                    if word not in self.GARBAGE_CATEGORIES and len(word) > 3:
                        has_meaningful = True
                        break
                if has_meaningful:
                    filtered.append(caveat)
            else:
                filtered.append(caveat)
        return filtered

    def _generate_json(
        self,
        elements: list[StoryboardElement],
        output_path: Path,
        viz_plan: dict[str, Any],
        build_context: str = "presentation"
    ) -> None:
        """Generate JSON storyboard."""
        storyboard_json = {
            "generated_at": datetime.now().isoformat(),
            "total_visuals": len(elements),
            "sections": [],
            "metadata": {
                "artifact_classification": "INTERNAL",
                "skill_id": self.skill_id,
                "visual_limit": self._get_max_visuals(build_context),
                "diversity_required": True,
            }
        }

        # Group elements by section
        sections_dict = {}
        for elem in elements:
            if elem.section not in sections_dict:
                sections_dict[elem.section] = []
            sections_dict[elem.section].append(elem)

        # Build section data
        for section_name in self.SECTIONS:
            if section_name not in sections_dict:
                continue

            section_elements = sections_dict[section_name]
            section_data = {
                "section": section_name,
                "visual_count": len(section_elements),
                "visuals": [
                    {
                        "order": elem.order,
                        "insight_id": elem.insight_id,
                        "insight_title": elem.insight_title,
                        "chart_ref": elem.chart_ref,
                        "visualization_type": elem.visualization_type,
                        "role": elem.role,
                        "transition_text": elem.transition_text,
                        "emphasis": elem.emphasis,
                        "caveats": elem.caveats,
                    }
                    for elem in section_elements
                ]
            }
            storyboard_json["sections"].append(section_data)

        with open(output_path, "w") as f:
            json.dump(storyboard_json, f, indent=2)

    def _generate_markdown(
        self,
        elements: list[StoryboardElement],
        output_path: Path,
        viz_plan: dict[str, Any],
        build_context: str = "presentation"
    ) -> None:
        """Generate markdown storyboard."""
        lines = []

        lines.append("# Visual Storyboard (Internal)\n")
        lines.append("*Consultant-grade visual narrative sequencing*\n")
        lines.append("")
        lines.append(f"**Total Visuals**: {len(elements)}")
        lines.append(f"**Visual Limit**: {self._get_max_visuals(build_context)}")
        lines.append("")

        # Group by section
        sections_dict = {}
        for elem in elements:
            if elem.section not in sections_dict:
                sections_dict[elem.section] = []
            sections_dict[elem.section].append(elem)

        # Write sections
        section_num = 0
        for section_name in self.SECTIONS:
            if section_name not in sections_dict:
                continue

            section_num += 1
            section_elements = sections_dict[section_name]

            lines.append(f"## {section_num}. {section_name}\n")
            lines.append(f"**Visuals**: {len(section_elements)}\n")
            lines.append("")

            for elem in section_elements:
                lines.append(f"### Visual {elem.order}: {elem.insight_title}\n")
                lines.append(f"- **Chart**: `{elem.chart_ref}`")
                lines.append(f"- **Type**: {elem.visualization_type}")
                lines.append(f"- **Role**: {elem.role}")
                lines.append(f"- **Transition**: {elem.transition_text}")
                lines.append(f"- **Emphasis**: {elem.emphasis}")

                if elem.caveats:
                    lines.append(f"- **Caveats**:")
                    for caveat in elem.caveats:
                        lines.append(f"  - {caveat}")

                lines.append("")

        output_path.write_text("\n".join(lines))
