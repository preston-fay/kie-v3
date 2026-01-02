"""
Area Chart Data Builder

Generates Recharts-compatible JSON configurations for area charts.
"""

from typing import Any, List, Dict, Optional, Union
from pathlib import Path
import pandas as pd

from kie.base import ChartBuilder, RechartsConfig
from kie.brand.colors import KDSColors
from kie.charts.schema import (
    AreaChartConfig,
    AxisConfig,
    AreaConfig,
    DataLabelConfig,
    LegendConfig,
    TooltipConfig,
)


class AreaChartBuilder(ChartBuilder):
    """
    Builder for area charts using Recharts.

    Supports:
    - Single and multi-series area charts
    - Stacked area charts
    - Smooth and linear curves
    - Customizable fill opacity
    - KDS-compliant styling
    """

    def __init__(
        self,
        stacked: bool = False,
        curve_type: str = "monotone",
        fill_opacity: float = 0.6,
        show_data_labels: bool = False,
        show_legend: bool = True,
        stroke_width: int = 2,
    ):
        """
        Initialize area chart builder.

        Args:
            stacked: Whether to stack areas
            curve_type: "monotone", "linear", "step", "natural"
            fill_opacity: Opacity of filled area (0.0 to 1.0)
            show_data_labels: Show values at data points
            show_legend: Show legend for multi-series charts
            stroke_width: Line thickness in pixels
        """
        self.stacked = stacked
        self.curve_type = curve_type
        self.fill_opacity = fill_opacity
        self.show_data_labels = show_data_labels
        self.show_legend = show_legend
        self.stroke_width = stroke_width

    def build(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        x_key: str,
        y_keys: Union[str, List[str]],
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        colors: Optional[List[str]] = None,
        **kwargs,
    ) -> RechartsConfig:
        """
        Build area chart configuration.

        Args:
            data: Input data (DataFrame or list of dicts)
            x_key: Column name for X axis
            y_keys: Column name(s) for Y axis - string or list
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

        # Normalize y_keys to list
        if isinstance(y_keys, str):
            y_keys = [y_keys]

        # Get colors
        if colors is None:
            colors = KDSColors.get_chart_colors(len(y_keys))
        elif len(colors) < len(y_keys):
            colors.extend(KDSColors.get_chart_colors(len(y_keys) - len(colors)))

        # Build area configs
        areas = []
        stack_id = "stack1" if self.stacked else None

        for i, y_key in enumerate(y_keys):
            area_config = AreaConfig(
                dataKey=y_key,
                fill=colors[i],
                stroke=colors[i],
                strokeWidth=self.stroke_width,
                fillOpacity=self.fill_opacity,
                label=DataLabelConfig(
                    position="top",
                    fill=colors[i],
                    fontSize=11,
                    fontWeight=500,
                ) if self.show_data_labels else None,
            )
            areas.append(area_config)

        # Build axis configs
        x_axis = AxisConfig(dataKey=x_key)
        y_axis = AxisConfig(dataKey="value")

        # Build chart config
        chart_config = AreaChartConfig(
            title=title,
            subtitle=subtitle,
            xAxis=x_axis,
            yAxis=y_axis,
            areas=areas,
            stackId=stack_id,
            legend=LegendConfig() if self.show_legend and len(y_keys) > 1 else None,
            tooltip=TooltipConfig(),
            gridLines=False,
            fontFamily="Inter, sans-serif",
            interactive=True,
        )

        # Create Recharts config
        recharts_config = RechartsConfig(
            chart_type="area",
            data=data_list,
            config=chart_config.model_dump(exclude_none=True),
            title=title,
            subtitle=subtitle,
        )

        return recharts_config


# Convenience functions
def area_chart(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    x: str,
    y: Union[str, List[str]],
    title: Optional[str] = None,
    output_path: Optional[Path] = None,
    **kwargs,
) -> RechartsConfig:
    """
    Quick function to create an area chart.

    Args:
        data: Input data
        x: X axis column
        y: Y axis column(s)
        title: Chart title
        output_path: Optional path to save JSON
        **kwargs: Additional options

    Returns:
        RechartsConfig

    Example:
        >>> data = [
        ...     {"month": "Jan", "revenue": 1200},
        ...     {"month": "Feb", "revenue": 1350},
        ...     {"month": "Mar", "revenue": 1480},
        ... ]
        >>> config = area_chart(data, x="month", y="revenue", title="Revenue Growth")
        >>> config.to_json(Path("outputs/charts/revenue_growth.json"))
    """
    builder = AreaChartBuilder(**kwargs)
    config = builder.build(data, x_key=x, y_keys=y, title=title)

    if output_path:
        config.to_json(output_path)

    return config


def stacked_area_chart(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    x: str,
    y: List[str],
    title: Optional[str] = None,
    output_path: Optional[Path] = None,
) -> RechartsConfig:
    """
    Quick function to create a stacked area chart.

    Args:
        data: Input data
        x: X axis column
        y: List of Y axis columns to stack
        title: Chart title
        output_path: Optional path to save JSON

    Returns:
        RechartsConfig
    """
    builder = AreaChartBuilder(stacked=True)
    config = builder.build(data, x_key=x, y_keys=y, title=title)

    if output_path:
        config.to_json(output_path)

    return config
