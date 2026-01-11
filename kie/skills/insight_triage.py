"""
Insight Triage Skill

WOW SKILL #1: Upgrades consultant judgment with opinionated, evidence-backed triage.

Helps consultants immediately understand:
- What insights matter most
- Why they matter
- How confident they should be
- What to ignore or de-prioritize

CRITICAL CONSTRAINTS:
- NO new analysis
- NO inference beyond existing artifacts
- Every claim must cite evidence with hash
- Opinionated scoring using deterministic logic
- Missing evidence must be called out explicitly
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from kie.insights import InsightCatalog, Insight
from kie.skills.base import Skill, SkillContext, SkillResult


class ConfidenceLevel(str, Enum):
    """Ordinal confidence levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TriageScore(str, Enum):
    """Ordinal triage scores."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class InsightTriageSkill(Skill):
    """
    Triages insights using opinionated, evidence-backed scoring.

    Provides consultant-ready guidance on:
    - Which insights to lead with
    - Which insights to mention cautiously
    - Which insights to avoid leading with

    Stage Scope: analyze, build, preview
    Required Artifacts: insights_catalog.json
    Produces: insight_triage.md, insight_triage.json
    """

    skill_id = "insight_triage"
    description = "Triage insights by decision relevance, evidence strength, and risk"
    stage_scope = ["analyze", "build", "preview"]
    required_artifacts = ["insights_catalog"]
    produces_artifacts = ["insight_triage.md", "insight_triage.json"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Triage insights from existing artifacts.

        Args:
            context: Skill execution context with artifacts

        Returns:
            SkillResult with triage paths and metadata
        """
        outputs_dir = context.project_root / "outputs"
        evidence_dir = context.project_root / "project_state" / "evidence_ledger"

        # Load artifacts - check both JSON and YAML formats
        insights_catalog_json = outputs_dir / "insights_catalog.json"
        insights_catalog_yaml = outputs_dir / "insights.yaml"

        if insights_catalog_json.exists():
            # Load JSON format
            with open(insights_catalog_json) as f:
                catalog_data = json.load(f)
            catalog = InsightCatalog.from_dict(catalog_data)
        elif insights_catalog_yaml.exists():
            # Load YAML format
            catalog = InsightCatalog.load(str(insights_catalog_yaml))
            # Also save as JSON for consistency
            catalog_data = catalog.to_dict()
            insights_catalog_json.write_text(json.dumps(catalog_data, indent=2))
        else:
            # Graceful failure - produce valid artifact stating no insights
            return self._handle_no_insights(outputs_dir)

        # Get artifact hashes from evidence ledger
        artifact_hashes = self._get_artifact_hashes(
            context.evidence_ledger_id, evidence_dir
        )

        # Handle empty catalog
        if not catalog.insights:
            return self._handle_no_insights(outputs_dir)

        # Triage insights using strict logic
        triage_result = self._triage_insights(catalog, artifact_hashes)

        # Generate markdown output
        markdown_content = self._generate_markdown(triage_result)
        markdown_path = outputs_dir / "insight_triage.md"
        markdown_path.write_text(markdown_content)

        # Generate JSON output
        json_path = outputs_dir / "insight_triage.json"
        json_path.write_text(json.dumps(triage_result, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "triage_markdown": str(markdown_path),
                "triage_json": str(json_path),
            },
            evidence={
                "total_candidate_insights": triage_result["total_candidate_insights"],
                "high_confidence_insights": triage_result["high_confidence_insights"],
                "top_insights_count": len(triage_result["top_insights"]),
                "evidence_backed": True,
            },
            metadata={
                "catalog_generated_at": catalog.generated_at,
                "triage_generated_at": datetime.now().isoformat(),
            }
        )

    def _handle_no_insights(self, outputs_dir: Path) -> SkillResult:
        """Handle case where no insights are available."""
        markdown_content = """# Insight Triage

## Executive Snapshot
- Total candidate insights: 0
- High-confidence insights: 0
- Use-with-caution insights: 0

## Status
**No insights available for triage.**

This may indicate:
- Analysis has not been run yet (try `/analyze`)
- Data does not contain sufficient variance for insights
- Insights catalog generation failed

## Consultant Guidance
- Lead with: None available
- Mention cautiously: None available
- Avoid leading with: None available

---

*Generated: {}*
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        markdown_path = outputs_dir / "insight_triage.md"
        markdown_path.write_text(markdown_content)

        json_data = {
            "total_candidate_insights": 0,
            "high_confidence_insights": 0,
            "use_with_caution_insights": 0,
            "top_insights": [],
            "deprioritized_insights": [],
            "consultant_guidance": {
                "lead_with": [],
                "mention_cautiously": [],
                "avoid_leading_with": []
            }
        }

        json_path = outputs_dir / "insight_triage.json"
        json_path.write_text(json.dumps(json_data, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "triage_markdown": str(markdown_path),
                "triage_json": str(json_path),
            },
            warnings=["No insights available for triage"],
            evidence={
                "total_candidate_insights": 0,
                "high_confidence_insights": 0,
                "evidence_backed": True,
            }
        )

    def _get_artifact_hashes(
        self, evidence_ledger_id: str | None, evidence_dir: Path
    ) -> dict[str, str]:
        """Get artifact hashes from evidence ledger."""
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

    def _triage_insights(
        self, catalog: InsightCatalog, artifact_hashes: dict[str, str]
    ) -> dict[str, Any]:
        """
        Triage insights using strict scoring logic.

        Scores each insight on:
        1. Decision relevance (Does this change what a client might do?)
        2. Evidence strength (Data completeness, artifact support)
        3. Risk of misinterpretation (Could this be misleading?)

        Returns:
            Triage result dictionary
        """
        # Score all insights
        scored_insights = []
        for insight in catalog.insights:
            score = self._score_insight(insight)
            scored_insights.append({
                "insight": insight,
                "score": score,
            })

        # Sort by composite score (decision relevance primary, evidence strength secondary)
        scored_insights.sort(
            key=lambda x: (
                self._score_to_numeric(x["score"]["decision_relevance"]),
                self._score_to_numeric(x["score"]["evidence_strength"]),
                -self._score_to_numeric(x["score"]["misinterpretation_risk"]),
            ),
            reverse=True
        )

        # Select top 3 (or fewer if evidence is weak)
        top_insights = []
        deprioritized_insights = []

        for item in scored_insights:
            insight = item["insight"]
            score = item["score"]

            # Only promote to "top" if evidence is at least Medium
            if (len(top_insights) < 3 and
                score["evidence_strength"] in [TriageScore.HIGH, TriageScore.MEDIUM]):

                # Calculate confidence level
                confidence = self._calculate_confidence(insight, score)

                # Build evidence references
                evidence_refs = self._build_evidence_references(
                    insight, artifact_hashes
                )

                # Build caveats
                caveats = self._build_caveats(insight, score)

                top_insights.append({
                    "title": insight.headline,
                    "why_it_matters": self._explain_decision_relevance(insight),
                    "evidence": evidence_refs,
                    "confidence": confidence.value,
                    "caveats": caveats,
                    "score": score,
                })
            else:
                # Deprioritize
                reason = self._explain_deprioritization(score)
                deprioritized_insights.append({
                    "insight": insight.headline,
                    "reason": reason,
                })

        # Build consultant guidance
        guidance = self._build_consultant_guidance(
            top_insights, deprioritized_insights, scored_insights
        )

        # Count high-confidence insights
        high_confidence_count = sum(
            1 for ti in top_insights if ti["confidence"] == ConfidenceLevel.HIGH.value
        )

        # Count use-with-caution insights
        use_with_caution_count = sum(
            1 for ti in top_insights if ti["confidence"] == ConfidenceLevel.LOW.value
        )

        return {
            "total_candidate_insights": len(catalog.insights),
            "high_confidence_insights": high_confidence_count,
            "use_with_caution_insights": use_with_caution_count,
            "top_insights": top_insights,
            "deprioritized_insights": deprioritized_insights,
            "consultant_guidance": guidance,
        }

    def _score_insight(self, insight: Insight) -> dict[str, TriageScore]:
        """
        Score an insight on three dimensions.

        Returns:
            Dictionary with ordinal scores
        """
        # 1. Decision relevance
        decision_relevance = self._score_decision_relevance(insight)

        # 2. Evidence strength
        evidence_strength = self._score_evidence_strength(insight)

        # 3. Misinterpretation risk
        misinterpretation_risk = self._score_misinterpretation_risk(insight)

        return {
            "decision_relevance": decision_relevance,
            "evidence_strength": evidence_strength,
            "misinterpretation_risk": misinterpretation_risk,
        }

    def _score_decision_relevance(self, insight: Insight) -> TriageScore:
        """Score decision relevance based on insight category and content."""
        from kie.insights import InsightCategory, InsightSeverity

        # Recommendations are inherently decision-relevant
        if insight.category == InsightCategory.RECOMMENDATION:
            return TriageScore.HIGH

        # Implications suggest decisions
        if insight.category == InsightCategory.IMPLICATION:
            return TriageScore.HIGH

        # Key insights are flagged as important
        if insight.severity == InsightSeverity.KEY:
            return TriageScore.HIGH

        # Findings with strong statistical significance
        if (insight.category == InsightCategory.FINDING and
            insight.is_statistically_significant and
            insight.statistical_significance is not None and
            insight.statistical_significance < 0.01):
            return TriageScore.HIGH

        # Other findings
        if insight.category == InsightCategory.FINDING:
            return TriageScore.MEDIUM

        # Trends and correlations (insight types)
        if insight.insight_type.value in ["trend", "correlation"]:
            return TriageScore.MEDIUM

        # Other insight types are descriptive
        return TriageScore.LOW

    def _score_evidence_strength(self, insight: Insight) -> TriageScore:
        """Score evidence strength based on confidence and evidence count."""
        # High confidence with multiple evidence points
        if insight.confidence >= 0.8 and len(insight.evidence) >= 2:
            return TriageScore.HIGH

        # Medium confidence with some evidence
        if insight.confidence >= 0.6 and len(insight.evidence) >= 1:
            return TriageScore.MEDIUM

        # Low confidence or no evidence
        return TriageScore.LOW

    def _score_misinterpretation_risk(self, insight: Insight) -> TriageScore:
        """Score risk of misinterpretation."""
        # High risk if not statistically significant
        if (insight.statistical_significance is not None and
            not insight.is_statistically_significant):
            return TriageScore.HIGH

        # High risk if low confidence
        if insight.confidence < 0.6:
            return TriageScore.HIGH

        # Medium risk if no statistical test performed
        if insight.statistical_significance is None:
            return TriageScore.MEDIUM

        # Low risk otherwise
        return TriageScore.LOW

    def _score_to_numeric(self, score: TriageScore) -> int:
        """Convert ordinal score to numeric for sorting."""
        mapping = {
            TriageScore.HIGH: 3,
            TriageScore.MEDIUM: 2,
            TriageScore.LOW: 1,
        }
        return mapping[score]

    def _calculate_confidence(
        self, insight: Insight, score: dict[str, TriageScore]
    ) -> ConfidenceLevel:
        """Calculate overall confidence level."""
        # High confidence only if strong evidence and low misinterpretation risk
        if (score["evidence_strength"] == TriageScore.HIGH and
            score["misinterpretation_risk"] == TriageScore.LOW):
            return ConfidenceLevel.HIGH

        # Low confidence if weak evidence or high risk
        if (score["evidence_strength"] == TriageScore.LOW or
            score["misinterpretation_risk"] == TriageScore.HIGH):
            return ConfidenceLevel.LOW

        # Medium otherwise
        return ConfidenceLevel.MEDIUM

    def _build_evidence_references(
        self, insight: Insight, artifact_hashes: dict[str, str]
    ) -> list[dict[str, str]]:
        """Build evidence references with artifact paths and hashes."""
        references = []

        for evidence in insight.evidence:
            ref = {
                "type": evidence.evidence_type,
                "reference": evidence.reference,
            }

            # Add hash if available
            if evidence.reference in artifact_hashes:
                ref["hash"] = artifact_hashes[evidence.reference][:16] + "..."

            references.append(ref)

        # Always include insights_catalog as evidence source
        catalog_path = "outputs/insights_catalog.json"
        if catalog_path not in [r["reference"] for r in references]:
            ref = {
                "type": "catalog",
                "reference": catalog_path,
            }
            if catalog_path in artifact_hashes:
                ref["hash"] = artifact_hashes[catalog_path][:16] + "..."
            references.append(ref)

        return references

    def _build_caveats(
        self, insight: Insight, score: dict[str, TriageScore]
    ) -> list[str]:
        """Build explicit caveats for the insight."""
        caveats = []

        # Statistical significance caveat
        if not insight.is_statistically_significant:
            if insight.statistical_significance is not None:
                caveats.append(
                    f"Not statistically significant (p={insight.statistical_significance:.4f})"
                )
            else:
                caveats.append("Statistical significance not assessed")

        # Low confidence caveat
        if insight.confidence < 0.7:
            caveats.append(f"Moderate confidence ({insight.confidence:.0%})")

        # Weak evidence caveat
        if score["evidence_strength"] == TriageScore.LOW:
            caveats.append("Limited supporting evidence")

        # High misinterpretation risk caveat
        if score["misinterpretation_risk"] == TriageScore.HIGH:
            caveats.append("Requires careful interpretation")

        return caveats

    def _explain_decision_relevance(self, insight: Insight) -> str:
        """Explain why this insight matters for decisions."""
        # Use supporting text as primary explanation
        return insight.supporting_text

    def _explain_deprioritization(self, score: dict[str, TriageScore]) -> str:
        """Explain why an insight was deprioritized."""
        # Primary reason: weak evidence
        if score["evidence_strength"] == TriageScore.LOW:
            return "Weak evidence"

        # Secondary reason: high misinterpretation risk
        if score["misinterpretation_risk"] == TriageScore.HIGH:
            return "High risk of misinterpretation"

        # Tertiary reason: low decision relevance
        if score["decision_relevance"] == TriageScore.LOW:
            return "Low decision impact"

        # Default: redundancy or lower priority
        return "Lower priority relative to top insights"

    def _build_consultant_guidance(
        self,
        top_insights: list[dict],
        deprioritized_insights: list[dict],
        all_scored: list[dict],
    ) -> dict[str, list[str]]:
        """Build consultant guidance based on triage results."""
        lead_with = []
        mention_cautiously = []
        avoid_leading_with = []

        # Top insights with high confidence -> lead with
        for ti in top_insights:
            if ti["confidence"] == ConfidenceLevel.HIGH.value:
                lead_with.append(ti["title"])
            elif ti["confidence"] == ConfidenceLevel.MEDIUM.value:
                mention_cautiously.append(ti["title"])
            else:
                mention_cautiously.append(ti["title"])

        # Deprioritized insights -> avoid leading with
        for di in deprioritized_insights:
            avoid_leading_with.append(di["insight"])

        return {
            "lead_with": lead_with,
            "mention_cautiously": mention_cautiously,
            "avoid_leading_with": avoid_leading_with,
        }

    def _generate_markdown(self, triage_result: dict[str, Any]) -> str:
        """Generate markdown output from triage result."""
        lines = []

        # Header
        lines.append("# Insight Triage")
        lines.append("")

        # Executive Snapshot
        lines.append("## Executive Snapshot")
        lines.append(f"- Total candidate insights: {triage_result['total_candidate_insights']}")
        lines.append(f"- High-confidence insights: {triage_result['high_confidence_insights']}")
        lines.append(f"- Use-with-caution insights: {triage_result['use_with_caution_insights']}")
        lines.append("")

        # Top Insights
        lines.append("## Top Insights")
        lines.append("")

        if triage_result["top_insights"]:
            for i, ti in enumerate(triage_result["top_insights"], 1):
                lines.append(f"### {i}. {ti['title']}")
                lines.append("")
                lines.append("**Why it matters:**")
                lines.append(ti["why_it_matters"])
                lines.append("")

                lines.append("**Evidence:**")
                for ev in ti["evidence"]:
                    ev_line = f"- {ev['type']}: {ev['reference']}"
                    if "hash" in ev:
                        ev_line += f" (hash: {ev['hash']})"
                    lines.append(ev_line)
                lines.append("")

                lines.append(f"**Confidence:** {ti['confidence']}")
                lines.append("")

                if ti["caveats"]:
                    lines.append("**Caveats:**")
                    for caveat in ti["caveats"]:
                        lines.append(f"- {caveat}")
                    lines.append("")

                lines.append("---")
                lines.append("")
        else:
            lines.append("*No insights met triage criteria for top-tier promotion.*")
            lines.append("")

        # Deprioritized Insights
        lines.append("## Deprioritized Insights")
        lines.append("")

        if triage_result["deprioritized_insights"]:
            for di in triage_result["deprioritized_insights"]:
                lines.append(f"- **{di['insight']}** — {di['reason']}")
            lines.append("")
        else:
            lines.append("*None*")
            lines.append("")

        # Consultant Guidance
        lines.append("## Consultant Guidance")
        lines.append("")

        guidance = triage_result["consultant_guidance"]

        lines.append("**Lead with:**")
        if guidance["lead_with"]:
            for item in guidance["lead_with"]:
                lines.append(f"- {item}")
        else:
            lines.append("- *None available*")
        lines.append("")

        lines.append("**Mention cautiously:**")
        if guidance["mention_cautiously"]:
            for item in guidance["mention_cautiously"]:
                lines.append(f"- {item}")
        else:
            lines.append("- *None*")
        lines.append("")

        lines.append("**Avoid leading with:**")
        if guidance["avoid_leading_with"]:
            for item in guidance["avoid_leading_with"]:
                lines.append(f"- {item}")
        else:
            lines.append("- *None*")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")

        return "\n".join(lines)
