"""
Tests for ComboChartBuilder

Tests cover:
- Basic combo charts (bar + line)
- Multiple bars and multiple lines
- Single bar with single line
- Multiple bars with multiple lines
- Color assignment across bars and lines
- Data labels on both bars and lines
- Legend configuration
- Edge cases (empty data, single point)
- KDS color compliance
- JSON serialization
- Convenience functions
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from kie.brand.colors import KDSColors
from kie.charts.builders.combo import ComboChartBuilder, combo_chart


# --- Fixtures ---


@pytest.fixture
def sample_actual_vs_target():
    """Actual vs target sales data."""
    return pd.DataFrame({
        "month": ["Jan", "Feb", "Mar", "Apr", "May"],
        "actual": [1200, 1350, 1180, 1420, 1550],
        "target": [1000, 1100, 1200, 1300, 1400],
    })


@pytest.fixture
def sample_multi_series():
    """Multiple bars and lines."""
    return pd.DataFrame({
        "quarter": ["Q1", "Q2", "Q3", "Q4"],
        "revenue": [1000, 1200, 1100, 1400],
        "costs": [700, 800, 750, 900],
        "target_revenue": [1100, 1150, 1250, 1350],
        "target_costs": [650, 700, 750, 800],
    })


@pytest.fixture
def sample_single_point():
    """Single data point."""
    return pd.DataFrame({
        "category": ["A"],
        "bar": [100],
        "line": [120],
    })


@pytest.fixture
def sample_empty():
    """Empty DataFrame."""
    return pd.DataFrame()


# --- Basic Functionality Tests ---


class TestBasicCombo:
    """Test basic combo chart generation."""

    def test_simple_combo(self, sample_actual_vs_target):
        """Test basic combo chart with one bar and one line."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
            title="Actual vs Target",
        )

        assert config.chart_type == "combo"
        assert len(config.data) == 5
        assert config.title == "Actual vs Target"
        assert config.config["xAxis"]["dataKey"] == "month"

    def test_combo_with_lists(self, sample_actual_vs_target):
        """Test combo chart with bar and line keys as lists."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys=["actual"],
            line_keys=["target"],
        )

        assert len(config.config["bars"]) == 1
        assert len(config.config["lines"]) == 1

    def test_list_of_dicts_input(self):
        """Test combo chart with list of dicts input."""
        data = [
            {"x": "A", "bar": 100, "line": 120},
            {"x": "B", "bar": 150, "line": 140},
        ]
        builder = ComboChartBuilder()
        config = builder.build(
            data=data,
            x_key="x",
            bar_keys="bar",
            line_keys="line",
        )

        assert len(config.data) == 2
        assert config.data[0]["x"] == "A"

    def test_string_normalization(self, sample_actual_vs_target):
        """Test that string bar/line keys are normalized to lists."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",  # String
            line_keys="target",  # String
        )

        assert isinstance(config.config["bars"], list)
        assert isinstance(config.config["lines"], list)
        assert len(config.config["bars"]) == 1
        assert len(config.config["lines"]) == 1


# --- Multi-Series Tests ---


class TestMultiSeries:
    """Test multiple bars and lines."""

    def test_multiple_bars_single_line(self, sample_multi_series):
        """Test combo with multiple bars and single line."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_multi_series,
            x_key="quarter",
            bar_keys=["revenue", "costs"],
            line_keys="target_revenue",
        )

        assert len(config.config["bars"]) == 2
        assert len(config.config["lines"]) == 1
        assert config.config["bars"][0]["dataKey"] == "revenue"
        assert config.config["bars"][1]["dataKey"] == "costs"
        assert config.config["lines"][0]["dataKey"] == "target_revenue"

    def test_single_bar_multiple_lines(self, sample_multi_series):
        """Test combo with single bar and multiple lines."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_multi_series,
            x_key="quarter",
            bar_keys="revenue",
            line_keys=["target_revenue", "target_costs"],
        )

        assert len(config.config["bars"]) == 1
        assert len(config.config["lines"]) == 2
        assert config.config["lines"][0]["dataKey"] == "target_revenue"
        assert config.config["lines"][1]["dataKey"] == "target_costs"

    def test_multiple_bars_multiple_lines(self, sample_multi_series):
        """Test combo with multiple bars and multiple lines."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_multi_series,
            x_key="quarter",
            bar_keys=["revenue", "costs"],
            line_keys=["target_revenue", "target_costs"],
        )

        assert len(config.config["bars"]) == 2
        assert len(config.config["lines"]) == 2


# --- Color Assignment Tests ---


class TestColorAssignment:
    """Test color assignment across bars and lines."""

    def test_default_colors_single_each(self, sample_actual_vs_target):
        """Test default KDS colors for single bar and line."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        expected_colors = KDSColors.get_chart_colors(2)
        assert config.config["bars"][0]["fill"] == expected_colors[0]
        assert config.config["lines"][0]["stroke"] == expected_colors[1]

    def test_default_colors_multi_series(self, sample_multi_series):
        """Test default colors for multiple series."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_multi_series,
            x_key="quarter",
            bar_keys=["revenue", "costs"],
            line_keys=["target_revenue", "target_costs"],
        )

        expected_colors = KDSColors.get_chart_colors(4)

        # Bars get first colors
        assert config.config["bars"][0]["fill"] == expected_colors[0]
        assert config.config["bars"][1]["fill"] == expected_colors[1]

        # Lines get subsequent colors
        assert config.config["lines"][0]["stroke"] == expected_colors[2]
        assert config.config["lines"][1]["stroke"] == expected_colors[3]

    def test_custom_colors(self, sample_actual_vs_target):
        """Test custom color override."""
        custom_colors = ["#D2D2D2", "#A5A6A5"]
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
            colors=custom_colors,
        )

        assert config.config["bars"][0]["fill"] == "#D2D2D2"
        assert config.config["lines"][0]["stroke"] == "#A5A6A5"

    def test_insufficient_custom_colors(self, sample_multi_series):
        """Test that KDS colors fill in when custom colors insufficient."""
        custom_colors = ["#D2D2D2"]  # Only 1 color for 4 series
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_multi_series,
            x_key="quarter",
            bar_keys=["revenue", "costs"],
            line_keys=["target_revenue", "target_costs"],
            colors=custom_colors,
        )

        # First bar uses custom color
        assert config.config["bars"][0]["fill"] == "#D2D2D2"

        # Rest should use KDS colors
        assert config.config["bars"][1]["fill"] in KDSColors.CHART_PALETTE
        assert config.config["lines"][0]["stroke"] in KDSColors.CHART_PALETTE
        assert config.config["lines"][1]["stroke"] in KDSColors.CHART_PALETTE

    def test_no_green_colors(self, sample_multi_series):
        """Test that KDS colors never include green."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_multi_series,
            x_key="quarter",
            bar_keys=["revenue", "costs"],
            line_keys=["target_revenue", "target_costs"],
        )

        all_colors = [bar["fill"] for bar in config.config["bars"]]
        all_colors.extend([line["stroke"] for line in config.config["lines"]])

        for color in all_colors:
            color_lower = color.lower()
            assert not color_lower.startswith("#0") or "f" in color_lower or "a" in color_lower or "d" in color_lower
            assert color_lower not in ["#00ff00", "#008000", "#90ee90", "#00ff7f"]


# --- Bar Configuration Tests ---


class TestBarConfiguration:
    """Test bar-specific configuration."""

    def test_bar_border_radius(self, sample_actual_vs_target):
        """Test that bars have rounded top corners."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        assert config.config["bars"][0]["radius"] == [4, 4, 0, 0]

    def test_bar_data_labels_enabled(self, sample_actual_vs_target):
        """Test bar data labels when enabled."""
        builder = ComboChartBuilder(show_data_labels=True)
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        bar_label = config.config["bars"][0]["label"]
        assert bar_label is not None
        assert bar_label["position"] == "top"
        assert bar_label["fontSize"] == 12

    def test_bar_data_labels_disabled(self, sample_actual_vs_target):
        """Test bar data labels when disabled."""
        builder = ComboChartBuilder(show_data_labels=False)
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        assert config.config["bars"][0].get("label") is None


# --- Line Configuration Tests ---


class TestLineConfiguration:
    """Test line-specific configuration."""

    def test_line_stroke_width(self, sample_actual_vs_target):
        """Test line stroke width."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        assert config.config["lines"][0]["strokeWidth"] == 3

    def test_line_dot_configuration(self, sample_actual_vs_target):
        """Test line dot markers."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        line = config.config["lines"][0]
        assert line["dot"]["r"] == 5
        assert "fill" in line["dot"]
        assert line["activeDot"]["r"] == 7

    def test_line_data_labels_enabled(self, sample_actual_vs_target):
        """Test line data labels when enabled."""
        builder = ComboChartBuilder(show_data_labels=True)
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        line_label = config.config["lines"][0]["label"]
        assert line_label is not None
        assert line_label["position"] == "top"
        assert line_label["fontWeight"] == 600

    def test_line_data_labels_disabled(self, sample_actual_vs_target):
        """Test line data labels when disabled."""
        builder = ComboChartBuilder(show_data_labels=False)
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        assert config.config["lines"][0].get("label") is None


# --- Legend Tests ---


class TestLegend:
    """Test legend configuration."""

    def test_legend_shown_by_default(self, sample_actual_vs_target):
        """Test that legend is shown by default."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        assert config.config["legend"] is not None

    def test_legend_can_be_disabled(self, sample_actual_vs_target):
        """Test disabling legend."""
        builder = ComboChartBuilder(show_legend=False)
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        assert config.config.get("legend") is None


# --- Edge Cases Tests ---


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self, sample_empty):
        """Test handling of empty DataFrame."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_empty,
            x_key="x",
            bar_keys="bar",
            line_keys="line",
        )

        assert len(config.data) == 0

    def test_single_data_point(self, sample_single_point):
        """Test combo chart with single data point."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_single_point,
            x_key="category",
            bar_keys="bar",
            line_keys="line",
        )

        assert len(config.data) == 1
        assert config.data[0]["category"] == "A"
        assert config.data[0]["bar"] == 100
        assert config.data[0]["line"] == 120

    def test_two_data_points(self):
        """Test combo chart with two points."""
        data = pd.DataFrame({
            "x": ["A", "B"],
            "bar": [100, 150],
            "line": [120, 140],
        })
        builder = ComboChartBuilder()
        config = builder.build(
            data=data,
            x_key="x",
            bar_keys="bar",
            line_keys="line",
        )

        assert len(config.data) == 2

    def test_zero_values(self):
        """Test combo chart with zero values."""
        data = pd.DataFrame({
            "category": ["A", "B", "C"],
            "bar": [0, 100, 0],
            "line": [50, 0, 75],
        })
        builder = ComboChartBuilder()
        config = builder.build(
            data=data,
            x_key="category",
            bar_keys="bar",
            line_keys="line",
        )

        assert len(config.data) == 3
        assert config.data[0]["bar"] == 0
        assert config.data[1]["line"] == 0

    def test_negative_values(self):
        """Test combo chart with negative values."""
        data = pd.DataFrame({
            "month": ["Jan", "Feb", "Mar"],
            "profit": [100, -50, 75],
            "target": [80, 90, 100],
        })
        builder = ComboChartBuilder()
        config = builder.build(
            data=data,
            x_key="month",
            bar_keys="profit",
            line_keys="target",
        )

        assert config.data[1]["profit"] == -50

    def test_large_dataset(self):
        """Test combo chart with large dataset."""
        large_data = pd.DataFrame({
            "x": list(range(100)),
            "bar": list(range(100)),
            "line": [i * 1.1 for i in range(100)],
        })
        builder = ComboChartBuilder()
        config = builder.build(
            data=large_data,
            x_key="x",
            bar_keys="bar",
            line_keys="line",
        )

        assert len(config.data) == 100

    def test_special_characters_in_columns(self):
        """Test handling of special characters in column names."""
        data = pd.DataFrame({
            "Month (2024)": ["Jan", "Feb"],
            "Actual ($)": [1000, 1500],
            "Target (%)": [90, 95],
        })
        builder = ComboChartBuilder()
        config = builder.build(
            data=data,
            x_key="Month (2024)",
            bar_keys="Actual ($)",
            line_keys="Target (%)",
        )

        assert config.config["xAxis"]["dataKey"] == "Month (2024)"
        assert config.config["bars"][0]["dataKey"] == "Actual ($)"
        assert config.config["lines"][0]["dataKey"] == "Target (%)"


# --- KDS Compliance Tests ---


class TestKDSCompliance:
    """Test Kearney Design System compliance."""

    def test_no_gridlines(self, sample_actual_vs_target):
        """Test that gridlines are disabled (KDS requirement)."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        assert config.config["gridLines"] is False

    def test_font_family(self, sample_actual_vs_target):
        """Test KDS font family."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        assert "Inter" in config.config["fontFamily"]

    def test_interactive_enabled(self, sample_actual_vs_target):
        """Test that charts are interactive."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        assert config.config["interactive"] is True

    def test_tooltip_present(self, sample_actual_vs_target):
        """Test that tooltip is configured."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        assert config.config["tooltip"] is not None


# --- JSON Serialization Tests ---


class TestJSONSerialization:
    """Test JSON export functionality."""

    def test_to_json_basic(self, sample_actual_vs_target, tmp_path):
        """Test basic JSON serialization."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
            title="Test Combo",
        )

        output_path = tmp_path / "combo.json"
        config.to_json(output_path)

        assert output_path.exists()

        # Verify JSON is valid
        with open(output_path) as f:
            data = json.load(f)

        assert data["type"] == "combo"
        assert data["title"] == "Test Combo"
        assert len(data["data"]) == 5

    def test_json_structure(self, sample_actual_vs_target):
        """Test JSON structure matches Recharts schema."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_actual_vs_target,
            x_key="month",
            bar_keys="actual",
            line_keys="target",
        )

        json_str = json.dumps(config.to_dict())
        parsed = json.loads(json_str)

        assert "type" in parsed
        assert "data" in parsed
        assert "config" in parsed
        assert "bars" in parsed["config"]
        assert "lines" in parsed["config"]
        assert "xAxis" in parsed["config"]
        assert "yAxis" in parsed["config"]

    def test_json_preserves_multi_series(self, sample_multi_series, tmp_path):
        """Test that JSON preserves multiple series correctly."""
        builder = ComboChartBuilder()
        config = builder.build(
            data=sample_multi_series,
            x_key="quarter",
            bar_keys=["revenue", "costs"],
            line_keys=["target_revenue", "target_costs"],
        )

        output_path = tmp_path / "combo_multi.json"
        config.to_json(output_path)

        with open(output_path) as f:
            data = json.load(f)

        assert len(data["config"]["bars"]) == 2
        assert len(data["config"]["lines"]) == 2


# --- Convenience Function Tests ---


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""

    def test_combo_chart_function(self, sample_actual_vs_target):
        """Test combo_chart() convenience function."""
        config = combo_chart(
            data=sample_actual_vs_target,
            x="month",
            bars="actual",
            lines="target",
            title="Quick Combo",
        )

        assert config.chart_type == "combo"
        assert config.title == "Quick Combo"
        assert len(config.data) == 5

    def test_combo_chart_with_output(self, sample_actual_vs_target, tmp_path):
        """Test combo_chart() with file output."""
        output_path = tmp_path / "quick_combo.json"
        config = combo_chart(
            data=sample_actual_vs_target,
            x="month",
            bars="actual",
            lines="target",
            output_path=output_path,
        )

        assert output_path.exists()

    def test_combo_chart_with_multiple_series(self, sample_multi_series):
        """Test combo_chart() with multiple bars and lines."""
        config = combo_chart(
            data=sample_multi_series,
            x="quarter",
            bars=["revenue", "costs"],
            lines=["target_revenue", "target_costs"],
            title="Multi-Series Combo",
        )

        assert len(config.config["bars"]) == 2
        assert len(config.config["lines"]) == 2

    def test_convenience_function_kwargs(self, sample_actual_vs_target):
        """Test passing kwargs to convenience function."""
        config = combo_chart(
            data=sample_actual_vs_target,
            x="month",
            bars="actual",
            lines="target",
            show_data_labels=False,
            show_legend=False,
        )

        assert config.config["bars"][0].get("label") is None
        assert config.config.get("legend") is None
