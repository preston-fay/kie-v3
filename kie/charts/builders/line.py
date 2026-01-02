"""
Line Chart Data Builder

Generates Recharts-compatible JSON configurations for line charts.
"""

from typing import Any, List, Dict, Optional, Union
from pathlib import Path
import pandas as pd

from kie.base import ChartBuilder, RechartsConfig
from kie.brand.colors import KDSColors
from kie.charts.schema import (
    LineChartConfig,
    AxisConfig,
    LineConfig,
    DataLabelConfig,
    LegendConfig,
    TooltipConfig,
)


class LineChartBuilder(ChartBuilder):
    """
    Builder for line charts using Recharts.

    Supports:
    - Single and multi-series line charts
    - Smooth and linear curves
    - Data point markers
    - KDS-compliant styling
    - Smart color selection
    """

    def __init__(
        self,
        curve_type: str = "monotone",
        show_dots: bool = True,
        show_data_labels: bool = False,
        show_legend: bool = True,
        stroke_width: int = 2,
    ):
        """
        Initialize line chart builder.

        Args:
            curve_type: "monotone", "linear", "step", "natural"
            show_dots: Show data point markers
            show_data_labels: Show values at data points
            show_legend: Show legend for multi-series charts
            stroke_width: Line thickness in pixels
        """
        self.curve_type = curve_type
        self.show_dots = show_dots
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
        Build line chart configuration.

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

        # Build line configs
        lines = []
        for i, y_key in enumerate(y_keys):
            line_config = LineConfig(
                dataKey=y_key,
                stroke=colors[i],
                strokeWidth=self.stroke_width,
                dot={"r": 4, "fill": colors[i]} if self.show_dots else False,
                activeDot={"r": 6, "fill": colors[i]},
                label=DataLabelConfig(
                    position="top",
                    fill=colors[i],
                    fontSize=11,
                    fontWeight=500,
                ) if self.show_data_labels else None,
            )
            lines.append(line_config)

        # Build axis configs
        x_axis = AxisConfig(dataKey=x_key)
        y_axis = AxisConfig(dataKey="value")

        # Build chart config
        chart_config = LineChartConfig(
            title=title,
            subtitle=subtitle,
            xAxis=x_axis,
            yAxis=y_axis,
            lines=lines,
            legend=LegendConfig() if self.show_legend and len(y_keys) > 1 else None,
            tooltip=TooltipConfig(),
            gridLines=False,
            fontFamily="Inter, sans-serif",
            interactive=True,
        )

        # Create Recharts config
        recharts_config = RechartsConfig(
            chart_type="line",
            data=data_list,
            config=chart_config.model_dump(exclude_none=True),
            title=title,
            subtitle=subtitle,
        )

        return recharts_config


# Convenience functions
def line_chart(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    x: str,
    y: Union[str, List[str]],
    title: Optional[str] = None,
    output_path: Optional[Path] = None,
    **kwargs,
) -> RechartsConfig:
    """
    Quick function to create a line chart.

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
        ...     {"month": "Jan", "sales": 1200},
        ...     {"month": "Feb", "sales": 1350},
        ...     {"month": "Mar", "sales": 1180},
        ... ]
        >>> config = line_chart(data, x="month", y="sales", title="Monthly Sales")
        >>> config.to_json(Path("outputs/charts/sales.json"))
    """
    builder = LineChartBuilder(**kwargs)
    config = builder.build(data, x_key=x, y_keys=y, title=title)

    if output_path:
        config.to_json(output_path)

    return config
