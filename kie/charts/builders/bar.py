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
from kie.formatting.field_registry import FieldRegistry


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

        # Beautify field names for display
        x_label = FieldRegistry.beautify(x_key)
        y_labels = {y_key: FieldRegistry.beautify(y_key) for y_key in y_keys}

        # Rename columns in data for client-friendly display
        beautified_data = []
        for row in data_list:
            new_row = {}
            for key, value in row.items():
                if key == x_key:
                    new_row[x_label] = value
                elif key in y_labels:
                    new_row[y_labels[key]] = value
                else:
                    new_row[key] = value
            beautified_data.append(new_row)

        # Get colors
        if colors is None:
            colors = KDSColors.get_chart_colors(len(y_keys))
        elif len(colors) < len(y_keys):
            # Extend with KDS colors if not enough provided
            colors.extend(KDSColors.get_chart_colors(len(y_keys) - len(colors)))

        # Build bar configs (using beautified keys)
        bars = []

        for i, y_key in enumerate(y_keys):
            bar_config = BarConfig(
                dataKey=y_labels[y_key],  # Use beautified name
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

        # Build axis configs (using beautified keys)
        if self.layout == "horizontal":
            x_axis = AxisConfig(dataKey=x_label)
            y_axis = AxisConfig(dataKey="value")
        else:
            x_axis = AxisConfig(dataKey="value")
            y_axis = AxisConfig(dataKey=x_label)

        # Detect formatters for smart number formatting
        formatters = self._detect_formatters(data, y_keys)

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

        # Create Recharts config (using beautified data)
        config_dict = chart_config.model_dump(exclude_none=True)

        # Add formatters to config for frontend consumption
        if formatters:
            config_dict["formatters"] = formatters

        recharts_config = RechartsConfig(
            chart_type="bar",
            data=beautified_data,
            config=config_dict,
            title=title,
            subtitle=subtitle,
        )

        return recharts_config

    def _detect_formatters(self, data: pd.DataFrame | list[dict[str, Any]], y_keys: list[str]) -> dict[str, Any]:
        """
        Detect appropriate formatters for Y-axis columns based on data characteristics.

        Args:
            data: Input data
            y_keys: Y-axis column names

        Returns:
            Dictionary with formatter specifications for yAxis and tooltip
        """
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data

        formatters = {}

        for y_key in y_keys:
            if y_key not in df.columns:
                continue

            col_data = df[y_key].dropna()
            if len(col_data) == 0:
                continue

            # Check column name for hints
            col_lower = y_key.lower()

            # Currency detection
            if any(keyword in col_lower for keyword in ['revenue', 'cost', 'price', 'sales', 'profit', 'margin', 'value', 'amount']):
                formatters[y_key] = {
                    "type": "currency",
                    "currency": "$",
                    "abbreviate": bool(col_data.max() >= 1000)  # Use K/M/B for large numbers
                }
            # Percentage detection
            elif any(keyword in col_lower for keyword in ['percent', 'rate', '%', 'share', 'ratio']):
                # Check if values are 0-1 (need multiply) or 0-100 (don't multiply)
                is_decimal = col_data.max() <= 1.0
                formatters[y_key] = {
                    "type": "percentage",
                    "multiply_by_100": bool(is_decimal)
                }
            # Large number detection
            elif col_data.max() >= 1000:
                formatters[y_key] = {
                    "type": "number",
                    "abbreviate": True
                }
            # Small decimal detection
            elif col_data.max() < 10 and (col_data % 1 != 0).any():
                formatters[y_key] = {
                    "type": "number",
                    "precision": 2,
                    "abbreviate": False
                }

        # If we detected any formatters, structure them for frontend
        if formatters:
            # For now, apply the first Y column's formatter to the Y-axis
            first_formatter = formatters.get(y_keys[0], {})
            return {
                "yAxis": first_formatter,
                "tooltip": formatters  # Pass all formatters for tooltip
            }

        return {}

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
