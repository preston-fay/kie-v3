"""
KIE Slide Types

Defines slide types and layouts for presentations.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class SlideType(Enum):
    """Types of slides supported."""
    TITLE = "title"
    SECTION = "section"
    CONTENT = "content"
    CHART = "chart"
    TABLE = "table"
    TWO_COLUMN = "two_column"
    THREE_COLUMN = "three_column"
    IMAGE = "image"
    COMPARISON = "comparison"
    TIMELINE = "timeline"
    CLOSING = "closing"
    AGENDA = "agenda"
    QUOTE = "quote"
    KEY_TAKEAWAY = "key_takeaway"
    PLACEHOLDER = "placeholder"


class SlideLayout(Enum):
    """Slide layout configurations."""
    FULL_WIDTH = "full_width"
    SPLIT_50_50 = "split_50_50"
    SPLIT_60_40 = "split_60_40"
    SPLIT_70_30 = "split_70_30"
    THREE_EQUAL = "three_equal"
    CENTERED = "centered"
    TOP_BOTTOM = "top_bottom"


@dataclass
class SlideTypeInfo:
    """Metadata about a slide type."""
    slide_type: SlideType
    name: str
    description: str
    consulting_use: str
    recommended_for: List[str]
    max_content_items: Optional[int] = None


# Slide type metadata
SLIDE_TYPE_INFO = {
    SlideType.TITLE: SlideTypeInfo(
        slide_type=SlideType.TITLE,
        name="Title Slide",
        description="Opening slide with main title and subtitle",
        consulting_use="First slide of any presentation. Sets the context.",
        recommended_for=["opening", "introduction"],
    ),
    SlideType.SECTION: SlideTypeInfo(
        slide_type=SlideType.SECTION,
        name="Section Divider",
        description="Divider slide between major sections",
        consulting_use="Create visual breaks between content sections.",
        recommended_for=["transitions", "structure"],
    ),
    SlideType.CONTENT: SlideTypeInfo(
        slide_type=SlideType.CONTENT,
        name="Content Slide",
        description="Bullet points or body text",
        consulting_use="Present key findings, recommendations, or details.",
        recommended_for=["findings", "details", "recommendations"],
        max_content_items=6,
    ),
    SlideType.CHART: SlideTypeInfo(
        slide_type=SlideType.CHART,
        name="Chart Slide",
        description="Data visualization with chart image",
        consulting_use="Present quantitative insights with visual evidence.",
        recommended_for=["data", "trends", "comparisons"],
    ),
    SlideType.TABLE: SlideTypeInfo(
        slide_type=SlideType.TABLE,
        name="Table Slide",
        description="Tabular data presentation",
        consulting_use="Present detailed data, comparisons, or matrices.",
        recommended_for=["data", "comparisons", "details"],
        max_content_items=10,
    ),
    SlideType.TWO_COLUMN: SlideTypeInfo(
        slide_type=SlideType.TWO_COLUMN,
        name="Two Column Slide",
        description="Side-by-side comparison or content",
        consulting_use="Compare options, show pros/cons, before/after.",
        recommended_for=["comparisons", "options", "pros_cons"],
    ),
    SlideType.THREE_COLUMN: SlideTypeInfo(
        slide_type=SlideType.THREE_COLUMN,
        name="Three Column Slide",
        description="Three parallel content areas",
        consulting_use="Present three options, phases, or categories.",
        recommended_for=["options", "phases", "categories"],
    ),
    SlideType.IMAGE: SlideTypeInfo(
        slide_type=SlideType.IMAGE,
        name="Image Slide",
        description="Full or prominent image with caption",
        consulting_use="Show diagrams, screenshots, or visual evidence.",
        recommended_for=["visuals", "diagrams", "screenshots"],
    ),
    SlideType.COMPARISON: SlideTypeInfo(
        slide_type=SlideType.COMPARISON,
        name="Comparison Slide",
        description="Structured comparison with headers",
        consulting_use="Competitive analysis, option evaluation.",
        recommended_for=["analysis", "evaluation", "alternatives"],
    ),
    SlideType.TIMELINE: SlideTypeInfo(
        slide_type=SlideType.TIMELINE,
        name="Timeline Slide",
        description="Horizontal timeline of events or phases",
        consulting_use="Project plans, implementation roadmaps.",
        recommended_for=["planning", "roadmap", "milestones"],
    ),
    SlideType.CLOSING: SlideTypeInfo(
        slide_type=SlideType.CLOSING,
        name="Closing Slide",
        description="Thank you or contact information slide",
        consulting_use="End presentations professionally.",
        recommended_for=["ending", "contact"],
    ),
    SlideType.AGENDA: SlideTypeInfo(
        slide_type=SlideType.AGENDA,
        name="Agenda Slide",
        description="Meeting or presentation agenda",
        consulting_use="Set expectations at the start.",
        recommended_for=["structure", "overview"],
    ),
    SlideType.QUOTE: SlideTypeInfo(
        slide_type=SlideType.QUOTE,
        name="Quote Slide",
        description="Featured quote or testimonial",
        consulting_use="Executive quotes, customer testimonials.",
        recommended_for=["quotes", "testimonials"],
    ),
    SlideType.KEY_TAKEAWAY: SlideTypeInfo(
        slide_type=SlideType.KEY_TAKEAWAY,
        name="Key Takeaway Slide",
        description="Single key message prominently displayed",
        consulting_use="Emphasize the most important insight.",
        recommended_for=["emphasis", "summary"],
    ),
    SlideType.PLACEHOLDER: SlideTypeInfo(
        slide_type=SlideType.PLACEHOLDER,
        name="Placeholder Slide",
        description="Placeholder for manual content",
        consulting_use="Reserve space for content to be added later.",
        recommended_for=["drafts", "planning"],
    ),
}


def get_slide_type_info(slide_type: SlideType) -> SlideTypeInfo:
    """Get metadata for a slide type."""
    return SLIDE_TYPE_INFO.get(slide_type)
