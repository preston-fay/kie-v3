"""
Narrative Synthesis Skill

Converts ranked insights (from insight_triage) into a consultant-grade
executive narrative artifact.

This is the bridge between "insights" and "deck-ready story."
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.insights import InsightCatalog
from kie.skills.base import Skill, SkillContext, SkillResult


class NarrativeSynthesisSkill(Skill):
    """
    Synthesizes ranked insights into executive narrative.

    INPUTS (read-only):
    - outputs/insight_triage.json (preferred)
    - outputs/insight_triage.md (fallback if JSON missing)
    - project_state/intent.yaml (optional, for framing)
    - Evidence Ledger (for traceability)

    OUTPUTS:
    - outputs/executive_narrative.md (INTERNAL)
    - outputs/executive_narrative.json (structured sections)

    STAGE SCOPE:
    - analyze
    - build
    - preview
    """

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill."""
        return "narrative_synthesis"

    @property
    def stage_scope(self) -> list[str]:
        """Stages where this skill should run."""
        return ["analyze", "build", "preview"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute narrative synthesis from triage.

        Args:
            context: Skill execution context with artifacts

        Returns:
            SkillResult with narrative paths and metadata
        """
        outputs_dir = context.project_root / "outputs"
        project_state_dir = context.project_root / "project_state"

        # Load triage data - check both JSON and YAML/MD formats
        triage_json_path = outputs_dir / "insight_triage.json"
        triage_md_path = outputs_dir / "insight_triage.md"

        if triage_json_path.exists():
            # Load JSON format (preferred)
            with open(triage_json_path) as f:
                triage_data = json.load(f)
        elif triage_md_path.exists():
            # Graceful fallback - produce narrative stating triage MD exists but JSON missing
            return self._handle_missing_triage_json(outputs_dir)
        else:
            # No triage available yet
            return self._handle_no_triage(outputs_dir)

        # Load intent if available (for framing)
        intent_text = self._load_intent(project_state_dir)

        # Load evidence ledger hashes if available
        evidence_hashes = self._load_evidence_hashes(
            context.evidence_ledger_id,
            project_state_dir / "evidence_ledger"
        )

        # Generate narrative from triage
        narrative_md = self._generate_narrative_markdown(
            triage_data, intent_text, evidence_hashes
        )
        narrative_json = self._generate_narrative_json(
            triage_data, intent_text, evidence_hashes
        )

        # Save outputs
        narrative_md_path = outputs_dir / "executive_narrative.md"
        narrative_json_path = outputs_dir / "executive_narrative.json"

        narrative_md_path.write_text(narrative_md)
        narrative_json_path.write_text(json.dumps(narrative_json, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "narrative_markdown": str(narrative_md_path),
                "narrative_json": str(narrative_json_path),
            },
            evidence={
                "triage_input": str(triage_json_path),
                "top_insights_count": len(triage_data.get("top_insights", [])),
                "narrative_sections": 5,
            },
        )

    def _handle_no_triage(self, outputs_dir: Path) -> SkillResult:
        """Handle case where no triage exists yet."""
        narrative_md = self._generate_no_triage_narrative()
        narrative_json = {
            "status": "no_triage_available",
            "message": "No ranked insights available yet. Run /analyze first.",
            "sections": {},
        }

        narrative_md_path = outputs_dir / "executive_narrative.md"
        narrative_json_path = outputs_dir / "executive_narrative.json"

        narrative_md_path.write_text(narrative_md)
        narrative_json_path.write_text(json.dumps(narrative_json, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "narrative_markdown": str(narrative_md_path),
                "narrative_json": str(narrative_json_path),
            },
            evidence={
                "status": "no_triage_available",
            },
        )

    def _handle_missing_triage_json(self, outputs_dir: Path) -> SkillResult:
        """Handle case where triage MD exists but JSON missing."""
        narrative_md = (
            "# Executive Narrative (Internal)\n\n"
            "**Status:** Insight triage markdown exists but structured JSON not available.\n\n"
            "The narrative synthesis skill requires structured triage output (JSON format) "
            "to generate the executive narrative. The triage markdown file exists, but the "
            "JSON file is missing.\n\n"
            "**Resolution:** Re-run /analyze to regenerate both triage outputs.\n"
        )

        narrative_json = {
            "status": "triage_json_missing",
            "message": "Triage markdown exists but JSON missing. Re-run /analyze.",
            "sections": {},
        }

        narrative_md_path = outputs_dir / "executive_narrative.md"
        narrative_json_path = outputs_dir / "executive_narrative.json"

        narrative_md_path.write_text(narrative_md)
        narrative_json_path.write_text(json.dumps(narrative_json, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "narrative_markdown": str(narrative_md_path),
                "narrative_json": str(narrative_json_path),
            },
            evidence={
                "status": "triage_json_missing",
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

    def _load_evidence_hashes(
        self, evidence_ledger_id: str | None, evidence_dir: Path
    ) -> dict[str, str]:
        """Load artifact hashes from evidence ledger."""
        hashes = {}

        if not evidence_ledger_id or not evidence_dir.exists():
            return hashes

        import yaml
        ledger_path = evidence_dir / f"{evidence_ledger_id}.yaml"
        if not ledger_path.exists():
            return hashes

        try:
            with open(ledger_path) as f:
                ledger = yaml.safe_load(f)

            for output in ledger.get("outputs", []):
                path = output.get("path", "")
                file_hash = output.get("hash")
                if file_hash:
                    hashes[path] = file_hash
        except Exception:
            pass

        return hashes

    def _generate_no_triage_narrative(self) -> str:
        """Generate narrative when no triage available."""
        return (
            "# Executive Narrative (Internal)\n\n"
            "**Status:** No ranked insights available yet.\n\n"
            "The narrative synthesis skill requires insight triage output to generate "
            "the executive narrative. No triage data was found.\n\n"
            "**Next step:** Run `/analyze` to extract and rank insights, then the narrative "
            "will be automatically generated.\n"
        )

    def _generate_narrative_markdown(
        self,
        triage_data: dict[str, Any],
        intent_text: str | None,
        evidence_hashes: dict[str, str],
    ) -> str:
        """
        Generate executive narrative markdown.

        MUST follow exact content contract order:
        1. What matters most (Top 3)
        2. What this means
        3. Recommended actions
        4. Risks and caveats
        5. Evidence index
        """
        lines = []

        # Header
        lines.append("# Executive Narrative (Internal)")
        lines.append("")
        if intent_text:
            lines.append(f"**Project Intent:** {intent_text}")
            lines.append("")

        # Section 1: What matters most (Top 3)
        lines.append("## 1. What matters most (Top 3)")
        lines.append("")

        top_insights = triage_data.get("top_insights", [])
        if not top_insights:
            lines.append("- No insights with sufficient confidence and evidence strength")
        else:
            for i, insight in enumerate(top_insights[:3], 1):
                title = insight.get("title", "Untitled insight")
                confidence = insight.get("confidence", "unknown")
                caveats = insight.get("caveats", [])

                # Plain-English statement
                lines.append(f"- **{title}**")
                lines.append(f"  - Confidence: {confidence}")

                # Add caveat if present
                if caveats:
                    lines.append(f"  - Caveat: {caveats[0]}")

        lines.append("")

        # Section 2: What this means
        lines.append("## 2. What this means")
        lines.append("")

        if not top_insights:
            lines.append("- No implications can be drawn without ranked insights")
        else:
            # Generate 3-6 implication bullets from top insights
            implications = self._generate_implications(top_insights)
            for implication in implications:
                lines.append(f"- {implication}")

        lines.append("")

        # Section 3: Recommended actions (Internal)
        lines.append("## 3. Recommended actions (Internal)")
        lines.append("")

        if not top_insights:
            lines.append("- Run /analyze to extract insights first")
        else:
            # Generate 3-7 action bullets
            actions = self._generate_actions(top_insights, triage_data)
            for action in actions:
                lines.append(f"- {action}")

        lines.append("")

        # Section 4: Risks and caveats
        lines.append("## 4. Risks and caveats")
        lines.append("")

        # Pull from triage caveats + confidence thresholds
        risks = self._generate_risks_and_caveats(triage_data)
        for risk in risks:
            lines.append(f"- {risk}")

        lines.append("")

        # Section 5: Evidence index
        lines.append("## 5. Evidence index")
        lines.append("")

        if not top_insights:
            lines.append("| Insight | Source | Hash | Confidence |")
            lines.append("|---------|--------|------|------------|")
            lines.append("| No insights available | — | — | — |")
        else:
            lines.append("| Insight | Source | Hash | Confidence |")
            lines.append("|---------|--------|------|------------|")

            for insight in top_insights:
                title = insight.get("title", "Untitled")[:40]
                confidence = insight.get("confidence", "unknown")
                evidence_refs = insight.get("evidence", [])

                # Get source artifact (first evidence reference)
                if evidence_refs:
                    source = evidence_refs[0].get("reference", "unknown")
                    # Check if hash available
                    if source in evidence_hashes:
                        hash_val = evidence_hashes[source][:12] + "..."
                    elif "hash" in evidence_refs[0]:
                        hash_val = evidence_refs[0]["hash"]
                    else:
                        hash_val = "hash unavailable"
                else:
                    source = "outputs/insight_triage.json"
                    hash_val = "hash unavailable"

                lines.append(f"| {title} | {source} | {hash_val} | {confidence} |")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        lines.append("**INTERNAL ONLY** - Not for client distribution")
        lines.append("")

        return "\n".join(lines)

    def _generate_implications(self, top_insights: list[dict[str, Any]]) -> list[str]:
        """
        Generate 3-6 implication bullets from top insights.

        No new claims beyond triage.
        """
        implications = []

        for insight in top_insights[:3]:
            why_matters = insight.get("why_it_matters", "")
            confidence = insight.get("confidence", "unknown")
            caveats = insight.get("caveats", [])

            if why_matters:
                # Extract implication from "why it matters" text
                implication = why_matters

                # Add uncertainty statement if confidence is medium/low
                if confidence == "LOW":
                    implication += " (confidence is low - further validation needed)"
                elif confidence == "MEDIUM":
                    implication += " (medium confidence - consider additional evidence)"

                implications.append(implication)

        # Ensure we have at least 3 implications
        if len(implications) < 3 and top_insights:
            implications.append(
                "Additional analysis may reveal further patterns and opportunities"
            )

        return implications[:6]  # Cap at 6

    def _generate_actions(
        self, top_insights: list[dict[str, Any]], triage_data: dict[str, Any]
    ) -> list[str]:
        """
        Generate 3-7 action bullets.

        Actions phrased as "next analyses / next decisions".
        No client commitments.
        """
        actions = []

        # Standard actions based on triage guidance
        guidance = triage_data.get("consultant_guidance", {})
        lead_with = guidance.get("lead_with", [])

        if lead_with:
            actions.append(
                "Lead client discussions with high-confidence insights: "
                + ", ".join(f'"{item}"' for item in lead_with[:2])
            )

        # Add analysis-focused actions
        actions.append("Validate findings with client stakeholders")
        actions.append("Gather additional data to strengthen medium-confidence insights")

        # Check for deprioritized insights
        deprioritized = triage_data.get("deprioritized_insights", [])
        if deprioritized:
            actions.append(
                f"Consider further analysis on {len(deprioritized)} deprioritized insights "
                "if client priorities shift"
            )

        # Add decision-focused actions
        use_with_caution = triage_data.get("use_with_caution_insights", 0)
        if use_with_caution > 0:
            actions.append(
                "Address caveats and data limitations before making recommendations"
            )

        actions.append("Determine next analytical steps based on client feedback")

        return actions[:7]  # Cap at 7

    def _generate_risks_and_caveats(self, triage_data: dict[str, Any]) -> list[str]:
        """
        Generate risks and caveats section.

        Pull from triage caveats + confidence thresholds.
        """
        risks = []

        # Add "Do not overclaim" bullets
        risks.append("Do not overclaim certainty - confidence levels are explicitly noted")

        # Pull from top insights caveats
        top_insights = triage_data.get("top_insights", [])
        for insight in top_insights:
            caveats = insight.get("caveats", [])
            for caveat in caveats:
                if caveat not in risks:
                    risks.append(caveat)

        # Add general guidance
        high_conf = triage_data.get("high_confidence_insights", 0)
        total = triage_data.get("total_candidate_insights", 0)
        if high_conf < total // 2 and total > 0:
            risks.append(
                f"Only {high_conf}/{total} insights have high confidence - "
                "further validation recommended"
            )

        # Add use-with-caution warning
        use_with_caution = triage_data.get("use_with_caution_insights", 0)
        if use_with_caution > 0:
            risks.append(
                f"{use_with_caution} insight(s) flagged as use-with-caution - "
                "avoid leading with these"
            )

        risks.append("All insights are INTERNAL ONLY until validated with client")

        return risks

    def _generate_narrative_json(
        self,
        triage_data: dict[str, Any],
        intent_text: str | None,
        evidence_hashes: dict[str, str],
    ) -> dict[str, Any]:
        """Generate structured JSON version of narrative."""
        top_insights = triage_data.get("top_insights", [])

        return {
            "generated_at": datetime.now().isoformat(),
            "project_intent": intent_text,
            "status": "complete" if top_insights else "no_insights",
            "sections": {
                "what_matters_most": [
                    {
                        "title": insight.get("title"),
                        "confidence": insight.get("confidence"),
                        "caveats": insight.get("caveats", []),
                    }
                    for insight in top_insights[:3]
                ],
                "implications": self._generate_implications(top_insights),
                "recommended_actions": self._generate_actions(top_insights, triage_data),
                "risks_and_caveats": self._generate_risks_and_caveats(triage_data),
            },
            "metadata": {
                "total_candidate_insights": triage_data.get("total_candidate_insights", 0),
                "high_confidence_insights": triage_data.get("high_confidence_insights", 0),
                "use_with_caution_insights": triage_data.get("use_with_caution_insights", 0),
            },
        }
