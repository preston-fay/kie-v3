"""
Client Readiness Filter Skill

WOW SKILL #2: Makes KIE "consultant-proof" by classifying output readiness.

Answers: "What is safe to show a client right now?"

Provides:
- Clear readiness labels (CLIENT_READY / CLIENT_READY_WITH_CAVEATS / INTERNAL_ONLY)
- Proof-backed reasons
- Exact caveats
- Approved talk-track (non-speculative)

CRITICAL CONSTRAINTS:
- NO new analysis
- NO inference beyond existing artifacts
- Every reason must cite evidence with hash
- Deterministic classification using contractual rules
- Missing evidence must be called out explicitly
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from kie.paths import ArtifactPaths
from kie.skills.base import Skill, SkillContext, SkillResult


class ReadinessLabel(str, Enum):
    """Ordinal readiness labels."""
    CLIENT_READY = "CLIENT_READY"
    CLIENT_READY_WITH_CAVEATS = "CLIENT_READY_WITH_CAVEATS"
    INTERNAL_ONLY = "INTERNAL_ONLY"


class ClientReadinessSkill(Skill):
    """
    Classifies deliverable artifacts by client readiness.

    Provides consultant-ready guidance on:
    - Which artifacts are safe to show clients
    - Which artifacts require caveats
    - Which artifacts are internal only
    - Approved client narrative
    - What to avoid saying

    Stage Scope: build, preview
    Required Artifacts: None (graceful when missing)
    Produces: client_readiness.md, client_readiness.json
    """

    skill_id = "client_readiness"
    description = "Classify deliverable artifacts by client readiness with evidence"
    stage_scope = ["build", "preview"]
    required_artifacts = []  # Graceful when missing
    produces_artifacts = ["client_readiness.md", "client_readiness.json"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Classify client readiness from existing artifacts.

        Args:
            context: Skill execution context with artifacts

        Returns:
            SkillResult with readiness classification and metadata
        """
        outputs_dir = context.project_root / "outputs"
        project_state_dir = context.project_root / "project_state"
        evidence_dir = project_state_dir / "evidence_ledger"

        # Load artifacts
        trust_bundle_path = project_state_dir / "trust_bundle.json"
        recovery_plan_path = project_state_dir / "recovery_plan.md"

        # Identify candidate artifacts
        candidate_artifacts = self._identify_candidates(outputs_dir)

        # Load evidence
        trust_bundle = self._load_trust_bundle(trust_bundle_path)
        recovery_plan_exists = recovery_plan_path.exists()
        artifact_hashes = self._get_artifact_hashes(
            context.evidence_ledger_id, evidence_dir
        )

        # Classify each candidate
        classifications = []
        for artifact_path in candidate_artifacts:
            classification = self._classify_artifact(
                artifact_path,
                trust_bundle,
                recovery_plan_exists,
                artifact_hashes,
                outputs_dir,
            )
            classifications.append(classification)

        # Determine overall readiness
        overall_readiness = self._determine_overall_readiness(classifications)

        # Generate outputs using centralized paths
        paths = ArtifactPaths(context.project_root)
        markdown_path = outputs_dir / "client_readiness.md"  # Keep MD in deliverables/
        json_path = paths.client_readiness_json(create_dirs=True)

        markdown_content = self._generate_markdown(
            overall_readiness,
            classifications,
            trust_bundle,
            recovery_plan_exists,
            context.evidence_ledger_id,
        )

        json_data = self._generate_json(
            overall_readiness,
            classifications,
            trust_bundle,
            recovery_plan_exists,
            context.evidence_ledger_id,
        )

        markdown_path.write_text(markdown_content)
        json_path.write_text(json.dumps(json_data, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "readiness_markdown": str(markdown_path),
                "readiness_json": str(json_path),
            },
            evidence={
                "overall_readiness": overall_readiness.value,
                "candidate_artifacts_count": len(candidate_artifacts),
                "client_ready_count": sum(
                    1 for c in classifications
                    if c["label"] == ReadinessLabel.CLIENT_READY
                ),
                "with_caveats_count": sum(
                    1 for c in classifications
                    if c["label"] == ReadinessLabel.CLIENT_READY_WITH_CAVEATS
                ),
                "internal_only_count": sum(
                    1 for c in classifications
                    if c["label"] == ReadinessLabel.INTERNAL_ONLY
                ),
            },
        )

    def _identify_candidates(self, outputs_dir: Path) -> list[Path]:
        """Identify deliverable candidate artifacts."""
        candidates = []

        # Check for known deliverable artifacts
        known_deliverables = [
            "insight_brief.md",
            "insight_brief.json",
            "run_story.md",
            "run_story.json",
            "insight_triage.md",
            "insight_triage.json",
        ]

        for deliverable in known_deliverables:
            path = outputs_dir / deliverable
            if path.exists():
                candidates.append(path)

        return candidates

    def _load_trust_bundle(self, trust_bundle_path: Path) -> dict[str, Any]:
        """Load trust bundle JSON."""
        if not trust_bundle_path.exists():
            return {}

        try:
            with open(trust_bundle_path) as f:
                return json.load(f)
        except Exception:
            return {}

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
                    # Normalize path
                    path_key = str(Path(path).name)
                    hashes[path_key] = hash_val

            return hashes

        except Exception:
            return {}

    def _classify_artifact(
        self,
        artifact_path: Path,
        trust_bundle: dict[str, Any],
        recovery_plan_exists: bool,
        artifact_hashes: dict[str, str],
        outputs_dir: Path,
    ) -> dict[str, Any]:
        """
        Classify a single artifact using deterministic rules.

        Returns:
            Classification dict with label, reasons, caveats, evidence
        """
        reasons = []
        caveats = []
        evidence = []

        artifact_name = artifact_path.name
        artifact_hash = artifact_hashes.get(artifact_name, "")

        # Rule 1: INTERNAL_ONLY conditions
        if recovery_plan_exists:
            reasons.append("Recovery plan exists for this run (WARN/BLOCK/FAIL)")
            label = ReadinessLabel.INTERNAL_ONLY
        elif not trust_bundle:
            reasons.append("Trust bundle missing - cannot verify evidence chain")
            label = ReadinessLabel.INTERNAL_ONLY
        elif not artifact_hash:
            reasons.append("Artifact lacks evidence hash reference")
            label = ReadinessLabel.INTERNAL_ONLY
        else:
            # Check trust bundle for missing critical items
            missing_items = trust_bundle.get("whats_missing", {}).get("items", [])
            critical_missing = [
                item for item in missing_items
                if item.get("severity") == "critical"
            ]

            if critical_missing:
                reasons.append(
                    f"Critical prerequisites missing: {len(critical_missing)} items"
                )
                label = ReadinessLabel.INTERNAL_ONLY
            else:
                # Not INTERNAL_ONLY - check for caveats
                label, artifact_reasons, artifact_caveats = self._check_caveats(
                    artifact_path, trust_bundle, outputs_dir
                )
                reasons.extend(artifact_reasons)
                caveats.extend(artifact_caveats)

        # Build evidence list
        if artifact_hash:
            evidence.append({
                "type": "artifact",
                "reference": str(artifact_path.relative_to(outputs_dir.parent)),
                "hash": artifact_hash,
            })

        if trust_bundle:
            run_id = trust_bundle.get("run_identity", {}).get("run_id", "")
            if run_id:
                evidence.append({
                    "type": "ledger",
                    "ledger_id": run_id,
                })

        return {
            "artifact": str(artifact_path.relative_to(outputs_dir.parent)),
            "label": label,
            "reasons": reasons,
            "caveats": caveats,
            "evidence": evidence,
        }

    def _check_caveats(
        self,
        artifact_path: Path,
        trust_bundle: dict[str, Any],
        outputs_dir: Path,
    ) -> tuple[ReadinessLabel, list[str], list[str]]:
        """
        Check for caveat conditions.

        Returns:
            Tuple of (label, reasons, caveats)
        """
        reasons = []
        caveats = []

        # Check if this is insight_triage artifact
        if "insight_triage" in artifact_path.name:
            triage_json_path = outputs_dir / "insight_triage.json"
            if triage_json_path.exists():
                try:
                    with open(triage_json_path) as f:
                        triage_data = json.load(f)

                    # Check confidence levels of top insights
                    top_insights = triage_data.get("top_insights", [])
                    non_high_confidence = [
                        ti for ti in top_insights
                        if ti.get("confidence") != "High"
                    ]

                    if non_high_confidence:
                        reasons.append(
                            f"Insight triage shows {len(non_high_confidence)} "
                            f"non-High confidence insights in top tier"
                        )
                        caveats.append(
                            "Some top insights have Medium or Low confidence - "
                            "present with appropriate hedging"
                        )

                    # Check for high misinterpretation risk
                    use_with_caution = triage_data.get("use_with_caution_insights", 0)
                    if use_with_caution > 0:
                        caveats.append(
                            f"{use_with_caution} insights flagged as 'use with caution' "
                            f"due to misinterpretation risk"
                        )

                except Exception:
                    pass

        # Check trust bundle warnings
        warnings_blocks = trust_bundle.get("warnings_blocks", {})
        warnings = warnings_blocks.get("warnings", [])
        if warnings:
            reasons.append(f"Trust bundle shows {len(warnings)} warnings")
            for warning in warnings[:3]:  # First 3 warnings
                caveats.append(warning)

        # Check for missing non-critical items
        missing_items = trust_bundle.get("whats_missing", {}).get("items", [])
        non_critical_missing = [
            item for item in missing_items
            if item.get("severity") != "critical"
        ]
        if non_critical_missing:
            reasons.append(
                f"Non-critical items missing: {len(non_critical_missing)}"
            )
            caveats.append(
                "Some supporting analysis incomplete - "
                "focus on high-confidence findings only"
            )

        # Determine label based on caveats
        if caveats:
            return ReadinessLabel.CLIENT_READY_WITH_CAVEATS, reasons, caveats
        else:
            reasons.append("Evidence ledger complete and no limitations detected")
            return ReadinessLabel.CLIENT_READY, reasons, caveats

    def _determine_overall_readiness(
        self, classifications: list[dict[str, Any]]
    ) -> ReadinessLabel:
        """Determine overall readiness from individual classifications."""
        if not classifications:
            return ReadinessLabel.INTERNAL_ONLY

        # If any INTERNAL_ONLY, overall is INTERNAL_ONLY
        if any(c["label"] == ReadinessLabel.INTERNAL_ONLY for c in classifications):
            return ReadinessLabel.INTERNAL_ONLY

        # If any WITH_CAVEATS, overall is WITH_CAVEATS
        if any(
            c["label"] == ReadinessLabel.CLIENT_READY_WITH_CAVEATS
            for c in classifications
        ):
            return ReadinessLabel.CLIENT_READY_WITH_CAVEATS

        # All CLIENT_READY
        return ReadinessLabel.CLIENT_READY

    def _generate_markdown(
        self,
        overall_readiness: ReadinessLabel,
        classifications: list[dict[str, Any]],
        trust_bundle: dict[str, Any],
        recovery_plan_exists: bool,
        ledger_id: str | None,
    ) -> str:
        """Generate markdown output."""
        lines = []

        lines.append("# Client Readiness")
        lines.append("")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("")

        # Executive Decision
        lines.append("## Executive Decision")
        lines.append("")
        lines.append(f"- **Overall Readiness**: {overall_readiness.value}")
        lines.append(f"- **Why**: {self._get_overall_reason(overall_readiness, classifications, recovery_plan_exists)}")
        lines.append("")

        # Artifact Decisions
        lines.append("## Artifact Decisions")
        lines.append("")

        if not classifications:
            lines.append("No candidate deliverables available.")
            lines.append("")
        else:
            for classification in classifications:
                lines.append(f"### {classification['artifact']}")
                lines.append("")
                lines.append(f"- **Label**: {classification['label'].value}")
                lines.append("")

                if classification["evidence"]:
                    lines.append("- **Evidence**:")
                    for ev in classification["evidence"]:
                        if ev["type"] == "artifact":
                            lines.append(f"  - Artifact: {ev['reference']}")
                            lines.append(f"    Hash: {ev['hash']}")
                        elif ev["type"] == "ledger":
                            lines.append(f"  - Ledger ID: {ev['ledger_id']}")
                    lines.append("")

                if classification["reasons"]:
                    lines.append("- **Reasons**:")
                    for reason in classification["reasons"]:
                        lines.append(f"  - {reason}")
                    lines.append("")

                if classification["caveats"]:
                    lines.append("- **Caveats**:")
                    for caveat in classification["caveats"]:
                        lines.append(f"  - {caveat}")
                    lines.append("")

        # Approved Client Narrative
        if overall_readiness != ReadinessLabel.INTERNAL_ONLY:
            lines.append("## Approved Client Narrative")
            lines.append("")
            narrative = self._generate_client_narrative(classifications, trust_bundle)
            for bullet in narrative:
                lines.append(f"- {bullet}")
            lines.append("")

        # Do Not Say
        lines.append("## Do Not Say")
        lines.append("")
        avoid_statements = self._generate_avoid_statements(
            overall_readiness, classifications, recovery_plan_exists
        )
        for statement in avoid_statements:
            lines.append(f"- {statement}")
        lines.append("")

        # Next Actions
        if overall_readiness != ReadinessLabel.CLIENT_READY:
            lines.append("## Next Actions to Reach CLIENT_READY")
            lines.append("")
            next_actions = self._generate_next_actions(
                trust_bundle, recovery_plan_exists
            )
            for action in next_actions:
                lines.append(f"- {action}")
            lines.append("")

        return "\n".join(lines)

    def _generate_json(
        self,
        overall_readiness: ReadinessLabel,
        classifications: list[dict[str, Any]],
        trust_bundle: dict[str, Any],
        recovery_plan_exists: bool,
        ledger_id: str | None,
    ) -> dict[str, Any]:
        """Generate JSON output."""
        return {
            "generated_at": datetime.now().isoformat(),
            "ledger_id": ledger_id,
            "overall_readiness": overall_readiness.value,
            "overall_reason": self._get_overall_reason(
                overall_readiness, classifications, recovery_plan_exists
            ),
            "artifact_classifications": classifications,
            "approved_client_narrative": (
                self._generate_client_narrative(classifications, trust_bundle)
                if overall_readiness != ReadinessLabel.INTERNAL_ONLY
                else []
            ),
            "do_not_say": self._generate_avoid_statements(
                overall_readiness, classifications, recovery_plan_exists
            ),
            "next_actions": (
                self._generate_next_actions(trust_bundle, recovery_plan_exists)
                if overall_readiness != ReadinessLabel.CLIENT_READY
                else []
            ),
        }

    def _get_overall_reason(
        self,
        overall_readiness: ReadinessLabel,
        classifications: list[dict[str, Any]],
        recovery_plan_exists: bool,
    ) -> str:
        """Get one-sentence reason for overall readiness."""
        if not classifications:
            return "No deliverable artifacts available for client presentation"

        if overall_readiness == ReadinessLabel.INTERNAL_ONLY:
            if recovery_plan_exists:
                return "Recovery plan exists - outputs require fixes before client presentation"
            return "Critical evidence or prerequisites missing - outputs not verified for client use"

        if overall_readiness == ReadinessLabel.CLIENT_READY_WITH_CAVEATS:
            return "Outputs are evidence-backed but contain limitations requiring explicit framing"

        return "All outputs have complete evidence chains and no material limitations"

    def _generate_client_narrative(
        self, classifications: list[dict[str, Any]], trust_bundle: dict[str, Any]
    ) -> list[str]:
        """Generate approved client narrative bullets."""
        narrative = []

        # Extract from insight triage if available
        for classification in classifications:
            if "insight_triage" in classification["artifact"]:
                artifact_path = Path(classification["artifact"])
                if artifact_path.exists():
                    try:
                        # Read the corresponding JSON
                        json_path = artifact_path.parent / "insight_triage.json"
                        if json_path.exists():
                            with open(json_path) as f:
                                triage_data = json.load(f)

                            # Get top insights with High confidence
                            top_insights = triage_data.get("top_insights", [])
                            high_confidence = [
                                ti for ti in top_insights
                                if ti.get("confidence") == "High"
                            ]

                            for insight in high_confidence[:3]:
                                narrative.append(
                                    f"{insight.get('title', 'Insight')} "
                                    f"(evidence: {len(insight.get('evidence', []))} artifacts)"
                                )
                    except Exception:
                        pass

        # Generic narrative if no specific insights
        if not narrative:
            narrative = [
                "Analysis complete with evidence-backed findings",
                "Key insights prioritized by decision relevance and evidence strength",
                "All claims linked to verified data artifacts",
            ]

        return narrative[:6]  # Max 6 bullets

    def _generate_avoid_statements(
        self,
        overall_readiness: ReadinessLabel,
        classifications: list[dict[str, Any]],
        recovery_plan_exists: bool,
    ) -> list[str]:
        """Generate statements to avoid."""
        avoid = []

        if recovery_plan_exists:
            avoid.append(
                "Do not present any outputs - recovery actions required first"
            )

        if overall_readiness == ReadinessLabel.CLIENT_READY_WITH_CAVEATS:
            avoid.append(
                "Do not claim 'high confidence' without explicitly stating confidence levels"
            )
            avoid.append(
                "Do not imply completeness if non-critical items are missing"
            )

        # Check for specific caveat patterns
        for classification in classifications:
            if classification["caveats"]:
                avoid.append(
                    f"Avoid leading with caveated insights from {Path(classification['artifact']).stem}"
                )

        # Generic avoidance statements
        avoid.extend([
            "Do not claim insights are 'statistical proof' - use 'statistically significant at p<0.05'",
            "Do not extrapolate beyond the data timeframe or scope analyzed",
            "Do not imply causation from correlation-based insights",
        ])

        return avoid[:8]  # Max 8 bullets

    def _generate_next_actions(
        self, trust_bundle: dict[str, Any], recovery_plan_exists: bool
    ) -> list[str]:
        """Generate next actions to reach CLIENT_READY."""
        actions = []

        if recovery_plan_exists:
            actions.append("Review and execute recovery plan")
            actions.append("python3 -m kie.cli doctor")

        # Check trust bundle for next CLI actions
        if trust_bundle:
            cli_actions = trust_bundle.get("next_cli_actions", [])
            actions.extend(cli_actions[:5])

        # Check for missing items
        missing_items = trust_bundle.get("whats_missing", {}).get("items", [])
        if missing_items:
            critical = [i for i in missing_items if i.get("severity") == "critical"]
            if critical:
                actions.append(
                    f"Address {len(critical)} critical missing prerequisites"
                )

        # Generic fallback
        if not actions:
            actions = [
                "python3 -m kie.cli validate",
                "Review trust bundle for missing items",
            ]

        return actions
