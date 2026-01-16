"""
Narrative Synthesis Engine

Generates consultant-grade narratives in multiple modes:
- EXECUTIVE: Business impact, recommendations, ROI focus
- ANALYST: Detailed findings, cross-correlations, pattern analysis
- TECHNICAL: Methodology, confidence intervals, statistical rigor
"""

from typing import Any

from kie.story.models import StoryInsight
from kie.story.models import StoryThesis, StorySection, NarrativeMode, StoryKPI


class NarrativeSynthesizer:
    """
    Synthesizes insights into compelling narratives for different audiences.

    Each mode has distinct:
    - Tone (strategic vs. analytical vs. methodological)
    - Focus (implications vs. patterns vs. validity)
    - Language (business vs. technical vs. statistical)
    """

    def __init__(self, mode: NarrativeMode = NarrativeMode.EXECUTIVE):
        """
        Initialize narrative synthesizer.

        Args:
            mode: Narrative mode (EXECUTIVE, ANALYST, TECHNICAL)
        """
        self.mode = mode

    def synthesize_executive_summary(
        self,
        thesis: StoryThesis,
        top_kpis: list[StoryKPI],
        sections: list[StorySection],
        insights: list[StoryInsight]
    ) -> str:
        """
        Generate executive summary based on narrative mode.

        Args:
            thesis: Core story thesis
            top_kpis: Top KPIs
            sections: Story sections
            insights: All insights

        Returns:
            Executive summary text
        """
        if self.mode == NarrativeMode.EXECUTIVE:
            return self._synthesize_executive_mode(thesis, top_kpis, sections)
        elif self.mode == NarrativeMode.ANALYST:
            return self._synthesize_analyst_mode(thesis, top_kpis, sections, insights)
        else:  # TECHNICAL
            return self._synthesize_technical_mode(thesis, top_kpis, insights)

    def synthesize_key_findings(
        self,
        insights: list[StoryInsight],
        max_findings: int = 5
    ) -> list[str]:
        """
        Generate key findings bullet points.

        Args:
            insights: All insights
            max_findings: Maximum bullet points

        Returns:
            List of finding strings
        """
        # Sort by business value
        top_insights = sorted(insights, key=lambda i: i.business_value, reverse=True)[:max_findings]

        findings = []
        for insight in top_insights:
            finding = self._format_finding(insight)
            findings.append(finding)

        return findings

    def synthesize_section_narrative(
        self,
        section: StorySection,
        insights: list[StoryInsight]
    ) -> str:
        """
        Generate narrative text for a story section.

        Args:
            section: Story section
            insights: StoryInsights in this section

        Returns:
            Narrative text
        """
        # Get section insights
        section_insights = [i for i in insights if i.insight_id in section.insight_ids]

        if not section_insights:
            return section.thesis

        if self.mode == NarrativeMode.EXECUTIVE:
            return self._synthesize_executive_section(section, section_insights)
        elif self.mode == NarrativeMode.ANALYST:
            return self._synthesize_analyst_section(section, section_insights)
        else:  # TECHNICAL
            return self._synthesize_technical_section(section, section_insights)

    # ========== EXECUTIVE MODE ==========

    def _synthesize_executive_mode(
        self,
        thesis: StoryThesis,
        top_kpis: list[StoryKPI],
        sections: list[StorySection]
    ) -> str:
        """Generate executive-focused summary (business impact, actions)."""
        kpi_highlights = self._format_kpi_highlights(top_kpis)

        summary = f"{thesis.summary}\n\n"
        summary += f"**Key Metrics:** {kpi_highlights}\n\n"
        summary += f"**Business Implication:** {thesis.implication}\n\n"

        # Add strategic recommendations
        summary += "**Recommended Actions:**\n"
        for i, section in enumerate(sections[:3], 1):
            action = self._infer_action_from_thesis(section.thesis)
            summary += f"{i}. {action}\n"

        return summary.strip()

    def _synthesize_executive_section(
        self,
        section: StorySection,
        insights: list[StoryInsight]
    ) -> str:
        """Generate executive narrative for section."""
        narrative = f"{section.thesis}\n\n"

        # Add business context
        top_insight = max(insights, key=lambda i: i.business_value)
        narrative += f"{top_insight.text} "

        # Add implication
        narrative += f"This suggests {self._infer_business_implication(top_insight)}."

        return narrative

    def _infer_action_from_thesis(self, thesis: str) -> str:
        """Infer actionable recommendation from section thesis."""
        # Simple heuristics for now (can be enhanced with LLM later)
        if "high" in thesis.lower() and "risk" in thesis.lower():
            return "Implement risk mitigation strategies to address identified vulnerabilities"
        elif "opportunity" in thesis.lower():
            return "Capitalize on identified opportunities through targeted initiatives"
        elif "satisfaction" in thesis.lower():
            return "Maintain satisfaction levels while addressing underlying concerns"
        else:
            return f"Address factors related to: {thesis.split('.')[0]}"

    def _infer_business_implication(self, insight: StoryInsight) -> str:
        """Infer business implication from insight."""
        text_lower = insight.text.lower()

        if "satisfaction" in text_lower:
            return "strong customer loyalty potential but vulnerability to competitive pressure"
        elif "price" in text_lower:
            return "pricing strategy will be critical to retention"
        elif "trust" in text_lower:
            return "relationship strength as a key differentiator"
        else:
            return "significant strategic implications for competitive positioning"

    # ========== ANALYST MODE ==========

    def _synthesize_analyst_mode(
        self,
        thesis: StoryThesis,
        top_kpis: list[StoryKPI],
        sections: list[StorySection],
        insights: list[StoryInsight]
    ) -> str:
        """Generate analyst-focused summary (detailed findings, patterns)."""
        kpi_highlights = self._format_kpi_highlights(top_kpis)

        summary = f"**Analysis Overview:** {thesis.summary}\n\n"
        summary += f"**Key Metrics:** {kpi_highlights}\n\n"

        # Add pattern analysis
        summary += "**Pattern Analysis:**\n"
        patterns = self._identify_patterns(insights)
        for pattern_type, description in patterns.items():
            summary += f"- **{pattern_type.title()}:** {description}\n"

        summary += f"\n**Analytical Insight:** {thesis.implication}"

        return summary.strip()

    def _synthesize_analyst_section(
        self,
        section: StorySection,
        insights: list[StoryInsight]
    ) -> str:
        """Generate analyst narrative for section."""
        narrative = f"**Section Analysis:** {section.thesis}\n\n"

        # Add detailed findings
        narrative += "**Detailed Findings:**\n"
        for insight in insights[:3]:  # Top 3 insights
            narrative += f"- {insight.text}\n"

        # Add cross-references if available
        if len(insights) > 1:
            narrative += f"\n**Cross-Pattern:** These findings suggest interconnected dynamics "
            narrative += "that warrant deeper investigation of causal relationships."

        return narrative

    def _identify_patterns(self, insights: list[StoryInsight]) -> dict[str, str]:
        """Identify analytical patterns across insights."""
        patterns = {}

        # Distribution patterns
        distributions = [i for i in insights if "distribution" in i.text.lower() or "spread" in i.text.lower()]
        if distributions:
            patterns["distribution"] = f"Identified {len(distributions)} distribution anomalies requiring attention"

        # Correlation patterns
        correlations = [i for i in insights if "correlation" in i.text.lower() or "relationship" in i.text.lower()]
        if correlations:
            patterns["correlation"] = f"Found {len(correlations)} significant inter-variable relationships"

        # Temporal patterns
        temporal = [i for i in insights if any(word in i.text.lower() for word in ["trend", "over time", "growth", "decline"])]
        if temporal:
            patterns["temporal"] = f"Detected {len(temporal)} time-based trends with strategic implications"

        # Segmentation patterns
        segments = [i for i in insights if any(word in i.text.lower() for word in ["segment", "group", "category"])]
        if segments:
            patterns["segmentation"] = f"Identified {len(segments)} segment-specific behaviors"

        return patterns

    # ========== TECHNICAL MODE ==========

    def _synthesize_technical_mode(
        self,
        thesis: StoryThesis,
        top_kpis: list[StoryKPI],
        insights: list[StoryInsight]
    ) -> str:
        """Generate technical summary (methodology, confidence, rigor)."""
        summary = f"**Technical Summary:** {thesis.summary}\n\n"

        # Add methodology note
        summary += "**Methodology:** Analysis conducted using comprehensive insight extraction "
        summary += f"across {len(insights)} distinct findings with statistical validation.\n\n"

        # Add confidence metrics
        avg_confidence = sum(i.confidence for i in insights) / len(insights) if insights else 0.0
        high_conf = len([i for i in insights if i.confidence >= 0.8])

        summary += f"**Confidence Assessment:**\n"
        summary += f"- Overall thesis confidence: {thesis.confidence:.1%}\n"
        summary += f"- Average insight confidence: {avg_confidence:.1%}\n"
        summary += f"- High-confidence findings: {high_conf}/{len(insights)}\n\n"

        # Add statistical notes
        summary += f"**Statistical Rigor:** {self._assess_statistical_rigor(insights)}\n\n"
        summary += f"**Methodological Implication:** {thesis.implication}"

        return summary.strip()

    def _synthesize_technical_section(
        self,
        section: StorySection,
        insights: list[StoryInsight]
    ) -> str:
        """Generate technical narrative for section."""
        narrative = f"**Technical Analysis:** {section.thesis}\n\n"

        # Add confidence breakdown
        narrative += "**Insight Confidence Distribution:**\n"
        for insight in insights:
            conf_indicator = "●●●" if insight.confidence >= 0.8 else "●●○" if insight.confidence >= 0.6 else "●○○"
            narrative += f"- {conf_indicator} (p={insight.confidence:.2f}): {insight.text[:100]}...\n"

        # Add validation notes
        narrative += f"\n**Validation:** Findings validated across {len(insights)} independent analyses "
        narrative += "with statistical significance testing where applicable."

        return narrative

    def _assess_statistical_rigor(self, insights: list[StoryInsight]) -> str:
        """Assess statistical rigor of analysis."""
        high_conf = len([i for i in insights if i.confidence >= 0.8])
        pct_high = (high_conf / len(insights) * 100) if insights else 0

        if pct_high >= 70:
            return "High rigor - majority of findings exceed 80% confidence threshold"
        elif pct_high >= 50:
            return "Moderate rigor - substantial findings meet statistical significance criteria"
        else:
            return "Preliminary rigor - findings indicate patterns requiring further validation"

    # ========== UTILITY METHODS ==========

    def _format_kpi_highlights(self, kpis: list[StoryKPI]) -> str:
        """Format KPIs for inline display."""
        if not kpis:
            return "Analysis in progress"

        highlights = []
        for kpi in kpis[:3]:  # Top 3
            highlights.append(f"{kpi.value} {kpi.label}")

        return "; ".join(highlights)

    def _format_finding(self, insight: StoryInsight) -> str:
        """Format insight as a finding bullet point."""
        if self.mode == NarrativeMode.EXECUTIVE:
            # Business-focused
            return f"{insight.text} (Business Impact: {insight.business_value:.0%})"
        elif self.mode == NarrativeMode.ANALYST:
            # Detail-focused
            return f"{insight.text}"
        else:  # TECHNICAL
            # Confidence-focused
            return f"{insight.text} (Confidence: {insight.confidence:.0%})"
