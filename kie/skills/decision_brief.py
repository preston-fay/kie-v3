"""
Decision Brief Skill

Consolidates the story into a one-page, consultant-ready internal memo format.
This is the daily driver artifact for consultants.

Contract (mandatory order):
1. Executive Takeaways (5-10 bullets with tags)
2. What to Do Next (5-10 bullets, next 7 days)
3. What We're Not Confident About (caveats)
4. Exhibit Index (table with PPT/dashboard locations)

Rules:
- No new claims
- No numbers invented
- Deterministic formatting
- Reads like a consultant memo, not an LLM essay
"""

import json
from datetime import datetime
from pathlib import Path

from kie.skills.base import Skill, SkillContext, SkillResult


class DecisionBriefSkill(Skill):
    """Generate one-page decision brief for consultants."""

    @property
    def skill_id(self) -> str:
        return "decision_brief"

    @property
    def description(self) -> str:
        return "Generate one-page decision brief for consultants"

    @property
    def stage_scope(self) -> list[str]:
        return ["build", "preview"]

    @property
    def required_artifacts(self) -> list[str]:
        return ["story_manifest"]

    def execute(self, context: SkillContext) -> SkillResult:
        """Execute decision brief generation."""
        outputs_dir = context.project_root / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        # Load story manifest (required)
        manifest_path = outputs_dir / "story_manifest.json"
        if not manifest_path.exists():
            return SkillResult(
                success=False,
                errors=["story_manifest.json not found - run build first"],
                artifacts={},
            )

        with open(manifest_path) as f:
            manifest = json.load(f)

        # Load executive summary (prefer consultant version)
        exec_summary_path = outputs_dir / "executive_summary_consultant.md"
        if not exec_summary_path.exists():
            exec_summary_path = outputs_dir / "executive_summary.md"

        exec_summary = ""
        if exec_summary_path.exists():
            exec_summary = exec_summary_path.read_text()

        # Load actionability scores (optional)
        actionability_path = outputs_dir / "actionability_scores.json"
        actionability_data = {}
        if actionability_path.exists():
            with open(actionability_path) as f:
                actionability_data = json.load(f)

        # Load visual QC (optional)
        visual_qc_path = outputs_dir / "visual_qc.json"
        visual_qc_data = {}
        if visual_qc_path.exists():
            with open(visual_qc_path) as f:
                visual_qc_data = json.load(f)

        # Generate decision brief
        brief_md = self._generate_decision_brief_md(
            manifest, exec_summary, actionability_data, visual_qc_data
        )

        # Save markdown
        brief_md_path = outputs_dir / "decision_brief.md"
        brief_md_path.write_text(brief_md)

        # Generate JSON (optional, for programmatic access)
        brief_json = self._generate_decision_brief_json(
            manifest, actionability_data, visual_qc_data
        )
        brief_json_path = outputs_dir / "decision_brief.json"
        with open(brief_json_path, "w") as f:
            json.dump(brief_json, f, indent=2)

        return SkillResult(
            success=True,
            artifacts={
                "decision_brief_md": str(brief_md_path),
                "decision_brief_json": str(brief_json_path),
            },
            evidence={
                "sections_generated": ["executive_takeaways", "next_actions", "caveats", "exhibit_index"],
                "total_exhibits": len(brief_json.get("exhibit_index", [])),
            },
        )

    def _generate_decision_brief_md(
        self,
        manifest: dict,
        exec_summary: str,
        actionability_data: dict,
        visual_qc_data: dict,
    ) -> str:
        """Generate decision brief markdown."""
        lines = []

        # Header
        lines.append("# Decision Brief (Internal)")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Project:** {manifest.get('project_name', 'Unnamed Project')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Section 1: Executive Takeaways
        lines.append("## 1) Executive Takeaways")
        lines.append("")
        takeaways = self._extract_executive_takeaways(manifest, exec_summary, actionability_data)
        for takeaway in takeaways[:10]:  # Max 10
            tag = takeaway["tag"]
            text = takeaway["text"]
            lines.append(f"- **[{tag}]** {text}")
        lines.append("")

        # Section 2: What to Do Next
        lines.append("## 2) What to Do Next (Next 7 days)")
        lines.append("")
        next_actions = self._extract_next_actions(manifest, actionability_data)
        for action in next_actions[:10]:  # Max 10
            lines.append(f"- {action}")
        lines.append("")

        # Section 3: What We're Not Confident About
        lines.append("## 3) What We're Not Confident About")
        lines.append("")
        caveats = self._extract_caveats(manifest, visual_qc_data)
        if caveats:
            for caveat in caveats:
                lines.append(f"- {caveat}")
        else:
            lines.append("- No significant caveats identified")
        lines.append("")

        # Section 4: Exhibit Index
        lines.append("## 4) Exhibit Index (What to show if asked)")
        lines.append("")
        exhibit_index = self._generate_exhibit_index(manifest, visual_qc_data)
        if exhibit_index:
            lines.append("| Exhibit | Location | Quality |")
            lines.append("|---------|----------|---------|")
            for exhibit in exhibit_index:
                lines.append(f"| {exhibit['name']} | {exhibit['location']} | {exhibit['quality']} |")
        else:
            lines.append("No exhibits available")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("**INTERNAL ONLY** - Not for client distribution")
        lines.append("")

        return "\n".join(lines)

    def _extract_executive_takeaways(
        self, manifest: dict, exec_summary: str, actionability_data: dict
    ) -> list[dict]:
        """Extract executive takeaways with tags."""
        takeaways = []

        # Extract from manifest's main story
        main_story = manifest.get("main_story", {})

        # Add headline as first takeaway (DIRECTION)
        if main_story.get("headline"):
            takeaways.append({
                "tag": "DIRECTION",
                "text": main_story["headline"]
            })

        # Add key insights from main story sections
        for section in main_story.get("sections", [])[:3]:  # Top 3 sections
            insight_text = section.get("insight_text", "")
            if insight_text:
                # Determine tag based on actionability
                tag = self._determine_tag(section.get("insight_id", ""), actionability_data)
                takeaways.append({
                    "tag": tag,
                    "text": insight_text
                })

        # Add decision-enabling insights from actionability
        insights = actionability_data.get("insights", [])
        for insight in insights[:5]:  # Top 5
            if insight.get("actionability") == "decision_enabling":
                title = insight.get("title", "")
                if title and not any(t["text"] == title for t in takeaways):
                    takeaways.append({
                        "tag": "DECISION",
                        "text": title
                    })

        return takeaways

    def _determine_tag(self, insight_id: str, actionability_data: dict) -> str:
        """Determine tag for an insight."""
        insights = actionability_data.get("insights", [])
        for insight in insights:
            if insight.get("insight_id") == insight_id:
                actionability = insight.get("actionability", "informational")
                if actionability == "decision_enabling":
                    return "DECISION"
                elif actionability == "action_required":
                    return "DIRECTION"
        return "INFO"

    def _extract_next_actions(
        self, manifest: dict, actionability_data: dict
    ) -> list[str]:
        """Extract next 7-day actions."""
        actions = []

        # Get decision-enabling insights first
        insights = actionability_data.get("insights", [])
        decision_enabling = [i for i in insights if i.get("actionability") == "decision_enabling"]

        for insight in decision_enabling[:5]:
            title = insight.get("title", "")
            if title:
                actions.append(f"Validate findings on: {title}")

        # Add recommendations from manifest
        recommendations = manifest.get("recommendations", [])
        for rec in recommendations[:5]:
            if isinstance(rec, str):
                actions.append(rec)
            elif isinstance(rec, dict):
                actions.append(rec.get("text", ""))

        # If no specific actions, add generic ones
        if not actions:
            actions.append("Review insights with stakeholders")
            actions.append("Prioritize decision-enabling findings")
            actions.append("Validate data quality assumptions")

        return actions

    def _extract_caveats(self, manifest: dict, visual_qc_data: dict) -> list[str]:
        """Extract consolidated caveats."""
        caveats = []

        # Collect caveats from manifest sections
        main_story = manifest.get("main_story", {})
        for section in main_story.get("sections", []):
            section_caveats = section.get("caveats", [])
            for caveat in section_caveats:
                if caveat not in caveats:
                    caveats.append(caveat)

        # Add visual QC warnings
        charts = visual_qc_data.get("charts", [])
        internal_only = [c for c in charts if c.get("quality_badge") == "internal_only"]
        if internal_only:
            chart_names = ", ".join([c.get("insight_title", "Unknown")[:30] for c in internal_only[:3]])
            caveats.append(f"Some visuals marked internal-only: {chart_names}")

        warning_charts = [c for c in charts if c.get("quality_badge") == "warning"]
        if warning_charts:
            caveats.append(f"{len(warning_charts)} visuals have quality warnings - review before presenting")

        return caveats

    def _generate_exhibit_index(self, manifest: dict, visual_qc_data: dict) -> list[dict]:
        """Generate exhibit index with locations and quality badges."""
        exhibits = []

        # Create map of insight_id to quality badge
        quality_map = {}
        charts = visual_qc_data.get("charts", [])
        for chart in charts:
            insight_id = chart.get("insight_id", "")
            quality_badge = chart.get("quality_badge", "ready")
            quality_map[insight_id] = quality_badge

        # Build exhibit list from manifest sections
        main_story = manifest.get("main_story", {})
        sections = main_story.get("sections", [])

        for idx, section in enumerate(sections, 1):
            insight_id = section.get("insight_id", "")
            insight_title = section.get("insight_title", "Untitled")

            # Determine location
            ppt_slide = f"Slide {idx + 2}"  # +2 for title and exec summary
            dashboard_section = section.get("section_name", f"Section {idx}")
            location = f"PPT: {ppt_slide} | Dashboard: {dashboard_section}"

            # Get quality badge
            quality = quality_map.get(insight_id, "ready")
            if quality == "ready":
                quality_display = "✓ Ready"
            elif quality == "warning":
                quality_display = "⚠️ Warning"
            else:
                quality_display = "Internal Only"

            exhibits.append({
                "name": insight_title[:50],  # Truncate long titles
                "location": location,
                "quality": quality_display
            })

        return exhibits

    def _generate_decision_brief_json(
        self, manifest: dict, actionability_data: dict, visual_qc_data: dict
    ) -> dict:
        """Generate JSON version for programmatic access."""
        return {
            "generated_at": datetime.now().isoformat(),
            "project_name": manifest.get("project_name", "Unnamed Project"),
            "executive_takeaways": self._extract_executive_takeaways(
                manifest, "", actionability_data
            ),
            "next_actions": self._extract_next_actions(manifest, actionability_data),
            "caveats": self._extract_caveats(manifest, visual_qc_data),
            "exhibit_index": self._generate_exhibit_index(manifest, visual_qc_data),
        }
