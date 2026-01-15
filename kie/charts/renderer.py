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

from kie.charts.formatting import format_number


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

    def render_charts(
        self, data_file: Path | None = None, validate: bool = True
    ) -> dict[str, Any]:
        """
        Render all charts from visualization plan.

        Args:
            data_file: Data file to use for charts (optional, will auto-detect)
            validate: If True, validate charts for KDS compliance (default: True)

        Returns:
            Dictionary with success status and rendered charts info

        Raises:
            FileNotFoundError: If visualization_plan.json is missing
            ValueError: If data file cannot be found
            BrandComplianceError: If charts violate KDS guidelines (when validate=True)
        """
        # REQUIREMENT: visualization_plan.json MUST exist
        viz_plan_path = self.outputs_dir / "internal" / "visualization_plan.json"
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

            # Check if spec has multiple visuals (Visual Pattern Library)
            if "visuals" in spec:
                # Multi-visual pattern - render each visual
                for visual_spec in spec["visuals"]:
                    chart_info = self._render_chart_from_visual(spec, visual_spec, df)
                    rendered_charts.append(chart_info)
            # Chart Excellence Plan: Check if spec has multiple chart versions
            elif "chart_versions" in spec:
                # Multiple chart versions - render each version
                for version_spec in spec["chart_versions"]:
                    chart_info = self._render_chart_version(spec, version_spec, df)
                    rendered_charts.append(chart_info)
            else:
                # Single visualization (original behavior)
                chart_info = self._render_chart(spec, df)
                rendered_charts.append(chart_info)

        # PR #1: RENDER-TIME KDS VALIDATION
        # Validate all rendered chart configs for KDS compliance
        if validate and rendered_charts:
            self._validate_kds_compliance()

        return {
            "success": True,
            "message": f"Rendered {len(rendered_charts)} charts from visualization plan",
            "charts_rendered": len(rendered_charts),
            "charts": rendered_charts,
            "visualizations_planned": len([s for s in specs if s.get("visualization_required", False)]),
            "visualizations_skipped": len([s for s in specs if not s.get("visualization_required", False)]),
            "kds_validated": validate,
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

    def _render_chart_from_visual(
        self, spec: dict[str, Any], visual_spec: dict[str, Any], df: pd.DataFrame
    ) -> dict[str, Any]:
        """
        Render a single chart from a visual specification within a multi-visual pattern.

        Args:
            spec: Parent insight specification
            visual_spec: Individual visual specification from pattern
            df: Source data

        Returns:
            Chart info dictionary
        """
        insight_id = spec.get("insight_id", "unknown")
        viz_type = visual_spec.get("visualization_type", "bar")
        purpose = visual_spec.get("purpose", "comparison")
        x_axis = visual_spec.get("x_axis")
        y_axis = visual_spec.get("y_axis")
        grouping = visual_spec.get("grouping")
        highlights = visual_spec.get("highlights", [])
        suppress = visual_spec.get("suppress", [])
        annotations = visual_spec.get("annotations", [])
        caveats = visual_spec.get("caveats", [])
        pattern_role = visual_spec.get("pattern_role", "")
        description = visual_spec.get("description", "")
        confidence = spec.get("confidence", {})

        # Map visualization type to chart implementation
        chart_data = self._map_visualization_type(
            viz_type, df, x_axis, y_axis, grouping, suppress, highlights
        )

        # Build chart config with KDS-compliant settings
        chart_config = {
            "insight_id": insight_id,
            "insight_title": spec.get("insight_title", "Untitled"),
            "visualization_type": viz_type,
            "purpose": purpose,
            "pattern_role": pattern_role,
            "description": description,
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
            "config": {
                # KDS compliance settings
                "gridLines": False,  # KDS: no gridlines
                "axisLine": False,   # KDS: no axis lines
                "tickLine": False,   # KDS: no tick lines
                "dataLabels": True,  # KDS: show data labels
                "fontFamily": "Inter, Arial, sans-serif",  # KDS typography
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source": "visualization_plan",
                "multi_visual_pattern": True,
            },
        }

        # Deterministic filename with pattern role
        filename = f"{insight_id}__{viz_type}__{pattern_role}.json" if pattern_role else f"{insight_id}__{viz_type}.json"
        output_path = self.charts_dir / filename

        # Save chart config
        with open(output_path, "w") as f:
            json.dump(chart_config, f, indent=2)

        return {
            "insight_id": insight_id,
            "visualization_type": viz_type,
            "pattern_role": pattern_role,
            "filename": filename,
            "path": str(output_path),
            "data_points": len(chart_data) if isinstance(chart_data, list) else 0,
        }

    def _render_chart_version(
        self, spec: dict[str, Any], version_spec: dict[str, Any], df: pd.DataFrame
    ) -> dict[str, Any]:
        """
        Render a chart version from specification (Chart Excellence Plan).

        Args:
            spec: Parent specification (contains insight metadata)
            version_spec: Version-specific visualization specification
            df: Source data

        Returns:
            Chart info dictionary
        """
        insight_id = spec.get("insight_id", "unknown")
        viz_type = version_spec.get("visualization_type", "bar")
        purpose = version_spec.get("purpose", "comparison")
        version_id = version_spec.get("version_id", "primary")
        is_primary = version_spec.get("is_primary", True)
        x_axis = version_spec.get("x_axis")
        y_axis = version_spec.get("y_axis")
        grouping = version_spec.get("grouping")
        highlights = version_spec.get("highlights", [])
        suppress = version_spec.get("suppress", [])
        annotations = version_spec.get("annotations", [])
        caveats = version_spec.get("caveats", [])
        confidence = spec.get("confidence", {})

        # Map visualization type to chart implementation
        chart_data = self._map_visualization_type(
            viz_type, df, x_axis, y_axis, grouping, suppress, highlights
        )

        # Build chart config with KDS-compliant settings
        chart_config = {
            "insight_id": insight_id,
            "insight_title": spec.get("insight_title", "Untitled"),
            "visualization_type": viz_type,
            "purpose": purpose,
            "version_id": version_id,
            "is_primary": is_primary,
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
            "config": {
                # KDS compliance settings
                "gridLines": False,  # KDS: no gridlines
                "axisLine": False,   # KDS: no axis lines
                "tickLine": False,   # KDS: no tick lines
                "dataLabels": True,  # KDS: show data labels
                "fontFamily": "Inter, Arial, sans-serif",  # KDS typography
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source": "visualization_plan",
                "chart_version": version_id,
            },
        }

        # Deterministic filename with version suffix
        # Primary: insight_123__bar.json
        # Alternative: insight_123__horizontal_bar__alt1.json
        if is_primary:
            filename = f"{insight_id}__{viz_type}.json"
        else:
            filename = f"{insight_id}__{viz_type}__{version_id}.json"

        output_path = self.charts_dir / filename

        # Save chart config
        with open(output_path, "w") as f:
            json.dump(chart_config, f, indent=2)

        return {
            "insight_id": insight_id,
            "visualization_type": viz_type,
            "version_id": version_id,
            "is_primary": is_primary,
            "filename": filename,
            "path": str(output_path),
            "data_points": len(chart_data) if isinstance(chart_data, list) else 0,
        }

    def _render_chart(self, spec: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
        """
        Render a single chart from specification using ChartFactory.

        Args:
            spec: Visualization specification
            df: Source data

        Returns:
            Chart info dictionary
        """
        from kie.charts import ChartFactory

        insight_id = spec.get("insight_id", "unknown")
        viz_type = spec.get("visualization_type", "bar")
        x_axis = spec.get("x_axis")
        y_axis = spec.get("y_axis")
        grouping = spec.get("grouping")
        suppress = spec.get("suppress", [])
        title = spec.get("insight_title", "Untitled")

        # Find actual column names (fuzzy match)
        x_col = self._find_column(df, x_axis) if x_axis else None
        y_col = self._find_column(df, y_axis) if y_axis else None

        # Apply suppressions before passing to ChartFactory
        if suppress:
            suppress_lower = [s.lower() for s in suppress]
            if x_col and x_col in df.columns:
                df = df[~df[x_col].astype(str).str.lower().isin(suppress_lower)]

        # Map visualization type to ChartFactory method
        try:
            chart_config = self._create_chart_via_factory(
                viz_type, df, x_col, y_col, grouping, title
            )
        except Exception as e:
            print(f"⚠️  Chart generation failed for {insight_id}: {e}")
            # Fallback to bar chart
            if x_col and y_col:
                chart_config = ChartFactory.bar(df, x=x_col, y=[y_col], title=title)
            else:
                # Last resort: use first categorical and first numeric
                categorical_cols = df.select_dtypes(include=["object", "category"]).columns
                numeric_cols = df.select_dtypes(include=["number"]).columns
                if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                    chart_config = ChartFactory.bar(
                        df, x=categorical_cols[0], y=[numeric_cols[0]], title=title
                    )
                else:
                    raise ValueError(f"Cannot generate chart: insufficient columns")

        # Deterministic filename
        filename = f"{insight_id}__{viz_type}.json"
        output_path = self.charts_dir / filename

        # Save JSON (for React rendering)
        chart_config.to_json(output_path)

        # Also save SVG (for static exports)
        svg_path = chart_config.to_svg(output_path.with_suffix('.svg'))

        return {
            "insight_id": insight_id,
            "visualization_type": viz_type,
            "filename": filename,
            "path": str(output_path),
            "svg_path": str(svg_path),
            "data_points": len(chart_config.data),
        }

    def _create_chart_via_factory(
        self,
        viz_type: str,
        df: pd.DataFrame,
        x_col: str | None,
        y_col: str | None,
        grouping: str | None,
        title: str,
    ):
        """
        Create a chart using ChartFactory based on visualization type.

        Args:
            viz_type: Visualization type from planner
            df: Source DataFrame
            x_col: X-axis column name
            y_col: Y-axis column name (or multiple for grouped charts)
            grouping: Grouping column name
            title: Chart title

        Returns:
            RechartsConfig object
        """
        from kie.charts import ChartFactory

        # Map visualization types to ChartFactory methods
        if viz_type == "bar":
            return ChartFactory.bar(df, x=x_col, y=[y_col], title=title)

        elif viz_type == "horizontal_bar":
            return ChartFactory.horizontal_bar(df, x=x_col, y=[y_col], title=title)

        elif viz_type == "stacked_bar":
            # For stacked bars, we need multiple y columns
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if y_col in numeric_cols:
                numeric_cols.remove(y_col)
            y_cols = [y_col] + numeric_cols[:2]  # Use up to 3 series
            return ChartFactory.stacked_bar(df, x=x_col, y=y_cols, title=title)

        elif viz_type == "line":
            return ChartFactory.line(df, x=x_col, y=[y_col], title=title)

        elif viz_type == "area":
            return ChartFactory.area(df, x=x_col, y=[y_col], title=title)

        elif viz_type == "stacked_area":
            # For stacked areas, we need multiple y columns
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if y_col in numeric_cols:
                numeric_cols.remove(y_col)
            y_cols = [y_col] + numeric_cols[:2]  # Use up to 3 series
            return ChartFactory.stacked_area(df, x=x_col, y=y_cols, title=title)

        elif viz_type == "pie":
            return ChartFactory.pie(df, name=x_col, value=y_col, title=title)

        elif viz_type == "donut":
            return ChartFactory.donut(df, name=x_col, value=y_col, title=title)

        elif viz_type == "scatter":
            # Scatter plots need 2 numeric columns
            category_col = grouping if grouping else None
            return ChartFactory.scatter(df, x=x_col, y=y_col, category=category_col, title=title)

        elif viz_type == "combo":
            # Combo charts need both bars and lines
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if y_col in numeric_cols:
                numeric_cols.remove(y_col)
            bar_cols = [y_col]
            line_cols = numeric_cols[:1] if len(numeric_cols) > 0 else [y_col]
            return ChartFactory.combo(df, x=x_col, bars=bar_cols, lines=line_cols, title=title)

        elif viz_type == "waterfall":
            # Waterfall charts need labels and values
            return ChartFactory.waterfall(df, labels=x_col, values=y_col, title=title)

        elif viz_type in ["distribution", "histogram"]:
            # Distribution charts are handled specially (not a standard chart type)
            # Fall back to bar chart of binned data
            return ChartFactory.bar(df, x=x_col if x_col else df.columns[0], y=[y_col], title=title)

        elif viz_type == "pareto":
            # Pareto is a combo of bar + line (cumulative %)
            return ChartFactory.combo(df, x=x_col, bars=[y_col], lines=["cumulative"], title=title)

        elif viz_type in ["map", "table"]:
            # Maps and tables are not chart types - skip
            raise ValueError(f"Chart type '{viz_type}' is not a visualization chart")

        else:
            # Default to bar chart
            return ChartFactory.bar(df, x=x_col, y=[y_col], title=title)

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
        elif viz_type == "distribution" or viz_type == "histogram":
            return self._generate_distribution_data(df, y_col, suppress)
        elif viz_type == "scatter":
            return self._generate_scatter_data(df, x_col, y_col, group_col, suppress)
        elif viz_type == "map":
            return self._generate_map_data(df, x_col, y_col, suppress)
        elif viz_type == "table":
            return self._generate_table_data(df, suppress)
        elif viz_type == "pareto":
            return self._generate_pareto_data(df, x_col, y_col, suppress)
        elif viz_type == "distribution_summary":
            return self._generate_distribution_summary(df, y_col, suppress)
        elif viz_type == "trend_summary":
            return self._generate_trend_summary(df, x_col, y_col, suppress)
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
                "bin": f"{format_number(interval.left, precision=1)}-{format_number(interval.right, precision=1)}",
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

    def _generate_pareto_data(
        self,
        df: pd.DataFrame,
        x_col: str | None,
        y_col: str | None,
        suppress: list[str],
    ) -> list[dict[str, Any]]:
        """
        Generate Pareto chart data (bar + cumulative line).

        Shows top contributors and their cumulative share.
        """
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

        # Calculate cumulative percentage
        total = grouped[y_col].sum()
        grouped["cumulative"] = grouped[y_col].cumsum()
        grouped["cumulative_pct"] = (grouped["cumulative"] / total * 100).round(1)

        # Take top 10
        grouped = grouped.head(10)

        # Build chart data
        chart_data = []
        for _, row in grouped.iterrows():
            chart_data.append({
                "category": str(row[x_col]),
                "value": float(row[y_col]),
                "cumulative_pct": float(row["cumulative_pct"]),
            })

        return chart_data

    def _generate_distribution_summary(
        self,
        df: pd.DataFrame,
        y_col: str | None,
        suppress: list[str],
    ) -> list[dict[str, Any]]:
        """
        Generate distribution summary statistics (table format).

        Shows min, Q1, median, Q3, max, IQR.
        """
        # Use first numeric column if not specified
        if y_col is None:
            numeric_cols = df.select_dtypes(include=["number"]).columns
            y_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[0]

        # Get values
        values = df[y_col].dropna()

        # Calculate statistics
        stats = {
            "min": float(values.min()),
            "q1": float(values.quantile(0.25)),
            "median": float(values.median()),
            "q3": float(values.quantile(0.75)),
            "max": float(values.max()),
            "mean": float(values.mean()),
            "std": float(values.std()),
            "iqr": float(values.quantile(0.75) - values.quantile(0.25)),
        }

        # Return as table-like structure
        return [
            {"metric": "Minimum", "value": stats["min"]},
            {"metric": "Q1 (25th percentile)", "value": stats["q1"]},
            {"metric": "Median (50th percentile)", "value": stats["median"]},
            {"metric": "Mean", "value": stats["mean"]},
            {"metric": "Q3 (75th percentile)", "value": stats["q3"]},
            {"metric": "Maximum", "value": stats["max"]},
            {"metric": "IQR (Interquartile Range)", "value": stats["iqr"]},
            {"metric": "Std Deviation", "value": stats["std"]},
        ]

    def _generate_trend_summary(
        self,
        df: pd.DataFrame,
        x_col: str | None,
        y_col: str | None,
        suppress: list[str],
    ) -> list[dict[str, Any]]:
        """
        Generate trend summary (trend direction and strength).

        Simple correlation-based trend analysis.
        """
        # Use first two numeric columns if not specified
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if x_col is None:
            x_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[0]
        if y_col is None:
            y_col = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0] if len(numeric_cols) > 0 else df.columns[1] if len(df.columns) > 1 else df.columns[0]

        # Convert to numeric if needed
        x_vals = pd.to_numeric(df[x_col], errors="coerce").dropna()
        y_vals = pd.to_numeric(df[y_col], errors="coerce").dropna()

        # Calculate correlation
        if len(x_vals) > 1 and len(y_vals) > 1:
            correlation = x_vals.corr(y_vals)

            # Determine trend direction and strength
            if abs(correlation) < 0.3:
                trend = "Weak relationship"
                strength = "low"
            elif abs(correlation) < 0.7:
                trend = "Moderate relationship"
                strength = "medium"
            else:
                trend = "Strong relationship"
                strength = "high"

            direction = "Positive" if correlation > 0 else "Negative"
        else:
            correlation = 0.0
            trend = "Insufficient data"
            strength = "none"
            direction = "Unknown"

        # Return as table-like structure
        return [
            {"metric": "Direction", "value": direction},
            {"metric": "Strength", "value": strength.title()},
            {"metric": "Correlation", "value": round(correlation, 3)},
            {"metric": "Assessment", "value": trend},
        ]

    def _validate_kds_compliance(self) -> None:
        """
        Validate all rendered chart configs for KDS compliance.

        This is the CRITICAL ENFORCEMENT GATE that prevents non-KDS
        charts from reaching consultants.

        Raises:
            BrandComplianceError: If any chart violates KDS guidelines
        """
        from kie.brand.validator import BrandValidator
        from kie.exceptions import BrandComplianceError

        validator = BrandValidator(strict=True)

        # Validate all chart JSON files in charts directory
        validation_result = validator.validate_directory(self.charts_dir)

        if not validation_result["compliant"]:
            # Build detailed error message
            error_lines = [
                "❌ KDS COMPLIANCE FAILURE",
                "",
                f"Charts violate Kearney Design System guidelines:",
                "",
            ]

            for violation in validation_result["violations"]:
                error_lines.append(f"  • {violation}")

            error_lines.extend([
                "",
                "Fix required before charts can be published.",
                "Charts must use KDS palette, no gridlines, proper typography.",
            ])

            error_message = "\n".join(error_lines)

            raise BrandComplianceError(
                error_message,
                details={
                    "violations": validation_result["violations"],
                    "files_checked": validation_result["files_checked"],
                    "charts_dir": str(self.charts_dir),
                },
            )
