"""
Bar Chart Data Builder

Generates Recharts-compatible JSON configurations for bar charts.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from kie.base import ChartBuilder, RechartsConfig
from kie.brand.colors import KDSColors
from kie.charts.schema import (
    AxisConfig,
    BarChartConfig,
    BarConfig,
    DataLabelConfig,
    LegendConfig,
    TooltipConfig,
)


class BarChartBuilder(ChartBuilder):
    """
    Builder for bar charts using Recharts.

    Supports:
    - Single and multi-series bar charts
    - Horizontal and vertical layouts
    - Grouped and stacked bars
    - KDS-compliant styling
    - Smart color selection
    - Automatic number formatting
    """

    def __init__(
        self,
        layout: str = "horizontal",
        stacked: bool = False,
        show_data_labels: bool = True,
        show_legend: bool = True,
    ):
        """
        Initialize bar chart builder.

        Args:
            layout: "horizontal" (vertical bars) or "vertical" (horizontal bars)
            stacked: Whether to stack bars
            show_data_labels: Show values on bars
            show_legend: Show legend for multi-series charts
        """
        self.layout = layout
        self.stacked = stacked
        self.show_data_labels = show_data_labels
        self.show_legend = show_legend

    def build(
        self,
        data: pd.DataFrame | list[dict[str, Any]],
        x_key: str,
        y_keys: str | list[str],
        title: str | None = None,
        subtitle: str | None = None,
        colors: list[str] | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """
        Build bar chart configuration.

        Args:
            data: Input data (DataFrame or list of dicts)
            x_key: Column name for X axis (categories)
            y_keys: Column name(s) for Y axis (values) - string or list
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
            # Extend with KDS colors if not enough provided
            colors.extend(KDSColors.get_chart_colors(len(y_keys) - len(colors)))

        # Build bar configs
        bars = []

        for i, y_key in enumerate(y_keys):
            bar_config = BarConfig(
                dataKey=y_key,
                fill=colors[i],
                radius=[4, 4, 0, 0] if self.layout == "horizontal" else [0, 4, 4, 0],
                label=DataLabelConfig(
                    position="top" if self.layout == "horizontal" else "right",
                    fill="currentColor",
                    fontSize=12,
                    fontWeight=500,
                ) if self.show_data_labels else None,
            )
            bars.append(bar_config)

        # Build axis configs
        if self.layout == "horizontal":
            x_axis = AxisConfig(dataKey=x_key)
            y_axis = AxisConfig(dataKey="value")
        else:
            x_axis = AxisConfig(dataKey="value")
            y_axis = AxisConfig(dataKey=x_key)

        # Build chart config
        chart_config = BarChartConfig(
            title=title,
            subtitle=subtitle,
            xAxis=x_axis,
            yAxis=y_axis,
            bars=bars,
            layout=self.layout,
            legend=LegendConfig() if self.show_legend and len(y_keys) > 1 else None,
            tooltip=TooltipConfig(),
            gridLines=False,
            fontFamily=KDSColors.__dict__.get("FONT_FAMILY", "Inter, sans-serif"),
            interactive=True,
        )

        # Create Recharts config
        recharts_config = RechartsConfig(
            chart_type="bar",
            data=data_list,
            config=chart_config.model_dump(exclude_none=True),
            title=title,
            subtitle=subtitle,
        )

        return recharts_config

    def build_grouped(
        self,
        data: pd.DataFrame | list[dict[str, Any]],
        x_key: str,
        y_keys: list[str],
        title: str | None = None,
        colors: list[str] | None = None,
    ) -> RechartsConfig:
        """
        Build grouped bar chart (multiple bars per category).

        Args:
            data: Input data
            x_key: Category column
            y_keys: List of value columns
            title: Chart title
            colors: Custom colors

        Returns:
            RechartsConfig for grouped bar chart
        """
        return self.build(
            data=data,
            x_key=x_key,
            y_keys=y_keys,
            title=title,
            colors=colors,
        )

    def build_stacked(
        self,
        data: pd.DataFrame | list[dict[str, Any]],
        x_key: str,
        y_keys: list[str],
        title: str | None = None,
        colors: list[str] | None = None,
    ) -> RechartsConfig:
        """
        Build stacked bar chart.

        Args:
            data: Input data
            x_key: Category column
            y_keys: List of value columns to stack
            title: Chart title
            colors: Custom colors

        Returns:
            RechartsConfig for stacked bar chart
        """
        builder = BarChartBuilder(
            layout=self.layout,
            stacked=True,
            show_data_labels=self.show_data_labels,
            show_legend=True,  # Always show legend for stacked
        )
        return builder.build(
            data=data,
            x_key=x_key,
            y_keys=y_keys,
            title=title,
            colors=colors,
        )


# Convenience functions
def bar_chart(
    data: pd.DataFrame | list[dict[str, Any]],
    x: str,
    y: str | list[str],
    title: str | None = None,
    output_path: Path | None = None,
    **kwargs,
) -> RechartsConfig:
    """
    Quick function to create a bar chart.

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
        ...     {"region": "North", "revenue": 1200},
        ...     {"region": "South", "revenue": 980},
        ...     {"region": "East", "revenue": 1450},
        ... ]
        >>> config = bar_chart(data, x="region", y="revenue", title="Revenue by Region")
        >>> config.to_json(Path("outputs/charts/revenue.json"))
    """
    builder = BarChartBuilder(**kwargs)
    config = builder.build(data, x_key=x, y_keys=y, title=title)

    if output_path:
        config.to_json(output_path)

    return config


def horizontal_bar_chart(
    data: pd.DataFrame | list[dict[str, Any]],
    x: str,
    y: str | list[str],
    title: str | None = None,
    output_path: Path | None = None,
) -> RechartsConfig:
    """
    Quick function to create a horizontal bar chart.

    Args:
        data: Input data
        x: Category column
        y: Value column(s)
        title: Chart title
        output_path: Optional path to save JSON

    Returns:
        RechartsConfig
    """
    builder = BarChartBuilder(layout="vertical")
    config = builder.build(data, x_key=x, y_keys=y, title=title)

    if output_path:
        config.to_json(output_path)

    return config
