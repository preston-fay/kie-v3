"""
Pie Chart Data Builder

Generates Recharts-compatible JSON configurations for pie and donut charts.
"""

from typing import Any, List, Dict, Optional, Union
from pathlib import Path
import pandas as pd

from kie.base import ChartBuilder, RechartsConfig
from kie.brand.colors import KDSColors
from kie.charts.schema import (
    PieChartConfig,
    PieConfig,
    LegendConfig,
    TooltipConfig,
)


class PieChartBuilder(ChartBuilder):
    """
    Builder for pie and donut charts using Recharts.

    Supports:
    - Pie charts (solid circle)
    - Donut charts (hollow center)
    - Custom colors from KDS palette
    - Labels and percentages
    - Interactive tooltips
    """

    def __init__(
        self,
        inner_radius: int = 0,  # 0 for pie, >0 for donut
        outer_radius: int = 80,
        show_labels: bool = True,
        show_legend: bool = True,
        show_percentages: bool = True,
    ):
        """
        Initialize pie chart builder.

        Args:
            inner_radius: Inner radius (0 for pie, e.g. 40 for donut)
            outer_radius: Outer radius
            show_labels: Show labels on slices
            show_legend: Show legend
            show_percentages: Show percentage values
        """
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.show_labels = show_labels
        self.show_legend = show_legend
        self.show_percentages = show_percentages

    def build(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        name_key: str,
        value_key: str,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        colors: Optional[List[str]] = None,
        **kwargs,
    ) -> RechartsConfig:
        """
        Build pie chart configuration.

        Args:
            data: Input data (DataFrame or list of dicts)
            name_key: Column name for slice names
            value_key: Column name for values
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

        # Get colors for each slice
        if colors is None:
            colors = KDSColors.get_chart_colors(len(data_list))
        elif len(colors) < len(data_list):
            colors.extend(KDSColors.get_chart_colors(len(data_list) - len(colors)))

        # Add colors to data
        for i, item in enumerate(data_list):
            item["fill"] = colors[i % len(colors)]

        # Calculate percentages if requested
        if self.show_percentages:
            total = sum(item[value_key] for item in data_list)
            for item in data_list:
                item["percentage"] = round((item[value_key] / total) * 100, 1)

        # Build pie config
        pie_config = PieConfig(
            dataKey=value_key,
            nameKey=name_key,
            cx="50%",
            cy="50%",
            innerRadius=self.inner_radius,
            outerRadius=self.outer_radius,
            paddingAngle=2,
            label={
                "position": "outside",
                "fontSize": 12,
                "fill": "currentColor",
            } if self.show_labels else None,
        )

        # Build chart config
        chart_config = PieChartConfig(
            title=title,
            subtitle=subtitle,
            pie=pie_config,
            colors=colors,
            legend=LegendConfig(
                verticalAlign="bottom",
                align="center",
            ) if self.show_legend else None,
            tooltip=TooltipConfig(),
            gridLines=False,
            fontFamily="Inter, sans-serif",
            interactive=True,
        )

        # Create Recharts config
        recharts_config = RechartsConfig(
            chart_type="pie",
            data=data_list,
            config=chart_config.model_dump(exclude_none=True),
            title=title,
            subtitle=subtitle,
        )

        return recharts_config


class DonutChartBuilder(PieChartBuilder):
    """
    Builder for donut charts (pie charts with hollow center).
    """

    def __init__(
        self,
        inner_radius: int = 40,
        outer_radius: int = 80,
        **kwargs,
    ):
        """
        Initialize donut chart builder.

        Args:
            inner_radius: Inner radius (default 40)
            outer_radius: Outer radius (default 80)
            **kwargs: Additional options passed to PieChartBuilder
        """
        super().__init__(
            inner_radius=inner_radius,
            outer_radius=outer_radius,
            **kwargs,
        )


# Convenience functions
def pie_chart(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    name: str,
    value: str,
    title: Optional[str] = None,
    output_path: Optional[Path] = None,
    **kwargs,
) -> RechartsConfig:
    """
    Quick function to create a pie chart.

    Args:
        data: Input data
        name: Name column
        value: Value column
        title: Chart title
        output_path: Optional path to save JSON
        **kwargs: Additional options

    Returns:
        RechartsConfig

    Example:
        >>> data = [
        ...     {"category": "Product A", "sales": 4500},
        ...     {"category": "Product B", "sales": 3200},
        ...     {"category": "Product C", "sales": 2800},
        ... ]
        >>> config = pie_chart(data, name="category", value="sales", title="Sales by Product")
        >>> config.to_json(Path("outputs/charts/product_sales.json"))
    """
    builder = PieChartBuilder(**kwargs)
    config = builder.build(data, name_key=name, value_key=value, title=title)

    if output_path:
        config.to_json(output_path)

    return config


def donut_chart(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    name: str,
    value: str,
    title: Optional[str] = None,
    output_path: Optional[Path] = None,
    **kwargs,
) -> RechartsConfig:
    """
    Quick function to create a donut chart.

    Args:
        data: Input data
        name: Name column
        value: Value column
        title: Chart title
        output_path: Optional path to save JSON
        **kwargs: Additional options

    Returns:
        RechartsConfig
    """
    builder = DonutChartBuilder(**kwargs)
    config = builder.build(data, name_key=name, value_key=value, title=title)

    if output_path:
        config.to_json(output_path)

    return config
