"""
Chart Factory

Unified interface for creating all chart types with smart defaults.
"""

from typing import Any, Literal

import pandas as pd

from kie.base import RechartsConfig
from kie.charts.builders.area import AreaChartBuilder
from kie.charts.builders.bar import BarChartBuilder
from kie.charts.builders.combo import ComboChartBuilder
from kie.charts.builders.line import LineChartBuilder
from kie.charts.builders.pie import DonutChartBuilder, PieChartBuilder
from kie.charts.builders.scatter import ScatterPlotBuilder
from kie.charts.builders.waterfall import WaterfallChartBuilder

ChartType = Literal[
    "bar", "horizontal_bar", "stacked_bar",
    "line", "area", "stacked_area",
    "pie", "donut",
    "scatter",
    "combo",
    "waterfall"
]


class ChartFactory:
    """
    Factory for creating charts with smart defaults.

    Provides a single entry point for all chart types with
    sensible defaults and KDS compliance.
    """

    @staticmethod
    def create(
        chart_type: ChartType,
        data: pd.DataFrame | list[dict[str, Any]],
        **kwargs,
    ) -> RechartsConfig:
        """
        Create a chart of the specified type.

        Args:
            chart_type: Type of chart to create
            data: Input data
            **kwargs: Chart-specific parameters

        Returns:
            RechartsConfig ready for JSON serialization

        Raises:
            ValueError: If chart_type is not recognized

        Example:
            >>> data = [{"region": "North", "revenue": 1200}, ...]
            >>> config = ChartFactory.create(
            ...     "bar",
            ...     data,
            ...     x="region",
            ...     y="revenue",
            ...     title="Revenue by Region"
            ... )
        """
        if chart_type == "bar":
            return ChartFactory.bar(data, **kwargs)
        elif chart_type == "horizontal_bar":
            return ChartFactory.horizontal_bar(data, **kwargs)
        elif chart_type == "stacked_bar":
            return ChartFactory.stacked_bar(data, **kwargs)
        elif chart_type == "line":
            return ChartFactory.line(data, **kwargs)
        elif chart_type == "area":
            return ChartFactory.area(data, **kwargs)
        elif chart_type == "stacked_area":
            return ChartFactory.stacked_area(data, **kwargs)
        elif chart_type == "pie":
            return ChartFactory.pie(data, **kwargs)
        elif chart_type == "donut":
            return ChartFactory.donut(data, **kwargs)
        elif chart_type == "scatter":
            return ChartFactory.scatter(data, **kwargs)
        elif chart_type == "combo":
            return ChartFactory.combo(data, **kwargs)
        elif chart_type == "waterfall":
            return ChartFactory.waterfall(data, **kwargs)
        else:
            raise ValueError(f"Unknown chart type: {chart_type}")

    @staticmethod
    def bar(
        data: pd.DataFrame | list[dict[str, Any]],
        x: str,
        y: str | list[str],
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create a bar chart."""
        builder = BarChartBuilder()
        return builder.build(data, x_key=x, y_keys=y, title=title, **kwargs)

    @staticmethod
    def horizontal_bar(
        data: pd.DataFrame | list[dict[str, Any]],
        x: str,
        y: str | list[str],
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create a horizontal bar chart."""
        builder = BarChartBuilder(layout="vertical")
        return builder.build(data, x_key=x, y_keys=y, title=title, **kwargs)

    @staticmethod
    def stacked_bar(
        data: pd.DataFrame | list[dict[str, Any]],
        x: str,
        y: list[str],
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create a stacked bar chart."""
        builder = BarChartBuilder(stacked=True)
        return builder.build(data, x_key=x, y_keys=y, title=title, **kwargs)

    @staticmethod
    def line(
        data: pd.DataFrame | list[dict[str, Any]],
        x: str,
        y: str | list[str],
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create a line chart."""
        builder = LineChartBuilder()
        return builder.build(data, x_key=x, y_keys=y, title=title, **kwargs)

    @staticmethod
    def area(
        data: pd.DataFrame | list[dict[str, Any]],
        x: str,
        y: str | list[str],
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create an area chart."""
        builder = AreaChartBuilder()
        return builder.build(data, x_key=x, y_keys=y, title=title, **kwargs)

    @staticmethod
    def stacked_area(
        data: pd.DataFrame | list[dict[str, Any]],
        x: str,
        y: list[str],
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create a stacked area chart."""
        builder = AreaChartBuilder(stacked=True)
        return builder.build(data, x_key=x, y_keys=y, title=title, **kwargs)

    @staticmethod
    def pie(
        data: pd.DataFrame | list[dict[str, Any]],
        name: str,
        value: str,
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create a pie chart."""
        builder = PieChartBuilder()
        return builder.build(data, name_key=name, value_key=value, title=title, **kwargs)

    @staticmethod
    def donut(
        data: pd.DataFrame | list[dict[str, Any]],
        name: str,
        value: str,
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create a donut chart."""
        builder = DonutChartBuilder()
        return builder.build(data, name_key=name, value_key=value, title=title, **kwargs)

    @staticmethod
    def scatter(
        data: pd.DataFrame | list[dict[str, Any]],
        x: str,
        y: str,
        category: str | None = None,
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create a scatter plot."""
        builder = ScatterPlotBuilder()
        return builder.build(data, x_key=x, y_key=y, category_key=category, title=title, **kwargs)

    @staticmethod
    def combo(
        data: pd.DataFrame | list[dict[str, Any]],
        x: str,
        bars: str | list[str],
        lines: str | list[str],
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create a combo chart (bar + line)."""
        builder = ComboChartBuilder()
        return builder.build(data, x_key=x, bar_keys=bars, line_keys=lines, title=title, **kwargs)

    @staticmethod
    def waterfall(
        data: pd.DataFrame | list[dict[str, Any]],
        labels: str,
        values: str,
        is_total: str | None = None,
        title: str | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """Create a waterfall chart."""
        builder = WaterfallChartBuilder()
        return builder.build(
            data,
            label_key=labels,
            value_key=values,
            is_total_key=is_total,
            title=title,
            **kwargs
        )

    @staticmethod
    def auto_detect(
        data: pd.DataFrame | list[dict[str, Any]],
        x: str | None = None,
        y: str | list[str] | None = None,
        **kwargs,
    ) -> RechartsConfig:
        """
        Automatically detect best chart type for data.

        Logic:
        - 1 categorical + 1 numeric → bar chart
        - 1 time series + 1 numeric → line chart
        - 1 time series + multiple numeric → stacked area
        - 2 numeric columns → scatter plot
        - 1 categorical + % values → pie chart

        Args:
            data: Input data
            x: X axis column (optional, will auto-detect)
            y: Y axis column(s) (optional, will auto-detect)
            **kwargs: Additional options

        Returns:
            RechartsConfig with auto-selected chart type
        """
        # Convert to DataFrame for easier analysis
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data

        # Auto-detect columns if not provided
        if x is None:
            # Find first categorical or date column
            for col in df.columns:
                if df[col].dtype in ['object', 'datetime64[ns]']:
                    x = col
                    break

        if y is None:
            # Find all numeric columns (excluding x)
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if x in numeric_cols:
                numeric_cols.remove(x)
            y = numeric_cols if len(numeric_cols) > 1 else numeric_cols[0]

        # Detect chart type
        if isinstance(y, list) and len(y) > 1:
            # Multiple numeric columns
            if df[x].dtype == 'datetime64[ns]':
                # Time series + multiple values → stacked area
                return ChartFactory.stacked_area(df, x=x, y=y, **kwargs)
            else:
                # Categorical + multiple values → grouped bar
                return ChartFactory.bar(df, x=x, y=y, **kwargs)
        else:
            # Single numeric column
            y_col = y if isinstance(y, str) else y[0]

            if df[x].dtype == 'datetime64[ns]':
                # Time series → line chart
                return ChartFactory.line(df, x=x, y=y_col, **kwargs)
            elif df[x].dtype == 'object' and len(df) <= 4:
                # Few categories (KDS: max 4 slices) → pie chart
                return ChartFactory.pie(df, name=x, value=y_col, **kwargs)
            elif df[x].dtype == 'object' and len(df) <= 10:
                # 5-10 categories → horizontal bar (better than pie)
                return ChartFactory.horizontal_bar(df, x=x, y=y_col, **kwargs)
            else:
                # Default to bar chart
                return ChartFactory.bar(df, x=x, y=y_col, **kwargs)


# Convenience alias
create_chart = ChartFactory.create
