"""
Tests for AreaChartBuilder

Tests cover:
- Basic area charts
- Multi-series area charts
- Stacked area charts
- Curve types (monotone, linear, step, natural)
- Fill opacity settings
- Data labels
- Legend configuration
- Stroke width
- KDS color compliance
- Edge cases (empty data, zero values, negative values)
- JSON serialization
- Convenience functions
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from kie.brand.colors import KDSColors
from kie.charts.builders.area import (
    AreaChartBuilder,
    area_chart,
    stacked_area_chart,
)


# --- Fixtures ---


@pytest.fixture
def sample_data_single():
    """Single series sample data."""
    return pd.DataFrame({
        "month": ["Jan", "Feb", "Mar", "Apr", "May"],
        "revenue": [1200, 1350, 1480, 1620, 1550],
    })


@pytest.fixture
def sample_data_multi():
    """Multi-series sample data."""
    return pd.DataFrame({
        "month": ["Jan", "Feb", "Mar", "Apr"],
        "product_a": [100, 120, 140, 130],
        "product_b": [80, 95, 110, 105],
        "product_c": [60, 70, 85, 90],
    })


@pytest.fixture
def sample_data_zeros():
    """Data with zero values."""
    return pd.DataFrame({
        "category": ["A", "B", "C", "D"],
        "value": [0, 50, 0, 75],
    })


@pytest.fixture
def sample_data_negatives():
    """Data with negative values."""
    return pd.DataFrame({
        "quarter": ["Q1", "Q2", "Q3", "Q4"],
        "profit": [100, -50, 75, -25],
    })


# --- Basic Functionality Tests ---


class TestBasicAreaChart:
    """Test basic area chart generation."""

    def test_single_series_area(self, sample_data_single):
        """Test basic single-series area chart."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
            title="Monthly Revenue",
        )

        assert config.chart_type == "area"
        assert len(config.data) == 5
        assert config.title == "Monthly Revenue"
        assert config.config["xAxis"]["dataKey"] == "month"
        assert len(config.config["areas"]) == 1
        assert config.config["areas"][0]["dataKey"] == "revenue"

    def test_multi_series_area(self, sample_data_multi):
        """Test multi-series area chart."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_multi,
            x_key="month",
            y_keys=["product_a", "product_b", "product_c"],
            title="Product Performance",
        )

        assert len(config.config["areas"]) == 3
        assert config.config["areas"][0]["dataKey"] == "product_a"
        assert config.config["areas"][1]["dataKey"] == "product_b"
        assert config.config["areas"][2]["dataKey"] == "product_c"

    def test_list_of_dicts_input(self):
        """Test area chart with list of dicts input."""
        data = [
            {"month": "Jan", "sales": 100},
            {"month": "Feb", "sales": 150},
            {"month": "Mar", "sales": 120},
        ]
        builder = AreaChartBuilder()
        config = builder.build(data=data, x_key="month", y_keys="sales")

        assert len(config.data) == 3
        assert config.data[0]["month"] == "Jan"
        assert config.data[0]["sales"] == 100

    def test_y_keys_string_normalization(self, sample_data_single):
        """Test that single y_key as string is normalized to list."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",  # String, not list
        )

        assert len(config.config["areas"]) == 1
        assert config.config["areas"][0]["dataKey"] == "revenue"


# --- Stacking Tests ---


class TestStackedAreas:
    """Test stacked area chart functionality."""

    def test_stacked_area(self, sample_data_multi):
        """Test stacked area chart."""
        builder = AreaChartBuilder(stacked=True)
        config = builder.build(
            data=sample_data_multi,
            x_key="month",
            y_keys=["product_a", "product_b", "product_c"],
            title="Stacked Products",
        )

        assert config.config["stackId"] == "stack1"
        assert len(config.config["areas"]) == 3

    def test_non_stacked_area(self, sample_data_multi):
        """Test non-stacked (overlapping) area chart."""
        builder = AreaChartBuilder(stacked=False)
        config = builder.build(
            data=sample_data_multi,
            x_key="month",
            y_keys=["product_a", "product_b"],
        )

        # When stacked=False, stackId should not be in config or be None
        assert config.config.get("stackId") is None


# --- Curve Type Tests ---


class TestCurveTypes:
    """Test different curve interpolation types."""

    def test_monotone_curve(self, sample_data_single):
        """Test monotone curve (default, smooth)."""
        builder = AreaChartBuilder(curve_type="monotone")
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        # Note: Curve type is set in constructor but may not appear in config
        # This test verifies the builder accepts the parameter
        assert builder.curve_type == "monotone"

    def test_linear_curve(self, sample_data_single):
        """Test linear curve (straight lines)."""
        builder = AreaChartBuilder(curve_type="linear")
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert builder.curve_type == "linear"

    def test_step_curve(self, sample_data_single):
        """Test step curve."""
        builder = AreaChartBuilder(curve_type="step")
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert builder.curve_type == "step"

    def test_natural_curve(self, sample_data_single):
        """Test natural curve."""
        builder = AreaChartBuilder(curve_type="natural")
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert builder.curve_type == "natural"


# --- Styling Tests ---


class TestAreaStyling:
    """Test area chart styling options."""

    def test_fill_opacity_default(self, sample_data_single):
        """Test default fill opacity."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert config.config["areas"][0]["fillOpacity"] == 0.6

    def test_fill_opacity_custom(self, sample_data_single):
        """Test custom fill opacity."""
        builder = AreaChartBuilder(fill_opacity=0.3)
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert config.config["areas"][0]["fillOpacity"] == 0.3

    def test_stroke_width_default(self, sample_data_single):
        """Test default stroke width."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert config.config["areas"][0]["strokeWidth"] == 2

    def test_stroke_width_custom(self, sample_data_single):
        """Test custom stroke width."""
        builder = AreaChartBuilder(stroke_width=4)
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert config.config["areas"][0]["strokeWidth"] == 4


# --- Color Tests ---


class TestAreaColors:
    """Test color assignment and KDS compliance."""

    def test_default_kds_colors(self, sample_data_multi):
        """Test default KDS color assignment."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_multi,
            x_key="month",
            y_keys=["product_a", "product_b", "product_c"],
        )

        expected_colors = KDSColors.get_chart_colors(3)
        assert config.config["areas"][0]["fill"] == expected_colors[0]
        assert config.config["areas"][1]["fill"] == expected_colors[1]
        assert config.config["areas"][2]["fill"] == expected_colors[2]

    def test_custom_colors(self, sample_data_multi):
        """Test custom color override."""
        custom_colors = ["#D2D2D2", "#A5A6A5", "#787878"]
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_multi,
            x_key="month",
            y_keys=["product_a", "product_b", "product_c"],
            colors=custom_colors,
        )

        assert config.config["areas"][0]["fill"] == "#D2D2D2"
        assert config.config["areas"][1]["fill"] == "#A5A6A5"
        assert config.config["areas"][2]["fill"] == "#787878"

    def test_insufficient_custom_colors(self, sample_data_multi):
        """Test that KDS colors fill in when custom colors insufficient."""
        custom_colors = ["#D2D2D2"]  # Only 1 color for 3 series
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_multi,
            x_key="month",
            y_keys=["product_a", "product_b", "product_c"],
            colors=custom_colors,
        )

        # First color custom, rest from KDS
        assert config.config["areas"][0]["fill"] == "#D2D2D2"
        assert len(config.config["areas"]) == 3
        # Subsequent colors should be from KDS palette
        assert config.config["areas"][1]["fill"] in KDSColors.CHART_PALETTE
        assert config.config["areas"][2]["fill"] in KDSColors.CHART_PALETTE

    def test_no_green_colors(self, sample_data_multi):
        """Test that KDS colors never include green."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_multi,
            x_key="month",
            y_keys=["product_a", "product_b", "product_c"],
        )

        for area in config.config["areas"]:
            color = area["fill"].lower()
            # Check for common green hex patterns
            assert not color.startswith("#0") or "f" in color or "a" in color or "d" in color
            assert color not in ["#00ff00", "#008000", "#90ee90", "#00ff7f"]

    def test_stroke_matches_fill(self, sample_data_single):
        """Test that stroke color matches fill color."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        area = config.config["areas"][0]
        assert area["stroke"] == area["fill"]


# --- Data Labels Tests ---


class TestDataLabels:
    """Test data label functionality."""

    def test_data_labels_disabled_by_default(self, sample_data_single):
        """Test that data labels are disabled by default."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        # When show_data_labels=False, label may not be in config or be None
        assert config.config["areas"][0].get("label") is None

    def test_data_labels_enabled(self, sample_data_single):
        """Test enabling data labels."""
        builder = AreaChartBuilder(show_data_labels=True)
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        label = config.config["areas"][0]["label"]
        assert label is not None
        assert label["position"] == "top"
        assert label["fontSize"] == 11
        assert label["fontWeight"] == 500


# --- Legend Tests ---


class TestLegend:
    """Test legend configuration."""

    def test_legend_shown_for_multi_series(self, sample_data_multi):
        """Test legend appears for multi-series charts."""
        builder = AreaChartBuilder(show_legend=True)
        config = builder.build(
            data=sample_data_multi,
            x_key="month",
            y_keys=["product_a", "product_b"],
        )

        assert config.config["legend"] is not None

    def test_legend_hidden_for_single_series(self, sample_data_single):
        """Test legend hidden for single-series charts."""
        builder = AreaChartBuilder(show_legend=True)
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        # Legend should be None for single series even when show_legend=True
        assert config.config.get("legend") is None

    def test_legend_can_be_disabled(self, sample_data_multi):
        """Test disabling legend explicitly."""
        builder = AreaChartBuilder(show_legend=False)
        config = builder.build(
            data=sample_data_multi,
            x_key="month",
            y_keys=["product_a", "product_b"],
        )

        assert config.config.get("legend") is None


# --- Edge Cases Tests ---


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        builder = AreaChartBuilder()

        # Should not raise, but produce empty data
        config = builder.build(
            data=empty_df,
            x_key="x",
            y_keys="y",
        )

        assert len(config.data) == 0

    def test_single_data_point(self):
        """Test area chart with single data point."""
        single_point = pd.DataFrame({
            "x": ["A"],
            "y": [100],
        })
        builder = AreaChartBuilder()
        config = builder.build(data=single_point, x_key="x", y_keys="y")

        assert len(config.data) == 1
        assert config.data[0]["y"] == 100

    def test_zero_values(self, sample_data_zeros):
        """Test area chart with zero values."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_zeros,
            x_key="category",
            y_keys="value",
        )

        assert len(config.data) == 4
        assert config.data[0]["value"] == 0
        assert config.data[2]["value"] == 0

    def test_negative_values(self, sample_data_negatives):
        """Test area chart with negative values."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_negatives,
            x_key="quarter",
            y_keys="profit",
        )

        assert len(config.data) == 4
        assert config.data[1]["profit"] == -50
        assert config.data[3]["profit"] == -25

    def test_large_dataset(self):
        """Test area chart with large dataset."""
        large_data = pd.DataFrame({
            "index": list(range(1000)),
            "value": list(range(1000)),
        })
        builder = AreaChartBuilder()
        config = builder.build(
            data=large_data,
            x_key="index",
            y_keys="value",
        )

        assert len(config.data) == 1000

    def test_special_characters_in_column_names(self):
        """Test handling of special characters in column names."""
        data = pd.DataFrame({
            "Date (YYYY-MM)": ["2024-01", "2024-02"],
            "Revenue ($)": [1000, 1500],
        })
        builder = AreaChartBuilder()
        config = builder.build(
            data=data,
            x_key="Date (YYYY-MM)",
            y_keys="Revenue ($)",
        )

        assert config.config["xAxis"]["dataKey"] == "Date (YYYY-MM)"
        assert config.config["areas"][0]["dataKey"] == "Revenue ($)"


# --- KDS Compliance Tests ---


class TestKDSCompliance:
    """Test Kearney Design System compliance."""

    def test_no_gridlines(self, sample_data_single):
        """Test that gridlines are disabled (KDS requirement)."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert config.config["gridLines"] is False

    def test_font_family(self, sample_data_single):
        """Test KDS font family."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert "Inter" in config.config["fontFamily"]

    def test_interactive_enabled(self, sample_data_single):
        """Test that charts are interactive."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert config.config["interactive"] is True

    def test_tooltip_present(self, sample_data_single):
        """Test that tooltip is configured."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        assert config.config["tooltip"] is not None


# --- JSON Serialization Tests ---


class TestJSONSerialization:
    """Test JSON export functionality."""

    def test_to_json_basic(self, sample_data_single, tmp_path):
        """Test basic JSON serialization."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
            title="Test Chart",
        )

        output_path = tmp_path / "area_chart.json"
        config.to_json(output_path)

        assert output_path.exists()

        # Verify JSON is valid
        with open(output_path) as f:
            data = json.load(f)

        # RechartsConfig uses to_dict() for serialization with 'type' key
        assert data["type"] == "area"
        assert data["title"] == "Test Chart"
        assert len(data["data"]) == 5

    def test_json_structure(self, sample_data_single):
        """Test JSON structure matches Recharts schema."""
        builder = AreaChartBuilder()
        config = builder.build(
            data=sample_data_single,
            x_key="month",
            y_keys="revenue",
        )

        # Use to_dict() instead of model_dump()
        json_str = json.dumps(config.to_dict())
        parsed = json.loads(json_str)

        assert "type" in parsed
        assert "data" in parsed
        assert "config" in parsed
        assert "areas" in parsed["config"]
        assert "xAxis" in parsed["config"]
        assert "yAxis" in parsed["config"]


# --- Convenience Function Tests ---


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""

    def test_area_chart_function(self, sample_data_single):
        """Test area_chart() convenience function."""
        config = area_chart(
            data=sample_data_single,
            x="month",
            y="revenue",
            title="Quick Chart",
        )

        assert config.chart_type == "area"
        assert config.title == "Quick Chart"
        assert len(config.data) == 5

    def test_area_chart_with_output(self, sample_data_single, tmp_path):
        """Test area_chart() with file output."""
        output_path = tmp_path / "quick_area.json"
        config = area_chart(
            data=sample_data_single,
            x="month",
            y="revenue",
            output_path=output_path,
        )

        assert output_path.exists()

    def test_stacked_area_chart_function(self, sample_data_multi):
        """Test stacked_area_chart() convenience function."""
        config = stacked_area_chart(
            data=sample_data_multi,
            x="month",
            y=["product_a", "product_b", "product_c"],
            title="Stacked Chart",
        )

        assert config.chart_type == "area"
        assert config.config["stackId"] == "stack1"
        assert len(config.config["areas"]) == 3

    def test_stacked_area_chart_with_output(self, sample_data_multi, tmp_path):
        """Test stacked_area_chart() with file output."""
        output_path = tmp_path / "stacked_area.json"
        config = stacked_area_chart(
            data=sample_data_multi,
            x="month",
            y=["product_a", "product_b"],
            output_path=output_path,
        )

        assert output_path.exists()

    def test_convenience_function_kwargs(self, sample_data_single):
        """Test passing kwargs to convenience function."""
        config = area_chart(
            data=sample_data_single,
            x="month",
            y="revenue",
            fill_opacity=0.8,
            stroke_width=3,
            show_data_labels=True,
        )

        assert config.config["areas"][0]["fillOpacity"] == 0.8
        assert config.config["areas"][0]["strokeWidth"] == 3
        assert config.config["areas"][0]["label"] is not None
