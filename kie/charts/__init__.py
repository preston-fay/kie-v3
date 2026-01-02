"""
KIE v3 Charts Module

Unified interface for generating Recharts-compatible JSON configurations.
"""

# Chart builders
from kie.charts.builders.bar import (
    BarChartBuilder,
    bar_chart,
    horizontal_bar_chart,
)
from kie.charts.builders.line import (
    LineChartBuilder,
    line_chart,
)
from kie.charts.builders.area import (
    AreaChartBuilder,
    area_chart,
    stacked_area_chart,
)
from kie.charts.builders.pie import (
    PieChartBuilder,
    DonutChartBuilder,
    pie_chart,
    donut_chart,
)
from kie.charts.builders.scatter import (
    ScatterPlotBuilder,
    scatter_plot,
)
from kie.charts.builders.combo import (
    ComboChartBuilder,
    combo_chart,
)
from kie.charts.builders.waterfall import (
    WaterfallChartBuilder,
    waterfall_chart,
)

# Factory
from kie.charts.factory import ChartFactory, create_chart

# Formatting utilities
from kie.charts.formatting import (
    format_number,
    format_currency,
    format_percentage,
    format_change,
    generate_label,
    calculate_percentages,
    smart_round,
    format_axis_label,
)

# Schema
from kie.charts.schema import (
    RechartsSchema,
    AxisConfig,
    DataLabelConfig,
    LegendConfig,
    TooltipConfig,
    BarConfig,
    LineConfig,
    AreaConfig,
    PieConfig,
    validate_kds_compliance,
)

__all__ = [
    # Builders
    "BarChartBuilder",
    "LineChartBuilder",
    "AreaChartBuilder",
    "PieChartBuilder",
    "DonutChartBuilder",
    "ScatterPlotBuilder",
    "ComboChartBuilder",
    "WaterfallChartBuilder",
    # Convenience functions
    "bar_chart",
    "horizontal_bar_chart",
    "line_chart",
    "area_chart",
    "stacked_area_chart",
    "pie_chart",
    "donut_chart",
    "scatter_plot",
    "combo_chart",
    "waterfall_chart",
    # Factory
    "ChartFactory",
    "create_chart",
    # Formatting
    "format_number",
    "format_currency",
    "format_percentage",
    "format_change",
    "generate_label",
    "calculate_percentages",
    "smart_round",
    "format_axis_label",
    # Schema
    "RechartsSchema",
    "AxisConfig",
    "DataLabelConfig",
    "LegendConfig",
    "TooltipConfig",
    "BarConfig",
    "LineConfig",
    "AreaConfig",
    "PieConfig",
    "validate_kds_compliance",
]
