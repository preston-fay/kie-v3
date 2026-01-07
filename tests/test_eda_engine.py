"""
Tests for EDA Engine (Exploratory Data Analysis)

Tests profiling, distribution analysis, correlation detection.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from kie.data.eda import EDA, run_eda
from kie.data.profile import DataProfile, ColumnProfile


@pytest.fixture
def sample_numeric_data():
    """Sample data with numeric columns."""
    return pd.DataFrame({
        'revenue': [100000, 200000, 150000, 300000, 250000],
        'cost': [60000, 120000, 90000, 180000, 150000],
        'profit': [40000, 80000, 60000, 120000, 100000],
        'year': [2020, 2021, 2022, 2023, 2024]
    })


@pytest.fixture
def sample_mixed_data():
    """Sample data with mixed column types."""
    return pd.DataFrame({
        'region': ['North', 'South', 'East', 'West', 'North'],
        'revenue': [100000, 200000, 150000, 300000, 250000],
        'active': [True, False, True, True, False],
        'date': pd.date_range('2024-01-01', periods=5, freq='ME')
    })


@pytest.fixture
def data_with_nulls():
    """Data with missing values."""
    return pd.DataFrame({
        'col_a': [1, 2, None, 4, None],
        'col_b': [None, None, None, 10, 20],  # 60% nulls
        'col_c': ['x', 'y', 'z', 'x', 'y']
    })


@pytest.fixture
def data_with_duplicates():
    """Data with duplicate rows."""
    return pd.DataFrame({
        'id': [1, 2, 3, 1, 2],  # duplicates
        'value': [10, 20, 30, 10, 20]
    })


@pytest.fixture
def high_cardinality_data():
    """Data with high cardinality categorical columns."""
    return pd.DataFrame({
        'unique_id': [f'ID_{i}' for i in range(100)],  # 100% unique
        'value': range(100)
    })


@pytest.fixture
def constant_column_data():
    """Data with constant columns."""
    return pd.DataFrame({
        'constant': ['A'] * 10,
        'variable': range(10)
    })


class TestEDABasics:
    """Test basic EDA initialization and analysis."""

    def test_eda_initialization(self):
        """Test EDA engine initialization."""
        eda = EDA()
        assert eda.high_null_threshold == 0.3
        assert eda.high_cardinality_threshold == 0.9
        assert eda.df is None
        assert eda.profile is None

    def test_eda_custom_thresholds(self):
        """Test EDA with custom thresholds."""
        eda = EDA(high_null_threshold=0.5, high_cardinality_threshold=0.8)
        assert eda.high_null_threshold == 0.5
        assert eda.high_cardinality_threshold == 0.8

    def test_analyze_dataframe(self, sample_numeric_data):
        """Test analyzing a DataFrame directly."""
        eda = EDA()
        profile = eda.analyze(sample_numeric_data)

        assert isinstance(profile, DataProfile)
        assert profile.rows == 5
        assert profile.columns == 4
        assert profile.memory_mb > 0

    def test_analyze_csv_file(self, sample_numeric_data):
        """Test analyzing a CSV file."""
        # Write temp CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_numeric_data.to_csv(f.name, index=False)
            temp_path = f.name

        try:
            eda = EDA()
            profile = eda.analyze(temp_path)

            assert profile.rows == 5
            assert profile.columns == 4
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_analyze_empty_dataframe(self):
        """Test analyzing empty DataFrame."""
        eda = EDA()
        empty_df = pd.DataFrame()
        profile = eda.analyze(empty_df)

        assert profile.rows == 0
        assert profile.columns == 0


class TestColumnProfiling:
    """Test column-level profiling."""

    def test_numeric_column_profiling(self, sample_numeric_data):
        """Test profiling of numeric columns."""
        eda = EDA()
        profile = eda.analyze(sample_numeric_data)

        # Check numeric columns detected
        assert 'revenue' in profile.numeric_columns
        assert 'cost' in profile.numeric_columns
        assert 'profit' in profile.numeric_columns
        assert 'year' in profile.numeric_columns

        # Check revenue column stats
        revenue_profile = profile.column_profiles['revenue']
        assert revenue_profile.dtype == 'int64'
        assert revenue_profile.mean == 200000.0
        assert revenue_profile.min == 100000.0
        assert revenue_profile.max == 300000.0
        assert revenue_profile.median == 200000.0
        assert revenue_profile.std is not None

    def test_categorical_column_profiling(self, sample_mixed_data):
        """Test profiling of categorical columns."""
        eda = EDA()
        profile = eda.analyze(sample_mixed_data)

        # Check categorical column detected
        assert 'region' in profile.categorical_columns

        # Check region column stats
        region_profile = profile.column_profiles['region']
        assert region_profile.unique_count == 4
        assert region_profile.top_values is not None
        assert 'North' in region_profile.top_values
        assert region_profile.value_counts is not None

    def test_datetime_column_profiling(self, sample_mixed_data):
        """Test profiling of datetime columns."""
        eda = EDA()
        profile = eda.analyze(sample_mixed_data)

        # Check datetime column detected
        assert 'date' in profile.datetime_columns

    def test_boolean_column_profiling(self, sample_mixed_data):
        """Test profiling of boolean columns."""
        eda = EDA()
        profile = eda.analyze(sample_mixed_data)

        # Boolean columns treated as categorical
        assert 'active' in profile.categorical_columns
        active_profile = profile.column_profiles['active']
        assert active_profile.unique_count == 2
        assert active_profile.top_values is not None

    def test_null_statistics(self, data_with_nulls):
        """Test null value statistics."""
        eda = EDA()
        profile = eda.analyze(data_with_nulls)

        # Check col_a (40% nulls)
        col_a_profile = profile.column_profiles['col_a']
        assert col_a_profile.null_count == 2
        assert col_a_profile.null_percent == 40.0
        assert col_a_profile.non_null_count == 3

        # Check col_b (60% nulls) - should be flagged as high null
        col_b_profile = profile.column_profiles['col_b']
        assert col_b_profile.null_count == 3
        assert col_b_profile.null_percent == 60.0
        assert 'col_b' in profile.high_null_columns

    def test_unique_value_statistics(self, sample_numeric_data):
        """Test unique value counting."""
        eda = EDA()
        profile = eda.analyze(sample_numeric_data)

        revenue_profile = profile.column_profiles['revenue']
        assert revenue_profile.unique_count == 5  # All values unique
        assert revenue_profile.unique_percent == 100.0


class TestDataQuality:
    """Test data quality analysis."""

    def test_overall_null_percentage(self, data_with_nulls):
        """Test overall null percentage calculation."""
        eda = EDA()
        profile = eda.analyze(data_with_nulls)

        # 5 nulls out of 15 total cells = 33.33%
        assert profile.total_nulls == 5
        assert 33.0 < profile.null_percent < 34.0

    def test_duplicate_detection(self, data_with_duplicates):
        """Test duplicate row detection."""
        eda = EDA()
        profile = eda.analyze(data_with_duplicates)

        # 2 duplicate rows out of 5 = 40%
        assert profile.duplicate_rows == 2
        assert profile.duplicate_percent == 40.0

    def test_high_null_column_detection(self, data_with_nulls):
        """Test detection of high null columns."""
        eda = EDA(high_null_threshold=0.5)  # 50% threshold
        profile = eda.analyze(data_with_nulls)

        # col_b has 60% nulls, should be flagged
        assert 'col_b' in profile.high_null_columns
        # col_a has 40% nulls, should not be flagged
        assert 'col_a' not in profile.high_null_columns

    def test_constant_column_detection(self, constant_column_data):
        """Test detection of constant columns."""
        eda = EDA()
        profile = eda.analyze(constant_column_data)

        assert 'constant' in profile.constant_columns
        assert 'variable' not in profile.constant_columns

    def test_high_cardinality_detection(self, high_cardinality_data):
        """Test detection of high cardinality columns."""
        eda = EDA(high_cardinality_threshold=0.9)
        profile = eda.analyze(high_cardinality_data)

        # unique_id is 100% unique, should be flagged
        assert 'unique_id' in profile.high_cardinality_columns


class TestCorrelationAnalysis:
    """Test correlation analysis."""

    def test_correlation_matrix_pearson(self, sample_numeric_data):
        """Test Pearson correlation calculation."""
        eda = EDA()
        eda.analyze(sample_numeric_data)
        corr = eda.get_correlations(method='pearson')

        assert corr is not None
        assert corr.shape == (4, 4)  # 4 numeric columns
        assert 'revenue' in corr.columns
        assert 'cost' in corr.columns

        # Check perfect correlation on diagonal
        assert corr.loc['revenue', 'revenue'] == 1.0

    def test_correlation_matrix_spearman(self, sample_numeric_data):
        """Test Spearman correlation calculation."""
        eda = EDA()
        eda.analyze(sample_numeric_data)
        corr = eda.get_correlations(method='spearman')

        assert corr is not None
        assert corr.shape == (4, 4)

    def test_correlation_matrix_kendall(self, sample_numeric_data):
        """Test Kendall correlation calculation."""
        eda = EDA()
        eda.analyze(sample_numeric_data)
        corr = eda.get_correlations(method='kendall')

        assert corr is not None
        assert corr.shape == (4, 4)

    def test_correlation_insufficient_numeric_columns(self, sample_mixed_data):
        """Test correlation with only one numeric column."""
        # Remove all but one numeric column
        df = sample_mixed_data[['region', 'revenue']].copy()

        eda = EDA()
        eda.analyze(df)
        corr = eda.get_correlations()

        # Should return None (need at least 2 numeric columns)
        assert corr is None

    def test_correlation_no_analysis_run(self):
        """Test correlation before running analysis."""
        eda = EDA()
        corr = eda.get_correlations()
        assert corr is None


class TestSummaryStatistics:
    """Test summary statistics."""

    def test_get_summary_stats(self, sample_numeric_data):
        """Test getting summary statistics."""
        eda = EDA()
        eda.analyze(sample_numeric_data)
        stats = eda.get_summary_stats()

        assert isinstance(stats, pd.DataFrame)
        assert 'revenue' in stats.index
        assert 'mean' in stats.columns or stats.shape[1] > 0

    def test_get_summary_stats_no_data(self):
        """Test getting summary stats with no data."""
        eda = EDA()
        stats = eda.get_summary_stats()
        assert isinstance(stats, pd.DataFrame)
        assert stats.empty


class TestAnalysisSuggestions:
    """Test intelligent analysis suggestions."""

    def test_suggest_correlation_analysis(self, sample_numeric_data):
        """Test suggestion for correlation analysis."""
        eda = EDA()
        eda.analyze(sample_numeric_data)
        suggestions = eda.suggest_analysis()

        # Should suggest correlation with 4 numeric columns
        assert any('Correlation analysis' in s for s in suggestions)
        assert any('4 numeric columns' in s for s in suggestions)

    def test_suggest_groupby_analysis(self, sample_mixed_data):
        """Test suggestion for group-by analysis."""
        eda = EDA()
        eda.analyze(sample_mixed_data)
        suggestions = eda.suggest_analysis()

        # Should suggest group-by with categorical + numeric
        assert any('Group-by analysis' in s for s in suggestions)

    def test_suggest_duplicate_investigation(self, data_with_duplicates):
        """Test suggestion to investigate duplicates."""
        eda = EDA()
        eda.analyze(data_with_duplicates)
        suggestions = eda.suggest_analysis()

        # Should suggest investigating duplicates
        assert any('duplicate' in s.lower() for s in suggestions)

    def test_suggest_missing_data_handling(self, data_with_nulls):
        """Test suggestion to handle missing data."""
        eda = EDA()
        eda.analyze(data_with_nulls)
        suggestions = eda.suggest_analysis()

        # Should suggest addressing missing data
        assert any('missing data' in s.lower() or 'col_b' in s for s in suggestions)

    def test_suggest_distribution_analysis(self, sample_mixed_data):
        """Test suggestion for distribution analysis."""
        eda = EDA()
        eda.analyze(sample_mixed_data)
        suggestions = eda.suggest_analysis()

        # Should suggest distribution for categorical columns
        assert any('Distribution analysis' in s for s in suggestions)

    def test_suggest_no_analysis_run(self):
        """Test suggestions before running analysis."""
        eda = EDA()
        suggestions = eda.suggest_analysis()
        assert suggestions == ["Run analyze() first"]


class TestProfileProperties:
    """Test ColumnProfile and DataProfile properties."""

    def test_column_profile_is_numeric(self):
        """Test ColumnProfile.is_numeric property."""
        profile = ColumnProfile(
            name='test',
            dtype='int64',
            non_null_count=10,
            null_count=0,
            null_percent=0.0,
            unique_count=10,
            unique_percent=100.0
        )
        assert profile.is_numeric is True

    def test_column_profile_is_categorical(self):
        """Test ColumnProfile.is_categorical property."""
        profile = ColumnProfile(
            name='test',
            dtype='object',
            non_null_count=10,
            null_count=0,
            null_percent=0.0,
            unique_count=5,
            unique_percent=50.0
        )
        assert profile.is_categorical is True

    def test_data_profile_summary(self, sample_numeric_data):
        """Test DataProfile.summary() output."""
        eda = EDA()
        profile = eda.analyze(sample_numeric_data)
        summary = profile.summary()

        assert '5 rows' in summary
        assert '4 columns' in summary
        assert 'Numeric: 4' in summary
        assert 'Missing values' in summary
        assert 'Duplicate rows' in summary

    def test_data_profile_to_dict(self, sample_numeric_data):
        """Test DataProfile.to_dict() conversion."""
        eda = EDA()
        profile = eda.analyze(sample_numeric_data)
        profile_dict = profile.to_dict()

        assert 'shape' in profile_dict
        assert profile_dict['shape']['rows'] == 5
        assert profile_dict['shape']['columns'] == 4
        assert 'quality' in profile_dict
        assert 'issues' in profile_dict


class TestConvenienceFunction:
    """Test run_eda() convenience function."""

    def test_run_eda_with_report(self, sample_numeric_data, capsys):
        """Test run_eda with report printing."""
        profile = run_eda(sample_numeric_data, print_report=True)

        assert isinstance(profile, DataProfile)
        assert profile.rows == 5

        # Check that report was printed
        captured = capsys.readouterr()
        assert 'EXPLORATORY DATA ANALYSIS REPORT' in captured.out

    def test_run_eda_without_report(self, sample_numeric_data, capsys):
        """Test run_eda without report printing."""
        profile = run_eda(sample_numeric_data, print_report=False)

        assert isinstance(profile, DataProfile)

        # Check that report was NOT printed
        captured = capsys.readouterr()
        assert 'EXPLORATORY DATA ANALYSIS REPORT' not in captured.out


class TestPrintReport:
    """Test formatted report printing."""

    def test_print_report_complete(self, sample_numeric_data, capsys):
        """Test printing complete EDA report."""
        eda = EDA()
        eda.analyze(sample_numeric_data)
        eda.print_report()

        captured = capsys.readouterr()
        output = captured.out

        # Check sections present
        assert 'EXPLORATORY DATA ANALYSIS REPORT' in output
        assert 'COLUMN DETAILS' in output
        assert 'CORRELATIONS' in output
        assert 'SUGGESTED ANALYSES' in output

        # Check column details present
        assert 'revenue' in output
        assert 'cost' in output

    def test_print_report_no_analysis(self, capsys):
        """Test printing report before running analysis."""
        eda = EDA()
        eda.print_report()

        captured = capsys.readouterr()
        assert 'No data analyzed' in captured.out

    def test_print_report_with_nulls(self, data_with_nulls, capsys):
        """Test report includes null information."""
        eda = EDA()
        eda.analyze(data_with_nulls)
        eda.print_report()

        captured = capsys.readouterr()
        output = captured.out

        # Should show high null columns
        assert 'High null columns' in output or 'col_b' in output


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_all_null_column(self):
        """Test column with all null values."""
        df = pd.DataFrame({
            'all_null': [None, None, None, None],
            'some_data': [1, 2, 3, 4]
        })

        eda = EDA()
        profile = eda.analyze(df)

        all_null_profile = profile.column_profiles['all_null']
        assert all_null_profile.null_percent == 100.0
        assert all_null_profile.mean is None  # Can't compute stats on all nulls

    def test_single_value_column(self):
        """Test column with single repeated value."""
        df = pd.DataFrame({
            'constant': [5, 5, 5, 5, 5],
            'variable': [1, 2, 3, 4, 5]
        })

        eda = EDA()
        profile = eda.analyze(df)

        # Should be flagged as constant
        assert 'constant' in profile.constant_columns
        constant_profile = profile.column_profiles['constant']
        assert constant_profile.unique_count == 1
        assert constant_profile.std == 0.0

    def test_single_row_dataframe(self):
        """Test DataFrame with only one row."""
        df = pd.DataFrame({
            'col_a': [1],
            'col_b': ['x']
        })

        eda = EDA()
        profile = eda.analyze(df)

        assert profile.rows == 1
        assert profile.columns == 2
        assert profile.duplicate_rows == 0

    def test_large_cardinality_value_counts(self):
        """Test value_counts limited to top 10."""
        df = pd.DataFrame({
            'many_values': [f'value_{i}' for i in range(100)]
        })

        eda = EDA()
        profile = eda.analyze(df)

        # Should only store top 10
        cat_profile = profile.column_profiles['many_values']
        assert len(cat_profile.value_counts) <= 10
        assert len(cat_profile.top_values) <= 5
