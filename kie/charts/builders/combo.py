"""
Combo Chart Data Builder

Generates Recharts-compatible JSON configurations for combo charts (bar + line).
"""

from typing import Any, List, Dict, Optional, Union
from pathlib import Path
import pandas as pd

from kie.base import ChartBuilder, RechartsConfig
from kie.brand.colors import KDSColors
from kie.charts.schema import (
    ComboChartConfig,
    AxisConfig,
    BarConfig,
    LineConfig,
    DataLabelConfig,
    LegendConfig,
    TooltipConfig,
)


class ComboChartBuilder(ChartBuilder):
    """
    Builder for combo charts (bar + line) using Recharts.

    Supports:
    - Multiple bars and lines in same chart
    - Dual Y-axes (optional)
    - KDS-compliant styling
    - Smart color allocation

    Common use case: Show actual vs target, or values vs trends.
    """

    def __init__(
        self,
        show_data_labels: bool = True,
        show_legend: bool = True,
    ):
        """
        Initialize combo chart builder.

        Args:
            show_data_labels: Show values on bars and lines
            show_legend: Show legend
        """
        self.show_data_labels = show_data_labels
        self.show_legend = show_legend

    def build(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        x_key: str,
        bar_keys: Union[str, List[str]],
        line_keys: Union[str, List[str]],
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        colors: Optional[List[str]] = None,
        **kwargs,
    ) -> RechartsConfig:
        """
        Build combo chart configuration.

        Args:
            data: Input data (DataFrame or list of dicts)
            x_key: Column name for X axis (categories)
            bar_keys: Column name(s) for bar series
            line_keys: Column name(s) for line series
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

        # Normalize keys to lists
        if isinstance(bar_keys, str):
            bar_keys = [bar_keys]
        if isinstance(line_keys, str):
            line_keys = [line_keys]

        total_series = len(bar_keys) + len(line_keys)

        # Get colors
        if colors is None:
            colors = KDSColors.get_chart_colors(total_series)
        elif len(colors) < total_series:
            colors.extend(KDSColors.get_chart_colors(total_series - len(colors)))

        # Build bar configs
        bars = []
        for i, bar_key in enumerate(bar_keys):
            bar_config = BarConfig(
                dataKey=bar_key,
                fill=colors[i],
                radius=[4, 4, 0, 0],
                label=DataLabelConfig(
                    position="top",
                    fill="currentColor",
                    fontSize=12,
                    fontWeight=500,
                ) if self.show_data_labels else None,
            )
            bars.append(bar_config)

        # Build line configs
        lines = []
        color_offset = len(bar_keys)
        for i, line_key in enumerate(line_keys):
            line_config = LineConfig(
                dataKey=line_key,
                stroke=colors[color_offset + i],
                strokeWidth=3,
                dot={"r": 5, "fill": colors[color_offset + i]},
                activeDot={"r": 7, "fill": colors[color_offset + i]},
                label=DataLabelConfig(
                    position="top",
                    fill=colors[color_offset + i],
                    fontSize=12,
                    fontWeight=600,
                ) if self.show_data_labels else None,
            )
            lines.append(line_config)

        # Build axis configs
        x_axis = AxisConfig(dataKey=x_key)
        y_axis = AxisConfig(dataKey="value")

        # Build chart config
        chart_config = ComboChartConfig(
            title=title,
            subtitle=subtitle,
            xAxis=x_axis,
            yAxis=y_axis,
            bars=bars,
            lines=lines,
            legend=LegendConfig() if self.show_legend else None,
            tooltip=TooltipConfig(),
            gridLines=False,
            fontFamily="Inter, sans-serif",
            interactive=True,
        )

        # Create Recharts config
        recharts_config = RechartsConfig(
            chart_type="combo",
            data=data_list,
            config=chart_config.model_dump(exclude_none=True),
            title=title,
            subtitle=subtitle,
        )

        return recharts_config


# Convenience function
def combo_chart(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    x: str,
    bars: Union[str, List[str]],
    lines: Union[str, List[str]],
    title: Optional[str] = None,
    output_path: Optional[Path] = None,
    **kwargs,
) -> RechartsConfig:
    """
    Quick function to create a combo chart (bar + line).

    Args:
        data: Input data
        x: X axis column
        bars: Bar series column(s)
        lines: Line series column(s)
        title: Chart title
        output_path: Optional path to save JSON
        **kwargs: Additional options

    Returns:
        RechartsConfig

    Example:
        >>> data = [
        ...     {"month": "Jan", "actual": 1200, "target": 1000},
        ...     {"month": "Feb", "actual": 1350, "target": 1100},
        ...     {"month": "Mar", "actual": 1180, "target": 1200},
        ... ]
        >>> config = combo_chart(
        ...     data,
        ...     x="month",
        ...     bars="actual",
        ...     lines="target",
        ...     title="Actual vs Target Sales"
        ... )
        >>> config.to_json(Path("outputs/charts/actual_vs_target.json"))
    """
    builder = ComboChartBuilder(**kwargs)
    config = builder.build(data, x_key=x, bar_keys=bars, line_keys=lines, title=title)

    if output_path:
        config.to_json(output_path)

    return config
