"""
Run Story Skill

Creates narrative artifacts summarizing full workflow runs.

CONVERTED FROM: kie/consultant/run_story.py
BEHAVIOR: Identical - no logic changes, only wrapped as Skill

CRITICAL CONSTRAINTS:
- Written in consultant language
- Fully backed by evidence
- Replaces fragmented interpretation across logs
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from kie.skills.base import Skill, SkillContext, SkillResult


class RunStorySkill(Skill):
    """
    Generates narrative "Run Story" artifacts.

    Creates a single consultant-readable document that answers:
    - What we did
    - What we found
    - What it means
    - What to do next

    Stage Scope: build, preview (after significant workflow completion)
    Required Artifacts: evidence_ledger entries
    Produces: run_story.md, run_story.json
    """

    skill_id = "run_story"
    description = "Generate consultant narrative from workflow execution"
    stage_scope = ["build", "preview"]
    required_artifacts = []  # Uses evidence ledger, not specific artifacts
    produces_artifacts = ["run_story.md", "run_story.json"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Generate Run Story from recent commands.

        Args:
            context: Skill execution context

        Returns:
            SkillResult with story paths
        """
        outputs_dir = context.project_root / "outputs"
        project_state_dir = context.project_root / "project_state"
        evidence_dir = project_state_dir / "evidence_ledger"

        # Collect evidence ledger entries (SAME LOGIC)
        entries = self._collect_ledger_entries(evidence_dir, since=None)

        if not entries:
            return SkillResult(
                success=False,
                warnings=["No evidence ledger entries found to generate story"],
            )

        # Load artifacts (SAME LOGIC)
        spec = self._load_spec(project_state_dir)
        insights_catalog = self._load_insights_catalog(outputs_dir)
        insight_brief = self._load_insight_brief(outputs_dir)

        # Generate story content (SAME LOGIC)
        story_content = self._generate_story_content(
            entries, spec, insights_catalog, insight_brief
        )

        # Save story
        story_path = outputs_dir / "run_story.md"
        story_path.write_text(story_content)

        # Save structured data
        story_data = self._generate_story_data(entries, spec, insights_catalog)
        story_json_path = outputs_dir / "run_story.json"
        story_json_path.write_text(json.dumps(story_data, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "story_markdown": str(story_path),
                "story_json": str(story_json_path),
            },
            evidence={
                "commands_included": len(entries),
                "evidence_backed": True,
            },
            metadata={
                "project_name": spec.get("project_name") if spec else None,
            }
        )

    def _collect_ledger_entries(self, evidence_dir: Path, since: str | None) -> list[dict[str, Any]]:
        """Collect evidence ledger entries (LOGIC UNCHANGED)."""
        if not evidence_dir.exists():
            return []

        entries = []
        for ledger_file in sorted(evidence_dir.glob("*.yaml")):
            with open(ledger_file) as f:
                entry = yaml.safe_load(f)

            # Filter by timestamp if requested
            if since:
                entry_time = entry.get("timestamp", "")
                if entry_time < since:
                    continue

            entries.append(entry)

        # Sort by timestamp
        entries.sort(key=lambda e: e.get("timestamp", ""))
        return entries

    def _load_spec(self, project_state_dir: Path) -> dict[str, Any] | None:
        """Load project spec (LOGIC UNCHANGED)."""
        spec_path = project_state_dir / "spec.yaml"
        if not spec_path.exists():
            return None

        with open(spec_path) as f:
            return yaml.safe_load(f)

    def _load_insights_catalog(self, outputs_dir: Path) -> dict[str, Any] | None:
        """Load insights catalog (LOGIC UNCHANGED)."""
        catalog_path = outputs_dir / "insights_catalog.json"
        if not catalog_path.exists():
            return None

        with open(catalog_path) as f:
            return json.load(f)

    def _load_insight_brief(self, outputs_dir: Path) -> str | None:
        """Load insight brief (LOGIC UNCHANGED)."""
        brief_path = outputs_dir / "insight_brief.md"
        if not brief_path.exists():
            return None

        return brief_path.read_text()

    def _generate_story_content(
        self,
        entries: list[dict[str, Any]],
        spec: dict | None,
        insights_catalog: dict | None,
        insight_brief: str | None,
    ) -> str:
        """Generate markdown story content (LOGIC UNCHANGED - copied from run_story.py)."""
        lines = []

        # Header
        lines.append("# Run Story")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if spec:
            lines.append(f"**Project:** {spec.get('project_name', 'Untitled')}")
            lines.append(f"**Client:** {spec.get('client_name', 'N/A')}")
            lines.append(f"**Objective:** {spec.get('objective', 'N/A')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # What We Did
        lines.append("## What We Did")
        lines.append("")
        lines.append("This analysis followed KIE's AI-on-Rails workflow:")
        lines.append("")

        for entry in entries:
            command = entry.get("command", "unknown")
            success = entry.get("success", False)
            timestamp = entry.get("timestamp", "")

            status_icon = "✓" if success else "✗"
            lines.append(f"**{status_icon} /{command}** ({timestamp})")

            # Add brief description of what happened
            if command == "eda":
                if success:
                    outputs = entry.get("outputs", [])
                    lines.append("  - Profiled data structure and quality")
                    lines.append(f"  - Generated {len(outputs)} analysis artifacts")
                else:
                    errors = entry.get("errors", [])
                    if errors:
                        lines.append(f"  - Failed: {errors[0]}")

            elif command == "analyze":
                if success:
                    lines.append("  - Extracted insights from data")
                    if insights_catalog:
                        insight_count = len(insights_catalog.get("insights", []))
                        lines.append(f"  - Generated {insight_count} insights")
                else:
                    errors = entry.get("errors", [])
                    if errors:
                        lines.append(f"  - Failed: {errors[0]}")

            elif command == "build":
                if success:
                    outputs = entry.get("outputs", [])
                    lines.append(f"  - Created deliverable artifacts")
                    lines.append(f"  - Generated {len(outputs)} output files")

            lines.append("")

        lines.append("---")
        lines.append("")

        # What We Found
        lines.append("## What We Found")
        lines.append("")

        if insights_catalog:
            # Use existing insights
            insights = insights_catalog.get("insights", [])
            key_insights = [i for i in insights if i.get("severity") == "key"]

            if key_insights:
                lines.append("**Key Insights:**")
                lines.append("")
                for insight in key_insights:
                    lines.append(f"- **{insight.get('headline', 'Untitled')}**")
                    lines.append(f"  {insight.get('supporting_text', '')}")
                    lines.append("")
            else:
                lines.append("*No key insights were identified in this analysis.*")
                lines.append("")

            # Data summary
            data_summary = insights_catalog.get("data_summary", {})
            if data_summary:
                lines.append("**Data Summary:**")
                row_count = data_summary.get("row_count", 0)
                col_count = data_summary.get("column_count", 0)
                lines.append(f"- {row_count:,} rows, {col_count} columns analyzed")
                lines.append("")
        else:
            lines.append("*Analysis incomplete - insights not yet generated.*")
            lines.append("")

        lines.append("---")
        lines.append("")

        # What It Means
        lines.append("## What It Means")
        lines.append("")

        if insight_brief:
            # Extract "What This Means for the Client" section from brief
            brief_lines = insight_brief.split("\n")
            in_means_section = False
            means_content = []

            for line in brief_lines:
                if "## What This Means for the Client" in line:
                    in_means_section = True
                    continue
                elif line.startswith("## ") and in_means_section:
                    break
                elif in_means_section and line.strip():
                    means_content.append(line)

            if means_content:
                lines.extend(means_content)
                lines.append("")
            else:
                lines.append("*Implications depend on business context and strategic priorities.*")
                lines.append("")
        else:
            if insights_catalog:
                lines.append("Based on the findings, the analysis reveals patterns that warrant attention.")
                lines.append("Specific implications depend on business context and strategic priorities.")
            else:
                lines.append("*Cannot determine implications without completed analysis.*")
            lines.append("")

        lines.append("---")
        lines.append("")

        # What To Do Next
        lines.append("## What To Do Next")
        lines.append("")

        # Determine next steps based on workflow state
        last_command = entries[-1].get("command") if entries else None
        last_success = entries[-1].get("success", False) if entries else False

        if last_command == "analyze" and last_success:
            lines.append("**Immediate Next Steps:**")
            lines.append("")
            lines.append("1. **Review findings** - Validate insights with stakeholders")
            lines.append("2. **Generate deliverables** - Run `/build presentation` or `/build dashboard`")
            lines.append("3. **Quality check** - Run `/validate` before delivery")
            lines.append("")

        elif last_command == "build" and last_success:
            lines.append("**Immediate Next Steps:**")
            lines.append("")
            lines.append("1. **Preview outputs** - Run `/preview` to review all deliverables")
            lines.append("2. **Quality check** - Run `/validate` to ensure KDS compliance")
            lines.append("3. **Deliver** - Share deliverables with client/stakeholders")
            lines.append("")

        else:
            lines.append("**Continue workflow:**")
            lines.append("")
            lines.append("- Complete any failed commands above")
            lines.append("- Follow Rails workflow progression")
            lines.append("- Run `/rails` to check current status")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Evidence Trail
        lines.append("## Evidence Trail")
        lines.append("")
        lines.append("This story is backed by the following evidence:")
        lines.append("")

        for entry in entries:
            run_id = entry.get("run_id", "unknown")
            command = entry.get("command", "unknown")
            lines.append(f"- **/{command}** - Evidence Ledger: `{run_id}.yaml`")

            outputs = entry.get("outputs", [])
            for output in outputs:
                path = output.get("path", "")
                file_hash = output.get("hash", "")
                if file_hash:
                    lines.append(f"  - `{path}` (hash: {file_hash[:16]}...)")

        lines.append("")
        lines.append("*All claims are traceable to Evidence Ledger entries.*")
        lines.append("")

        return "\n".join(lines)

    def _generate_story_data(
        self,
        entries: list[dict[str, Any]],
        spec: dict | None,
        insights_catalog: dict | None,
    ) -> dict[str, Any]:
        """Generate structured JSON story data (LOGIC UNCHANGED)."""
        return {
            "generated_at": datetime.now().isoformat(),
            "project": {
                "name": spec.get("project_name") if spec else None,
                "client": spec.get("client_name") if spec else None,
                "objective": spec.get("objective") if spec else None,
            },
            "workflow": {
                "commands_executed": len(entries),
                "commands": [
                    {
                        "command": e.get("command"),
                        "timestamp": e.get("timestamp"),
                        "success": e.get("success"),
                        "run_id": e.get("run_id"),
                    }
                    for e in entries
                ],
            },
            "findings": {
                "total_insights": len(insights_catalog.get("insights", [])) if insights_catalog else 0,
                "key_insights": [
                    i.get("headline")
                    for i in insights_catalog.get("insights", [])
                    if i.get("severity") == "key"
                ] if insights_catalog else [],
            },
            "evidence_trail": [
                {
                    "command": e.get("command"),
                    "ledger_id": e.get("run_id"),
                    "outputs": e.get("outputs", []),
                }
                for e in entries
            ],
        }
