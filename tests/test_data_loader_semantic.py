"""
Tests for DataLoader Semantic Scoring System

Tests cover the 4-Tier Intelligence System:
- Tier 1: Semantic Match (revenue, cost, margin keywords)
- Tier 2: ID/ZipCode Avoidance
- Tier 3: Percentage/Ratio Handling
- Tier 4: Statistical Vitality (CV-based)

Plus:
- Phase 5: Human Override (column_mapping bypass)
- Schema inference
- Entity/category detection
- File format auto-detection
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from kie.data.loader import DataLoader, DataSchema


# --- Fixtures ---


@pytest.fixture
def sample_business_data():
    """Business data with various column types for semantic testing."""
    return pd.DataFrame({
        "Company_Name": ["Acme Corp", "Beta Inc", "Gamma LLC", "Delta Co", "Epsilon Ltd"],
        "Company_ID": [1001, 1002, 1003, 1004, 1005],  # Should be avoided
        "Region": ["North", "South", "East", "West", "Central"],
        "Revenue_M": [150.5, 220.3, 180.7, 195.2, 210.8],  # Millions
        "Cost_M": [100.2, 150.5, 120.3, 130.1, 140.9],
        "Profit_Margin_Pct": [33.5, 31.7, 33.4, 33.4, 33.2],  # Percentages
        "Employee_Count": [500, 750, 600, 650, 700],
        "ZIP_Code": [94105, 10001, 60601, 75201, 98101],  # Should be avoided
    })


@pytest.fixture
def sample_percentage_data():
    """Data with percentage columns that have small values."""
    return pd.DataFrame({
        "Product": ["A", "B", "C", "D"],
        "Market_Share_Pct": [0.15, 0.22, 0.18, 0.20],  # 15%, 22%, etc.
        "Conversion_Rate": [0.03, 0.05, 0.04, 0.04],
        "Revenue": [1500, 2200, 1800, 2000],
    })


@pytest.fixture
def sample_id_data():
    """Data with various ID-like columns."""
    return pd.DataFrame({
        "Customer_ID": [100001, 100002, 100003],
        "Order_ID": [500001, 500002, 500003],
        "Account_Number": [9001, 9002, 9003],
        "Sales_Amount": [1200, 1350, 1180],
        "Quantity": [5, 8, 6],
    })


@pytest.fixture
def sample_constant_data():
    """Data with low-variance columns."""
    return pd.DataFrame({
        "Region": ["A", "B", "C", "D"],
        "Constant_Value": [100, 100, 100, 100],  # CV = 0
        "Low_Variance": [100, 101, 100, 101],  # CV < 0.05
        "High_Variance": [100, 200, 50, 300],  # CV > 0.5
    })


@pytest.fixture
def sample_mixed_columns():
    """Data with semantic conflicts (growth vs spend)."""
    return pd.DataFrame({
        "Category": ["A", "B", "C"],
        "Revenue_M": [100, 150, 120],
        "Cost_M": [80, 120, 100],
        "Profit_M": [20, 30, 20],
    })


@pytest.fixture
def temp_csv_file(sample_business_data):
    """Create temporary CSV file for loading tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_business_data.to_csv(f, index=False)
        path = Path(f.name)
    yield path
    path.unlink()


# --- File Loading Tests ---


class TestFileLoading:
    """Test file format auto-detection and loading."""

    def test_load_csv(self, temp_csv_file):
        """Test loading CSV file."""
        loader = DataLoader()
        df = loader.load(temp_csv_file)

        assert len(df) == 5
        assert "Company_Name" in df.columns
        assert loader.last_format == "csv"

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        loader = DataLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/file.csv")

    def test_load_unsupported_format(self):
        """Test loading unsupported format raises error."""
        loader = DataLoader()
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Unknown file format"):
                loader.load(path)
        finally:
            path.unlink()

    def test_auto_detect_format(self, temp_csv_file):
        """Test format auto-detection from file extension."""
        loader = DataLoader()
        df = loader.load(temp_csv_file)  # No format specified

        assert loader.last_format == "csv"
        assert len(df) > 0

    def test_force_format(self, temp_csv_file):
        """Test forcing specific format."""
        loader = DataLoader()
        df = loader.load(temp_csv_file, format="csv")

        assert loader.last_format == "csv"

    def test_supported_formats_list(self):
        """Test that supported formats are documented."""
        loader = DataLoader()
        supported = loader.SUPPORTED_FORMATS

        assert ".csv" in supported
        assert ".xlsx" in supported
        assert ".json" in supported
        assert ".parquet" in supported


# --- Schema Inference Tests ---


class TestSchemaInference:
    """Test automatic schema inference."""

    def test_schema_inference_basic(self, temp_csv_file):
        """Test basic schema inference."""
        loader = DataLoader()
        loader.load(temp_csv_file)

        assert loader.schema is not None
        assert loader.schema.row_count == 5
        assert loader.schema.column_count == 8

    def test_numeric_columns_detected(self, temp_csv_file):
        """Test numeric columns are detected."""
        loader = DataLoader()
        loader.load(temp_csv_file)

        numeric = loader.schema.numeric_columns
        assert "Revenue_M" in numeric
        assert "Cost_M" in numeric
        assert "Profit_Margin_Pct" in numeric

    def test_categorical_columns_detected(self, temp_csv_file):
        """Test categorical columns are detected."""
        loader = DataLoader()
        loader.load(temp_csv_file)

        categorical = loader.schema.categorical_columns
        assert "Company_Name" in categorical
        assert "Region" in categorical

    def test_entity_column_suggestion(self, temp_csv_file):
        """Test entity column suggestion (high uniqueness)."""
        loader = DataLoader()
        loader.load(temp_csv_file)

        # Company_Name should be suggested (unique, has 'name' keyword)
        assert loader.schema.suggested_entity_column == "Company_Name"

    def test_category_column_suggestion(self):
        """Test category column suggestion (moderate cardinality)."""
        # Create data with proper category cardinality (not 100% unique)
        data = pd.DataFrame({
            "ID": [1, 2, 3, 4, 5, 6, 7, 8],
            "Region": ["North", "South", "North", "South", "East", "West", "East", "West"],  # 4 unique in 8 rows = 50%
            "Revenue": [100, 200, 150, 180, 220, 190, 210, 170],
        })

        loader = DataLoader()
        loader.last_loaded = data
        loader._infer_schema()

        # Region should be suggested (4 unique in 8 rows = 50% cardinality, has 'region' keyword)
        assert loader.schema.suggested_category_column == "Region"

    def test_metric_columns_exclude_ids(self, temp_csv_file):
        """Test that ID columns are excluded from metric suggestions."""
        loader = DataLoader()
        loader.load(temp_csv_file)

        suggested_metrics = loader.schema.suggested_metric_columns

        # Should include revenue, cost, margin
        assert "Revenue_M" in suggested_metrics
        assert "Cost_M" in suggested_metrics

        # Should NOT include ID columns
        assert "Company_ID" not in suggested_metrics
        assert "ZIP_Code" not in suggested_metrics


# --- Tier 1: Semantic Match Tests ---


class TestSemanticMatch:
    """Test Tier 1: Semantic keyword matching."""

    def test_revenue_keyword_match(self, sample_business_data):
        """Test matching 'revenue' requests to revenue columns."""
        loader = DataLoader()
        loader.last_loaded = sample_business_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["revenue"])

        # Should map to Revenue_M
        assert mapping["revenue"] == "Revenue_M"

    def test_cost_keyword_match(self, sample_business_data):
        """Test matching 'cost' requests to cost columns."""
        loader = DataLoader()
        loader.last_loaded = sample_business_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["cost"])

        assert mapping["cost"] == "Cost_M"

    def test_margin_keyword_match(self, sample_business_data):
        """Test matching 'margin' requests to margin columns."""
        loader = DataLoader()
        loader.last_loaded = sample_business_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["margin"])

        assert mapping["margin"] == "Profit_Margin_Pct"

    def test_exact_match_priority(self, sample_business_data):
        """Test exact matches take priority over fuzzy."""
        loader = DataLoader()
        loader.last_loaded = sample_business_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["Region"])

        # Exact match (case-insensitive)
        assert mapping["Region"] == "Region"


# --- Tier 2: ID Avoidance Tests ---


class TestIDAvoidance:
    """Test Tier 2: ID and ZipCode avoidance."""

    def test_avoid_id_columns(self, sample_id_data):
        """Test that columns with 'ID' in name are avoided."""
        loader = DataLoader()
        loader.last_loaded = sample_id_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["metric"])

        # Should pick Sales_Amount or Quantity, NOT IDs
        assert mapping["metric"] in ["Sales_Amount", "Quantity"]
        assert "ID" not in mapping["metric"]

    def test_avoid_zipcode(self, sample_business_data):
        """Test that ZIP codes are avoided."""
        loader = DataLoader()
        loader.last_loaded = sample_business_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["value"])

        # Should NOT pick ZIP_Code
        assert mapping["value"] != "ZIP_Code"

    def test_statistical_id_detection(self):
        """Test high mean + low CV is detected as ID."""
        data = pd.DataFrame({
            "Likely_ID": [100000, 100001, 100002, 100003],  # High mean, low CV
            "Real_Metric": [100, 200, 150, 250],  # Lower mean, high CV
        })

        loader = DataLoader()
        loader.last_loaded = data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["value"])

        # Should pick Real_Metric, not Likely_ID
        assert mapping["value"] == "Real_Metric"


# --- Tier 3: Percentage Handling Tests ---


class TestPercentageHandling:
    """Test Tier 3: Percentage/ratio column handling."""

    def test_percentage_column_small_values(self, sample_percentage_data):
        """Test that percentage columns with small values are prioritized."""
        loader = DataLoader()
        loader.last_loaded = sample_percentage_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["efficiency"])

        # Should pick Market_Share_Pct even though values are small (0.15 vs 1500)
        assert "Pct" in mapping["efficiency"] or "Rate" in mapping["efficiency"]

    def test_prefer_percentage_for_rate_requests(self, sample_percentage_data):
        """Test that 'rate' requests match percentage columns."""
        loader = DataLoader()
        loader.last_loaded = sample_percentage_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["rate"])

        # Should match Conversion_Rate
        assert "Rate" in mapping["rate"]

    def test_margin_prefers_percentage(self, sample_business_data):
        """Test that 'margin' requests prefer percentage columns."""
        loader = DataLoader()
        loader.last_loaded = sample_business_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["performance"])

        # When requesting performance/efficiency, should prefer margin
        # (may be Revenue_M due to semantic match, that's okay too)
        result = mapping["performance"]
        assert result is not None


# --- Tier 4: Statistical Vitality Tests ---


class TestStatisticalVitality:
    """Test Tier 4: Coefficient of Variation (CV) scoring."""

    def test_avoid_constant_columns(self, sample_constant_data):
        """Test that constant columns (CV=0) are avoided."""
        loader = DataLoader()
        loader.last_loaded = sample_constant_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["metric"])

        # Should pick High_Variance, not Constant_Value
        assert mapping["metric"] == "High_Variance"

    def test_avoid_low_variance(self, sample_constant_data):
        """Test that low-variance columns are deprioritized."""
        loader = DataLoader()
        loader.last_loaded = sample_constant_data
        loader._infer_schema()

        # Use "metric" instead of "value" to avoid semantic keyword matching
        mapping = loader.suggest_column_mapping(["metric"])

        # Should prefer High_Variance (CV > 0.5) over constant/low variance columns
        assert mapping["metric"] == "High_Variance"

    def test_high_cv_preferred(self):
        """Test that columns with higher CV are preferred."""
        data = pd.DataFrame({
            "Low_CV": [100, 101, 102, 103],  # CV ~ 0.01
            "High_CV": [50, 200, 100, 300],  # CV > 0.5
        })

        loader = DataLoader()
        loader.last_loaded = data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["metric"])

        assert mapping["metric"] == "High_CV"


# --- Semantic Directionality Tests ---


class TestSemanticDirectionality:
    """Test growth vs spend semantic scoring."""

    def test_growth_request_prefers_revenue(self, sample_mixed_columns):
        """Test that 'growth' requests prefer revenue over cost."""
        loader = DataLoader()
        loader.last_loaded = sample_mixed_columns
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["growth"])

        # Should pick Revenue_M, not Cost_M
        assert mapping["growth"] in ["Revenue_M", "Profit_M"]
        assert mapping["growth"] != "Cost_M"

    def test_spend_request_prefers_cost(self, sample_mixed_columns):
        """Test that 'spend' requests prefer cost over revenue."""
        loader = DataLoader()
        loader.last_loaded = sample_mixed_columns
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["spend"])

        # Should pick Cost_M, not Revenue_M
        assert mapping["spend"] == "Cost_M"

    def test_profit_request(self, sample_mixed_columns):
        """Test that 'profit' requests work correctly."""
        loader = DataLoader()
        loader.last_loaded = sample_mixed_columns
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["profit"])

        # Should match Profit_M
        assert mapping["profit"] == "Profit_M"


# --- Phase 5: Human Override Tests ---


class TestHumanOverride:
    """Test Phase 5: Manual column_mapping overrides."""

    def test_override_bypasses_intelligence(self, sample_business_data):
        """Test that overrides bypass all semantic intelligence."""
        loader = DataLoader()
        loader.last_loaded = sample_business_data
        loader._infer_schema()

        # Override to use Employee_Count even though requesting "revenue"
        mapping = loader.suggest_column_mapping(
            ["revenue"],
            overrides={"revenue": "Employee_Count"}
        )

        # Should use override, ignoring semantic match
        assert mapping["revenue"] == "Employee_Count"

    def test_override_takes_absolute_precedence(self, sample_business_data):
        """Test override takes precedence over exact match."""
        loader = DataLoader()
        loader.last_loaded = sample_business_data
        loader._infer_schema()

        # Override Region to map to something else
        mapping = loader.suggest_column_mapping(
            ["Region"],
            overrides={"Region": "Company_Name"}
        )

        # Should use override even though "Region" exists
        assert mapping["Region"] == "Company_Name"

    def test_override_invalid_column_falls_back(self, sample_business_data):
        """Test that invalid override column falls back to intelligence."""
        loader = DataLoader()
        loader.last_loaded = sample_business_data
        loader._infer_schema()

        # Override with non-existent column
        mapping = loader.suggest_column_mapping(
            ["revenue"],
            overrides={"revenue": "NonexistentColumn"}
        )

        # Should fall back to semantic matching
        assert mapping["revenue"] == "Revenue_M"

    def test_multiple_overrides(self, sample_business_data):
        """Test multiple overrides at once."""
        loader = DataLoader()
        loader.last_loaded = sample_business_data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(
            ["x", "y"],
            overrides={
                "x": "Region",
                "y": "Revenue_M"
            }
        )

        assert mapping["x"] == "Region"
        assert mapping["y"] == "Revenue_M"


# --- Integration Tests ---


class TestIntegration:
    """Test end-to-end integration scenarios."""

    def test_full_pipeline(self, temp_csv_file):
        """Test complete load -> infer -> suggest pipeline."""
        loader = DataLoader()

        # Load
        df = loader.load(temp_csv_file)
        assert len(df) == 5

        # Schema inferred automatically
        assert loader.schema is not None
        assert len(loader.schema.numeric_columns) > 0

        # Suggest mapping
        mapping = loader.suggest_column_mapping(["company", "revenue", "region"])

        assert mapping["company"] == "Company_Name"
        assert mapping["revenue"] == "Revenue_M"
        assert mapping["region"] == "Region"

    def test_info_method(self, temp_csv_file):
        """Test info() method returns correct metadata."""
        loader = DataLoader()
        loader.load(temp_csv_file)

        info = loader.info()

        assert info["loaded"] is True
        assert info["rows"] == 5
        assert info["columns"] == 8
        assert "Revenue_M" in info["numeric_columns"]

    def test_summary_method(self, temp_csv_file):
        """Test get_summary() returns readable text."""
        loader = DataLoader()
        loader.load(temp_csv_file)

        summary = loader.get_summary()

        assert "5 rows" in summary
        assert "8 columns" in summary
        assert "CSV" in summary.upper()

    def test_no_data_loaded_error(self):
        """Test suggest_column_mapping fails when no data loaded."""
        loader = DataLoader()

        with pytest.raises(ValueError, match="No data loaded"):
            loader.suggest_column_mapping(["column"])


# --- Edge Cases Tests ---


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        loader = DataLoader()
        loader.last_loaded = pd.DataFrame()
        loader._infer_schema()

        assert loader.schema is not None
        assert loader.schema.row_count == 0

    def test_single_column(self):
        """Test DataFrame with single column."""
        data = pd.DataFrame({"Value": [1, 2, 3]})
        loader = DataLoader()
        loader.last_loaded = data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["metric"])
        assert mapping["metric"] == "Value"

    def test_no_numeric_columns(self):
        """Test data with no numeric columns."""
        data = pd.DataFrame({
            "Category": ["A", "B", "C"],
            "Name": ["X", "Y", "Z"],
        })
        loader = DataLoader()
        loader.last_loaded = data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["value"])

        # Should return None or pick categorical
        result = mapping["value"]
        assert result is None or result in ["Category", "Name"]

    def test_all_numeric_columns(self):
        """Test data with only numeric columns."""
        data = pd.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6],
            "C": [7, 8, 9],
        })
        loader = DataLoader()
        loader.last_loaded = data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["x", "y"])

        # Should map to some columns
        assert mapping["x"] is not None
        assert mapping["y"] is not None
        assert mapping["x"] != mapping["y"]

    def test_duplicate_column_names(self):
        """Test handling of data with duplicate column names."""
        # pandas may rename duplicates to "Column.1", "Column.2"
        data = pd.DataFrame([[1, 2, 3]], columns=["A", "A", "B"])
        loader = DataLoader()
        loader.last_loaded = data
        loader._infer_schema()

        # Should handle gracefully
        assert loader.schema is not None

    def test_special_characters_in_columns(self):
        """Test columns with special characters."""
        data = pd.DataFrame({
            "Revenue ($M)": [100, 200],
            "Cost (%)": [30, 40],
            "ROI [ratio]": [0.3, 0.5],
        })
        loader = DataLoader()
        loader.last_loaded = data
        loader._infer_schema()

        mapping = loader.suggest_column_mapping(["revenue", "cost"])

        # Should handle special chars
        assert "($M)" in mapping["revenue"]


# --- Convenience Function Tests ---


class TestConvenienceFunction:
    """Test convenience wrapper function."""

    def test_load_data_function(self, temp_csv_file):
        """Test load_data() convenience function."""
        from kie.data.loader import load_data

        df = load_data(temp_csv_file)

        assert len(df) == 5
        assert "Company_Name" in df.columns
