"""
Story Builder - Orchestrates Story-First Architecture

Coordinates thesis extraction, KPI extraction, section grouping, and narrative
synthesis to produce a complete StoryManifest for consultant-grade output.
"""

from pathlib import Path
from typing import Any

from kie.story.models import StoryInsight
from kie.story.models import (
    StoryManifest,
    StoryThesis,
    StoryKPI,
    StorySection,
    NarrativeMode,
)
from kie.story.thesis_extractor import ThesisExtractor
from kie.story.kpi_extractor import KPIExtractor
from kie.story.section_grouper import SectionGrouper
from kie.story.narrative_synthesizer import NarrativeSynthesizer


class StoryBuilder:
    """
    Orchestrates the story-first architecture pipeline.

    Pipeline:
    1. Extract thesis (core narrative)
    2. Extract top KPIs (headline numbers)
    3. Group insights into sections
    4. Extract section KPIs
    5. Synthesize narratives (mode-specific)
    6. Build complete manifest
    """

    def __init__(self, narrative_mode: NarrativeMode = NarrativeMode.EXECUTIVE):
        """
        Initialize story builder.

        Args:
            narrative_mode: Narrative synthesis mode
        """
        self.narrative_mode = narrative_mode
        self.thesis_extractor = ThesisExtractor()
        self.kpi_extractor = KPIExtractor()
        self.section_grouper = SectionGrouper()
        self.narrative_synthesizer = NarrativeSynthesizer(mode=narrative_mode)

    def build_story(
        self,
        insights: list[StoryInsight],
        project_name: str,
        objective: str | None = None,
        chart_refs: dict[str, str] | None = None,
        context_str: str = "",
    ) -> StoryManifest:
        """
        Build complete story manifest from insights.

        Args:
            insights: List of insights to transform into story
            project_name: Project name
            objective: Optional project objective for framing
            chart_refs: Optional mapping of insight_id -> chart_path
            context_str: Optional context (e.g., "n=511 growers")

        Returns:
            StoryManifest ready for deliverable generation
        """
        chart_refs = chart_refs or {}

        # Step 1: Extract thesis
        thesis = self.thesis_extractor.extract_thesis(
            insights=insights,
            project_name=project_name,
            objective=objective
        )

        # Step 2: Extract top KPIs (for hero section)
        top_kpis = self.kpi_extractor.extract_kpis(
            insights=insights,
            max_kpis=5,
            context_str=context_str
        )

        # Step 3: Group insights into sections
        sections = self.section_grouper.group_insights(
            insights=insights,
            chart_refs=chart_refs,
            min_section_size=2
        )

        # Step 4: Extract section-specific KPIs
        for section in sections:
            section_insights = [i for i in insights if i.insight_id in section.insight_ids]
            section_kpis = self.kpi_extractor.extract_section_kpis(
                section_insights=section_insights,
                max_kpis=3,
                context_str=context_str
            )
            section.kpis = section_kpis

        # Step 5: Synthesize section narratives
        for section in sections:
            section_insights = [i for i in insights if i.insight_id in section.insight_ids]
            narrative = self.narrative_synthesizer.synthesize_section_narrative(
                section=section,
                insights=section_insights
            )
            section.narrative_text = narrative

        # Step 6: Synthesize executive summary
        executive_summary = self.narrative_synthesizer.synthesize_executive_summary(
            thesis=thesis,
            top_kpis=top_kpis,
            sections=sections,
            insights=insights
        )

        # Step 7: Generate key findings
        key_findings = self.narrative_synthesizer.synthesize_key_findings(
            insights=insights,
            max_findings=5
        )

        # Step 8: Create manifest
        story_id = self._generate_story_id(project_name)

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
                "objective": objective,
                "total_insights": len(insights),
                "total_sections": len(sections),
                "context": context_str,
            }
        )

        return manifest

    def build_and_save(
        self,
        insights: list[StoryInsight],
        project_name: str,
        output_path: Path,
        objective: str | None = None,
        chart_refs: dict[str, str] | None = None,
        context_str: str = "",
    ) -> StoryManifest:
        """
        Build story and save manifest to file.

        Args:
            insights: List of insights
            project_name: Project name
            output_path: Where to save manifest JSON
            objective: Optional objective
            chart_refs: Optional chart references
            context_str: Optional context

        Returns:
            StoryManifest (also saved to disk)
        """
        manifest = self.build_story(
            insights=insights,
            project_name=project_name,
            objective=objective,
            chart_refs=chart_refs,
            context_str=context_str
        )

        # Save to disk
        manifest.save(output_path)

        return manifest

    def _generate_story_id(self, project_name: str) -> str:
        """Generate unique story ID from project name."""
        # Simple slug generation
        slug = project_name.lower()
        slug = slug.replace(" ", "_")
        slug = "".join(c for c in slug if c.isalnum() or c == "_")

        # Add timestamp for uniqueness
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"story_{slug}_{timestamp}"

    def update_narrative_mode(self, mode: NarrativeMode) -> None:
        """
        Update narrative mode and reinitialize synthesizer.

        Args:
            mode: New narrative mode
        """
        self.narrative_mode = mode
        self.narrative_synthesizer = NarrativeSynthesizer(mode=mode)

    def rebuild_narratives(
        self,
        manifest: StoryManifest,
        insights: list[StoryInsight],
        mode: NarrativeMode | None = None
    ) -> StoryManifest:
        """
        Rebuild narratives with different mode (keeping thesis/KPIs/sections).

        Useful for generating multiple narrative versions without re-analyzing.

        Args:
            manifest: Existing story manifest
            insights: Original insights
            mode: Optional new mode (uses current if not specified)

        Returns:
            Updated StoryManifest with new narratives
        """
        if mode:
            self.update_narrative_mode(mode)

        # Rebuild executive summary
        manifest.executive_summary = self.narrative_synthesizer.synthesize_executive_summary(
            thesis=manifest.thesis,
            top_kpis=manifest.top_kpis,
            sections=manifest.sections,
            insights=insights
        )

        # Rebuild section narratives
        for section in manifest.sections:
            section_insights = [i for i in insights if i.insight_id in section.insight_ids]
            section.narrative_text = self.narrative_synthesizer.synthesize_section_narrative(
                section=section,
                insights=section_insights
            )

        # Rebuild key findings
        manifest.key_findings = self.narrative_synthesizer.synthesize_key_findings(
            insights=insights,
            max_findings=5
        )

        # Update mode
        manifest.narrative_mode = self.narrative_mode

        return manifest
