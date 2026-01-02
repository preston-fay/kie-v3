"""
Table System for KIE v3

Comprehensive table builder with smart formatting, conditional formatting,
and KDS styling.
"""

from kie.tables.schema import (
    TableConfig,
    ColumnConfig,
    ColumnType,
    Alignment,
    NumberFormat,
    CurrencyFormat,
    PercentageFormat,
    ConditionalFormat,
    ConditionalFormatType,
    SparklineConfig,
)
from kie.tables.builder import (
    TableBuilder,
    ComparisonTableBuilder,
    FinancialTableBuilder,
)
from kie.tables.factory import TableFactory

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
