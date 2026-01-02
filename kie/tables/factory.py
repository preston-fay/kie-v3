"""
Table Factory

Unified interface for creating tables with smart defaults.
"""

from typing import Union, List, Dict, Any, Optional
import pandas as pd
from pathlib import Path

from kie.tables.builder import (
    TableBuilder,
    ComparisonTableBuilder,
    FinancialTableBuilder,
)
from kie.tables.schema import TableConfig


class TableFactory:
    """
    Factory for creating tables with smart defaults.

    Provides a single entry point for all table types.
    """

    @staticmethod
    def create(
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        title: Optional[str] = None,
        table_type: str = "standard",
        **kwargs,
    ) -> TableConfig:
        """
        Create a table of the specified type.

        Args:
            data: Input data
            title: Table title
            table_type: Type of table ("standard", "comparison", "financial")
            **kwargs: Table-specific parameters

        Returns:
            TableConfig ready for JSON serialization
        """
        if table_type == "comparison":
            return TableFactory.comparison(data, title=title, **kwargs)
        elif table_type == "financial":
            return TableFactory.financial(data, title=title, **kwargs)
        else:
            return TableFactory.standard(data, title=title, **kwargs)

    @staticmethod
    def standard(
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        title: Optional[str] = None,
        **kwargs,
    ) -> TableConfig:
        """
        Create a standard table with auto-detected columns.

        Args:
            data: Input data
            title: Table title
            **kwargs: Additional TableConfig parameters

        Returns:
            TableConfig
        """
        builder = TableBuilder()
        return builder.build(data, title=title, **kwargs)

    @staticmethod
    def comparison(
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        entity_column: str,
        comparison_columns: List[str],
        title: Optional[str] = None,
        **kwargs,
    ) -> TableConfig:
        """
        Create a comparison table (e.g., competitive analysis).

        Args:
            data: Input data
            entity_column: Column with entity names
            comparison_columns: Columns to compare
            title: Table title
            **kwargs: Additional parameters

        Returns:
            TableConfig
        """
        builder = ComparisonTableBuilder()
        return builder.build_comparison(
            data,
            entity_column=entity_column,
            comparison_columns=comparison_columns,
            title=title,
            **kwargs,
        )

    @staticmethod
    def financial(
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        title: Optional[str] = None,
        currency_columns: Optional[List[str]] = None,
        percentage_columns: Optional[List[str]] = None,
        **kwargs,
    ) -> TableConfig:
        """
        Create a financial table (P&L, balance sheet, etc.).

        Args:
            data: Input data
            title: Table title
            currency_columns: Columns to format as currency
            percentage_columns: Columns to format as percentages
            **kwargs: Additional parameters

        Returns:
            TableConfig
        """
        builder = FinancialTableBuilder()
        return builder.build_financial(
            data,
            title=title,
            currency_columns=currency_columns,
            percentage_columns=percentage_columns,
            **kwargs,
        )

    @staticmethod
    def top_n(
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        sort_column: str,
        n: int = 10,
        ascending: bool = False,
        title: Optional[str] = None,
        **kwargs,
    ) -> TableConfig:
        """
        Create a "Top N" table (e.g., "Top 10 Customers by Revenue").

        Args:
            data: Input data
            sort_column: Column to sort by
            n: Number of rows to show
            ascending: Sort order
            title: Table title
            **kwargs: Additional parameters

        Returns:
            TableConfig
        """
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        # Sort and take top N
        df_sorted = df.sort_values(sort_column, ascending=ascending).head(n)

        # Build table
        builder = TableBuilder()
        config = builder.build(df_sorted, title=title, **kwargs)

        # Disable pagination for top N tables
        config.pagination.enabled = False

        # Set default sort
        from kie.tables.schema import SortDirection

        builder.set_default_sort(
            config,
            sort_column,
            SortDirection.ASC if ascending else SortDirection.DESC,
        )

        return config

    @staticmethod
    def save_json(config: TableConfig, output_path: Union[str, Path]) -> Path:
        """
        Save table configuration to JSON file.

        Args:
            config: TableConfig to save
            output_path: Output file path

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write(config.model_dump_json(indent=2))

        return output_path
