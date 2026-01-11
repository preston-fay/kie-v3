"""
Chart Renderer from Visualization Plan

Renders charts STRICTLY from outputs/visualization_plan.json.

This is pure execution wiring - no judgment, no opinions.
Reads visualization specifications and generates charts deterministically.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


class ChartRenderer:
    """
    Renders charts from visualization_plan.json.

    RULES:
    1. Input source: ONLY visualization_plan.json
    2. For each visualization_required == true → render ONE chart
    3. Data filtering: suppress listed categories, highlight specified values
    4. Output location: outputs/charts/<insight_id>__<visualization_type>.json
    5. No extra charts: N specs → exactly N charts
    """

    def __init__(self, project_root: Path):
        """
        Initialize chart renderer.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.outputs_dir = project_root / "outputs"
        self.charts_dir = self.outputs_dir / "charts"
        self.data_dir = project_root / "data"

    def render_charts(self, data_file: Path | None = None) -> dict[str, Any]:
        """
        Render all charts from visualization plan.

        Args:
            data_file: Data file to use for charts (optional, will auto-detect)

        Returns:
            Dictionary with success status and rendered charts info

        Raises:
            FileNotFoundError: If visualization_plan.json is missing
            ValueError: If data file cannot be found
        """
        # REQUIREMENT: visualization_plan.json MUST exist
        viz_plan_path = self.outputs_dir / "visualization_plan.json"
        if not viz_plan_path.exists():
            raise FileNotFoundError(
                "Chart rendering requires visualization_plan.json. "
                "Run /analyze first to generate visualization plan."
            )

        # Load visualization plan
        with open(viz_plan_path) as f:
            viz_plan = json.load(f)

        specs = viz_plan.get("specifications", [])
        if not specs:
            return {
                "success": True,
                "message": "No visualization specifications found",
                "charts_rendered": 0,
                "charts": [],
            }

        # Get data file
        if data_file is None:
            data_file = self._auto_detect_data_file()
        if not data_file or not data_file.exists():
            raise ValueError(
                "No data files found in data/ directory. "
                "Run /eda first to analyze your data."
            )

        # Load data
        df = self._load_data(data_file)

        # Create charts directory
        self.charts_dir.mkdir(parents=True, exist_ok=True)

        # Render charts for each spec where visualization_required == true
        rendered_charts = []
        for spec in specs:
            if not spec.get("visualization_required", False):
                # Skip - no chart for this insight
                continue

            # Render chart
            chart_info = self._render_chart(spec, df)
            rendered_charts.append(chart_info)

        return {
            "success": True,
            "message": f"Rendered {len(rendered_charts)} charts from visualization plan",
            "charts_rendered": len(rendered_charts),
            "charts": rendered_charts,
            "visualizations_planned": len([s for s in specs if s.get("visualization_required", False)]),
            "visualizations_skipped": len([s for s in specs if not s.get("visualization_required", False)]),
        }

    def _auto_detect_data_file(self) -> Path | None:
        """Auto-detect data file from data/ directory."""
        if not self.data_dir.exists():
            return None

        # Supported formats
        extensions = [".csv", ".xlsx", ".xls", ".parquet", ".json"]

        # Find first data file
        for ext in extensions:
            files = list(self.data_dir.glob(f"*{ext}"))
            if files:
                return files[0]

        return None

    def _load_data(self, data_file: Path) -> pd.DataFrame:
        """
        Load data from file.

        Args:
            data_file: Path to data file

        Returns:
            DataFrame with data
        """
        from kie.data.loader import DataLoader

        loader = DataLoader()
        return loader.load(data_file)

    def _render_chart(self, spec: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
        """
        Render a single chart from specification.

        Args:
            spec: Visualization specification
            df: Source data

        Returns:
            Chart info dictionary
        """
        insight_id = spec.get("insight_id", "unknown")
        viz_type = spec.get("visualization_type", "bar")
        purpose = spec.get("purpose", "comparison")
        x_axis = spec.get("x_axis")
        y_axis = spec.get("y_axis")
        grouping = spec.get("grouping")
        highlights = spec.get("highlights", [])
        suppress = spec.get("suppress", [])
        annotations = spec.get("annotations", [])
        caveats = spec.get("caveats", [])
        confidence = spec.get("confidence", {})

        # Map visualization type to chart implementation
        chart_data = self._map_visualization_type(
            viz_type, df, x_axis, y_axis, grouping, suppress, highlights
        )

        # Build chart config
        chart_config = {
            "insight_id": insight_id,
            "insight_title": spec.get("insight_title", "Untitled"),
            "visualization_type": viz_type,
            "purpose": purpose,
            "data": chart_data,
            "axes": {
                "x": x_axis,
                "y": y_axis,
                "grouping": grouping,
            },
            "highlights": highlights,
            "suppress": suppress,
            "annotations": annotations,
            "caveats": caveats,
            "confidence": confidence,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source": "visualization_plan",
            },
        }

        # Deterministic filename
        filename = f"{insight_id}__{viz_type}.json"
        output_path = self.charts_dir / filename

        # Save chart config
        with open(output_path, "w") as f:
            json.dump(chart_config, f, indent=2)

        return {
            "insight_id": insight_id,
            "visualization_type": viz_type,
            "filename": filename,
            "path": str(output_path),
            "data_points": len(chart_data) if isinstance(chart_data, list) else 0,
        }

    def _map_visualization_type(
        self,
        viz_type: str,
        df: pd.DataFrame,
        x_axis: str | None,
        y_axis: str | None,
        grouping: str | None,
        suppress: list[str],
        highlights: list[str],
    ) -> list[dict[str, Any]]:
        """
        Map visualization type to chart data.

        Args:
            viz_type: Visualization type (bar, line, distribution, scatter, map, table)
            df: Source DataFrame
            x_axis: X-axis column name
            y_axis: Y-axis column name
            grouping: Grouping column name
            suppress: Categories to suppress
            highlights: Categories to highlight

        Returns:
            Chart data as list of dictionaries
        """
        # Find closest matching columns if exact names don't exist
        x_col = self._find_column(df, x_axis) if x_axis else None
        y_col = self._find_column(df, y_axis) if y_axis else None
        group_col = self._find_column(df, grouping) if grouping else None

        # Map viz type to chart data generation
        if viz_type == "bar":
            return self._generate_bar_data(df, x_col, y_col, suppress, highlights)
        elif viz_type == "line":
            return self._generate_line_data(df, x_col, y_col, group_col, suppress)
        elif viz_type == "distribution":
            return self._generate_distribution_data(df, y_col, suppress)
        elif viz_type == "scatter":
            return self._generate_scatter_data(df, x_col, y_col, group_col, suppress)
        elif viz_type == "map":
            return self._generate_map_data(df, x_col, y_col, suppress)
        elif viz_type == "table":
            return self._generate_table_data(df, suppress)
        else:
            # Default to bar chart
            return self._generate_bar_data(df, x_col, y_col, suppress, highlights)

    def _find_column(self, df: pd.DataFrame, target: str | None) -> str | None:
        """
        Find closest matching column name.

        Args:
            df: DataFrame
            target: Target column name

        Returns:
            Closest matching column name, or None
        """
        if not target:
            return None

        # Exact match
        if target in df.columns:
            return target

        # Case-insensitive match
        target_lower = target.lower()
        for col in df.columns:
            if col.lower() == target_lower:
                return col

        # Partial match (contains)
        for col in df.columns:
            if target_lower in col.lower() or col.lower() in target_lower:
                return col

        # No match found - return None (will use first available column as fallback)
        return None

    def _generate_bar_data(
        self,
        df: pd.DataFrame,
        x_col: str | None,
        y_col: str | None,
        suppress: list[str],
        highlights: list[str],
    ) -> list[dict[str, Any]]:
        """Generate bar chart data."""
        # Use first categorical column for x if not specified
        if x_col is None:
            categorical_cols = df.select_dtypes(include=["object", "category"]).columns
            x_col = categorical_cols[0] if len(categorical_cols) > 0 else df.columns[0]

        # Use first numeric column for y if not specified
        if y_col is None:
            numeric_cols = df.select_dtypes(include=["number"]).columns
            y_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[1] if len(df.columns) > 1 else df.columns[0]

        # Group by x_col and aggregate y_col
        grouped = df.groupby(x_col)[y_col].sum().reset_index()

        # Filter out suppressed categories
        suppress_lower = [s.lower() for s in suppress]
        grouped = grouped[~grouped[x_col].astype(str).str.lower().isin(suppress_lower)]

        # Filter out null/empty categories
        grouped = grouped[grouped[x_col].notna()]
        grouped = grouped[grouped[x_col].astype(str).str.strip() != ""]

        # Sort by value descending
        grouped = grouped.sort_values(y_col, ascending=False)

        # Take top 10
        grouped = grouped.head(10)

        # Build chart data
        chart_data = []
        for _, row in grouped.iterrows():
            category = str(row[x_col])
            value = float(row[y_col])

            # Check if highlighted
            is_highlighted = any(
                h.lower() in category.lower() for h in highlights
            ) if highlights else False

            chart_data.append({
                "category": category,
                "value": value,
                "highlighted": is_highlighted,
            })

        return chart_data

    def _generate_line_data(
        self,
        df: pd.DataFrame,
        x_col: str | None,
        y_col: str | None,
        group_col: str | None,
        suppress: list[str],
    ) -> list[dict[str, Any]]:
        """Generate line chart data."""
        # Use first date/time column for x if not specified
        if x_col is None:
            date_cols = df.select_dtypes(include=["datetime", "datetime64"]).columns
            x_col = date_cols[0] if len(date_cols) > 0 else df.columns[0]

        # Use first numeric column for y if not specified
        if y_col is None:
            numeric_cols = df.select_dtypes(include=["number"]).columns
            y_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[1] if len(df.columns) > 1 else df.columns[0]

        # Sort by x_col
        df_sorted = df.sort_values(x_col)

        # If grouping, create series for each group
        if group_col:
            chart_data = []
            for group_val in df_sorted[group_col].unique():
                if pd.isna(group_val) or str(group_val).lower() in [s.lower() for s in suppress]:
                    continue

                group_df = df_sorted[df_sorted[group_col] == group_val]
                for _, row in group_df.iterrows():
                    chart_data.append({
                        "x": str(row[x_col]),
                        "y": float(row[y_col]),
                        "group": str(group_val),
                    })
        else:
            # Single series
            chart_data = []
            for _, row in df_sorted.iterrows():
                chart_data.append({
                    "x": str(row[x_col]),
                    "y": float(row[y_col]),
                })

        return chart_data

    def _generate_distribution_data(
        self,
        df: pd.DataFrame,
        y_col: str | None,
        suppress: list[str],
    ) -> list[dict[str, Any]]:
        """Generate distribution/histogram data."""
        # Use first numeric column if not specified
        if y_col is None:
            numeric_cols = df.select_dtypes(include=["number"]).columns
            y_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[0]

        # Create bins
        values = df[y_col].dropna()
        hist, bin_edges = pd.cut(values, bins=10, retbins=True, duplicates="drop")
        counts = hist.value_counts().sort_index()

        chart_data = []
        for interval, count in counts.items():
            chart_data.append({
                "bin": f"{interval.left:.1f}-{interval.right:.1f}",
                "count": int(count),
            })

        return chart_data

    def _generate_scatter_data(
        self,
        df: pd.DataFrame,
        x_col: str | None,
        y_col: str | None,
        group_col: str | None,
        suppress: list[str],
    ) -> list[dict[str, Any]]:
        """Generate scatter plot data."""
        # Use first two numeric columns if not specified
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if x_col is None:
            x_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[0]
        if y_col is None:
            y_col = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0] if len(numeric_cols) > 0 else df.columns[1] if len(df.columns) > 1 else df.columns[0]

        chart_data = []
        for _, row in df.iterrows():
            # Skip suppressed groups
            if group_col and pd.notna(row[group_col]):
                if str(row[group_col]).lower() in [s.lower() for s in suppress]:
                    continue

            point = {
                "x": float(row[x_col]) if pd.notna(row[x_col]) else 0,
                "y": float(row[y_col]) if pd.notna(row[y_col]) else 0,
            }

            if group_col and pd.notna(row[group_col]):
                point["group"] = str(row[group_col])

            chart_data.append(point)

        return chart_data[:100]  # Limit to 100 points for performance

    def _generate_map_data(
        self,
        df: pd.DataFrame,
        location_col: str | None,
        value_col: str | None,
        suppress: list[str],
    ) -> list[dict[str, Any]]:
        """Generate map data."""
        # Find location column (state, region, etc.)
        if location_col is None:
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ["state", "region", "location", "territory", "country", "city"]):
                    location_col = col
                    break

        if location_col is None:
            location_col = df.columns[0]

        # Find value column
        if value_col is None:
            numeric_cols = df.select_dtypes(include=["number"]).columns
            value_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[1] if len(df.columns) > 1 else df.columns[0]

        # Group by location
        grouped = df.groupby(location_col)[value_col].sum().reset_index()

        # Filter suppressed
        suppress_lower = [s.lower() for s in suppress]
        grouped = grouped[~grouped[location_col].astype(str).str.lower().isin(suppress_lower)]

        chart_data = []
        for _, row in grouped.iterrows():
            chart_data.append({
                "location": str(row[location_col]),
                "value": float(row[value_col]),
            })

        return chart_data

    def _generate_table_data(
        self,
        df: pd.DataFrame,
        suppress: list[str],
    ) -> list[dict[str, Any]]:
        """Generate table data."""
        # Return first 50 rows as dictionaries
        df_filtered = df.head(50)
        return df_filtered.to_dict(orient="records")
