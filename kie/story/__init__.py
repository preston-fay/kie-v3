"""
Story-First Architecture - Consultant-Grade Output Generation

This module implements the story-first approach where insights are transformed
into compelling narratives with clear thesis, KPIs, and visual hierarchy.

Key Components:
- Thesis Extraction: Identifies the core story/paradox in the data
- KPI Extraction: Surfaces the most impactful numbers
- Narrative Synthesis: Generates executive/analyst/technical narratives
- Story Sections: Groups insights into coherent narrative sections
- Interactive Story: Web-first scrolling narrative with embedded visuals
"""

from kie.story.models import (
    StoryInsight,
    StoryThesis,
    StoryKPI,
    StorySection,
    StoryManifest,
    NarrativeMode,
    KPIType,
)
from kie.story.thesis_extractor import ThesisExtractor
from kie.story.kpi_extractor import KPIExtractor
from kie.story.section_grouper import SectionGrouper
from kie.story.narrative_synthesizer import NarrativeSynthesizer
from kie.story.story_builder import StoryBuilder

# LLM-powered components (domain-agnostic, works for ANY data)
from kie.story.llm_grouper import LLMSectionGrouper
from kie.story.llm_chart_selector import LLMChartSelector
from kie.story.llm_narrative_synthesizer import LLMNarrativeSynthesizer
from kie.story.llm_story_builder import LLMStoryBuilder

# Output renderers (KDS-compliant)
from kie.story.react_story_renderer import ReactStoryRenderer
from kie.story.pptx_story_renderer import PPTXStoryRenderer

__all__ = [
    # Core models
    "StoryInsight",
    "StoryThesis",
    "StoryKPI",
    "StorySection",
    "StoryManifest",
    "NarrativeMode",
    "KPIType",
    # Original components (rule-based)
    "ThesisExtractor",
    "KPIExtractor",
    "SectionGrouper",
    "NarrativeSynthesizer",
    "StoryBuilder",
    # LLM-powered components (domain-agnostic)
    "LLMSectionGrouper",
    "LLMChartSelector",
    "LLMNarrativeSynthesizer",
    "LLMStoryBuilder",
    # Output renderers (KDS-compliant)
    "ReactStoryRenderer",
    "PPTXStoryRenderer",
]
