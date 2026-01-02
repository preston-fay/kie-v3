"""
Scatter Plot Data Builder

Generates Recharts-compatible JSON configurations for scatter plots.
"""

from typing import Any, List, Dict, Optional, Union
from pathlib import Path
import pandas as pd

from kie.base import ChartBuilder, RechartsConfig
from kie.brand.colors import KDSColors
from kie.charts.schema import (
    ScatterChartConfig,
    AxisConfig,
    TooltipConfig,
)


class ScatterPlotBuilder(ChartBuilder):
    """
    Builder for scatter plots using Recharts.

    Supports:
    - Single and multi-series scatter plots
    - Customizable point sizes and shapes
    - Color coding by category
    - Trend lines (optional)
    - KDS-compliant styling
    """

    def __init__(
        self,
        point_size: int = 6,
        show_legend: bool = True,
    ):
        """
        Initialize scatter plot builder.

        Args:
            point_size: Size of scatter points
            show_legend: Show legend for multi-series charts
        """
        self.point_size = point_size
        self.show_legend = show_legend

    def build(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        x_key: str,
        y_key: str,
        category_key: Optional[str] = None,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        colors: Optional[List[str]] = None,
        **kwargs,
    ) -> RechartsConfig:
        """
        Build scatter plot configuration.

        Args:
            data: Input data (DataFrame or list of dicts)
            x_key: Column name for X axis
            y_key: Column name for Y axis
            category_key: Optional column for categorizing points (colors them differently)
            title: Chart title
            subtitle: Chart subtitle
            colors: Custom colors (defaults to KDS palette)
            **kwargs: Additional configuration options

        Returns:
            RechartsConfig ready for JSON serialization
        """
        # Normalize data to list of dicts
        if isinstance(data, pd.DataFrame):
            data_list = data.to_dict("records")
        else:
            data_list = data

        # If category_key provided, group data by category
        if category_key:
            categories = list(set(item[category_key] for item in data_list))
            if colors is None:
                colors = KDSColors.get_chart_colors(len(categories))

            # Add color to each data point based on category
            category_color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(categories)}
            for item in data_list:
                item["fill"] = category_color_map[item[category_key]]
        else:
            # Single color for all points
            if colors is None:
                colors = [KDSColors.CHART_PALETTE[9]]  # Kearney Purple
            for item in data_list:
                item["fill"] = colors[0]

        # Build scatter config
        scatter_config = {
            "dataKey": y_key,
            "fill": colors[0] if not category_key else None,
            "shape": "circle",
            "r": self.point_size,
        }

        # Build axis configs
        x_axis = AxisConfig(
            dataKey=x_key,
            label={"value": x_key.replace("_", " ").title(), "position": "bottom"}
        )
        y_axis = AxisConfig(
            dataKey=y_key,
            label={"value": y_key.replace("_", " ").title(), "angle": -90, "position": "left"}
        )

        # Build chart config
        chart_config = ScatterChartConfig(
            title=title,
            subtitle=subtitle,
            xAxis=x_axis,
            yAxis=y_axis,
            scatter=scatter_config,
            tooltip=TooltipConfig(),
            gridLines=False,
            fontFamily="Inter, sans-serif",
            interactive=True,
        )

        # Create Recharts config
        recharts_config = RechartsConfig(
            chart_type="scatter",
            data=data_list,
            config=chart_config.model_dump(exclude_none=True),
            title=title,
            subtitle=subtitle,
        )

        return recharts_config


# Convenience function
def scatter_plot(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    x: str,
    y: str,
    category: Optional[str] = None,
    title: Optional[str] = None,
    output_path: Optional[Path] = None,
    **kwargs,
) -> RechartsConfig:
    """
    Quick function to create a scatter plot.

    Args:
        data: Input data
        x: X axis column
        y: Y axis column
        category: Optional category column for color coding
        title: Chart title
        output_path: Optional path to save JSON
        **kwargs: Additional options

    Returns:
        RechartsConfig

    Example:
        >>> data = [
        ...     {"price": 100, "sales": 1200, "region": "North"},
        ...     {"price": 120, "sales": 1050, "region": "North"},
        ...     {"price": 90, "sales": 1350, "region": "South"},
        ... ]
        >>> config = scatter_plot(
        ...     data,
        ...     x="price",
        ...     y="sales",
        ...     category="region",
        ...     title="Price vs Sales by Region"
        ... )
        >>> config.to_json(Path("outputs/charts/price_sales_scatter.json"))
    """
    builder = ScatterPlotBuilder(**kwargs)
    config = builder.build(data, x_key=x, y_key=y, category_key=category, title=title)

    if output_path:
        config.to_json(output_path)

    return config
