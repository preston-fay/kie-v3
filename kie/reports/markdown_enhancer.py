"""
Markdown Enhancement Utilities

Provides utilities for creating consultant-friendly markdown with:
- Formatted tables (proper markdown table syntax)
- Chart embeds (SVG references and base64 data URIs)
- Professional formatting

Phase 5 of Consultant UX improvements.
"""

import base64
from pathlib import Path
from typing import Any


def format_markdown_table(
    headers: list[str],
    rows: list[list[Any]],
    alignments: list[str] | None = None
) -> str:
    """
    Create properly formatted markdown table.

    Args:
        headers: Table header row
        rows: Table data rows
        alignments: Optional alignment per column ('left', 'center', 'right')

    Returns:
        Markdown table string

    Example:
        >>> headers = ["Metric", "Value", "Status"]
        >>> rows = [["Rows", "1,000", "✅"], ["Quality", "95%", "✅"]]
        >>> print(format_markdown_table(headers, rows))
        | Metric | Value | Status |
        |--------|-------|--------|
        | Rows | 1,000 | ✅ |
        | Quality | 95% | ✅ |
    """
    if not headers or not rows:
        return ""

    # Default to left alignment
    if alignments is None:
        alignments = ["left"] * len(headers)

    lines = []

    # Header row
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    lines.append(header_line)

    # Separator row with alignment
    sep_cells = []
    for alignment in alignments:
        if alignment == "center":
            sep_cells.append(":------:")
        elif alignment == "right":
            sep_cells.append("-------:")
        else:  # left (default)
            sep_cells.append("--------")

    sep_line = "|" + "|".join(sep_cells) + "|"
    lines.append(sep_line)

    # Data rows
    for row in rows:
        row_line = "| " + " | ".join(str(cell) for cell in row) + " |"
        lines.append(row_line)

    return "\n".join(lines)


def create_data_quality_table(
    row_count: int,
    column_count: int,
    null_rate: float,
    duplicate_count: int,
    memory_usage_mb: float | None = None,
) -> str:
    """
    Create data quality overview table.

    Args:
        row_count: Total rows in dataset
        column_count: Total columns
        null_rate: Null rate (0.0-1.0)
        duplicate_count: Number of duplicate rows
        memory_usage_mb: Optional memory usage in MB

    Returns:
        Markdown table string
    """
    headers = ["Metric", "Value"]
    rows = [
        ["**Total Rows**", f"{row_count:,}"],
        ["**Total Columns**", f"{column_count}"],
        ["**Null Rate**", f"{null_rate * 100:.1f}%"],
        ["**Duplicate Rows**", f"{duplicate_count:,}"],
    ]

    if memory_usage_mb is not None:
        rows.append(["**Memory Usage**", f"{memory_usage_mb:.1f} MB"])

    return format_markdown_table(headers, rows, alignments=["left", "right"])


def create_insight_distribution_table(
    insights: list[dict[str, Any]],
    strength_key: str = "strength",
    confidence_key: str = "confidence"
) -> str:
    """
    Create insight strength/confidence distribution table.

    Args:
        insights: List of insight dictionaries
        strength_key: Key for strength field
        confidence_key: Key for confidence field

    Returns:
        Markdown table string
    """
    # Count by strength
    strength_counts = {}
    for insight in insights:
        strength = insight.get(strength_key, "supporting")
        # Handle dict values (e.g., confidence: {"numeric": 0.85, "label": "HIGH"})
        if isinstance(strength, dict):
            strength = strength.get("label", "supporting").lower()
        strength_counts[strength] = strength_counts.get(strength, 0) + 1

    total = len(insights)

    headers = ["Strength", "Count", "Percentage"]
    rows = []

    for strength in ["key", "supporting", "contextual"]:
        count = strength_counts.get(strength, 0)
        pct = (count / total * 100) if total > 0 else 0
        rows.append([f"**{strength.title()}**", count, f"{pct:.1f}%"])

    return format_markdown_table(headers, rows, alignments=["left", "center", "right"])


def create_confidence_distribution_table(
    insights: list[dict[str, Any]],
    confidence_field: str = "confidence"
) -> str:
    """
    Create confidence level distribution table.

    Args:
        insights: List of insight dictionaries
        confidence_field: Key for confidence field (can be nested dict)

    Returns:
        Markdown table string
    """
    # Count by confidence level
    confidence_counts = {}

    for insight in insights:
        confidence_val = insight.get(confidence_field, {})

        # Handle nested confidence (e.g., {"label": "HIGH", "numeric": 0.85})
        if isinstance(confidence_val, dict):
            label = confidence_val.get("label", "UNKNOWN")
        else:
            label = str(confidence_val)

        confidence_counts[label] = confidence_counts.get(label, 0) + 1

    total = len(insights)

    headers = ["Confidence Level", "Count", "Percentage"]
    rows = []

    # Order: VERY HIGH, HIGH, MEDIUM, LOW
    for level in ["VERY HIGH", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
        count = confidence_counts.get(level, 0)
        if count > 0:  # Only show levels that exist
            pct = (count / total * 100) if total > 0 else 0
            rows.append([f"**{level}**", count, f"{pct:.1f}%"])

    return format_markdown_table(headers, rows, alignments=["left", "center", "right"])


def embed_chart(
    chart_id: str,
    title: str,
    charts_dir: Path | str = "charts",
    relative_path: bool = True
) -> str:
    """
    Embed chart reference in markdown.

    Creates both an image embed (for HTML rendering) and a link to interactive version.

    Args:
        chart_id: Chart identifier (without extension)
        title: Alt text for chart
        charts_dir: Directory containing charts (relative or absolute)
        relative_path: Use relative path (default) vs absolute

    Returns:
        Markdown with embedded chart

    Example:
        >>> embed_chart("revenue_bar", "Revenue by Region")
        ![Revenue by Region](charts/revenue_bar.svg)

        *[View interactive chart](charts/revenue_bar.json)*
    """
    charts_dir = Path(charts_dir)

    if relative_path:
        svg_path = str(charts_dir / f"{chart_id}.svg")
        json_path = str(charts_dir / f"{chart_id}.json")
    else:
        svg_path = str(charts_dir.resolve() / f"{chart_id}.svg")
        json_path = str(charts_dir.resolve() / f"{chart_id}.json")

    lines = []
    lines.append(f"![{title}]({svg_path})")
    lines.append("")
    lines.append(f"*[View interactive chart]({json_path})*")

    return "\n".join(lines)


def embed_chart_base64(
    svg_path: Path | str,
    title: str,
    as_html: bool = True
) -> str:
    """
    Embed SVG chart as base64 data URI for self-contained HTML.

    Args:
        svg_path: Path to SVG file
        title: Alt text for chart
        as_html: If True, return HTML img tag; if False, return markdown

    Returns:
        HTML img tag or markdown with data URI

    Example:
        >>> embed_chart_base64("outputs/charts/revenue.svg", "Revenue Chart")
        '<img src="data:image/svg+xml;base64,..." alt="Revenue Chart" />'
    """
    svg_path = Path(svg_path)

    if not svg_path.exists():
        # Return placeholder if file doesn't exist
        if as_html:
            return f'<p><em>Chart not found: {svg_path}</em></p>'
        return f"*Chart not found: {svg_path}*"

    # Read and encode SVG
    svg_content = svg_path.read_bytes()
    b64_data = base64.b64encode(svg_content).decode('utf-8')
    data_uri = f"data:image/svg+xml;base64,{b64_data}"

    if as_html:
        return f'<img src="{data_uri}" alt="{title}" style="max-width: 100%; height: auto;" />'
    else:
        return f"![{title}]({data_uri})"


def create_section_with_chart(
    section_title: str,
    section_content: list[str],
    chart_id: str | None = None,
    chart_title: str | None = None
) -> str:
    """
    Create markdown section with optional chart embed.

    Args:
        section_title: Section heading (e.g., "Key Findings")
        section_content: List of bullet points or paragraphs
        chart_id: Optional chart to embed
        chart_title: Optional chart title (defaults to section_title)

    Returns:
        Markdown section string
    """
    lines = []

    lines.append(f"## {section_title}")
    lines.append("")

    # Add content
    for item in section_content:
        if item.strip():
            lines.append(item)

    lines.append("")

    # Add chart if specified
    if chart_id:
        chart_title = chart_title or section_title
        lines.append(embed_chart(chart_id, chart_title))
        lines.append("")

    return "\n".join(lines)


def create_kpi_card_table(kpis: list[dict[str, Any]]) -> str:
    """
    Create KPI summary table.

    Args:
        kpis: List of KPI dicts with keys: name, value, change, status

    Returns:
        Markdown table string

    Example:
        >>> kpis = [
        ...     {"name": "Revenue", "value": "$1.2M", "change": "+15%", "status": "✅"},
        ...     {"name": "Margin", "value": "32%", "change": "-2%", "status": "⚠️"}
        ... ]
        >>> print(create_kpi_card_table(kpis))
    """
    headers = ["KPI", "Value", "Change", "Status"]
    rows = []

    for kpi in kpis:
        rows.append([
            f"**{kpi.get('name', '')}**",
            kpi.get('value', ''),
            kpi.get('change', ''),
            kpi.get('status', '')
        ])

    return format_markdown_table(headers, rows, alignments=["left", "right", "right", "center"])
