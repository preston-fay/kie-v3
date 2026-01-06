"""
Waterfall Chart Data Builder

Generates Recharts-compatible JSON configurations for waterfall charts.
Waterfall charts show cumulative effect of sequential positive/negative values.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from kie.base import ChartBuilder, RechartsConfig
from kie.brand.colors import KDSColors


class WaterfallChartBuilder(ChartBuilder):
    """
    Builder for waterfall charts using Recharts.

    Waterfall charts are common in consulting for showing:
    - Revenue/profit bridges
    - Cost breakdowns
    - Sequential changes from start to end

    Displays bars that float to show increases/decreases from a baseline.
    """

    def __init__(
        self,
        show_data_labels: bool = True,
        show_connectors: bool = True,
        positive_color: str | None = None,
        negative_color: str | None = None,
        total_color: str | None = None,
    ):
        """
        Initialize waterfall chart builder.

        Args:
            show_data_labels: Show values on bars
            show_connectors: Show connecting lines between bars
            positive_color: Color for positive changes (default: KDS bright purple)
            negative_color: Color for negative changes (default: KDS dark gray)
            total_color: Color for total bars (default: KDS primary purple)
        """
        self.show_data_labels = show_data_labels
        self.show_connectors = show_connectors
        self.positive_color = positive_color or KDSColors.CHART_PALETTE[9]  # Bright purple
        self.negative_color = negative_color or KDSColors.CHART_PALETTE[3]  # Dark gray
        self.total_color = total_color or KDSColors.PRIMARY  # Kearney purple

    def build(
        self,
        data: pd.DataFrame | list[dict[str, Any]],
        label_key: str,
        value_key: str,
        is_total_key: str | None = None,
        title: str | None = None,
        subtitle: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """
        Build waterfall chart configuration.

        Args:
            data: Input data (DataFrame or list of dicts)
            label_key: Column name for labels (categories)
            value_key: Column name for values (changes)
            is_total_key: Optional column indicating if row is a total (boolean)
            title: Chart title
            subtitle: Chart subtitle
            **kwargs: Additional configuration options

        Returns:
            RechartsConfig ready for JSON serialization

        Data format:
            Each row should have:
            - label: Name of the step
            - value: Change amount (positive or negative)
            - is_total: (optional) True for total bars

        Example:
            [
                {"step": "Starting Revenue", "change": 1000, "is_total": True},
                {"step": "New Sales", "change": 200, "is_total": False},
                {"step": "Returns", "change": -50, "is_total": False},
                {"step": "Ending Revenue", "change": 1150, "is_total": True},
            ]
        """
        # Normalize data to list of dicts
        if isinstance(data, pd.DataFrame):
            data_list = data.to_dict("records")
        else:
            data_list = data

        # Calculate cumulative values and floating bar positions
        cumulative = 0
        processed_data = []

        for item in data_list:
            value = item[value_key]
            is_total = item.get(is_total_key, False) if is_total_key else False

            if is_total:
                # Total bars start from 0
                bar_start = 0
                bar_end = value
                cumulative = value
                color = self.total_color
            else:
                # Floating bars
                if value >= 0:
                    bar_start = cumulative
                    bar_end = cumulative + value
                    color = self.positive_color
                else:
                    bar_start = cumulative + value
                    bar_end = cumulative
                    color = self.negative_color
                cumulative += value

            processed_item = {
                label_key: item[label_key],
                "start": bar_start,
                "end": bar_end,
                "value": value,
                "cumulative": cumulative,
                "fill": color,
                "is_total": is_total,
            }
            processed_data.append(processed_item)

        # Build waterfall config
        # Waterfall charts use stacked bars to create the floating effect
        config = {
            "type": "waterfall",
            "data": processed_data,
            "config": {
                "xKey": label_key,
                "startKey": "start",
                "endKey": "end",
                "valueKey": "value",
                "cumulativeKey": "cumulative",
                "title": title,
                "subtitle": subtitle,
                "showDataLabels": self.show_data_labels,
                "showConnectors": self.show_connectors,
                "positiveColor": self.positive_color,
                "negativeColor": self.negative_color,
                "totalColor": self.total_color,
                "fontFamily": "Inter, sans-serif",
                "gridLines": False,
                "axisLine": False,
                "tickLine": False,
                "interactive": True,
            },
        }

        # Create Recharts config
        recharts_config = RechartsConfig(
            chart_type="waterfall",
            data=processed_data,
            config=config["config"],
            title=title,
            subtitle=subtitle,
        )

        return recharts_config


# Convenience function
def waterfall_chart(
    data: pd.DataFrame | list[dict[str, Any]],
    labels: str,
    values: str,
    is_total: str | None = None,
    title: str | None = None,
    output_path: Path | None = None,
    **kwargs,
) -> RechartsConfig:
    """
    Quick function to create a waterfall chart.

    Args:
        data: Input data
        labels: Label column name
        values: Value column name
        is_total: Optional column indicating total bars
        title: Chart title
        output_path: Optional path to save JSON
        **kwargs: Additional options

    Returns:
        RechartsConfig

    Example:
        >>> data = [
        ...     {"step": "Q1 Revenue", "change": 1000, "is_total": True},
        ...     {"step": "New Customers", "change": 200, "is_total": False},
        ...     {"step": "Churn", "change": -50, "is_total": False},
        ...     {"step": "Price Increase", "change": 100, "is_total": False},
        ...     {"step": "Q2 Revenue", "change": 1250, "is_total": True},
        ... ]
        >>> config = waterfall_chart(
        ...     data,
        ...     labels="step",
        ...     values="change",
        ...     is_total="is_total",
        ...     title="Revenue Bridge Q1 to Q2"
        ... )
        >>> config.to_json(Path("outputs/charts/revenue_bridge.json"))
    """
    builder = WaterfallChartBuilder(**kwargs)
    config = builder.build(
        data,
        label_key=labels,
        value_key=values,
        is_total_key=is_total,
        title=title
    )

    if output_path:
        config.to_json(output_path)

    return config
