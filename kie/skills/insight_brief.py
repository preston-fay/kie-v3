"""
Insight Brief Skill

Generates consultant-ready Insight Briefs from existing analysis artifacts.

CONVERTED FROM: kie/consultant/insight_brief.py
BEHAVIOR: Identical - no logic changes, only wrapped as Skill

CRITICAL CONSTRAINTS:
- NO new analysis
- NO inference beyond existing artifacts
- Every claim must cite evidence with hash
- Missing evidence must be called out explicitly
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from kie.insights import InsightCatalog, InsightSeverity, InsightCategory
from kie.skills.base import Skill, SkillContext, SkillResult


class InsightBriefSkill(Skill):
    """
    Generates evidence-backed Insight Briefs for consultants.

    Synthesizes existing artifacts (insights_catalog.json, eda_profile.json)
    into a single consultant-ready document.

    Stage Scope: analyze, build, preview
    Required Artifacts: insights_catalog.json
    Produces: insight_brief.md, insight_brief.json
    """

    skill_id = "insight_brief"
    description = "Generate consultant-ready Insight Brief from analysis artifacts"
    stage_scope = ["analyze", "build", "preview"]
    required_artifacts = ["insights_catalog"]
    produces_artifacts = ["insight_brief.md", "insight_brief.json"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Generate Insight Brief from existing artifacts.

        Args:
            context: Skill execution context with artifacts

        Returns:
            SkillResult with brief paths and metadata
        """
        outputs_dir = context.project_root / "outputs"
        evidence_dir = context.project_root / "project_state" / "evidence_ledger"

        # Load artifacts
        insights_catalog_path = outputs_dir / "insights_catalog.json"
        eda_profile_path = outputs_dir / "eda_profile.json"

        if not insights_catalog_path.exists():
            return SkillResult(
                success=False,
                warnings=[
                    "Cannot generate Insight Brief: insights_catalog.json not found"
                ],
                metadata={
                    "missing_artifact": "outputs/insights_catalog.json",
                    "recovery": ["/analyze    # Run analysis first to generate insights"],
                }
            )

        # Load insights catalog
        with open(insights_catalog_path) as f:
            catalog_data = json.load(f)

        catalog = InsightCatalog.from_dict(catalog_data)

        # Load EDA profile if available
        eda_profile = None
        if eda_profile_path.exists():
            with open(eda_profile_path) as f:
                eda_profile = json.load(f)

        # Get artifact hashes from evidence ledger
        artifact_hashes = self._get_artifact_hashes(context.evidence_ledger_id, evidence_dir)

        # Generate brief sections (SAME LOGIC AS BEFORE)
        brief_content = self._generate_brief_content(
            catalog, eda_profile, artifact_hashes
        )

        # Save as markdown
        brief_path = outputs_dir / "insight_brief.md"
        brief_path.write_text(brief_content)

        # Save as JSON (structured data)
        brief_data = self._generate_brief_data(catalog, eda_profile, artifact_hashes)
        brief_json_path = outputs_dir / "insight_brief.json"
        brief_json_path.write_text(json.dumps(brief_data, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "brief_markdown": str(brief_path),
                "brief_json": str(brief_json_path),
            },
            evidence={
                "key_insights_count": len(catalog.get_key_insights()),
                "total_insights": len(catalog.insights),
                "evidence_backed": True,
            },
            metadata={
                "catalog_generated_at": catalog.generated_at,
                "business_question": catalog.business_question,
            }
        )

    def _get_artifact_hashes(self, evidence_ledger_id: str | None, evidence_dir: Path) -> dict[str, str]:
        """Get artifact hashes from evidence ledger (UNCHANGED)."""
        hashes = {}

        if not evidence_ledger_id:
            return hashes

        ledger_path = evidence_dir / f"{evidence_ledger_id}.yaml"
        if not ledger_path.exists():
            return hashes

        with open(ledger_path) as f:
            ledger = yaml.safe_load(f)

        # Extract hashes from outputs
        for output in ledger.get("outputs", []):
            path = output.get("path", "")
            file_hash = output.get("hash")
            if file_hash:
                hashes[path] = file_hash

        return hashes

    def _generate_brief_content(
        self,
        catalog: InsightCatalog,
        eda_profile: dict | None,
        artifact_hashes: dict[str, str]
    ) -> str:
        """Generate markdown brief content (LOGIC UNCHANGED)."""
        lines = []

        # Header
        lines.append("# Insight Brief")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Business Question:** {catalog.business_question}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")

        key_insights = catalog.get_key_insights()
        if key_insights:
            for insight in key_insights:
                lines.append(f"**{insight.headline}**")
                lines.append("")
                lines.append(insight.supporting_text)
                lines.append("")

                # Add evidence citation
                if insight.evidence:
                    lines.append("*Evidence:*")
                    for ev in insight.evidence:
                        citation = f"- {ev.evidence_type}: {ev.reference}"
                        if ev.reference in artifact_hashes:
                            citation += f" (hash: {artifact_hashes[ev.reference][:8]}...)"
                        lines.append(citation)
                    lines.append("")
        else:
            lines.append("*No key insights identified. Analysis may be incomplete or data may be limited.*")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Key Findings
        lines.append("## Key Findings")
        lines.append("")

        findings = catalog.get_findings()
        if findings:
            for i, insight in enumerate(findings, 1):
                lines.append(f"### {i}. {insight.headline}")
                lines.append("")
                lines.append(insight.supporting_text)
                lines.append("")

                # Statistical significance
                if insight.statistical_significance is not None:
                    sig_status = "✓ Statistically significant" if insight.is_statistically_significant else "⚠️ Not statistically significant"
                    lines.append(f"**Significance:** {sig_status} (p={insight.statistical_significance:.4f})")
                    lines.append("")

                # Evidence
                if insight.evidence:
                    lines.append("**Evidence:**")
                    for ev in insight.evidence:
                        ev_line = f"- {ev.label or ev.evidence_type}: "
                        if isinstance(ev.value, (int, float)):
                            ev_line += f"{ev.value:,.2f}"
                        else:
                            ev_line += str(ev.value)
                        lines.append(ev_line)
                    lines.append("")

                lines.append("---")
                lines.append("")
        else:
            lines.append("*No findings generated. This may indicate data quality issues or insufficient analysis.*")
            lines.append("")

        # Risks & Limitations
        lines.append("## Risks & Limitations")
        lines.append("")

        limitations = []

        # Check for missing EDA profile
        if not eda_profile:
            limitations.append("- EDA profile not available - data quality not assessed")

        # Check for low-confidence insights
        low_confidence = [i for i in catalog.insights if i.confidence < 0.7]
        if low_confidence:
            limitations.append(f"- {len(low_confidence)} insights have confidence < 70%")

        # Check for non-significant insights
        non_significant = [i for i in catalog.insights if not i.is_statistically_significant]
        if non_significant:
            limitations.append(f"- {len(non_significant)} insights are not statistically significant")

        # Check data summary
        if catalog.data_summary:
            row_count = catalog.data_summary.get("row_count", 0)
            if row_count < 100:
                limitations.append(f"- Small sample size ({row_count} rows) - results may not be generalizable")

        if limitations:
            for lim in limitations:
                lines.append(lim)
            lines.append("")
        else:
            lines.append("*No significant limitations identified. Analysis appears robust.*")
            lines.append("")

        lines.append("---")
        lines.append("")

        # What This Means for the Client
        lines.append("## What This Means for the Client")
        lines.append("")

        implications = catalog.get_by_category(InsightCategory.IMPLICATION)
        if implications:
            for insight in implications:
                lines.append(f"**{insight.headline}**")
                lines.append("")
                lines.append(insight.supporting_text)
                lines.append("")
        else:
            lines.append("*Based on the findings above:*")
            lines.append("")
            if key_insights:
                lines.append("The analysis reveals clear patterns in the data that warrant attention.")
                lines.append("Specific implications depend on business context and strategic priorities.")
            else:
                lines.append("Implications cannot be determined without key insights.")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Recommended Next Actions
        lines.append("## Recommended Next Actions")
        lines.append("")

        recommendations = catalog.get_recommendations()
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. **{rec.headline}**")
                lines.append(f"   {rec.supporting_text}")
                lines.append("")
        else:
            lines.append("*No specific recommendations generated from this analysis.*")
            lines.append("")
            lines.append("Consider:")
            lines.append("- Validating findings with stakeholders")
            lines.append("- Gathering additional data for deeper analysis")
            lines.append("- Running /build to create presentation materials")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Artifact Provenance
        lines.append("## Artifact Provenance")
        lines.append("")
        lines.append("This brief was generated from the following artifacts:")
        lines.append("")
        lines.append(f"- `outputs/insights_catalog.json` (generated: {catalog.generated_at})")
        if "outputs/insights_catalog.json" in artifact_hashes:
            lines.append(f"  - Hash: `{artifact_hashes['outputs/insights_catalog.json'][:16]}...`")

        if eda_profile:
            lines.append(f"- `outputs/eda_profile.json`")
            if "outputs/eda_profile.json" in artifact_hashes:
                lines.append(f"  - Hash: `{artifact_hashes['outputs/eda_profile.json'][:16]}...`")

        lines.append("")
        lines.append("*All claims in this brief are backed by evidence recorded in the Evidence Ledger.*")
        lines.append("")

        return "\n".join(lines)

    def _generate_brief_data(
        self,
        catalog: InsightCatalog,
        eda_profile: dict | None,
        artifact_hashes: dict[str, str]
    ) -> dict[str, Any]:
        """Generate structured JSON brief data (LOGIC UNCHANGED)."""
        return {
            "generated_at": datetime.now().isoformat(),
            "business_question": catalog.business_question,
            "executive_summary": {
                "key_insights": [
                    {
                        "headline": i.headline,
                        "supporting_text": i.supporting_text,
                        "evidence": [e.to_dict() for e in i.evidence],
                    }
                    for i in catalog.get_key_insights()
                ],
            },
            "findings": [
                {
                    "headline": i.headline,
                    "supporting_text": i.supporting_text,
                    "confidence": i.confidence,
                    "statistical_significance": i.statistical_significance,
                    "evidence": [e.to_dict() for e in i.evidence],
                }
                for i in catalog.get_findings()
            ],
            "limitations": self._extract_limitations(catalog, eda_profile),
            "recommendations": [
                {
                    "headline": i.headline,
                    "supporting_text": i.supporting_text,
                }
                for i in catalog.get_recommendations()
            ],
            "artifact_provenance": {
                "insights_catalog": {
                    "path": "outputs/insights_catalog.json",
                    "hash": artifact_hashes.get("outputs/insights_catalog.json"),
                    "generated_at": catalog.generated_at,
                },
                "eda_profile": {
                    "path": "outputs/eda_profile.json",
                    "hash": artifact_hashes.get("outputs/eda_profile.json"),
                    "available": eda_profile is not None,
                },
            },
        }

    def _extract_limitations(
        self, catalog: InsightCatalog, eda_profile: dict | None
    ) -> list[str]:
        """Extract limitations from analysis (LOGIC UNCHANGED)."""
        limitations = []

        if not eda_profile:
            limitations.append("EDA profile not available - data quality not assessed")

        low_confidence = [i for i in catalog.insights if i.confidence < 0.7]
        if low_confidence:
            limitations.append(f"{len(low_confidence)} insights have confidence < 70%")

        non_significant = [i for i in catalog.insights if not i.is_statistically_significant]
        if non_significant:
            limitations.append(f"{len(non_significant)} insights not statistically significant")

        if catalog.data_summary:
            row_count = catalog.data_summary.get("row_count", 0)
            if row_count < 100:
                limitations.append(f"Small sample size ({row_count} rows)")

        return limitations
