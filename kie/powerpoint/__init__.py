"""
PowerPoint Integration for KIE v3

Native, editable chart embedding in PowerPoint slides.
"""

from kie.powerpoint.chart_embedder import (
    PowerPointChartEmbedder,
    embed_chart_in_slide,
)
from kie.powerpoint.slide_builder import SlideBuilder

__all__ = [
    "PowerPointChartEmbedder",
    "embed_chart_in_slide",
    "SlideBuilder",
]
