"""
Data Profile

Structured container for data profiling results.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional


class ColumnProfile(BaseModel):
    """Profile for a single column."""

    name: str
    dtype: str
    non_null_count: int
    null_count: int
    null_percent: float
    unique_count: int
    unique_percent: float

    # For numeric columns
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    median: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None

    # For categorical columns
    top_values: Optional[list] = None
    value_counts: Optional[dict] = None

    @property
    def is_numeric(self) -> bool:
        return self.dtype in ("int64", "float64", "int32", "float32")

    @property
    def is_categorical(self) -> bool:
        return self.dtype in ("object", "category", "bool")


class DataProfile(BaseModel):
    """Complete profile of a dataset."""

    rows: int
    columns: int
    memory_mb: float
    column_profiles: dict = Field(default_factory=dict)

    # Data quality
    total_nulls: int = 0
    null_percent: float = 0.0
    duplicate_rows: int = 0
    duplicate_percent: float = 0.0

    # Column type breakdown
    numeric_columns: list = Field(default_factory=list)
    categorical_columns: list = Field(default_factory=list)
    datetime_columns: list = Field(default_factory=list)

    # Potential issues
    high_cardinality_columns: list = Field(default_factory=list)
    high_null_columns: list = Field(default_factory=list)
    constant_columns: list = Field(default_factory=list)

    def summary(self) -> str:
        """Get text summary of profile."""
        lines = [
            f"Dataset: {self.rows:,} rows x {self.columns} columns ({self.memory_mb:.2f} MB)",
            "",
            "Column Types:",
            f"  Numeric: {len(self.numeric_columns)}",
            f"  Categorical: {len(self.categorical_columns)}",
            f"  Datetime: {len(self.datetime_columns)}",
            "",
            "Data Quality:",
            f"  Missing values: {self.null_percent:.1f}%",
            f"  Duplicate rows: {self.duplicate_rows:,} ({self.duplicate_percent:.1f}%)",
        ]

        if self.high_null_columns:
            lines.append(f"  High null columns: {', '.join(self.high_null_columns)}")

        if self.constant_columns:
            lines.append(f"  Constant columns: {', '.join(self.constant_columns)}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "shape": {"rows": self.rows, "columns": self.columns},
            "memory_mb": self.memory_mb,
            "column_types": {
                "numeric": self.numeric_columns,
                "categorical": self.categorical_columns,
                "datetime": self.datetime_columns,
            },
            "quality": {
                "null_percent": self.null_percent,
                "duplicate_rows": self.duplicate_rows,
                "duplicate_percent": self.duplicate_percent,
            },
            "issues": {
                "high_null_columns": self.high_null_columns,
                "constant_columns": self.constant_columns,
                "high_cardinality_columns": self.high_cardinality_columns,
            },
        }
