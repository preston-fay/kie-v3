"""
Story Manifest Skill

WHAT THIS SKILL DOES:
Creates the ONE canonical story representation that both PPT and Dashboard render from.
This enforces alignment across all output formats.

INPUTS (read-only, required):
- outputs/insight_triage.json
- outputs/executive_summary.md (or .json)
- outputs/visual_storyboard.json
- outputs/visualization_plan.json
- outputs/charts/* (rendered chart artifacts)
- project_state/intent.yaml

OUTPUTS (canonical artifacts):
- outputs/story_manifest.json
- outputs/story_manifest.md

STAGE SCOPE: build, preview

CONTRACT (NON-NEGOTIABLE):
The manifest represents THE story with all elements needed by renderers.

Required fields:
- story_id: unique identifier
- project_name: from spec
- objective: from intent
- generated_at: timestamp
- execution_mode: rails/notebook
- sections: ordered list of story sections

Each section:
- section_id: unique identifier
- title: section name
- purpose: context/comparison/drivers/risk/actions
- narrative:
  - headline: main message
  - supporting_bullets: 2-6 bullets
  - caveats: 0-5 caveats
- visuals: ordered list (0-3 per section)
  - chart_ref: path to chart JSON (must exist)
  - visualization_type: bar/line/pie/area
  - role: baseline/comparison/driver/risk/action
  - emphasis: key takeaway
- evidence_index: references to insight IDs with confidence
- client_readiness_hint: internal label

RULES:
- Fully consistent with visual_storyboard order
- No suppressed insights
- No "Do not lead with" insights
- Every chart_ref must exist on disk or build fails
- No placeholders or unrendered charts
"""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.skills.base import Skill, SkillContext, SkillResult


@dataclass
class StoryNarrative:
    """Narrative content for a section."""

    headline: str
    supporting_bullets: list[str]
    caveats: list[str]


@dataclass
class StoryVisual:
    """Visual element in a section."""

    chart_ref: str
    visualization_type: str
    role: str
    emphasis: str


@dataclass
class StorySection:
    """A section in the story manifest."""

    section_id: str
    title: str
    purpose: str
    narrative: StoryNarrative
    visuals: list[StoryVisual]
    evidence_index: list[dict[str, Any]]
    client_readiness_hint: str
    actionability_level: str  # decision_enabling, directional, informational


@dataclass
class StoryManifest:
    """The canonical story representation."""

    story_id: str
    project_name: str
    objective: str
    generated_at: str
    execution_mode: str
    sections: list[StorySection]


class StoryManifestSkill(Skill):
    """
    Story Manifest Skill.

    Creates canonical story representation from judged artifacts.
    Both PPT and Dashboard render from this manifest to ensure alignment.
    """

    @property
    def skill_id(self) -> str:
        return "story_manifest"

    @property
    def description(self) -> str:
        return "Create canonical story manifest for aligned rendering"

    @property
    def stage_scope(self) -> list[str]:
        return ["build", "preview"]

    @property
    def required_artifacts(self) -> list[str]:
        return [
            "insight_triage",
            "executive_summary",
            "visual_storyboard",
            "visualization_plan",
            "actionability_scores",
        ]

    @property
    def produces_artifacts(self) -> list[str]:
        return ["story_manifest_json", "story_manifest_markdown"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute story manifest generation.

        Args:
            context: Read-only context with project state and artifacts

        Returns:
            SkillResult with manifest artifacts and status
        """
        warnings = []
        errors = []

        outputs_dir = context.project_root / "outputs"
        project_state_dir = context.project_root / "project_state"
        charts_dir = outputs_dir / "charts"

        # Validate required inputs
        triage_path = outputs_dir / "insight_triage.json"
        storyboard_path = outputs_dir / "visual_storyboard.json"
        viz_plan_path = outputs_dir / "visualization_plan.json"
        actionability_path = outputs_dir / "actionability_scores.json"
        intent_path = project_state_dir / "intent.yaml"
        exec_summary_md = outputs_dir / "executive_summary.md"
        exec_summary_json = outputs_dir / "executive_summary.json"

        # Check inputs exist
        if not triage_path.exists():
            errors.append("insight_triage.json not found")
            return SkillResult(
                success=False,
                artifacts={},
                evidence=[],
                warnings=warnings,
                errors=errors,
            )

        if not actionability_path.exists():
            errors.append("actionability_scores.json not found")
            return SkillResult(
                success=False,
                artifacts={},
                evidence=[],
                warnings=warnings,
                errors=errors,
            )

        if not storyboard_path.exists():
            errors.append("visual_storyboard.json not found")
            return SkillResult(
                success=False,
                artifacts={},
                evidence=[],
                warnings=warnings,
                errors=errors,
            )

        if not viz_plan_path.exists():
            errors.append("visualization_plan.json not found")
            return SkillResult(
                success=False,
                artifacts={},
                evidence=[],
                warnings=warnings,
                errors=errors,
            )

        if not intent_path.exists():
            errors.append("intent.yaml not found")
            return SkillResult(
                success=False,
                artifacts={},
                evidence=[],
                warnings=warnings,
                errors=errors,
            )

        if not exec_summary_md.exists() and not exec_summary_json.exists():
            errors.append("executive_summary not found")
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

        with open(actionability_path) as f:
            actionability_data = json.load(f)

        with open(storyboard_path) as f:
            storyboard_data = json.load(f)

        with open(viz_plan_path) as f:
            viz_plan = json.load(f)

        import yaml

        with open(intent_path) as f:
            intent_data = yaml.safe_load(f)

        # Load executive summary
        exec_summary_content = self._load_executive_summary(
            exec_summary_md, exec_summary_json
        )

        # Get project metadata
        project_name = context.artifacts.get("project_name", "Analysis")
        objective = intent_data.get("objective", "")
        execution_mode = context.artifacts.get("execution_mode", "rails")

        # Validate storyboard has elements
        elements = storyboard_data.get("elements", [])
        if not elements:
            errors.append("visual_storyboard.json contains no elements")
            return SkillResult(
                success=False,
                artifacts={},
                evidence=[],
                warnings=warnings,
                errors=errors,
            )

        # Validate all chart refs exist
        missing_charts = []
        for element in elements:
            chart_ref = element.get("chart_ref", "")
            if chart_ref:
                chart_path = charts_dir / chart_ref
                if not chart_path.exists():
                    missing_charts.append(chart_ref)

        if missing_charts:
            errors.append(
                f"Charts referenced in storyboard not found: {', '.join(missing_charts)}"
            )
            return SkillResult(
                success=False,
                artifacts={},
                evidence=[],
                warnings=warnings,
                errors=errors,
            )

        # Build manifest
        manifest = self._build_manifest(
            project_name=project_name,
            objective=objective,
            execution_mode=execution_mode,
            storyboard_data=storyboard_data,
            triage_data=triage_data,
            actionability_data=actionability_data,
            exec_summary_content=exec_summary_content,
        )

        # Save JSON
        manifest_json_path = outputs_dir / "story_manifest.json"
        manifest_dict = self._manifest_to_dict(manifest)
        with open(manifest_json_path, "w") as f:
            json.dump(manifest_dict, f, indent=2)

        # Save Markdown
        manifest_md_path = outputs_dir / "story_manifest.md"
        manifest_md = self._generate_markdown(manifest)
        manifest_md_path.write_text(manifest_md)

        return SkillResult(
            success=True,
            artifacts={
                "story_manifest_json": manifest_json_path,
                "story_manifest_markdown": manifest_md_path,
            },
            evidence=[
                f"Generated story manifest with {len(manifest.sections)} sections",
                f"Total visuals: {sum(len(s.visuals) for s in manifest.sections)}",
            ],
            warnings=warnings,
            errors=errors,
        )

    def _load_executive_summary(
        self, md_path: Path, json_path: Path
    ) -> dict[str, Any]:
        """Load executive summary from markdown or JSON."""
        if md_path.exists():
            content = md_path.read_text()
            return {"markdown": content, "bullets": [], "caveats": []}
        elif json_path.exists():
            with open(json_path) as f:
                return json.load(f)
        return {}

    def _build_manifest(
        self,
        project_name: str,
        objective: str,
        execution_mode: str,
        storyboard_data: dict[str, Any],
        triage_data: dict[str, Any],
        actionability_data: dict[str, Any],
        exec_summary_content: dict[str, Any],
    ) -> StoryManifest:
        """Build story manifest from inputs."""
        # Generate story ID
        story_id = str(uuid.uuid4())
        generated_at = datetime.now().isoformat()

        # Build actionability lookup by insight_id
        actionability_lookup: dict[str, str] = {}
        for scored_insight in actionability_data.get("insights", []):
            insight_id = scored_insight.get("insight_id", "")
            actionability = scored_insight.get("actionability", "informational")
            if insight_id:
                actionability_lookup[insight_id] = actionability

        # Extract executive summary bullets and caveats
        exec_bullets = self._extract_summary_bullets(exec_summary_content)
        exec_caveats = self._extract_caveats(exec_summary_content)

        # Group storyboard elements by section
        elements = storyboard_data.get("elements", [])
        sections_dict: dict[str, list[dict[str, Any]]] = {}

        for element in elements:
            section = element.get("section", "Context & Baseline")
            if section not in sections_dict:
                sections_dict[section] = []
            sections_dict[section].append(element)

        # Build sections in canonical order
        SECTION_ORDER = [
            "Context & Baseline",
            "Dominance & Comparison",
            "Drivers & Structure",
            "Risk, Outliers & Caveats",
            "Implications & Actions",
        ]

        PURPOSE_MAP = {
            "Context & Baseline": "context",
            "Dominance & Comparison": "comparison",
            "Drivers & Structure": "drivers",
            "Risk, Outliers & Caveats": "risk",
            "Implications & Actions": "actions",
        }

        sections = []
        for section_title in SECTION_ORDER:
            if section_title not in sections_dict:
                continue

            section_elements = sections_dict[section_title]

            # Build narrative from elements
            headlines = []
            bullets = []
            caveats = []

            for element in section_elements:
                if element.get("insight_title"):
                    headlines.append(element["insight_title"])
                if element.get("transition_text"):
                    bullets.append(element["transition_text"])
                if element.get("caveats"):
                    caveats.extend(element["caveats"])

            # Use first headline or section title
            headline = headlines[0] if headlines else section_title

            # Limit bullets to 2-6
            bullets = bullets[:6]

            # Build visuals
            visuals = []
            for element in section_elements:
                if element.get("chart_ref"):
                    visual = StoryVisual(
                        chart_ref=element["chart_ref"],
                        visualization_type=element.get("visualization_type", "bar"),
                        role=element.get("role", "baseline"),
                        emphasis=element.get("emphasis", ""),
                    )
                    visuals.append(visual)

            # Build evidence index with actionability annotations
            evidence_index = []
            section_actionability_levels = []

            for element in section_elements:
                insight_id = element.get("insight_id", "")
                if insight_id:
                    # Find insight in triage data
                    for insight in triage_data.get("judged_insights", []):
                        if insight.get("insight_id") == insight_id:
                            actionability = actionability_lookup.get(insight_id, "informational")
                            section_actionability_levels.append(actionability)

                            evidence_index.append(
                                {
                                    "insight_id": insight_id,
                                    "confidence": insight.get("confidence", "unknown"),
                                    "headline": insight.get("headline", ""),
                                    "actionability": actionability,
                                }
                            )
                            break

            # Determine section-level actionability (highest level wins)
            if "decision_enabling" in section_actionability_levels:
                section_actionability = "decision_enabling"
            elif "directional" in section_actionability_levels:
                section_actionability = "directional"
            else:
                section_actionability = "informational"

            section = StorySection(
                section_id=str(uuid.uuid4()),
                title=section_title,
                purpose=PURPOSE_MAP.get(section_title, "context"),
                narrative=StoryNarrative(
                    headline=headline, supporting_bullets=bullets, caveats=caveats
                ),
                visuals=visuals,
                evidence_index=evidence_index,
                client_readiness_hint="approved",
                actionability_level=section_actionability,
            )
            sections.append(section)

        # Sort sections: decision_enabling first, then directional, then informational
        # Within each actionability level, preserve canonical order
        actionability_priority = {
            "decision_enabling": 0,
            "directional": 1,
            "informational": 2,
        }

        sections.sort(
            key=lambda s: (
                actionability_priority.get(s.actionability_level, 2),
                SECTION_ORDER.index(s.title) if s.title in SECTION_ORDER else 999,
            )
        )

        # Add executive summary as first section if we have bullets
        if exec_bullets:
            exec_section = StorySection(
                section_id=str(uuid.uuid4()),
                title="Executive Summary",
                purpose="context",
                narrative=StoryNarrative(
                    headline="Key Findings",
                    supporting_bullets=exec_bullets,
                    caveats=exec_caveats,
                ),
                visuals=[],
                evidence_index=[],
                client_readiness_hint="approved",
                actionability_level="decision_enabling",  # Always high priority
            )
            sections.insert(0, exec_section)

        return StoryManifest(
            story_id=story_id,
            project_name=project_name,
            objective=objective,
            generated_at=generated_at,
            execution_mode=execution_mode,
            sections=sections,
        )

    def _extract_summary_bullets(self, exec_summary: dict[str, Any]) -> list[str]:
        """Extract summary bullets from executive summary."""
        bullets = []
        if exec_summary.get("bullets"):
            return exec_summary["bullets"]
        markdown = exec_summary.get("markdown", "")
        if markdown:
            lines = markdown.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("-") or line.startswith("*") or line.startswith("•"):
                    bullet = line.lstrip("-*• ").strip()
                    if (
                        bullet
                        and not bullet.lower().startswith("risk")
                        and not bullet.lower().startswith("caveat")
                    ):
                        bullets.append(bullet)
        return bullets[:6]

    def _extract_caveats(self, exec_summary: dict[str, Any]) -> list[str]:
        """Extract caveats from executive summary."""
        caveats = []
        if exec_summary.get("caveats"):
            return exec_summary["caveats"]
        markdown = exec_summary.get("markdown", "")
        if markdown:
            lines = markdown.split("\n")
            in_caveats_section = False
            for line in lines:
                line = line.strip()
                if "risk" in line.lower() or "caveat" in line.lower():
                    in_caveats_section = True
                    continue
                if in_caveats_section and (
                    line.startswith("-")
                    or line.startswith("*")
                    or line.startswith("•")
                ):
                    caveat = line.lstrip("-*• ").strip()
                    if caveat:
                        caveats.append(caveat)
        return caveats

    def _manifest_to_dict(self, manifest: StoryManifest) -> dict[str, Any]:
        """Convert manifest to dictionary for JSON serialization."""
        return {
            "story_id": manifest.story_id,
            "project_name": manifest.project_name,
            "objective": manifest.objective,
            "generated_at": manifest.generated_at,
            "execution_mode": manifest.execution_mode,
            "sections": [
                {
                    "section_id": section.section_id,
                    "title": section.title,
                    "purpose": section.purpose,
                    "narrative": {
                        "headline": section.narrative.headline,
                        "supporting_bullets": section.narrative.supporting_bullets,
                        "caveats": section.narrative.caveats,
                    },
                    "visuals": [
                        {
                            "chart_ref": visual.chart_ref,
                            "visualization_type": visual.visualization_type,
                            "role": visual.role,
                            "emphasis": visual.emphasis,
                        }
                        for visual in section.visuals
                    ],
                    "evidence_index": section.evidence_index,
                    "client_readiness_hint": section.client_readiness_hint,
                    "actionability_level": section.actionability_level,
                }
                for section in manifest.sections
            ],
        }

    def _generate_markdown(self, manifest: StoryManifest) -> str:
        """Generate markdown representation of manifest."""
        lines = [
            f"# {manifest.project_name}",
            "",
            f"**Objective**: {manifest.objective}",
            "",
            f"**Story ID**: {manifest.story_id}",
            f"**Generated**: {manifest.generated_at}",
            f"**Execution Mode**: {manifest.execution_mode}",
            "",
            "---",
            "",
        ]

        for i, section in enumerate(manifest.sections, 1):
            lines.append(f"## Section {i}: {section.title}")
            lines.append("")
            lines.append(f"**Purpose**: {section.purpose}")
            lines.append(f"**Actionability**: {section.actionability_level}")
            lines.append("")
            lines.append(f"### {section.narrative.headline}")
            lines.append("")

            if section.narrative.supporting_bullets:
                for bullet in section.narrative.supporting_bullets:
                    lines.append(f"- {bullet}")
                lines.append("")

            if section.narrative.caveats:
                lines.append("**Caveats:**")
                for caveat in section.narrative.caveats:
                    lines.append(f"- {caveat}")
                lines.append("")

            if section.visuals:
                lines.append("**Visuals:**")
                for visual in section.visuals:
                    lines.append(
                        f"- {visual.visualization_type} chart: `{visual.chart_ref}` ({visual.role})"
                    )
                    if visual.emphasis:
                        lines.append(f"  - Emphasis: {visual.emphasis}")
                lines.append("")

            if section.evidence_index:
                lines.append("**Evidence:**")
                for evidence in section.evidence_index:
                    actionability = evidence.get("actionability", "unknown")
                    lines.append(
                        f"- {evidence['headline']} (confidence: {evidence['confidence']}, actionability: {actionability})"
                    )
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)
