"""
Table System for KIE v3

Comprehensive table builder with smart formatting, conditional formatting,
and KDS styling.
"""

from kie.tables.builder import (
    ComparisonTableBuilder,
    FinancialTableBuilder,
    TableBuilder,
)
from kie.tables.factory import TableFactory
from kie.tables.schema import (
    Alignment,
    ColumnConfig,
    ColumnType,
    ConditionalFormat,
    ConditionalFormatType,
    CurrencyFormat,
    NumberFormat,
    PercentageFormat,
    SparklineConfig,
    TableConfig,
)

__all__ = [
    # Schema
    "TableConfig",
    "ColumnConfig",
    "ColumnType",
    "Alignment",
    "NumberFormat",
    "CurrencyFormat",
    "PercentageFormat",
    "ConditionalFormat",
    "ConditionalFormatType",
    "SparklineConfig",
    # Builders
    "TableBuilder",
    "ComparisonTableBuilder",
    "FinancialTableBuilder",
    # Factory
    "TableFactory",
]
