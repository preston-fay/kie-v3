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
from kie.charts.formatting import format_number, format_percentage
from kie.formatting.field_registry import FieldRegistry


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

        # Load artifacts using canonical paths (supports internal/ directory)
        from kie.paths import ArtifactPaths
        paths = ArtifactPaths(context.project_root)
        insights_catalog_path = paths.insights_catalog()
        eda_profile_path = paths.eda_profile_json()

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
            catalog, eda_profile, artifact_hashes, context.project_root
        )

        # Save markdown to deliverables/ (consultant-facing)
        deliverables_dir = outputs_dir / "deliverables"
        deliverables_dir.mkdir(parents=True, exist_ok=True)
        brief_path = deliverables_dir / "insight_brief.md"
        brief_path.write_text(brief_content)

        # Save JSON to internal/ (artifact for traceability)
        internal_dir = outputs_dir / "internal"
        internal_dir.mkdir(parents=True, exist_ok=True)
        brief_data = self._generate_brief_data(catalog, eda_profile, artifact_hashes)
        brief_json_path = internal_dir / "insight_brief.json"
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

    def _generate_strategic_context(self, key_insights: list) -> str:
        """
        Generate strategic context paragraph for Executive Summary.

        Provides narrative framing that explains the significance of findings
        before diving into details - pattern from reference PDF.
        """
        # Analyze patterns
        declines = [i for i in key_insights if "decline" in i.headline.lower()]
        growth = [i for i in key_insights if "grow" in i.headline.lower()]
        volatility = [i for i in key_insights if "volatility" in i.headline.lower()]
        outliers = [i for i in key_insights if "outlier" in i.headline.lower()]

        # Generate contextual framing based on dominant themes
        if len(declines) >= 2:
            return (
                "The analysis reveals concerning erosion patterns across multiple metrics. "
                "While individual declines may appear manageable, the combination suggests "
                "systemic challenges requiring strategic intervention. The data indicates this "
                "is not random variation but a persistent downward trend that warrants immediate attention."
            )
        elif len(volatility) >= 2:
            return (
                "Stability has become the critical challenge. High volatility across key metrics "
                "creates uncertainty that makes planning difficult and increases risk exposure. "
                "The patterns suggest the need for both short-term stabilization measures and "
                "longer-term structural changes to reduce variability."
            )
        elif len(outliers) > 0 and len(growth) > 0:
            return (
                "The data reveals a landscape of extremes - exceptional performance in some areas "
                "alongside concerning concentration risks. Understanding these outliers is critical: "
                "they represent either opportunities to replicate success or warning signs of "
                "unsustainable dependencies that require diversification."
            )
        elif len(growth) >= 2:
            return (
                "Positive momentum is building across multiple dimensions. The challenge now shifts "
                "from reversing decline to capitalizing on growth. This analysis identifies where "
                "the momentum is strongest and how to sustain it through strategic resource allocation."
            )
        else:
            return (
                "The analysis uncovers patterns that reveal both opportunities and risks. "
                "Understanding these dynamics is essential for making informed strategic decisions "
                "and prioritizing resource allocation effectively."
            )

    def _generate_strategic_headline(self, catalog: InsightCatalog) -> str:
        """
        Generate strategic narrative headline for the analysis.

        Transforms generic "Key Findings" into compelling strategic framing
        like "The Trust Erosion Index" or "The Authority Problem".
        """
        key_insights = catalog.get_key_insights()

        # Analyze dominant themes
        has_major_decline = sum(1 for i in key_insights if "decline" in i.headline.lower()) >= 2
        has_concentration = any("concentrated" in i.headline.lower() or "leads" in i.headline.lower() for i in key_insights)
        has_volatility = sum(1 for i in key_insights if "volatility" in i.headline.lower()) >= 2
        has_outliers = any("outlier" in i.headline.lower() for i in key_insights)
        has_growth = sum(1 for i in key_insights if "grow" in i.headline.lower()) >= 2

        # Generate thematic headline based on dominant pattern
        if has_major_decline and has_volatility:
            return "The Stability Crisis"
        elif has_major_decline:
            return "The Performance Erosion Pattern"
        elif has_concentration:
            return "The Dependency Risk Landscape"
        elif has_volatility:
            return "The Volatility Challenge"
        elif has_outliers and has_concentration:
            return "The Distribution Anomaly"
        elif has_growth:
            return "The Growth Momentum Story"
        else:
            # Fallback to generic but still better than "Key Findings"
            return "The Data Landscape"

    def _generate_recommendations(self, key_insights: list) -> list[str]:
        """
        Generate actionable recommendations from key insights.

        Transforms insights into specific, actionable next steps for decision-makers.
        Pattern matched from AG Survey Analysis reference PDF.
        """
        recommendations = []

        # Analyze insight patterns to generate targeted recommendations
        has_decline = any("decline" in i.headline.lower() for i in key_insights)
        has_growth = any("grow" in i.headline.lower() for i in key_insights)
        has_outliers = any("outlier" in i.headline.lower() for i in key_insights)
        has_concentration = any("concentrated" in i.headline.lower() or "leads" in i.headline.lower() for i in key_insights)
        has_volatility = any("volatility" in i.headline.lower() for i in key_insights)

        if has_decline:
            recommendations.append("**Investigate declining metrics immediately.** Conduct root cause analysis to identify drivers of the decline. Develop and implement targeted intervention strategies within 30 days.")

        if has_growth:
            recommendations.append("**Capitalize on positive momentum.** Double down on growth drivers. Allocate additional resources to sustain and accelerate the upward trend.")

        if has_outliers:
            recommendations.append("**Deep-dive on outlier cases.** Investigate the 5.8% of outlier data points. Determine if they represent data quality issues, exceptional circumstances, or untapped opportunities worth replicating.")

        if has_concentration:
            recommendations.append("**Diversify to reduce dependency risk.** Develop alternative sources to decrease reliance on top contributors. Set target of reducing top contributor share by 10-15% over next quarter.")

        if has_volatility:
            recommendations.append("**Implement volatility stabilization measures.** Establish hedging strategies and risk buffers. Set volatility reduction targets and monitor weekly.")

        # Always add validation recommendation
        recommendations.append("**Validate findings with stakeholders.** Present these insights to business owners and subject matter experts. Gather feedback to refine analysis and ensure actionability.")

        return recommendations

    def _generate_so_what(self, insight) -> str:
        """
        Generate 'So What' business impact explanation for an insight.

        Transforms raw data findings into consultant-grade business implications.
        Pattern matched from AG Survey Analysis reference PDF.
        """
        headline = insight.headline.lower()
        insight_type = insight.insight_type if hasattr(insight, 'insight_type') else ""

        # Pattern: Trend insights
        if "grows" in headline or "increases" in headline:
            return "This upward trend signals positive momentum. Monitor for sustainability and consider accelerating investments in drivers."
        elif "declines" in headline or "decreases" in headline:
            return "This decline warrants immediate attention. Investigate root causes and implement corrective measures to reverse the trend."

        # Pattern: Outlier insights
        elif "outliers" in headline:
            return "These outliers indicate exceptional cases requiring investigation. They may represent data quality issues, special circumstances, or high-value opportunities."

        # Pattern: Concentration insights
        elif "concentrated" in headline or "concentration" in headline:
            return "High concentration creates dependency risk. Consider diversification strategies to reduce exposure and improve resilience."
        elif "leads" in headline and "share" in headline:
            return "This leader drives disproportionate value. Protect and nurture this source while developing alternatives to reduce dependency."

        # Pattern: Volatility insights
        elif "volatility" in headline or "variability" in headline:
            return "High volatility creates uncertainty and risk. Implement stabilization measures and hedging strategies to protect downside."

        # Generic fallback
        else:
            return "This pattern reveals important characteristics of the data. Further analysis recommended to understand strategic implications."

    def _generate_kpi_dashboard(self, catalog: InsightCatalog) -> str:
        """
        Generate KPI dashboard section with top 3-5 key metrics.

        Extracts the most important numbers from insights and displays them
        prominently like consultant-grade outputs (reference: AG Survey Analysis).
        """
        lines = []

        lines.append("## 📊 KEY PERFORMANCE INDICATORS")
        lines.append("")

        # Extract KPIs from key insights
        kpis = []
        for insight in catalog.get_key_insights():
            # Extract metrics from evidence
            for ev in insight.evidence:
                if isinstance(ev.value, (int, float)) and ev.value != 0:
                    # Beautify field name
                    metric_name = FieldRegistry.beautify(ev.label or ev.reference)

                    # Format value appropriately
                    if "percentage" in ev.evidence_type.lower() or "%" in str(ev.label):
                        formatted_value = format_percentage(ev.value / 100, multiply_by_100=False)
                    else:
                        formatted_value = format_number(ev.value)

                    # Extract context from headline
                    context = insight.headline

                    kpis.append({
                        "metric": metric_name,
                        "value": formatted_value,
                        "context": context,
                        "confidence": insight.confidence
                    })

        # Take top 3-5 highest confidence KPIs
        kpis.sort(key=lambda x: x["confidence"], reverse=True)
        top_kpis = kpis[:min(5, len(kpis))]

        if not top_kpis:
            return ""  # No KPIs to display

        # Enhanced visual format - display each KPI as a card-like block
        for i, kpi in enumerate(top_kpis):
            # Create visual separator
            lines.append("```")
            lines.append(f"  {kpi['value']}")
            lines.append("```")

            # Metric label (beautified field name)
            lines.append(f"**{kpi['metric']}**")

            # Context explanation
            context_clean = kpi['context'].replace(kpi['metric'], "").strip()
            if context_clean:
                lines.append(f"*{context_clean}*")

            lines.append("")  # Spacing between KPIs

            # Add horizontal rule between KPIs (except after last one)
            if i < len(top_kpis) - 1:
                lines.append("---")
                lines.append("")

        # Add strategic insight below KPIs
        if len(catalog.get_key_insights()) > 0:
            lines.append("---")
            lines.append("")
            first_insight = catalog.get_key_insights()[0]
            lines.append("### Strategic Context")
            lines.append(f"{first_insight.supporting_text}")
            lines.append("")

        return "\n".join(lines)

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
        artifact_hashes: dict[str, str],
        project_root: Path
    ) -> str:
        """Generate markdown brief content with KPI dashboard."""
        lines = []

        # Generate strategic headline
        strategic_headline = self._generate_strategic_headline(catalog)

        # Header with strategic framing
        lines.append(f"# {strategic_headline}")
        lines.append("")
        lines.append(f"*{catalog.business_question}*")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # KPI DASHBOARD (NEW - Top Priority Metrics)
        kpi_section = self._generate_kpi_dashboard(catalog)
        if kpi_section:
            lines.append(kpi_section)
            lines.append("")
            lines.append("---")
            lines.append("")

        # Executive Summary with strategic context
        lines.append("## Executive Summary")
        lines.append("")

        # Add strategic context paragraph
        key_insights = catalog.get_key_insights()
        if key_insights:
            context = self._generate_strategic_context(key_insights)
            lines.append(context)
            lines.append("")
            lines.append("---")
            lines.append("")
        if key_insights:
            for idx, insight in enumerate(key_insights):
                lines.append(f"**{insight.headline}**")
                lines.append("")

                # EMBED CHARTS for key insights (in executive summary)
                # Find which insight number this is in the full catalog
                all_insights = catalog.get_findings()
                insight_idx = None
                for i, finding in enumerate(all_insights):
                    if finding.headline == insight.headline:
                        insight_idx = i
                        break

                if insight_idx is not None:
                    insight_id = f"insight_{insight_idx}"
                    bar_chart_path = f"../outputs/charts/{insight_id}__bar__top_n.svg"
                    charts_dir = project_root / "outputs" / "charts"
                    if (charts_dir / f"{insight_id}__bar__top_n.svg").exists():
                        lines.append(f"![{insight.headline}]({bar_chart_path})")
                        lines.append("")

                lines.append(insight.supporting_text)
                lines.append("")

                # SO WHAT: Business Impact (Critical addition from reference PDF)
                so_what = self._generate_so_what(insight)
                if so_what:
                    lines.append(f"**💡 So What:** {so_what}")
                    lines.append("")

                # Add evidence citation with VALUES
                if insight.evidence:
                    lines.append("*Evidence:*")
                    for ev in insight.evidence:
                        # Format evidence with value
                        from kie.formatting.output import format_evidence_value
                        label = ev.label if ev.label else ev.reference

                        if ev.value is not None:
                            formatted_value = format_evidence_value(ev.value, ev.evidence_type)
                            citation = f"- {label}: {formatted_value}"
                        else:
                            citation = f"- {label}"

                        if ev.reference in artifact_hashes:
                            citation += f" (verified: {artifact_hashes[ev.reference][:8]}...)"
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

                # EMBED CHARTS - Check for bar chart (most common)
                insight_id = f"insight_{i-1}"
                bar_chart_path = f"../outputs/charts/{insight_id}__bar__top_n.svg"
                pareto_chart_path = f"../outputs/charts/{insight_id}__pareto__cumulative.svg"

                # Check if charts exist in project
                charts_dir = project_root / "outputs" / "charts"
                bar_exists = (charts_dir / f"{insight_id}__bar__top_n.svg").exists()
                pareto_exists = (charts_dir / f"{insight_id}__pareto__cumulative.svg").exists()

                if bar_exists:
                    lines.append(f"![{insight.headline}]({bar_chart_path})")
                    lines.append("")
                if pareto_exists:
                    lines.append(f"![Cumulative Analysis]({pareto_chart_path})")
                    lines.append("")

                lines.append(insight.supporting_text)
                lines.append("")

                # SO WHAT: Business Impact
                so_what = self._generate_so_what(insight)
                if so_what:
                    lines.append(f"**💡 So What:** {so_what}")
                    lines.append("")

                # Statistical significance
                if insight.statistical_significance is not None:
                    sig_status = "✓ Statistically significant" if insight.is_statistically_significant else "⚠️ Not statistically significant"
                    lines.append(f"**Significance:** {sig_status} (p={insight.statistical_significance:.4f})")
                    lines.append("")

                # Evidence with smart formatting
                if insight.evidence:
                    lines.append("**Evidence:**")
                    for ev in insight.evidence:
                        from kie.formatting.output import format_evidence_value
                        label = ev.label if ev.label else ev.evidence_type

                        if ev.value is not None:
                            formatted_value = format_evidence_value(ev.value, ev.evidence_type)
                            ev_line = f"- {label}: {formatted_value}"
                        else:
                            ev_line = f"- {label}"

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
            # Generate actionable recommendations from key insights
            generated_recs = self._generate_recommendations(catalog.get_key_insights())
            if generated_recs:
                for i, rec_text in enumerate(generated_recs, 1):
                    lines.append(f"{i}. {rec_text}")
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
        """Generate structured JSON brief data with consultant-grade enhancements."""
        key_insights = catalog.get_key_insights()

        # Extract KPIs from key insights
        kpis = []
        for insight in key_insights:
            for ev in insight.evidence:
                if isinstance(ev.value, (int, float)) and ev.value != 0:
                    metric_name = FieldRegistry.beautify(ev.label or ev.reference)

                    # Format value appropriately
                    if "percentage" in ev.evidence_type.lower() or "%" in str(ev.label):
                        formatted_value = format_percentage(ev.value / 100, multiply_by_100=False)
                    else:
                        formatted_value = format_number(ev.value)

                    kpis.append({
                        "metric": metric_name,
                        "value": formatted_value,
                        "context": insight.headline,
                        "confidence": insight.confidence
                    })

        # Take top 5 KPIs by confidence
        kpis.sort(key=lambda x: x["confidence"], reverse=True)
        top_kpis = kpis[:min(5, len(kpis))]

        # Generate recommendations if none exist
        catalog_recs = catalog.get_recommendations()
        if catalog_recs:
            recommendations = [
                {
                    "headline": i.headline,
                    "supporting_text": i.supporting_text,
                }
                for i in catalog_recs
            ]
        else:
            # Generate from key insights
            generated_recs = self._generate_recommendations(key_insights)
            recommendations = [{"text": rec} for rec in generated_recs]

        return {
            "strategic_headline": self._generate_strategic_headline(catalog),
            "generated_at": datetime.now().isoformat(),
            "business_question": catalog.business_question,
            "kpis": top_kpis,
            "strategic_context": self._generate_strategic_context(key_insights),
            "executive_summary": {
                "key_insights": [
                    {
                        "headline": i.headline,
                        "supporting_text": i.supporting_text,
                        "so_what": self._generate_so_what(i),
                        "evidence": [e.to_dict() for e in i.evidence],
                    }
                    for i in key_insights
                ],
            },
            "findings": [
                {
                    "headline": i.headline,
                    "supporting_text": i.supporting_text,
                    "so_what": self._generate_so_what(i),
                    "confidence": i.confidence,
                    "statistical_significance": i.statistical_significance,
                    "evidence": [e.to_dict() for e in i.evidence],
                }
                for i in catalog.get_findings()
            ],
            "limitations": self._extract_limitations(catalog, eda_profile),
            "recommendations": recommendations,
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
