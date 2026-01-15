"""
Table Builder

Creates JSON configurations for KDS-styled tables with smart formatting.
"""

from datetime import date, datetime
from typing import Any, Literal

import pandas as pd

from kie.brand.theme import get_theme
from kie.formatting.field_registry import FieldRegistry
from kie.tables.schema import (
    Alignment,
    ColumnConfig,
    ColumnType,
    ConditionalFormat,
    ConditionalFormatType,
    CurrencyFormat,
    DateFormat,
    NumberFormat,
    PercentageFormat,
    SortConfig,
    SortDirection,
    SparklineConfig,
    TableConfig,
)


class TableBuilder:
    """
    Build table configurations with smart column detection and formatting.

    Automatically detects column types, applies appropriate formatting,
    and generates KDS-compliant table configs.
    """

    def __init__(self):
        """Initialize table builder."""
        self.theme = get_theme()

    def build(
        self,
        data: pd.DataFrame | list[dict[str, Any]],
        title: str | None = None,
        columns: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> TableConfig:
        """
        Build table configuration from data.

        Args:
            data: DataFrame or list of dicts
            title: Table title
            columns: Optional custom column configurations
            **kwargs: Additional TableConfig parameters

        Returns:
            TableConfig ready for JSON serialization
        """
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        # Auto-detect columns if not provided
        if columns is None:
            column_configs = self._auto_detect_columns(df)
        else:
            column_configs = self._build_column_configs(columns, df)

        # Convert DataFrame to dict records
        data_records = df.to_dict("records")

        # Build table config
        config = TableConfig(
            title=title,
            columns=column_configs,
            data=data_records,
            theme_mode=self.theme.mode.value,
            **kwargs,
        )

        return config

    def _auto_detect_columns(self, df: pd.DataFrame) -> list[ColumnConfig]:
        """
        Auto-detect column types and formats from DataFrame.

        Args:
            df: DataFrame

        Returns:
            List of ColumnConfig
        """
        columns = []

        for col in df.columns:
            # Sample values for type detection
            sample = df[col].dropna().head(10)

            if len(sample) == 0:
                # Empty column - treat as text
                columns.append(
                    ColumnConfig(
                        key=col,
                        header=self._format_header(col),
                        type=ColumnType.TEXT,
                    )
                )
                continue

            # Detect type
            col_type, format_config = self._detect_column_type(sample, col)

            # Determine alignment
            if col_type in [
                ColumnType.NUMBER,
                ColumnType.CURRENCY,
                ColumnType.PERCENTAGE,
            ]:
                alignment = Alignment.RIGHT
            elif col_type in [ColumnType.DATE, ColumnType.DATETIME]:
                alignment = Alignment.CENTER
            else:
                alignment = Alignment.LEFT

            # Build column config
            col_config = ColumnConfig(
                key=col,
                header=self._format_header(col),
                type=col_type,
                alignment=alignment,
                **format_config,
            )

            columns.append(col_config)

        return columns

    def _detect_column_type(
        self, sample: pd.Series, col_name: str
    ) -> tuple[ColumnType, dict[str, Any]]:
        """
        Detect column type from sample data.

        Args:
            sample: Sample values
            col_name: Column name

        Returns:
            Tuple of (ColumnType, format_config_dict)
        """
        # Check for specific patterns in column name
        col_lower = col_name.lower()

        # Currency detection
        if any(
            keyword in col_lower
            for keyword in ["revenue", "cost", "price", "amount", "salary", "budget"]
        ):
            return ColumnType.CURRENCY, {
                "currency_format": CurrencyFormat(
                    abbreviate=True if sample.max() >= 1000000 else False
                )
            }

        # Percentage detection
        if any(
            keyword in col_lower
            for keyword in [
                "percent",
                "pct",
                "rate",
                "growth",
                "margin",
                "ratio",
                "%",
            ]
        ):
            # Check if values are 0-1 or 0-100
            max_val = sample.max()
            multiply = max_val <= 1.0
            return ColumnType.PERCENTAGE, {
                "percentage_format": PercentageFormat(multiply_by_100=multiply)
            }

        # Date detection
        if pd.api.types.is_datetime64_any_dtype(sample):
            return ColumnType.DATETIME, {
                "date_format": DateFormat(format="MM/DD/YYYY HH:mm")
            }

        # Check first value
        first_val = sample.iloc[0]

        if isinstance(first_val, date | datetime):
            return ColumnType.DATE, {"date_format": DateFormat(format="MM/DD/YYYY")}

        if isinstance(first_val, bool):
            return ColumnType.BOOLEAN, {}

        if isinstance(first_val, int | float):
            # Number - check if should abbreviate
            max_val = abs(sample).max()
            return ColumnType.NUMBER, {
                "number_format": NumberFormat(
                    abbreviate=max_val >= 1000000, thousands_separator=True
                )
            }

        # Default to text
        return ColumnType.TEXT, {}

    def _format_header(self, col_name: str) -> str:
        """
        Format column name for display using semantic field registry.

        Args:
            col_name: Column name

        Returns:
            Formatted header (client-friendly)
        """
        # Use FieldRegistry for consultant-friendly names
        return FieldRegistry.beautify(col_name)

    def _build_column_configs(
        self, columns: list[dict[str, Any]], df: pd.DataFrame
    ) -> list[ColumnConfig]:
        """
        Build column configs from custom specifications.

        Args:
            columns: List of column spec dicts
            df: DataFrame

        Returns:
            List of ColumnConfig
        """
        configs = []

        for col_spec in columns:
            # Convert dict to ColumnConfig
            config = ColumnConfig(**col_spec)
            configs.append(config)

        return configs

    def add_conditional_formatting(
        self,
        config: TableConfig,
        column: str,
        format_type: ConditionalFormatType,
        **kwargs,
    ) -> TableConfig:
        """
        Add conditional formatting to a column.

        Args:
            config: TableConfig to modify
            column: Column key
            format_type: Type of conditional formatting
            **kwargs: Format-specific parameters

        Returns:
            Modified TableConfig
        """
        # Find column
        for col in config.columns:
            if col.key == column:
                # Create conditional format
                cond_format = ConditionalFormat(
                    type=format_type, column=column, **kwargs
                )
                col.conditional_formats.append(cond_format)
                break

        return config

    def add_totals_row(self, config: TableConfig) -> TableConfig:
        """
        Enable totals row with appropriate aggregations.

        Args:
            config: TableConfig to modify

        Returns:
            Modified TableConfig
        """
        config.show_totals_row = True

        # Auto-add sum aggregations for numeric columns
        for col in config.columns:
            if col.type in [ColumnType.NUMBER, ColumnType.CURRENCY]:
                col.footer_aggregate = "sum"
            elif col.type == ColumnType.PERCENTAGE:
                col.footer_aggregate = "avg"

        return config

    def set_default_sort(
        self, config: TableConfig, column: str, direction: SortDirection = SortDirection.DESC
    ) -> TableConfig:
        """
        Set default sort order.

        Args:
            config: TableConfig to modify
            column: Column to sort by
            direction: Sort direction

        Returns:
            Modified TableConfig
        """
        config.initial_sort = [SortConfig(column=column, direction=direction)]
        return config

    def add_sparkline_column(
        self,
        config: TableConfig,
        column_key: str,
        header: str,
        data_key: str,
        chart_type: Literal["line", "bar", "area"] = "line",
    ) -> TableConfig:
        """
        Add a sparkline column.

        Args:
            config: TableConfig to modify
            column_key: New column key
            header: Column header
            data_key: Key in row data containing array of values
            chart_type: Type of sparkline

        Returns:
            Modified TableConfig
        """
        # Add sparkline column
        sparkline_col = ColumnConfig(
            key=column_key,
            header=header,
            type=ColumnType.SPARKLINE,
            alignment=Alignment.CENTER,
            sortable=False,
            filterable=False,
            sparkline_config=SparklineConfig(
                type=chart_type,
                data_key=data_key,
                color=self.theme.colors.brand_primary,
            ),
        )

        config.columns.append(sparkline_col)
        return config


class ComparisonTableBuilder(TableBuilder):
    """
    Builder for comparison tables (e.g., competitive analysis).

    Optimized for side-by-side comparisons with highlighting.
    """

    def build_comparison(
        self,
        data: pd.DataFrame | list[dict[str, Any]],
        entity_column: str,
        comparison_columns: list[str],
        title: str | None = None,
        highlight_best: bool = True,
    ) -> TableConfig:
        """
        Build comparison table.

        Args:
            data: Data to compare
            entity_column: Column with entity names (e.g., "Company")
            comparison_columns: Columns to compare
            title: Table title
            highlight_best: Highlight best value in each comparison column

        Returns:
            TableConfig
        """
        # Build base config
        config = self.build(data, title=title)

        # Freeze entity column
        for col in config.columns:
            if col.key == entity_column:
                col.frozen = True
                break

        # Add conditional formatting to highlight best values
        if highlight_best:
            for col_key in comparison_columns:
                # Find column
                col = next((c for c in config.columns if c.key == col_key), None)
                if not col:
                    continue

                # Determine if higher or lower is better based on column name
                col_lower = col_key.lower()
                higher_is_better = any(
                    keyword in col_lower
                    for keyword in ["revenue", "growth", "score", "rating"]
                )

                # Add highlighting
                self.add_conditional_formatting(
                    config,
                    col_key,
                    ConditionalFormatType.THRESHOLD,
                    operator="eq" if higher_is_better else "eq",
                    background_color=self.theme.colors.brand_light,
                    font_weight="bold",
                )

        return config


class FinancialTableBuilder(TableBuilder):
    """
    Builder for financial tables (P&L, balance sheets, etc.).

    Includes subtotals, percentage calculations, and financial formatting.
    """

    def build_financial(
        self,
        data: pd.DataFrame | list[dict[str, Any]],
        title: str | None = None,
        currency_columns: list[str] | None = None,
        percentage_columns: list[str] | None = None,
    ) -> TableConfig:
        """
        Build financial table.

        Args:
            data: Financial data
            title: Table title
            currency_columns: Columns to format as currency
            percentage_columns: Columns to format as percentages

        Returns:
            TableConfig
        """
        # Build base config
        config = self.build(data, title=title)

        # Override types for currency columns
        if currency_columns:
            for col in config.columns:
                if col.key in currency_columns:
                    col.type = ColumnType.CURRENCY
                    col.currency_format = CurrencyFormat(
                        abbreviate=True, thousands_separator=True
                    )
                    col.alignment = Alignment.RIGHT

        # Override types for percentage columns
        if percentage_columns:
            for col in config.columns:
                if col.key in percentage_columns:
                    col.type = ColumnType.PERCENTAGE
                    col.percentage_format = PercentageFormat()
                    col.alignment = Alignment.RIGHT

        # Enable totals row
        self.add_totals_row(config)

        # Style for financial tables
        config.style.bordered = True
        config.style.compact = False

        return config
