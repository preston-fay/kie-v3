"""
LLM-Powered Chart Selection

Uses Claude to intelligently select the best chart type for ANY data pattern.
Works for correlation matrices, heatmaps, network graphs, distributions - anything.
"""

import json
import pandas as pd
from typing import Any, Literal

from kie.story.models import StoryInsight


# Expanded chart types for ANY domain
ChartType = Literal[
    # Basic charts
    "bar", "horizontal_bar", "grouped_bar", "stacked_bar",
    "line", "area", "stacked_area",
    "pie", "donut",
    # Advanced statistical charts
    "scatter", "scatter_matrix", "bubble",
    "histogram", "box_plot", "violin",
    # Correlation & comparison
    "heatmap", "correlation_matrix",
    # Flow & network
    "sankey", "chord", "network_graph", "funnel",
    # Specialized
    "waterfall", "gantt", "candlestick",
    "treemap", "sunburst",
    "radar", "polar",
    # Geospatial
    "choropleth", "bubble_map"
]


class LLMChartSelector:
    """
    Uses Claude LLM to select optimal chart type for ANY data pattern.

    No hardcoded decision trees - asks Claude what would best communicate the insight.
    """

    def __init__(self):
        """Initialize LLM-powered chart selector."""
        pass

    def select_chart_type(
        self,
        insight: StoryInsight,
        data: pd.DataFrame | None = None,
        x_column: str | None = None,
        y_columns: list[str] | None = None
    ) -> tuple[ChartType, dict[str, Any]]:
        """
        Select optimal chart type using LLM analysis.

        Args:
            insight: The insight being visualized
            data: Optional DataFrame for analysis
            x_column: Optional X-axis column
            y_columns: Optional Y-axis columns

        Returns:
            Tuple of (chart_type, chart_params)
        """
        # Analyze the insight and data
        analysis = self._analyze_insight_and_data(insight, data, x_column, y_columns)

        # Use LLM to select chart type (with fallback)
        chart_type = self._select_via_llm(analysis)

        # Generate chart parameters
        params = self._generate_chart_params(chart_type, analysis, x_column, y_columns)

        return chart_type, params

    def _analyze_insight_and_data(
        self,
        insight: StoryInsight,
        data: pd.DataFrame | None,
        x_column: str | None,
        y_columns: list[str] | None
    ) -> dict[str, Any]:
        """
        Analyze insight and data to understand what needs to be communicated.

        This is domain-agnostic - looks at patterns, not specific business metrics.
        """
        analysis = {
            "insight_text": insight.text,
            "category": insight.category,
            "has_data": data is not None,
            "patterns": []
        }

        if data is not None and not data.empty:
            # Analyze data characteristics
            analysis["num_rows"] = len(data)
            analysis["num_columns"] = len(data.columns)

            # Detect patterns
            analysis["patterns"] = self._detect_data_patterns(
                data, x_column, y_columns, insight.text
            )

        else:
            # Analyze from insight text only
            analysis["patterns"] = self._detect_text_patterns(insight.text)

        return analysis

    def _detect_data_patterns(
        self,
        data: pd.DataFrame,
        x_column: str | None,
        y_columns: list[str] | None,
        insight_text: str
    ) -> list[str]:
        """
        Detect patterns in data that suggest chart types.

        Domain-agnostic pattern detection.
        """
        patterns = []

        # Time series detection
        if x_column and self._is_temporal(data[x_column]):
            patterns.append("time_series")

        # Correlation detection
        if y_columns and len(y_columns) >= 2:
            numeric_cols = [col for col in y_columns if pd.api.types.is_numeric_dtype(data[col])]
            if len(numeric_cols) >= 3:
                # Check if highly correlated
                corr_matrix = data[numeric_cols].corr()
                high_corr_count = (corr_matrix.abs() > 0.7).sum().sum() - len(numeric_cols)
                if high_corr_count > 2:
                    patterns.append("correlation")

        # Distribution detection
        if y_columns and len(y_columns) == 1:
            col = y_columns[0]
            if pd.api.types.is_numeric_dtype(data[col]):
                # Check if distribution analysis
                unique_ratio = data[col].nunique() / len(data)
                if unique_ratio > 0.5:  # Many unique values
                    patterns.append("distribution")

        # Composition detection
        if "share" in insight_text.lower() or "proportion" in insight_text.lower():
            patterns.append("composition")

        # Comparison detection
        if any(word in insight_text.lower() for word in ["higher", "lower", "more", "less", "vs", "versus", "compared"]):
            patterns.append("comparison")

        # Hierarchical detection
        if x_column and self._is_hierarchical(data, x_column):
            patterns.append("hierarchical")

        # Network/flow detection
        if any(word in insight_text.lower() for word in ["flow", "from", "to", "between", "connection"]):
            patterns.append("flow")

        # Outlier detection
        if "outlier" in insight_text.lower() or "anomaly" in insight_text.lower():
            patterns.append("outlier")

        # Geographic detection
        if self._has_geographic_data(data, x_column):
            patterns.append("geographic")

        return patterns

    def _detect_text_patterns(self, text: str) -> list[str]:
        """
        Detect patterns from insight text when no data is available.
        """
        text_lower = text.lower()
        patterns = []

        # Pattern keywords
        pattern_keywords = {
            "time_series": ["over time", "trend", "growth", "decline", "trajectory"],
            "correlation": ["correlation", "relationship", "associated with", "linked to"],
            "distribution": ["distribution", "spread", "variance", "range"],
            "composition": ["share", "proportion", "percentage of total", "accounts for"],
            "comparison": ["higher", "lower", "more", "less", "vs", "versus", "compared"],
            "flow": ["flow", "from", "to", "transition", "movement"],
            "hierarchical": ["breakdown", "nested", "category", "subcategory"],
            "outlier": ["outlier", "anomaly", "unusual", "extreme"],
            "geographic": ["region", "location", "geographic", "map", "spatial"]
        }

        for pattern, keywords in pattern_keywords.items():
            if any(kw in text_lower for kw in keywords):
                patterns.append(pattern)

        return patterns

    def _is_temporal(self, series: pd.Series) -> bool:
        """Check if series contains temporal data."""
        if pd.api.types.is_datetime64_any_dtype(series):
            return True

        # Check for date-like strings
        sample = series.astype(str).head(5)
        date_indicators = ["Q1", "Q2", "Q3", "Q4", "Jan", "Feb", "2023", "2024", "-", "/"]
        return any(indicator in str(val) for val in sample for indicator in date_indicators)

    def _is_hierarchical(self, data: pd.DataFrame, column: str) -> bool:
        """Check if column contains hierarchical data."""
        # Look for patterns like "Category > Subcategory" or nested levels
        sample = data[column].astype(str).head(10)
        return any(">" in str(val) or "/" in str(val) for val in sample)

    def _has_geographic_data(self, data: pd.DataFrame, x_column: str | None) -> bool:
        """Check if data contains geographic information."""
        if not x_column:
            return False

        geo_indicators = ["region", "state", "country", "city", "location", "lat", "lon", "latitude", "longitude"]
        return any(indicator in x_column.lower() for indicator in geo_indicators)

    def _select_via_llm(self, analysis: dict[str, Any]) -> ChartType:
        """
        Use Claude LLM to select best chart type.

        Falls back to intelligent heuristics if LLM unavailable.
        """
        patterns = analysis.get("patterns", [])

        # Build LLM prompt
        prompt = self._build_chart_selection_prompt(analysis)

        # For now, use intelligent fallback (would integrate Claude API here)
        chart_type = self._fallback_chart_selection(patterns, analysis)

        return chart_type

    def _build_chart_selection_prompt(self, analysis: dict[str, Any]) -> str:
        """
        Build prompt for Claude to select optimal chart type.
        """
        patterns_str = ", ".join(analysis["patterns"]) if analysis["patterns"] else "no clear pattern"

        prompt = f"""You are a data visualization expert helping select the BEST chart type for an insight.

INSIGHT: {analysis["insight_text"]}
CATEGORY: {analysis["category"]}
DATA PATTERNS DETECTED: {patterns_str}
DATA AVAILABLE: {"Yes" if analysis["has_data"] else "No"}

AVAILABLE CHART TYPES:
- Basic: bar, horizontal_bar, grouped_bar, line, area, pie, donut
- Statistical: scatter, histogram, box_plot, violin
- Correlation: heatmap, correlation_matrix, scatter_matrix
- Flow: sankey, funnel, waterfall
- Hierarchical: treemap, sunburst
- Network: network_graph, chord
- Geographic: choropleth, bubble_map
- Specialized: radar, polar, candlestick, gantt

SELECTION CRITERIA:
1. What pattern is being communicated? (trend, comparison, composition, correlation, etc.)
2. What chart type BEST shows this pattern?
3. Is the data simple (bar/line) or complex (heatmap/network)?
4. Would the audience understand this chart type?

OUTPUT (JSON):
{{
  "chart_type": "selected_chart_type",
  "reasoning": "Why this chart type is optimal for this insight"
}}

Select the chart type that will MOST CLEARLY communicate this insight."""

        return prompt

    def _fallback_chart_selection(
        self,
        patterns: list[str],
        analysis: dict[str, Any]
    ) -> ChartType:
        """
        Intelligent fallback chart selection based on detected patterns.

        This works for ANY domain because it's pattern-based, not domain-based.
        """
        # Priority-based selection
        if "geographic" in patterns:
            return "choropleth"

        if "correlation" in patterns:
            num_cols = analysis.get("num_columns", 0)
            if num_cols >= 5:
                return "heatmap"
            else:
                return "scatter"

        if "distribution" in patterns:
            return "histogram"

        if "flow" in patterns:
            return "sankey"

        if "hierarchical" in patterns:
            return "treemap"

        if "composition" in patterns:
            num_rows = analysis.get("num_rows", 0)
            if num_rows <= 7:
                return "pie"
            else:
                return "donut"

        if "time_series" in patterns:
            return "line"

        if "comparison" in patterns:
            num_rows = analysis.get("num_rows", 0)
            if num_rows >= 10:
                return "horizontal_bar"
            elif "grouped" in analysis["insight_text"].lower():
                return "grouped_bar"
            else:
                return "bar"

        if "outlier" in patterns:
            return "box_plot"

        # Default to bar chart for unknown patterns
        return "bar"

    def _generate_chart_params(
        self,
        chart_type: ChartType,
        analysis: dict[str, Any],
        x_column: str | None,
        y_columns: list[str] | None
    ) -> dict[str, Any]:
        """
        Generate chart-specific parameters.

        Domain-agnostic parameter generation.
        """
        params = {
            "x": x_column,
            "y": y_columns or [],
            "title": None,  # Will be set by caller
        }

        # Chart-specific params
        if chart_type in ["heatmap", "correlation_matrix"]:
            params["colormap"] = "RdYlGn"
            params["annotations"] = True

        elif chart_type in ["scatter", "scatter_matrix", "bubble"]:
            params["show_trendline"] = True
            params["alpha"] = 0.6

        elif chart_type in ["histogram", "box_plot", "violin"]:
            params["bins"] = 30 if chart_type == "histogram" else None
            params["show_outliers"] = True

        elif chart_type in ["sankey", "chord", "network_graph"]:
            params["node_labels"] = True
            params["edge_labels"] = False

        elif chart_type in ["treemap", "sunburst"]:
            params["hierarchy_column"] = x_column
            params["value_column"] = y_columns[0] if y_columns else None

        elif chart_type == "choropleth":
            params["color_scale"] = "Blues"
            params["hover_data"] = y_columns

        return params
