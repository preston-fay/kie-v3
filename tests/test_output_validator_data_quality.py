"""
Tests for OutputValidator data quality checks.

Tests the data quality validation including:
- Null value detection (all-null columns, high null percentage)
- Duplicate row detection
- Suspicious values (all zeros, single unique value)
- Synthetic data detection (sequential IDs, round numbers, fake names)
- Calculation validation (negative percentages, extreme values, infinity/NaN)
"""

import pandas as pd
import pytest

from kie.validation.validators import (
    OutputValidator,
    ValidationCategory,
    ValidationLevel,
)


class TestDataQualityValidation:
    """Tests for _validate_data_quality method."""

    def test_all_null_column_critical(self):
        """Test detection of columns with all null values."""
        df = pd.DataFrame(
            {
                "valid_col": [1, 2, 3],
                "null_col": [None, None, None],
                "another_null": [pd.NA, pd.NA, pd.NA],
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have critical failure for null columns
        null_results = [
            r
            for r in results
            if r.category == ValidationCategory.DATA_QUALITY
            and "null values" in r.message.lower()
            and r.level == ValidationLevel.CRITICAL
        ]

        assert not passed, "Should fail with all-null columns"
        assert len(null_results) >= 1, "Should detect all-null columns"

    def test_high_null_percentage_warning(self):
        """Test detection of columns with >50% null values."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East", "West"],
                "revenue": [100, None, None, None],  # 75% null
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have warning for high null percentage
        null_pct_warnings = [
            r
            for r in results
            if r.category == ValidationCategory.DATA_QUALITY
            and "null values" in r.message.lower()
            and r.level == ValidationLevel.WARNING
        ]

        assert len(null_pct_warnings) >= 1, "Should warn about high null percentage"

    def test_duplicate_rows_warning(self):
        """Test detection of duplicate rows."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "North", "South"],
                "revenue": [100, 200, 100, 200],  # Exact duplicates
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have warning for duplicates
        dup_warnings = [
            r
            for r in results
            if r.category == ValidationCategory.DATA_QUALITY
            and "duplicate" in r.message.lower()
        ]

        assert len(dup_warnings) == 1, "Should detect duplicate rows"
        assert "2 duplicate" in dup_warnings[0].message

    def test_all_zeros_warning(self):
        """Test detection of columns with all zero values."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East"],
                "revenue": [0, 0, 0],  # All zeros
                "cost": [100, 200, 150],
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have warning for all-zero column
        zero_warnings = [
            r
            for r in results
            if r.category == ValidationCategory.DATA_QUALITY
            and "all zeros" in r.message.lower()
        ]

        assert len(zero_warnings) == 1, "Should detect all-zero column"
        assert "revenue" in zero_warnings[0].message

    def test_single_unique_value_warning(self):
        """Test detection of columns with only one unique value."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East"],
                "revenue": [100, 200, 300],
                "constant": [42, 42, 42],  # Only one unique value
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have warning for single unique value
        single_value_warnings = [
            r
            for r in results
            if r.category == ValidationCategory.DATA_QUALITY
            and "one unique value" in r.message.lower()
        ]

        assert len(single_value_warnings) == 1, "Should detect single unique value"
        assert "constant" in single_value_warnings[0].message

    def test_clean_data_passes(self):
        """Test that clean data passes all quality checks."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East", "West"],
                "revenue": [100, 200, 150, 180],
                "cost": [50, 100, 75, 90],
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have no data quality failures
        quality_failures = [
            r
            for r in results
            if r.category == ValidationCategory.DATA_QUALITY and not r.passed
        ]

        assert len(quality_failures) == 0, "Clean data should pass all checks"

    def test_empty_dataframe(self):
        """Test validation of empty DataFrame."""
        df = pd.DataFrame()

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Empty DataFrame should not crash, but may have no results
        # This is acceptable behavior


class TestSyntheticDataDetection:
    """Tests for _detect_synthetic_data method."""

    def test_sequential_ids_detected(self):
        """Test detection of sequential ID patterns."""
        df = pd.DataFrame(
            {
                "customer_id": [1, 2, 3, 4, 5],  # Sequential
                "revenue": [100, 200, 150, 180, 220],
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should detect sequential pattern
        synthetic_results = [
            r
            for r in results
            if r.category == ValidationCategory.SYNTHETIC_DATA
        ]

        assert len(synthetic_results) >= 1, "Should detect sequential IDs"
        assert not passed, "Should fail with synthetic data"
        assert any(
            "sequential" in r.message.lower() or "customer_id" in str(r.details)
            for r in synthetic_results
        ), "Should mention sequential values"

    def test_sequential_descending_detected(self):
        """Test detection of descending sequential patterns."""
        df = pd.DataFrame(
            {
                "order_num": [100, 99, 98, 97, 96],  # Descending sequential
                "revenue": [100, 200, 150, 180, 220],
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should detect sequential pattern
        synthetic_results = [
            r
            for r in results
            if r.category == ValidationCategory.SYNTHETIC_DATA
        ]

        assert len(synthetic_results) >= 1, "Should detect descending sequential"

    def test_round_thousands_detected(self):
        """Test detection of suspiciously round numbers."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East", "West", "Central", "Northwest"],
                "revenue": [1000, 2000, 3000, 4000, 5000, 6000],  # All round thousands
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should detect round numbers
        synthetic_results = [
            r
            for r in results
            if r.category == ValidationCategory.SYNTHETIC_DATA
        ]

        assert len(synthetic_results) >= 1, "Should detect round thousands"
        assert any(
            "round" in r.message.lower() or "round" in str(r.details)
            for r in synthetic_results
        )

    def test_fake_names_lorem_detected(self):
        """Test detection of Lorem Ipsum placeholder text."""
        df = pd.DataFrame(
            {
                "client_name": ["Lorem Corp", "Ipsum Inc", "Real Client"],
                "revenue": [100, 200, 300],
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should detect Lorem/Ipsum
        synthetic_results = [
            r
            for r in results
            if r.category == ValidationCategory.SYNTHETIC_DATA
        ]

        assert len(synthetic_results) >= 1, "Should detect Lorem/Ipsum"
        assert not passed, "Should fail with fake names"

    def test_fake_names_test_detected(self):
        """Test detection of 'Test' in data."""
        df = pd.DataFrame(
            {
                "company": ["Test Company", "Another Test", "Real Corp"],
                "revenue": [100, 200, 300],
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should detect "test"
        synthetic_results = [
            r
            for r in results
            if r.category == ValidationCategory.SYNTHETIC_DATA
        ]

        assert len(synthetic_results) >= 1, "Should detect 'test' keyword"

    def test_fake_names_sample_detected(self):
        """Test detection of 'Sample' in data."""
        df = pd.DataFrame(
            {
                "name": ["Sample Client", "Sample Data", "Real Client"],
                "value": [1, 2, 3],
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should detect "sample"
        synthetic_results = [
            r
            for r in results
            if r.category == ValidationCategory.SYNTHETIC_DATA
        ]

        assert len(synthetic_results) >= 1, "Should detect 'sample' keyword"

    def test_fake_names_acme_detected(self):
        """Test detection of 'Acme' (classic fake company name)."""
        df = pd.DataFrame(
            {
                "customer": ["Acme Corp", "Acme Industries", "Real Business"],
                "sales": [100, 200, 300],
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should detect "acme"
        synthetic_results = [
            r
            for r in results
            if r.category == ValidationCategory.SYNTHETIC_DATA
        ]

        assert len(synthetic_results) >= 1, "Should detect 'Acme' keyword"

    def test_real_data_passes(self):
        """Test that real-looking data passes synthetic checks."""
        df = pd.DataFrame(
            {
                "company": ["Microsoft", "Apple", "Google", "Amazon"],
                "revenue": [12345, 23456, 34567, 45678],  # Not perfectly round
                "employee_id": [1001, 1003, 1005, 1009],  # Not sequential
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have no synthetic data failures
        synthetic_results = [
            r
            for r in results
            if r.category == ValidationCategory.SYNTHETIC_DATA
        ]

        assert len(synthetic_results) == 0, "Real-looking data should pass"

    def test_case_insensitive_fake_detection(self):
        """Test that fake name detection is case-insensitive."""
        df = pd.DataFrame(
            {
                "name": ["LOREM Company", "Test Corp", "dummy data"],
                "value": [1, 2, 3],
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should detect regardless of case
        synthetic_results = [
            r
            for r in results
            if r.category == ValidationCategory.SYNTHETIC_DATA
        ]

        assert len(synthetic_results) >= 1, "Should detect fake names case-insensitively"


class TestCalculationValidation:
    """Tests for _validate_calculations method."""

    def test_negative_percentages_critical(self):
        """Test detection of negative percentage values."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East"],
                "growth_pct": [0.10, -0.05, 0.15],  # Negative percentage
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have critical failure for negative percentages
        calc_failures = [
            r
            for r in results
            if r.category == ValidationCategory.CALCULATION
            and "negative percentages" in r.message.lower()
        ]

        assert not passed, "Should fail with negative percentages"
        assert len(calc_failures) >= 1, "Should detect negative percentages"

    def test_extreme_percentages_warning(self):
        """Test detection of percentages over 150%."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East"],
                "margin_percent": [0.10, 2.5, 0.15],  # 250% is extreme
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have warning for extreme percentages
        calc_warnings = [
            r
            for r in results
            if r.category == ValidationCategory.CALCULATION
            and "over 150%" in r.message.lower()
        ]

        assert len(calc_warnings) >= 1, "Should warn about extreme percentages"

    def test_extremely_large_values_warning(self):
        """Test detection of extremely large values (>1e15)."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East"],
                "revenue": [100, 1e16, 300],  # Extremely large value
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have warning for extremely large values
        calc_warnings = [
            r
            for r in results
            if r.category == ValidationCategory.CALCULATION
            and "extremely large" in r.message.lower()
        ]

        assert len(calc_warnings) >= 1, "Should warn about extremely large values"

    def test_infinity_values_critical(self):
        """Test detection of infinite values."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East"],
                "ratio": [1.5, float("inf"), 2.0],  # Infinity value
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have critical failure for infinity
        calc_failures = [
            r
            for r in results
            if r.category == ValidationCategory.CALCULATION
            and "infinite" in r.message.lower()
        ]

        assert not passed, "Should fail with infinite values"
        assert len(calc_failures) >= 1, "Should detect infinite values"

    def test_negative_infinity_critical(self):
        """Test detection of negative infinite values."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East"],
                "profit": [100, float("-inf"), 300],  # Negative infinity
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have critical failure for negative infinity
        calc_failures = [
            r
            for r in results
            if r.category == ValidationCategory.CALCULATION
            and "infinite" in r.message.lower()
        ]

        assert not passed, "Should fail with negative infinite values"
        assert len(calc_failures) >= 1, "Should detect negative infinite values"

    def test_valid_percentages_pass(self):
        """Test that valid percentage values pass."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East", "West"],
                "growth_pct": [0.10, 0.15, 0.05, 0.20],  # Valid percentages
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have no calculation failures
        calc_failures = [
            r
            for r in results
            if r.category == ValidationCategory.CALCULATION and not r.passed
        ]

        assert len(calc_failures) == 0, "Valid percentages should pass"

    def test_valid_large_values_pass(self):
        """Test that large but not extreme values pass."""
        df = pd.DataFrame(
            {
                "region": ["North", "South", "East"],
                "revenue": [1e12, 2e12, 3e12],  # Large but valid (trillions)
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should have no calculation failures
        calc_failures = [
            r
            for r in results
            if r.category == ValidationCategory.CALCULATION and not r.passed
        ]

        assert len(calc_failures) == 0, "Large but valid values should pass"

    def test_percentage_column_name_detection(self):
        """Test that 'percent' and 'pct' column names trigger percentage validation."""
        df = pd.DataFrame(
            {
                "margin_pct": [0.1, 0.2, 0.3],  # 'pct' in name
                "growth_percent": [0.05, 0.10, 0.15],  # 'percent' in name
                "value": [100, 200, 300],  # Not a percentage
            }
        )

        validator = OutputValidator()
        # Should not fail, just testing name detection works
        validator.validate_all(data=df)

        # No assertion - just ensuring no crashes


class TestIntegrationScenarios:
    """Integration tests combining multiple validation types."""

    def test_multiple_quality_issues(self):
        """Test data with multiple quality issues."""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4],  # Sequential (synthetic)
                "null_col": [None, None, None, None],  # All null (quality)
                "zero_col": [0, 0, 0, 0],  # All zeros (quality)
                "growth_pct": [-0.1, 0.2, 0.3, 0.4],  # Negative % (calculation)
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)

        # Should fail overall
        assert not passed, "Should fail with multiple issues"

        # Should have multiple categories of failures
        categories = {r.category for r in results if not r.passed}
        assert len(categories) >= 2, "Should detect multiple issue categories"

    def test_validation_summary_accuracy(self):
        """Test that validation summary accurately reflects results."""
        df = pd.DataFrame(
            {
                "region": ["Test Corp", "Sample Inc"],  # Synthetic
                "revenue": [0, 0],  # All zeros
            }
        )

        validator = OutputValidator()
        passed, results = validator.validate_all(data=df)
        summary = validator.get_validation_summary()

        # Summary should match results
        assert summary["total_checks"] == len(results)
        assert summary["failed"] > 0
        assert not summary["overall_pass"]

    def test_no_data_provided(self):
        """Test validation when no data is provided."""
        validator = OutputValidator()
        passed, results = validator.validate_all()

        # Should not crash, should pass (no checks to run)
        assert passed, "Should pass when no data provided"
        assert len(results) == 0, "Should have no results when no input"

    def test_strict_mode_with_warnings(self):
        """Test that strict mode treats warnings as failures."""
        from kie.validation.validators import validate_output

        df = pd.DataFrame(
            {
                "region": ["North", "South", "East"],
                "constant": [42, 42, 42],  # Only one unique value (WARNING)
            }
        )

        # Non-strict mode
        passed_normal, results, summary = validate_output(data=df, strict=False)

        # Strict mode
        passed_strict, _, _ = validate_output(data=df, strict=True)

        # In strict mode, warnings should block
        if summary["by_level"]["warning"] > 0:
            assert passed_normal, "Non-strict should pass with only warnings"
            assert not passed_strict, "Strict mode should fail with warnings"
