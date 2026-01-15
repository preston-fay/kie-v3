"""
Line Chart Data Builder

Generates Recharts-compatible JSON configurations for line charts.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from kie.base import ChartBuilder, RechartsConfig
from kie.brand.colors import KDSColors
from kie.charts.schema import (
    AxisConfig,
    DataLabelConfig,
    LegendConfig,
    LineChartConfig,
    LineConfig,
    TooltipConfig,
)
from kie.formatting.field_registry import FieldRegistry


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
        data: pd.DataFrame | list[dict[str, Any]],
        x_key: str,
        y_keys: str | list[str],
        title: str | None = None,
        subtitle: str | None = None,
        colors: list[str] | None = None,
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
            colors.extend(KDSColors.get_chart_colors(len(y_keys) - len(colors)))

        # Build line configs (using beautified keys)
        lines = []
        for i, y_key in enumerate(y_keys):
            line_config = LineConfig(
                dataKey=y_labels[y_key],  # Use beautified name
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

        # Build axis configs (using beautified keys)
        x_axis = AxisConfig(dataKey=x_label)
        y_axis = AxisConfig(dataKey="value")

        # Detect formatters for smart number formatting
        formatters = self._detect_formatters(data, y_keys)

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

        # Create Recharts config (using beautified data)
        config_dict = chart_config.model_dump(exclude_none=True)

        # Add formatters to config for frontend consumption
        if formatters:
            config_dict["formatters"] = formatters

        recharts_config = RechartsConfig(
            chart_type="line",
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


# Convenience functions
def line_chart(
    data: pd.DataFrame | list[dict[str, Any]],
    x: str,
    y: str | list[str],
    title: str | None = None,
    output_path: Path | None = None,
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
