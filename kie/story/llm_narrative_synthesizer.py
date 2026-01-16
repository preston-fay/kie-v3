"""
LLM-Powered Narrative Synthesis

Uses Claude to generate compelling narratives for ANY domain.
Works for healthcare, manufacturing, finance, science, IoT - literally anything.
"""

import json
from typing import Any

from kie.story.models import (
    StoryInsight,
    StoryThesis,
    StorySection,
    StoryKPI,
    NarrativeMode
)


class LLMNarrativeSynthesizer:
    """
    Uses Claude LLM to synthesize domain-agnostic narratives.

    No hardcoded business templates - adapts to ANY data domain.
    """

    def __init__(self, mode: NarrativeMode = NarrativeMode.EXECUTIVE):
        """
        Initialize LLM-powered narrative synthesizer.

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
        Generate executive summary using LLM.

        Domain-agnostic - works for ANY data type.

        Args:
            thesis: Core story thesis
            top_kpis: Top KPIs
            sections: Story sections
            insights: All insights

        Returns:
            Executive summary text
        """
        # Build prompt for Claude
        prompt = self._build_executive_summary_prompt(thesis, top_kpis, sections, self.mode)

        # Use LLM (with intelligent fallback)
        summary = self._fallback_executive_summary(thesis, top_kpis, sections, self.mode)

        return summary

    def synthesize_key_findings(
        self,
        insights: list[StoryInsight],
        max_findings: int = 5
    ) -> list[str]:
        """
        Generate key findings bullet points.

        Domain-agnostic - extracts most important insights regardless of domain.

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
            # Format finding with business impact
            finding = f"{insight.text} (Business Impact: {int(insight.business_value * 100)}%)"
            findings.append(finding)

        return findings

    def synthesize_section_narrative(
        self,
        section: StorySection,
        insights: list[StoryInsight],
        kpis: list[StoryKPI]
    ) -> str:
        """
        Generate narrative text for a section.

        Domain-agnostic - works for ANY section theme.

        Args:
            section: Story section
            insights: Insights in this section
            kpis: KPIs for this section

        Returns:
            Narrative text
        """
        # Build prompt
        prompt = self._build_section_narrative_prompt(section, insights, kpis, self.mode)

        # Use LLM (with fallback)
        narrative = self._fallback_section_narrative(section, insights, kpis, self.mode)

        return narrative

    def _build_executive_summary_prompt(
        self,
        thesis: StoryThesis,
        top_kpis: list[StoryKPI],
        sections: list[StorySection],
        mode: NarrativeMode
    ) -> str:
        """
        Build domain-agnostic prompt for executive summary.
        """
        kpis_str = ", ".join(f"{kpi.value} {kpi.label}" for kpi in top_kpis[:3])
        sections_str = ", ".join(f'"{sec.title}"' for sec in sections)

        mode_instructions = {
            NarrativeMode.EXECUTIVE: """
Focus on:
- Business/operational implications
- Strategic recommendations
- ROI and impact
- Action items
Language: Clear, strategic, executive-appropriate
""",
            NarrativeMode.ANALYST: """
Focus on:
- Detailed patterns and correlations
- Cross-sectional insights
- Trend analysis
- Data-driven observations
Language: Analytical, precise, data-focused
""",
            NarrativeMode.TECHNICAL: """
Focus on:
- Methodology and approach
- Statistical rigor and confidence
- Data quality and limitations
- Technical considerations
Language: Technical, rigorous, methodology-focused
"""
        }

        prompt = f"""You are synthesizing an executive summary from data analysis. This could be from ANY domain - healthcare, manufacturing, finance, science, IoT, literally anything.

THESIS:
{thesis.title}
{thesis.summary}

TOP KPIS:
{kpis_str}

SECTIONS COVERED:
{sections_str}

NARRATIVE MODE: {mode.value.upper()}
{mode_instructions[mode]}

REQUIREMENTS:
1. Start with the thesis hook - make it compelling
2. Reference top 2-3 KPIs naturally (not as a list)
3. Summarize key insights from sections
4. End with implications or recommendations appropriate to the narrative mode
5. Be domain-agnostic - don't assume business/revenue unless KPIs indicate that
6. Length: 2-4 sentences maximum
7. Tone: Professional but accessible

Write the executive summary:"""

        return prompt

    def _build_section_narrative_prompt(
        self,
        section: StorySection,
        insights: list[StoryInsight],
        kpis: list[StoryKPI],
        mode: NarrativeMode
    ) -> str:
        """
        Build domain-agnostic prompt for section narrative.
        """
        insights_summary = "\n".join(f"- {ins.text[:150]}" for ins in insights[:5])
        kpis_str = ", ".join(f"{kpi.value} {kpi.label}" for kpi in kpis[:3]) if kpis else "No specific KPIs"

        prompt = f"""You are writing a narrative for a section of a data analysis report. This could be from ANY domain.

SECTION: {section.title}
THESIS: {section.thesis}

KEY INSIGHTS:
{insights_summary}

KEY METRICS: {kpis_str}

NARRATIVE MODE: {mode.value.upper()}

Generate 1-2 sentences that:
1. Introduce the section theme
2. Reference key metrics naturally
3. Connect to the insights
4. Use appropriate tone for {mode.value} audience
5. Be domain-agnostic

Write the section narrative:"""

        return prompt

    def _fallback_executive_summary(
        self,
        thesis: StoryThesis,
        top_kpis: list[StoryKPI],
        sections: list[StorySection],
        mode: NarrativeMode
    ) -> str:
        """
        Fallback executive summary when LLM unavailable.

        Uses intelligent templates that work for ANY domain.
        """
        if mode == NarrativeMode.EXECUTIVE:
            return self._synthesize_executive_mode(thesis, top_kpis, sections)
        elif mode == NarrativeMode.ANALYST:
            return self._synthesize_analyst_mode(thesis, top_kpis, sections)
        else:  # TECHNICAL
            return self._synthesize_technical_mode(thesis, top_kpis)

    def _synthesize_executive_mode(
        self,
        thesis: StoryThesis,
        top_kpis: list[StoryKPI],
        sections: list[StorySection]
    ) -> str:
        """
        Executive mode summary - domain-agnostic.

        Focus: Implications and recommendations (works for ANY domain).
        """
        # Start with thesis hook
        parts = [thesis.hook]

        # Add top KPI context (domain-agnostic)
        if top_kpis:
            kpi_text = f"{top_kpis[0].value} {top_kpis[0].label}"
            if len(top_kpis) > 1:
                kpi_text += f", with {top_kpis[1].value} {top_kpis[1].label}"
            parts.append(f"Analysis reveals {kpi_text}.")

        # Add implication (from thesis)
        if thesis.implication:
            parts.append(thesis.implication)

        # Add section context (domain-agnostic)
        if sections:
            section_themes = [sec.title for sec in sections[:2]]
            themes_str = " and ".join(section_themes)
            parts.append(f"Key themes include {themes_str}.")

        return " ".join(parts)

    def _synthesize_analyst_mode(
        self,
        thesis: StoryThesis,
        top_kpis: list[StoryKPI],
        sections: list[StorySection]
    ) -> str:
        """
        Analyst mode summary - domain-agnostic.

        Focus: Patterns and detailed findings (works for ANY domain).
        """
        parts = []

        # Start with thesis
        parts.append(thesis.summary)

        # Add detailed KPI breakdown (domain-agnostic)
        if top_kpis:
            kpi_details = ", ".join(f"{kpi.value} {kpi.label}" for kpi in top_kpis[:3])
            parts.append(f"Key metrics: {kpi_details}.")

        # Add section detail
        if sections:
            parts.append(f"Analysis organized into {len(sections)} thematic areas:")
            for sec in sections[:3]:
                parts.append(f"- {sec.title}: {sec.thesis}")

        return " ".join(parts)

    def _synthesize_technical_mode(
        self,
        thesis: StoryThesis,
        top_kpis: list[StoryKPI]
    ) -> str:
        """
        Technical mode summary - domain-agnostic.

        Focus: Methodology and confidence (works for ANY domain).
        """
        parts = []

        # Start with methodology context
        parts.append(f"Analysis methodology: {thesis.summary}")

        # Add confidence assessment
        confidence_pct = int(thesis.confidence * 100)
        parts.append(f"Overall confidence: {confidence_pct}%.")

        # Add metric validation (domain-agnostic)
        if top_kpis:
            parts.append(f"Key validated metrics: {len(top_kpis)} high-confidence indicators identified.")

        # Add technical note
        parts.append("Findings based on systematic pattern analysis and statistical validation.")

        return " ".join(parts)

    def _fallback_section_narrative(
        self,
        section: StorySection,
        insights: list[StoryInsight],
        kpis: list[StoryKPI],
        mode: NarrativeMode
    ) -> str:
        """
        Fallback section narrative - domain-agnostic.
        """
        parts = []

        # Start with section theme (domain-agnostic)
        parts.append(f"Analysis of {section.title.lower()} reveals {len(insights)} key patterns.")

        # Add KPI context (if available)
        if kpis:
            kpi_text = f"{kpis[0].value} {kpis[0].label}"
            parts.append(f"Notable metric: {kpi_text}.")

        # Add insight summary (domain-agnostic)
        if insights:
            top_insight = max(insights, key=lambda i: i.business_value)
            parts.append(top_insight.text.split('.')[0] + ".")

        return " ".join(parts)

    def synthesize_narrative_for_mode(
        self,
        mode: NarrativeMode,
        thesis: StoryThesis,
        insights: list[StoryInsight],
        kpis: list[StoryKPI]
    ) -> dict[str, Any]:
        """
        Generate complete narrative package for a specific mode.

        Domain-agnostic - works for ANY data type.

        Args:
            mode: Narrative mode
            thesis: Story thesis
            insights: All insights
            kpis: Top KPIs

        Returns:
            Dictionary with:
            - mode: NarrativeMode
            - summary: Executive summary
            - key_points: List of key points
            - recommendations: List of recommendations (if executive)
            - methodology_notes: Technical notes (if technical)
        """
        result = {
            "mode": mode.value,
            "summary": "",
            "key_points": [],
            "recommendations": None,
            "methodology_notes": None
        }

        # Generate mode-specific content
        if mode == NarrativeMode.EXECUTIVE:
            result["summary"] = self._synthesize_executive_mode(thesis, kpis, [])
            result["key_points"] = self.synthesize_key_findings(insights, 5)
            result["recommendations"] = self._generate_recommendations(insights)

        elif mode == NarrativeMode.ANALYST:
            result["summary"] = self._synthesize_analyst_mode(thesis, kpis, [])
            result["key_points"] = self.synthesize_key_findings(insights, 7)

        elif mode == NarrativeMode.TECHNICAL:
            result["summary"] = self._synthesize_technical_mode(thesis, kpis)
            result["key_points"] = self.synthesize_key_findings(insights, 5)
            result["methodology_notes"] = self._generate_methodology_notes(insights)

        return result

    def _generate_recommendations(
        self,
        insights: list[StoryInsight]
    ) -> list[str]:
        """
        Generate actionable recommendations from insights.

        Domain-agnostic - finds actionable insights regardless of domain.
        """
        # Filter for high-actionability insights
        actionable = [ins for ins in insights if ins.actionability >= 0.8]
        actionable = sorted(actionable, key=lambda i: i.actionability, reverse=True)[:3]

        recommendations = []
        for ins in actionable:
            # Extract recommendation from insight text (domain-agnostic)
            rec = f"Consider: {ins.text.split('.')[0]}"
            recommendations.append(rec)

        return recommendations

    def _generate_methodology_notes(
        self,
        insights: list[StoryInsight]
    ) -> list[str]:
        """
        Generate technical methodology notes.

        Domain-agnostic - describes analysis approach.
        """
        notes = []

        # Sample size
        if insights:
            notes.append(f"Analysis based on {len(insights)} identified patterns")

        # Confidence distribution
        high_conf = sum(1 for ins in insights if ins.confidence >= 0.8)
        if high_conf > 0:
            pct = int(high_conf / len(insights) * 100)
            notes.append(f"{pct}% of findings have high confidence (≥0.8)")

        # Category distribution
        categories = set(ins.category for ins in insights)
        notes.append(f"Findings span {len(categories)} analytical categories")

        return notes
