"""
Regression test for categorical_cols NameError bug in react_builder.py.

Bug: Line 631 (now 634 after fix) referenced categorical_cols which was only defined inside
the else block, causing NameError when column_mapping path was taken.

Fix: Define categorical_cols before the if/else block (line 598).

This test proves the fix works by exercising the column_mapping code path.
"""

import pytest
from pathlib import Path
from kie.export.react_builder import ReactDashboardBuilder
from kie.data.loader import DataSchema


def test_categorical_cols_bug_fixed_with_column_mapping(tmp_path):
    """
    Regression test: Verify categorical_cols NameError is fixed.

    This test exercises the if path (column_mapping provided) which previously
    caused NameError when reaching line 634 (state_col fallback logic).
    """
    # Create schema with categorical columns
    schema = DataSchema(
        columns=['Region', 'State', 'Revenue', 'Cost'],
        numeric_columns=['Revenue', 'Cost'],
        categorical_columns=['Region', 'State'],
        datetime_columns=[],
        row_count=100,
        column_count=4
    )

    # Initialize builder WITH column_mapping (this triggers the bug path)
    builder = ReactDashboardBuilder(
        project_name="Test Dashboard",
        client_name="Test Client",
        objective="Test objective",
        data_schema=schema,
        column_mapping={'revenue': 'Revenue', 'category': 'Region'}
    )

    # Create minimal data file for the dashboard
    data_path = tmp_path / "data.json"
    data_path.write_text('[{"Region":"North","State":"CA","Revenue":1000,"Cost":400}]')

    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # This should NOT crash with NameError: name 'categorical_cols' is not defined
    # The bug was on line 631 (now 634): state_col fallback tried to access categorical_cols
    try:
        builder._generate_dashboard_component(
            src_dir=src_dir,
            data_path=data_path
        )
        # If we got here, no crash occurred
        assert True
    except NameError as e:
        if 'categorical_cols' in str(e):
            pytest.fail(f"categorical_cols NameError not fixed: {e}")
        raise  # Re-raise if it's a different NameError


def test_categorical_cols_fallback_path_still_works(tmp_path):
    """
    Test that the fallback path (no column_mapping) still works correctly.
    """
    schema = DataSchema(
        columns=['Category', 'Value'],
        numeric_columns=['Value'],
        categorical_columns=['Category'],
        datetime_columns=[],
        row_count=50,
        column_count=2
    )

    # Initialize builder WITHOUT column_mapping (else branch)
    builder = ReactDashboardBuilder(
        project_name="Test Dashboard 2",
        client_name="Test Client 2",
        objective="Test objective 2",
        data_schema=schema,
        column_mapping=None
    )

    data_path = tmp_path / "data2.json"
    data_path.write_text('[{"Category":"A","Value":10}]')

    src_dir = tmp_path / "src2"
    src_dir.mkdir(parents=True, exist_ok=True)

    # This should work - uses the else branch where categorical_cols is explicitly defined
    builder._generate_dashboard_component(
        src_dir=src_dir,
        data_path=data_path
    )

    assert True
