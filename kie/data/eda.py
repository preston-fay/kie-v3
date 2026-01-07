"""
Exploratory Data Analysis (EDA)

Automatic data profiling and analysis.
"""

from pathlib import Path
from typing import Optional, Union
import pandas as pd
import numpy as np

from .loader import load_data
from .profile import DataProfile, ColumnProfile


class EDA:
    """Exploratory Data Analysis engine."""

    def __init__(
        self,
        high_null_threshold: float = 0.3,
        high_cardinality_threshold: float = 0.9,
    ):
        """
        Initialize EDA engine.

        Args:
            high_null_threshold: Fraction of nulls to flag as high (default 30%)
            high_cardinality_threshold: Fraction of unique values to flag (default 90%)
        """
        self.high_null_threshold = high_null_threshold
        self.high_cardinality_threshold = high_cardinality_threshold
        self.df: Optional[pd.DataFrame] = None
        self.profile: Optional[DataProfile] = None

    def analyze(self, data: Union[str, Path, pd.DataFrame]) -> DataProfile:
        """
        Analyze data and generate profile.

        Args:
            data: Path to file or DataFrame

        Returns:
            DataProfile with complete analysis
        """
        # Load if path
        if isinstance(data, (str, Path)):
            self.df = load_data(data)
        else:
            self.df = data

        # Basic info
        rows, cols = self.df.shape
        memory_mb = self.df.memory_usage(deep=True).sum() / (1024 * 1024)

        # Initialize profile
        self.profile = DataProfile(
            rows=rows,
            columns=cols,
            memory_mb=memory_mb,
        )

        # Analyze columns
        self._analyze_columns()

        # Data quality
        self._analyze_quality()

        return self.profile

    def _analyze_columns(self):
        """Analyze each column."""
        for col in self.df.columns:
            series = self.df[col]
            dtype = str(series.dtype)

            # Basic stats
            non_null = series.notna().sum()
            null_count = series.isna().sum()
            null_pct = null_count / len(series) * 100
            unique_count = series.nunique()
            unique_pct = unique_count / len(series) * 100

            col_profile = ColumnProfile(
                name=col,
                dtype=dtype,
                non_null_count=int(non_null),
                null_count=int(null_count),
                null_percent=round(null_pct, 2),
                unique_count=int(unique_count),
                unique_percent=round(unique_pct, 2),
            )

            # Numeric columns (excluding boolean)
            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                self.profile.numeric_columns.append(col)
                col_profile.mean = round(float(series.mean()), 4) if not series.isna().all() else None
                col_profile.std = round(float(series.std()), 4) if not series.isna().all() else None
                col_profile.min = float(series.min()) if not series.isna().all() else None
                col_profile.max = float(series.max()) if not series.isna().all() else None
                col_profile.median = float(series.median()) if not series.isna().all() else None
                col_profile.q25 = float(series.quantile(0.25)) if not series.isna().all() else None
                col_profile.q75 = float(series.quantile(0.75)) if not series.isna().all() else None

            # Categorical columns (including boolean)
            elif pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series) or pd.api.types.is_bool_dtype(series):
                self.profile.categorical_columns.append(col)
                vc = series.value_counts()
                col_profile.top_values = list(vc.head(5).index)
                col_profile.value_counts = vc.head(10).to_dict()

            # Datetime columns
            elif pd.api.types.is_datetime64_any_dtype(series):
                self.profile.datetime_columns.append(col)

            # Flag issues
            if null_pct / 100 > self.high_null_threshold:
                self.profile.high_null_columns.append(col)

            if unique_count == 1:
                self.profile.constant_columns.append(col)

            if unique_pct / 100 > self.high_cardinality_threshold and not pd.api.types.is_numeric_dtype(series):
                self.profile.high_cardinality_columns.append(col)

            self.profile.column_profiles[col] = col_profile

    def _analyze_quality(self):
        """Analyze overall data quality."""
        # Total nulls
        total_nulls = self.df.isna().sum().sum()
        total_cells = self.df.shape[0] * self.df.shape[1]
        self.profile.total_nulls = int(total_nulls)
        self.profile.null_percent = round(total_nulls / total_cells * 100, 2)

        # Duplicates
        duplicates = self.df.duplicated().sum()
        self.profile.duplicate_rows = int(duplicates)
        self.profile.duplicate_percent = round(duplicates / len(self.df) * 100, 2)

    def get_correlations(self, method: str = "pearson") -> Optional[pd.DataFrame]:
        """
        Get correlation matrix for numeric columns.

        Args:
            method: Correlation method (pearson, spearman, kendall)

        Returns:
            Correlation matrix DataFrame
        """
        if self.df is None:
            return None

        numeric_cols = self.profile.numeric_columns if self.profile else self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return None

        return self.df[numeric_cols].corr(method=method)

    def get_summary_stats(self) -> pd.DataFrame:
        """Get summary statistics for all columns."""
        if self.df is None:
            return pd.DataFrame()

        return self.df.describe(include="all").T

    def suggest_analysis(self) -> list[str]:
        """
        Suggest analysis directions based on data.

        Returns:
            List of analysis suggestions
        """
        if self.profile is None:
            return ["Run analyze() first"]

        suggestions = []

        # Based on column types
        if len(self.profile.numeric_columns) >= 2:
            suggestions.append(f"Correlation analysis between {len(self.profile.numeric_columns)} numeric columns")

        if self.profile.categorical_columns and self.profile.numeric_columns:
            suggestions.append(f"Group-by analysis: {self.profile.categorical_columns[0]} vs {self.profile.numeric_columns[0]}")

        # Based on data characteristics
        if self.profile.duplicate_rows > 0:
            suggestions.append(f"Investigate {self.profile.duplicate_rows} duplicate rows")

        if self.profile.high_null_columns:
            suggestions.append(f"Address missing data in: {', '.join(self.profile.high_null_columns)}")

        # Value distribution
        for col in self.profile.categorical_columns[:3]:
            cp = self.profile.column_profiles[col]
            if cp.value_counts:
                suggestions.append(f"Distribution analysis for '{col}' ({cp.unique_count} categories)")

        return suggestions

    def print_report(self):
        """Print formatted EDA report."""
        if self.profile is None:
            print("No data analyzed. Run analyze() first.")
            return

        print("=" * 60)
        print("EXPLORATORY DATA ANALYSIS REPORT")
        print("=" * 60)
        print()
        print(self.profile.summary())
        print()

        # Column details
        print("-" * 60)
        print("COLUMN DETAILS")
        print("-" * 60)

        for col, cp in self.profile.column_profiles.items():
            print(f"\n{col} ({cp.dtype})")
            print(f"  Non-null: {cp.non_null_count:,} | Null: {cp.null_count:,} ({cp.null_percent}%)")
            print(f"  Unique: {cp.unique_count:,} ({cp.unique_percent:.1f}%)")

            if cp.is_numeric and cp.mean is not None:
                print(f"  Range: {cp.min:,.2f} - {cp.max:,.2f}")
                print(f"  Mean: {cp.mean:,.2f} | Median: {cp.median:,.2f} | Std: {cp.std:,.2f}")

            if cp.top_values:
                print(f"  Top values: {cp.top_values[:5]}")

        # Correlations
        corr = self.get_correlations()
        if corr is not None and len(corr) > 1:
            print()
            print("-" * 60)
            print("CORRELATIONS (top pairs)")
            print("-" * 60)

            # Get top correlations (excluding self-correlation)
            corr_pairs = []
            for i in range(len(corr.columns)):
                for j in range(i + 1, len(corr.columns)):
                    corr_pairs.append((
                        corr.columns[i],
                        corr.columns[j],
                        corr.iloc[i, j]
                    ))

            corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            for c1, c2, val in corr_pairs[:5]:
                print(f"  {c1} <-> {c2}: {val:.3f}")

        # Suggestions
        suggestions = self.suggest_analysis()
        if suggestions:
            print()
            print("-" * 60)
            print("SUGGESTED ANALYSES")
            print("-" * 60)
            for i, s in enumerate(suggestions, 1):
                print(f"  {i}. {s}")

        print()
        print("=" * 60)


def run_eda(data: Union[str, Path, pd.DataFrame], print_report: bool = True) -> DataProfile:
    """
    Convenience function to run EDA.

    Args:
        data: Path to file or DataFrame
        print_report: Whether to print report (default True)

    Returns:
        DataProfile with analysis results
    """
    eda = EDA()
    profile = eda.analyze(data)

    if print_report:
        eda.print_report()

    return profile
