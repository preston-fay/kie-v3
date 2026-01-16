"""
LLM-Powered Story Builder

Enhanced story builder that uses Claude LLM for domain-agnostic story generation.
Works for ANY data type - healthcare, manufacturing, finance, IoT, literally anything.
"""

import uuid
from datetime import datetime
from typing import Any

from kie.story.models import (
    StoryInsight,
    StoryManifest,
    NarrativeMode
)
from kie.story.thesis_extractor import ThesisExtractor
from kie.story.kpi_extractor import KPIExtractor
from kie.story.llm_grouper import LLMSectionGrouper
from kie.story.llm_narrative_synthesizer import LLMNarrativeSynthesizer
from kie.story.llm_chart_selector import LLMChartSelector


class LLMStoryBuilder:
    """
    Builds complete story manifests using LLM-powered components.

    This version works for ANY domain - no hardcoded business assumptions.
    Fully leverages Claude's understanding of data patterns.
    """

    def __init__(
        self,
        narrative_mode: NarrativeMode = NarrativeMode.EXECUTIVE,
        use_llm_grouping: bool = True,
        use_llm_narrative: bool = True,
        use_llm_charts: bool = True
    ):
        """
        Initialize LLM-powered story builder.

        Args:
            narrative_mode: Narrative mode (EXECUTIVE, ANALYST, TECHNICAL)
            use_llm_grouping: Use LLM for section grouping (vs rule-based)
            use_llm_narrative: Use LLM for narrative synthesis (vs templates)
            use_llm_charts: Use LLM for chart selection (vs heuristics)
        """
        self.narrative_mode = narrative_mode
        self.use_llm_grouping = use_llm_grouping
        self.use_llm_narrative = use_llm_narrative
        self.use_llm_charts = use_llm_charts

        # Initialize components
        self.thesis_extractor = ThesisExtractor()  # Already domain-agnostic
        self.kpi_extractor = KPIExtractor()  # Already domain-agnostic

        # Choose grouper (LLM vs rule-based)
        if use_llm_grouping:
            self.section_grouper = LLMSectionGrouper()
        else:
            from kie.story.section_grouper import SectionGrouper
            self.section_grouper = SectionGrouper()

        # Choose narrative synthesizer (LLM vs template)
        if use_llm_narrative:
            self.narrative_synthesizer = LLMNarrativeSynthesizer(narrative_mode)
        else:
            from kie.story.narrative_synthesizer import NarrativeSynthesizer
            self.narrative_synthesizer = NarrativeSynthesizer(narrative_mode)

        # Chart selector (LLM vs heuristic)
        if use_llm_charts:
            self.chart_selector = LLMChartSelector()
        else:
            from kie.story.chart_selector import ChartSelector
            self.chart_selector = ChartSelector()

    def build_story(
        self,
        insights: list[StoryInsight],
        project_name: str,
        objective: str | None = None,
        chart_refs: dict[str, str] | None = None,
        context_str: str = ""
    ) -> StoryManifest:
        """
        Build complete story manifest from insights.

        Works for ANY data domain - healthcare, manufacturing, finance, etc.

        Args:
            insights: List of insights to build story from
            project_name: Name of the project
            objective: Optional objective/intent
            chart_refs: Optional mapping of insight_id -> chart_path
            context_str: Additional context about the data

        Returns:
            Complete StoryManifest ready for rendering
        """
        if not insights:
            raise ValueError("Cannot build story with no insights")

        chart_refs = chart_refs or {}

        # Step 1: Extract thesis (domain-agnostic pattern detection)
        thesis = self.thesis_extractor.extract_thesis(
            insights,
            project_name,
            objective
        )

        # Step 2: Extract top KPIs (domain-agnostic number extraction)
        top_kpis = self.kpi_extractor.extract_kpis(
            insights,
            max_kpis=5,
            context_str=context_str or objective or project_name
        )

        # Step 3: Group insights into sections (LLM-powered or rule-based)
        sections = self.section_grouper.group_insights(
            insights,
            chart_refs,
            min_section_size=2
        )

        # Step 4: Extract section-level KPIs
        for section in sections:
            section_insights = [ins for ins in insights if ins.insight_id in section.insight_ids]
            section_kpis = self.kpi_extractor.extract_section_kpis(
                section_insights,
                max_kpis=3,
                context_str=section.title
            )
            section.kpis = section_kpis

        # Step 5: Synthesize narratives (LLM-powered or template-based)
        for section in sections:
            section_insights = [ins for ins in insights if ins.insight_id in section.insight_ids]

            # Check if using LLM narrative synthesizer (3 args) or rule-based (2 args)
            if self.use_llm_narrative:
                section.narrative_text = self.narrative_synthesizer.synthesize_section_narrative(
                    section,
                    section_insights,
                    section.kpis
                )
            else:
                # Rule-based synthesizer only takes 2 args (section, insights)
                section.narrative_text = self.narrative_synthesizer.synthesize_section_narrative(
                    section,
                    section_insights
                )

        # Step 6: Generate executive summary
        executive_summary = self.narrative_synthesizer.synthesize_executive_summary(
            thesis,
            top_kpis,
            sections,
            insights
        )

        # Step 7: Generate key findings
        key_findings = self.narrative_synthesizer.synthesize_key_findings(
            insights,
            max_findings=5
        )

        # Step 8: Build manifest
        story_id = f"story_{project_name.replace(' ', '').replace('-', '')[:20].lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        manifest = StoryManifest(
            story_id=story_id,
            project_name=project_name,
            thesis=thesis,
            top_kpis=top_kpis,
            sections=sections,
            narrative_mode=self.narrative_mode,
            executive_summary=executive_summary,
            key_findings=key_findings,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "objective": objective,
                "insight_count": len(insights),
                "section_count": len(sections),
                "kpi_count": len(top_kpis),
                "llm_powered": {
                    "grouping": self.use_llm_grouping,
                    "narrative": self.use_llm_narrative,
                    "charts": self.use_llm_charts
                }
            }
        )

        return manifest
