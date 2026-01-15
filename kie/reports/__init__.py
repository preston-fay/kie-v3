"""
KIE Reports Module

Consultant-friendly report generation (HTML, enhanced markdown).
"""

from kie.reports.html_generator import markdown_to_html
from kie.reports.markdown_enhancer import (
    create_data_quality_table,
    create_insight_distribution_table,
    embed_chart,
    format_markdown_table,
)

__all__ = [
    "markdown_to_html",
    "create_data_quality_table",
    "create_insight_distribution_table",
    "embed_chart",
    "format_markdown_table",
]
