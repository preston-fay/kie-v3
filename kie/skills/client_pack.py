"""
Client Pack Skill

WOW SKILL #3: Deliverable assembly and packaging.

Creates a single, consultant-friendly "Client Pack" that:
- Aggregates best existing artifacts
- Includes deterministic TOC + evidence links
- Is safe, honest, and immediately usable

CRITICAL CONSTRAINTS:
- NO new analysis
- NO new claims beyond existing artifacts
- Only recompose and package existing outputs
- Preserve all evidence references
- Explicit about what's missing
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from kie.skills.base import Skill, SkillContext, SkillResult


class ClientPackSkill(Skill):
    """
    Packages existing skill outputs into a single client-ready deliverable.

    Provides consultant-ready Client Pack with:
    - Readiness gate (from client_readiness)
    - Executive narrative (from run_story or insight_brief)
    - Top insights (from insight_triage)
    - Client-safe talking points
    - Caveats and limitations
    - Evidence index with hashes

    Stage Scope: preview (only)
    Required Artifacts: None (graceful when missing)
    Produces: client_pack.md, client_pack.json (optional)
    """

    skill_id = "client_pack"
    description = "Package existing artifacts into a single client-ready deliverable"
    stage_scope = ["preview"]
    required_artifacts = []  # Graceful when missing
    produces_artifacts = ["client_pack.md", "client_pack.json"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Package client deliverables from existing artifacts.

        Args:
            context: Skill execution context with artifacts

        Returns:
            SkillResult with client pack paths and metadata
        """
        outputs_dir = context.project_root / "outputs"
        project_state_dir = context.project_root / "project_state"
        evidence_dir = project_state_dir / "evidence_ledger"

        # Load key artifacts
        client_readiness = self._load_client_readiness(outputs_dir)
        insight_triage = self._load_insight_triage(outputs_dir)
        insight_brief = self._load_insight_brief(outputs_dir)
        run_story = self._load_run_story(outputs_dir)
        trust_bundle = self._load_trust_bundle(project_state_dir)
        recovery_plan_exists = (project_state_dir / "recovery_plan.md").exists()

        # Get evidence
        artifact_hashes = self._get_artifact_hashes(
            context.evidence_ledger_id, evidence_dir
        )

        # Determine overall readiness
        overall_readiness = self._determine_readiness(
            client_readiness, recovery_plan_exists
        )

        is_client_ready = overall_readiness in ["CLIENT_READY", "CLIENT_READY_WITH_CAVEATS"]

        # Generate pack
        pack_markdown = self._generate_pack_markdown(
            overall_readiness=overall_readiness,
            client_readiness=client_readiness,
            insight_triage=insight_triage,
            insight_brief=insight_brief,
            run_story=run_story,
            trust_bundle=trust_bundle,
            recovery_plan_exists=recovery_plan_exists,
            artifact_hashes=artifact_hashes,
            ledger_id=context.evidence_ledger_id,
        )

        pack_json = self._generate_pack_json(
            overall_readiness=overall_readiness,
            client_readiness=client_readiness,
            insight_triage=insight_triage,
            insight_brief=insight_brief,
            run_story=run_story,
            artifact_hashes=artifact_hashes,
            ledger_id=context.evidence_ledger_id,
        )

        # Write outputs
        pack_md_path = outputs_dir / "client_pack.md"
        pack_json_path = outputs_dir / "client_pack.json"

        pack_md_path.write_text(pack_markdown)
        pack_json_path.write_text(json.dumps(pack_json, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "client_pack_markdown": str(pack_md_path),
                "client_pack_json": str(pack_json_path),
            },
            evidence={
                "overall_readiness": overall_readiness,
                "is_client_ready": is_client_ready,
                "artifacts_included": len([
                    x for x in [client_readiness, insight_triage, insight_brief, run_story]
                    if x
                ]),
                "evidence_index_count": len(artifact_hashes),
            },
        )

    def _load_client_readiness(self, outputs_dir: Path) -> dict[str, Any] | None:
        """Load client_readiness.json if available."""
        path = outputs_dir / "client_readiness.json"
        if not path.exists():
            return None

        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None

    def _load_insight_triage(self, outputs_dir: Path) -> dict[str, Any] | None:
        """Load insight_triage.json if available."""
        path = outputs_dir / "insight_triage.json"
        if not path.exists():
            return None

        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None

    def _load_insight_brief(self, outputs_dir: Path) -> str | None:
        """Load insight_brief.md if available."""
        path = outputs_dir / "insight_brief.md"
        if not path.exists():
            return None

        try:
            return path.read_text()
        except Exception:
            return None

    def _load_run_story(self, outputs_dir: Path) -> str | None:
        """Load run_story.md if available."""
        path = outputs_dir / "run_story.md"
        if not path.exists():
            return None

        try:
            return path.read_text()
        except Exception:
            return None

    def _load_trust_bundle(self, project_state_dir: Path) -> dict[str, Any] | None:
        """Load trust_bundle.json if available."""
        path = project_state_dir / "trust_bundle.json"
        if not path.exists():
            return None

        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None

    def _get_artifact_hashes(
        self, ledger_id: str | None, evidence_dir: Path
    ) -> dict[str, str]:
        """Get artifact hashes from evidence ledger."""
        if not ledger_id or not evidence_dir.exists():
            return {}

        ledger_path = evidence_dir / f"{ledger_id}.yaml"
        if not ledger_path.exists():
            return {}

        try:
            with open(ledger_path) as f:
                ledger_data = yaml.safe_load(f)

            hashes = {}
            for output in ledger_data.get("outputs", []):
                path = output.get("path", "")
                hash_val = output.get("hash", "")
                if path and hash_val:
                    # Store full path as key
                    hashes[path] = hash_val

            return hashes

        except Exception:
            return {}

    def _determine_readiness(
        self, client_readiness: dict[str, Any] | None, recovery_plan_exists: bool
    ) -> str:
        """Determine overall readiness for the pack."""
        if recovery_plan_exists:
            return "INTERNAL_ONLY"

        if not client_readiness:
            return "INTERNAL_ONLY"

        return client_readiness.get("overall_readiness", "INTERNAL_ONLY")

    def _generate_pack_markdown(
        self,
        overall_readiness: str,
        client_readiness: dict[str, Any] | None,
        insight_triage: dict[str, Any] | None,
        insight_brief: str | None,
        run_story: str | None,
        trust_bundle: dict[str, Any] | None,
        recovery_plan_exists: bool,
        artifact_hashes: dict[str, str],
        ledger_id: str | None,
    ) -> str:
        """Generate the client pack markdown."""
        lines = []

        # Title
        if overall_readiness == "INTERNAL_ONLY":
            lines.append("# Client Pack (NOT CLIENT READY)")
        else:
            lines.append("# Client Pack")

        lines.append("")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("")

        # 0. Readiness Gate
        lines.append("## 0. Readiness Gate")
        lines.append("")
        lines.append(f"**Overall Readiness**: {overall_readiness}")
        lines.append("")

        if ledger_id:
            lines.append(f"**Evidence Ledger**: `project_state/evidence_ledger/{ledger_id}.yaml`")
        if trust_bundle:
            lines.append("**Trust Bundle**: `project_state/trust_bundle.json`")
        lines.append("")

        if overall_readiness == "INTERNAL_ONLY":
            lines.append("### ⚠️ Why Not Client-Ready")
            lines.append("")

            if recovery_plan_exists:
                lines.append("- Recovery plan exists (WARN/BLOCK/FAIL condition)")
            elif not client_readiness:
                lines.append("- Client readiness assessment missing")
            elif client_readiness:
                lines.append(f"- {client_readiness.get('overall_reason', 'Unknown reason')}")

            lines.append("")

            # Next actions
            lines.append("### Next CLI Actions")
            lines.append("")
            if client_readiness and client_readiness.get("next_actions"):
                for action in client_readiness["next_actions"]:
                    lines.append(f"- `{action}`")
            else:
                lines.append("- `python3 -m kie.cli validate`")
                lines.append("- `python3 -m kie.cli build`")
            lines.append("")

        # 1. Executive Narrative
        lines.append("## 1. Executive Narrative")
        lines.append("")

        if run_story:
            # Extract narrative from run_story
            lines.append(self._extract_narrative(run_story))
        elif insight_brief:
            # Extract narrative from insight_brief
            lines.append(self._extract_narrative(insight_brief))
        else:
            lines.append("*Executive narrative not available - generate with `/build`*")

        lines.append("")

        # 2. Top Insights (Triage)
        lines.append("## 2. Top Insights")
        lines.append("")

        if insight_triage:
            top_insights = insight_triage.get("top_insights", [])
            if top_insights:
                for i, insight in enumerate(top_insights, 1):
                    lines.append(f"### {i}. {insight.get('title', 'Untitled')}")
                    lines.append("")
                    lines.append(f"**Confidence**: {insight.get('confidence', 'Unknown')}")
                    lines.append("")

                    # Evidence
                    evidence = insight.get("evidence", [])
                    if evidence:
                        lines.append("**Evidence**:")
                        for ev in evidence[:3]:  # First 3 pieces
                            ref = ev.get("reference", "")
                            lines.append(f"- {ref}")
                        lines.append("")

                    # Caveats
                    caveats = insight.get("caveats", [])
                    if caveats:
                        lines.append("**Caveats**:")
                        for caveat in caveats:
                            lines.append(f"- {caveat}")
                        lines.append("")
            else:
                lines.append("*No insights available from triage*")
                lines.append("")
        else:
            lines.append("*Insight triage not available - generate with `/analyze` and `/build`*")
            lines.append("")

        # 3. Client-Safe Talking Points
        lines.append("## 3. Client-Safe Talking Points")
        lines.append("")

        if client_readiness and overall_readiness != "INTERNAL_ONLY":
            narrative = client_readiness.get("approved_client_narrative", [])
            if narrative:
                for bullet in narrative:
                    lines.append(f"- {bullet}")
                lines.append("")
            else:
                lines.append("*No approved narrative available*")
                lines.append("")
        else:
            lines.append("*Not available - outputs are INTERNAL_ONLY*")
            lines.append("")

        # 4. Caveats & Limitations
        lines.append("## 4. Caveats & Limitations")
        lines.append("")

        caveats_found = False

        if client_readiness and overall_readiness == "CLIENT_READY_WITH_CAVEATS":
            classifications = client_readiness.get("artifact_classifications", [])
            for classification in classifications:
                artifact_caveats = classification.get("caveats", [])
                if artifact_caveats:
                    caveats_found = True
                    artifact_name = Path(classification["artifact"]).stem
                    lines.append(f"**{artifact_name}**:")
                    for caveat in artifact_caveats:
                        lines.append(f"- {caveat}")
                    lines.append("")

        if insight_triage:
            guidance = insight_triage.get("consultant_guidance", {})
            mention_cautiously = guidance.get("mention_cautiously", [])
            if mention_cautiously:
                caveats_found = True
                lines.append("**Mention Cautiously**:")
                for item in mention_cautiously:
                    lines.append(f"- {item}")
                lines.append("")

        if not caveats_found:
            if overall_readiness == "CLIENT_READY":
                lines.append("*No material caveats - outputs are fully client-ready*")
            else:
                lines.append("*No specific caveats identified*")
            lines.append("")

        # 5. Do Not Say
        lines.append("## 5. Do Not Say")
        lines.append("")

        if client_readiness:
            do_not_say = client_readiness.get("do_not_say", [])
            if do_not_say:
                for statement in do_not_say:
                    lines.append(f"- {statement}")
                lines.append("")
            else:
                lines.append("*No specific avoidance guidance*")
                lines.append("")
        else:
            lines.append("*Client readiness assessment not available*")
            lines.append("")

        # 6. Evidence Index
        lines.append("## 6. Evidence Index")
        lines.append("")

        if artifact_hashes:
            lines.append("| Artifact | Hash | Ledger ID |")
            lines.append("|----------|------|-----------|")

            for path, hash_val in sorted(artifact_hashes.items()):
                # Normalize path display
                display_path = path.replace("outputs/", "")
                short_hash = hash_val[:12] if len(hash_val) > 12 else hash_val
                lines.append(f"| `{display_path}` | `{short_hash}...` | `{ledger_id or 'N/A'}` |")

            lines.append("")
        else:
            lines.append("*No artifacts with evidence hashes available*")
            lines.append("")

        return "\n".join(lines)

    def _generate_pack_json(
        self,
        overall_readiness: str,
        client_readiness: dict[str, Any] | None,
        insight_triage: dict[str, Any] | None,
        insight_brief: str | None,
        run_story: str | None,
        artifact_hashes: dict[str, str],
        ledger_id: str | None,
    ) -> dict[str, Any]:
        """Generate the client pack JSON."""
        return {
            "generated_at": datetime.now().isoformat(),
            "ledger_id": ledger_id,
            "overall_readiness": overall_readiness,
            "is_client_ready": overall_readiness in ["CLIENT_READY", "CLIENT_READY_WITH_CAVEATS"],
            "artifacts_included": {
                "client_readiness": client_readiness is not None,
                "insight_triage": insight_triage is not None,
                "insight_brief": insight_brief is not None,
                "run_story": run_story is not None,
            },
            "evidence_index": [
                {
                    "artifact": path,
                    "hash": hash_val,
                    "ledger_id": ledger_id,
                }
                for path, hash_val in sorted(artifact_hashes.items())
            ],
        }

    def _extract_narrative(self, markdown_content: str) -> str:
        """Extract a narrative summary from markdown content."""
        # Simple extraction - take first few meaningful paragraphs
        lines = markdown_content.split("\n")

        narrative_lines = []
        in_content = False
        para_count = 0

        for line in lines:
            # Skip headers and metadata
            if line.startswith("#"):
                in_content = True
                continue

            if in_content and line.strip():
                # Skip lines that look like metadata
                if "Generated:" in line or "Ledger:" in line or "Stage:" in line:
                    continue

                narrative_lines.append(line.strip())
                if line.strip().endswith(".") or line.strip().endswith(":"):
                    para_count += 1

                # Stop after ~3 paragraphs
                if para_count >= 3:
                    break

        if narrative_lines:
            return "\n".join(narrative_lines[:5])  # Max 5 lines
        else:
            return "*Narrative extraction not available*"
