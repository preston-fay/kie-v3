"""
Smart Chart Type Selection

Intelligently selects the optimal chart type based on:
- Data characteristics (time-series, categorical, numeric)
- Insight pattern (trend, comparison, composition, distribution)
- Number of series (single vs multi-series)
- Business context (revenue, satisfaction, demographics, etc.)
"""

import re
from typing import Any, Literal

import pandas as pd

from kie.story.models import StoryInsight

ChartType = Literal[
    "bar", "horizontal_bar", "stacked_bar", "grouped_bar",
    "line", "area", "stacked_area",
    "pie", "donut",
    "scatter",
    "combo",
    "waterfall"
]


class ChartSelector:
    """
    Selects optimal chart type for an insight based on data and context.

    Decision tree:
    1. Time-series data → line/area
    2. Composition (parts of whole) → pie/donut
    3. Change over stages → waterfall
    4. Correlation → scatter
    5. Comparison (categories) → bar/horizontal_bar/grouped_bar
    6. Multiple series trends → stacked_area/combo
    """

    def __init__(self):
        """Initialize chart selector."""
        pass

    def select_chart_type(
        self,
        insight: StoryInsight,
        data: pd.DataFrame,
        x_column: str | None = None,
        y_columns: list[str] | None = None,
    ) -> tuple[ChartType, dict[str, Any]]:
        """
        Select optimal chart type for an insight.

        Args:
            insight: StoryInsight to visualize
            data: Data for visualization
            x_column: Optional X-axis column (auto-detected if None)
            y_columns: Optional Y-axis columns (auto-detected if None)

        Returns:
            Tuple of (chart_type, chart_params)
        """
        # Auto-detect columns if not provided
        if x_column is None or y_columns is None:
            x_column, y_columns = self._detect_columns(data)

        # Analyze data characteristics
        is_timeseries = self._is_timeseries(data, x_column)
        is_composition = self._is_composition(insight, data, y_columns)
        is_change_flow = self._is_change_flow(insight)
        is_correlation = self._is_correlation(insight, y_columns)
        is_comparison = self._is_comparison(insight)
        is_multi_series = len(y_columns) > 1

        # Decision tree
        if is_timeseries:
            if is_multi_series and len(y_columns) <= 3:
                chart_type = "line"
            elif is_multi_series:
                chart_type = "stacked_area"
            else:
                chart_type = "area"
        elif is_composition and len(data) <= 6:
            chart_type = "pie" if len(data) <= 5 else "donut"
        elif is_change_flow:
            chart_type = "waterfall"
        elif is_correlation and len(y_columns) >= 2:
            chart_type = "scatter"
        elif is_comparison:
            if is_multi_series:
                chart_type = "grouped_bar"
            elif len(data) > 8:
                chart_type = "horizontal_bar"  # Better for long category names
            else:
                chart_type = "bar"
        else:
            # Default to bar chart
            chart_type = "bar"

        # Build chart params
        params = {
            "x": x_column,
            "y": y_columns if len(y_columns) > 1 else y_columns[0],
            "title": self._generate_chart_title(insight, x_column, y_columns),
        }

        return chart_type, params

    def _detect_columns(self, data: pd.DataFrame) -> tuple[str, list[str]]:
        """
        Auto-detect X and Y columns from data.

        Returns:
            Tuple of (x_column, y_columns)
        """
        # X column: first categorical/string column or first column
        x_column = None
        for col in data.columns:
            if pd.api.types.is_string_dtype(data[col]) or pd.api.types.is_categorical_dtype(data[col]):
                x_column = col
                break

        if x_column is None:
            x_column = data.columns[0]

        # Y columns: all numeric columns except X
        y_columns = []
        for col in data.columns:
            if col != x_column and pd.api.types.is_numeric_dtype(data[col]):
                y_columns.append(col)

        # Fallback if no numeric columns
        if not y_columns:
            y_columns = [c for c in data.columns if c != x_column][:1]

        return x_column, y_columns

    def _is_timeseries(self, data: pd.DataFrame, x_column: str) -> bool:
        """Check if data represents time-series."""
        # Check column name
        time_keywords = ["date", "time", "year", "month", "quarter", "week", "day", "period"]
        col_lower = x_column.lower()

        if any(kw in col_lower for kw in time_keywords):
            return True

        # Check data type
        if x_column in data.columns:
            if pd.api.types.is_datetime64_any_dtype(data[x_column]):
                return True

            # Check if values look like dates
            try:
                sample = data[x_column].dropna().head(5).astype(str)
                # Simple heuristic: contains "Q1", "Q2", "2023", "2024", etc.
                if any(re.search(r'(Q[1-4]|20\d{2}|\d{4})', val) for val in sample):
                    return True
            except:
                pass

        return False

    def _is_composition(
        self,
        insight: StoryInsight,
        data: pd.DataFrame,
        y_columns: list[str]
    ) -> bool:
        """Check if insight shows parts-of-whole composition."""
        text_lower = insight.text.lower()

        # Keywords indicating composition
        composition_keywords = [
            "share", "proportion", "distribution", "breakdown",
            "makes up", "accounts for", "comprises", "consists of",
            "segment", "category", "split"
        ]

        if any(kw in text_lower for kw in composition_keywords):
            return True

        # Check if Y column suggests percentages that sum to ~100%
        if len(y_columns) == 1 and y_columns[0] in data.columns:
            total = data[y_columns[0]].sum()
            if 95 <= total <= 105:  # Allow some rounding error
                return True

        return False

    def _is_change_flow(self, insight: StoryInsight) -> bool:
        """Check if insight shows change/flow over stages."""
        text_lower = insight.text.lower()

        # Keywords indicating waterfall/change
        change_keywords = [
            "change", "increase", "decrease", "growth", "decline",
            "from", "to", "net", "total impact", "contribution",
            "variance", "delta"
        ]

        # Need at least 2 change keywords for waterfall
        matches = sum(1 for kw in change_keywords if kw in text_lower)
        return matches >= 2

    def _is_correlation(self, insight: StoryInsight, y_columns: list[str]) -> bool:
        """Check if insight shows correlation between variables."""
        text_lower = insight.text.lower()

        correlation_keywords = [
            "correlation", "relationship", "associated with",
            "linked to", "connected to", "related to",
            "vs", "versus", "compared to"
        ]

        return (
            any(kw in text_lower for kw in correlation_keywords)
            and len(y_columns) >= 2
        )

    def _is_comparison(self, insight: StoryInsight) -> bool:
        """Check if insight compares categories."""
        text_lower = insight.text.lower()

        comparison_keywords = [
            "higher", "lower", "more", "less", "greater", "smaller",
            "compared", "versus", "than", "between",
            "leads", "followed by", "ranks", "top", "bottom"
        ]

        return any(kw in text_lower for kw in comparison_keywords)

    def _generate_chart_title(
        self,
        insight: StoryInsight,
        x_column: str,
        y_columns: list[str]
    ) -> str:
        """Generate chart title from insight."""
        # Try to extract a natural title from the insight text
        text = insight.text.strip()

        # If insight starts with a percentage/number, use the text after it
        match = re.match(r'^\d+\.?\d*%?\s*(.+)', text)
        if match:
            title_candidate = match.group(1)
            # Take first sentence
            first_sentence = title_candidate.split('.')[0]
            if len(first_sentence) <= 80:
                return first_sentence

        # Fallback: use first sentence of insight
        first_sentence = text.split('.')[0]
        if len(first_sentence) <= 80:
            return first_sentence

        # Fallback: generic title from columns
        y_display = ", ".join(y_columns) if len(y_columns) <= 3 else f"{len(y_columns)} metrics"
        return f"{y_display} by {x_column}"
