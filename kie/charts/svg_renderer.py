"""
SVG Chart Renderer using Pygal

Converts RechartsConfig JSON to actual SVG files using Pygal library.
Pure Python - no Node.js, no system dependencies.

CRITICAL: All charts MUST comply with KDS (Kearney Design System):
- Pie charts: 2-4 segments only (strict enforcement)
- Gauge charts: Use sparingly - prefer progress bars
- No gridlines (absolute rule)
- KDS colors only (#7823DC, #9150E1, etc.)
- Inter/Arial typography
- Data labels required
- No axis lines/tick lines
"""

from pathlib import Path
from typing import Any

import pygal
from pygal.style import Style

from kie.base import RechartsConfig
from kie.charts.formatting import format_number, format_currency, format_percentage


# KDS Color Palette (10-color chart palette)
KDS_COLORS = [
    '#7823DC',  # Kearney Purple (primary)
    '#9150E1',  # Bright Purple
    '#AF7DEB',  # Medium Purple
    '#C8A5F0',  # Medium Light Purple
    '#E0D2FA',  # Light Purple
    '#787878',  # Dark Gray
    '#A5A6A5',  # Medium Gray
    '#D2D2D2',  # Light Gray
    '#4B4B4B',  # Charcoal
    '#1E1E1E',  # Kearney Black
]

# KDS Style for Pygal - Enforces brand compliance
kds_style = Style(
    background='white',
    plot_background='white',
    foreground='#787878',
    foreground_strong='#1E1E1E',
    foreground_subtle='#D2D2D2',
    colors=KDS_COLORS,
    font_family='Inter, Arial, sans-serif',  # KDS typography
    label_font_size=12,
    major_label_font_size=12,
    value_font_size=12,
    title_font_size=16,
    legend_font_size=12,
    no_data_font_size=14,
)


def kds_value_formatter(value):
    """
    Format numeric values for chart display using smart number formatting.

    Uses K/M/B abbreviations for large numbers to improve readability.

    Args:
        value: Numeric value to format

    Returns:
        Formatted string (e.g., "1.2M" instead of "1234567")
    """
    if value is None:
        return ''
    return format_number(value, precision=1, abbreviate=True)


def validate_pie_chart_data(data: list[dict]) -> tuple[bool, str]:
    """
    Validate pie chart against KDS 2-4 segment rule.

    KDS Guidelines (kds/KDS_AI_GUIDELINES.md:328):
    - Pie charts FORBIDDEN with >4 segments
    - Use sparingly (prefer bar charts)
    - Allowed only with 2-4 segments

    Args:
        data: List of chart data dictionaries

    Returns:
        Tuple of (is_valid, message)
    """
    num_segments = len(data)

    if num_segments < 2:
        return False, "Pie chart requires at least 2 segments (use KPI card for single value)"

    if num_segments > 4:
        return False, f"KDS forbids pie charts with {num_segments} segments (max: 4). Use bar chart instead."

    if num_segments == 2:
        return True, "⚠️  Consider bar chart - pie charts should be used sparingly (KDS)"

    return True, f"OK: {num_segments} segments (within KDS 2-4 range)"


def svg_to_png(svg_path: Path, png_path: Path, dpi: int = 300) -> Path:
    """
    Convert SVG file to high-resolution PNG for PowerPoint embedding.

    Args:
        svg_path: Path to source SVG file
        png_path: Path to save PNG file
        dpi: Resolution in dots per inch (default: 300 for print quality)

    Returns:
        Path to saved PNG file

    Raises:
        ImportError: If cairosvg not installed
        FileNotFoundError: If SVG file doesn't exist
    """
    if not svg_path.exists():
        raise FileNotFoundError(f"SVG file not found: {svg_path}")

    try:
        import cairosvg
    except ImportError:
        raise ImportError(
            "cairosvg not installed. Install with: pip install cairosvg\n"
            "On macOS: brew install cairo pkg-config\n"
            "On Ubuntu: sudo apt-get install libcairo2-dev"
        )

    # Convert SVG to PNG with high resolution
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        dpi=dpi,
    )

    return png_path


def to_svg(config: RechartsConfig, output_path: Path) -> Path:
    """
    Convert RechartsConfig to SVG using Pygal.

    Args:
        config: Recharts chart configuration
        output_path: Path to save SVG file

    Returns:
        Path to saved SVG file

    Raises:
        ValueError: If chart type not supported or KDS validation fails
    """
    chart_type = config.chart_type
    data = config.data
    title = config.title

    # KDS Validation: Pie charts must have 2-4 segments
    if chart_type in ["pie", "donut"]:
        is_valid, message = validate_pie_chart_data(data)
        if not is_valid:
            raise ValueError(f"KDS Validation Failed: {message}")
        if "⚠️" in message:
            print(f"   {message}")

    # Create appropriate Pygal chart
    if chart_type == "bar":
        chart = _create_bar_chart(data, title, config)
    elif chart_type == "line":
        chart = _create_line_chart(data, title, config)
    elif chart_type == "pie":
        chart = _create_pie_chart(data, title, config)
    elif chart_type == "donut":
        chart = _create_donut_chart(data, title, config)
    elif chart_type == "radar":
        chart = _create_radar_chart(data, title, config)
    elif chart_type == "funnel":
        chart = _create_funnel_chart(data, title, config)
    elif chart_type == "gauge":
        print("   ⚠️  Gauge chart used - KDS recommends using sparingly (prefer progress bars)")
        chart = _create_gauge_chart(data, title, config)
    elif chart_type == "box":
        chart = _create_box_chart(data, title, config)
    elif chart_type == "treemap":
        chart = _create_treemap_chart(data, title, config)
    elif chart_type == "world_map":
        chart = _create_world_map(data, title, config)
    elif chart_type == "scatter":
        chart = _create_scatter_chart(data, title, config)
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")

    # Render to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chart.render_to_file(str(output_path))

    return output_path


# ============================================================================
# STANDARD BUSINESS CHARTS
# ============================================================================

def _create_bar_chart(data: list[dict[str, Any]], title: str | None, config: RechartsConfig) -> pygal.Bar:
    """Create KDS-compliant bar chart."""
    chart = pygal.Bar(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
        show_legend=False,
        print_values=True,  # KDS: Data labels required
        print_values_position='top',
        show_x_guides=False,  # KDS: No gridlines
        show_y_guides=False,  # KDS: No gridlines
        value_formatter=kds_value_formatter,  # Smart number formatting (K/M/B)
    )

    if title:
        chart.title = title

    # Extract x-axis labels and values
    x_labels = []
    values = []

    for item in data:
        # Handle various data formats
        category = item.get('category', item.get('name', item.get('x', 'Unknown')))
        value = item.get('value', item.get('y', 0))

        x_labels.append(str(category))
        values.append(value)

    chart.x_labels = x_labels
    chart.add('', values)  # Empty label since show_legend=False

    return chart


def _create_line_chart(data: list[dict[str, Any]], title: str | None, config: RechartsConfig) -> pygal.Line:
    """Create KDS-compliant line chart."""
    chart = pygal.Line(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
        show_legend=True,
        print_values=False,
        dots_size=4,
        show_x_guides=False,  # KDS: No gridlines
        show_y_guides=False,  # KDS: No gridlines
        value_formatter=kds_value_formatter,  # Smart number formatting (K/M/B)
    )

    if title:
        chart.title = title

    # Group data by series
    series_data = {}
    x_labels = []

    for item in data:
        group = item.get('group', item.get('series', 'Series'))
        x_val = item.get('x', item.get('category', item.get('name', '')))
        y_val = item.get('y', item.get('value', 0))

        if x_val not in x_labels:
            x_labels.append(str(x_val))

        if group not in series_data:
            series_data[group] = []
        series_data[group].append(y_val)

    chart.x_labels = x_labels

    # Add each series
    for series_name, values in series_data.items():
        chart.add(series_name, values)

    return chart


def _create_scatter_chart(data: list[dict[str, Any]], title: str | None, config: RechartsConfig) -> pygal.XY:
    """
    Create KDS-compliant scatter plot using Pygal XY chart.

    Expected data format:
    [
        {"x": 1.5, "y": 2.3},
        {"x": 2.1, "y": 3.5},
        ...
    ]
    """
    chart = pygal.XY(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
        show_legend=False,
        print_values=False,  # Too cluttered for scatter plots
        dots_size=3,
        stroke=False,  # No lines between points
        show_x_guides=False,  # KDS: No gridlines
        show_y_guides=False,  # KDS: No gridlines
    )

    if title:
        chart.title = title

    # Extract x-y coordinate pairs
    xy_data = []
    for item in data:
        x_val = item.get('x', 0)
        y_val = item.get('y', 0)
        xy_data.append((x_val, y_val))

    # Add single series (unlabeled since show_legend=False)
    chart.add('', xy_data)

    return chart


def _create_pie_chart(data: list[dict[str, Any]], title: str | None, config: RechartsConfig) -> pygal.Pie:
    """
    Create KDS-compliant pie chart.

    CRITICAL: KDS allows 2-4 segments only. Validation must have passed before this.
    """
    chart = pygal.Pie(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
        show_legend=True,
        print_values=True,  # KDS: Data labels required
        print_values_position='outside',
        value_formatter=kds_value_formatter,  # Smart number formatting (K/M/B)
    )

    if title:
        chart.title = title

    # Add each slice
    for item in data:
        label = item.get('category', item.get('name', item.get('label', 'Unknown')))
        value = item.get('value', 0)
        chart.add(str(label), value)

    return chart


def _create_donut_chart(data: list[dict[str, Any]], title: str | None, config: RechartsConfig) -> pygal.Pie:
    """Create KDS-compliant donut chart (pie with inner radius)."""
    chart = pygal.Pie(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
        show_legend=True,
        print_values=True,
        print_values_position='outside',
        inner_radius=0.4,  # Creates donut effect
        value_formatter=kds_value_formatter,  # Smart number formatting (K/M/B)
    )

    if title:
        chart.title = title

    for item in data:
        label = item.get('category', item.get('name', 'Unknown'))
        value = item.get('value', 0)
        chart.add(str(label), value)

    return chart


# ============================================================================
# CONSULTING SPECIALTY CHARTS
# ============================================================================

def _create_radar_chart(data: list[dict[str, Any]], title: str | None, config: RechartsConfig) -> pygal.Radar:
    """Create KDS-compliant radar chart for multi-dimensional comparisons."""
    chart = pygal.Radar(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
        show_legend=True,
        print_values=False,
        value_formatter=kds_value_formatter,  # Smart number formatting (K/M/B)
    )

    if title:
        chart.title = title

    # Extract dimensions and values
    dimensions = [item.get('dimension', item.get('category', item.get('name', 'Unknown'))) for item in data]
    values = [item.get('value', 0) for item in data]

    chart.x_labels = dimensions
    chart.add('Performance', values)

    return chart


def _create_funnel_chart(data: list[dict[str, Any]], title: str | None, config: RechartsConfig) -> pygal.Funnel:
    """Create KDS-compliant funnel chart for conversion analysis."""
    chart = pygal.Funnel(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
        show_legend=False,
        value_formatter=kds_value_formatter,  # Smart number formatting (K/M/B)
    )

    if title:
        chart.title = title

    # Funnel stages sorted by value descending
    sorted_data = sorted(data, key=lambda x: x.get('value', 0), reverse=True)

    for item in sorted_data:
        stage = item.get('stage', item.get('category', item.get('name', 'Unknown')))
        value = item.get('value', 0)
        chart.add(str(stage), value)

    return chart


def _create_gauge_chart(data: list[dict[str, Any]], title: str | None, config: RechartsConfig) -> pygal.Gauge:
    """
    Create KDS-compliant gauge chart.

    WARNING: KDS recommends using gauges sparingly - prefer progress bars.
    """
    chart = pygal.Gauge(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
        human_readable=True,
        value_formatter=kds_value_formatter,  # Smart number formatting (K/M/B)
    )

    if title:
        chart.title = title

    # Assumes single value data
    if data:
        label = data[0].get('label', data[0].get('name', 'Value'))
        value = data[0].get('value', 0)
        chart.add(str(label), value)

    return chart


def _create_box_chart(data: list[dict[str, Any]], title: str | None, config: RechartsConfig) -> pygal.Box:
    """Create KDS-compliant box plot for statistical distributions."""
    chart = pygal.Box(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
        show_legend=True,
        value_formatter=kds_value_formatter,  # Smart number formatting (K/M/B)
    )

    if title:
        chart.title = title

    # Group data by category
    categories = {}
    for item in data:
        category = item.get('category', item.get('group', 'Data'))
        value = item.get('value', 0)

        if category not in categories:
            categories[category] = []
        categories[category].append(value)

    # Add box plots
    for category, values in categories.items():
        chart.add(str(category), values)

    return chart


def _create_treemap_chart(data: list[dict[str, Any]], title: str | None, config: RechartsConfig) -> pygal.Treemap:
    """Create KDS-compliant treemap for hierarchical data."""
    chart = pygal.Treemap(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
        value_formatter=kds_value_formatter,  # Smart number formatting (K/M/B)
    )

    if title:
        chart.title = title

    # Add hierarchical data
    for item in data:
        label = item.get('label', item.get('name', item.get('category', 'Unknown')))
        value = item.get('value', 0)
        chart.add(str(label), value)

    return chart


def _create_world_map(data: list[dict[str, Any]], title: str | None, config: RechartsConfig):
    """Create KDS-compliant world map visualization."""
    try:
        from pygal.maps.world import World
    except (ImportError, AttributeError):
        # Fallback to bar chart if world maps not available
        print("   ⚠️  World maps not available - using bar chart instead")
        return _create_bar_chart(data, title, config)

    chart = World(
        style=kds_style,
        width=800,
        height=400,
        explicit_size=True,
    )

    if title:
        chart.title = title

    # Group data by country code
    country_data = {}
    for item in data:
        country_code = item.get('country_code', item.get('code', 'us'))
        value = item.get('value', 0)
        country_data[country_code.lower()] = value

    chart.add('', country_data)

    return chart
