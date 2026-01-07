"""
Tests for WaterfallChartBuilder

Tests cover:
- Basic waterfall charts with positive/negative changes
- Total bars vs incremental bars
- Cumulative value calculation
- Floating bar positioning (start/end coordinates)
- Color coding (positive, negative, total)
- Data labels and connectors
- Negative values and mixed sequences
- Edge cases (all positive, all negative, single bar, zeros)
- KDS color compliance
- JSON serialization
- Convenience functions
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from kie.brand.colors import KDSColors
from kie.charts.builders.waterfall import (
    WaterfallChartBuilder,
    waterfall_chart,
)


# --- Fixtures ---


@pytest.fixture
def sample_revenue_bridge():
    """Sample revenue bridge waterfall data."""
    return pd.DataFrame({
        "step": ["Starting Revenue", "New Sales", "Returns", "Price Increase", "Ending Revenue"],
        "change": [1000, 200, -50, 100, 1250],
        "is_total": [True, False, False, False, True],
    })


@pytest.fixture
def sample_cost_breakdown():
    """Sample cost breakdown with all incremental changes."""
    return pd.DataFrame({
        "category": ["Materials", "Labor", "Overhead", "Shipping"],
        "amount": [500, 300, -50, 150],
    })


@pytest.fixture
def sample_all_positive():
    """All positive changes."""
    return pd.DataFrame({
        "step": ["Start", "A", "B", "C", "Total"],
        "value": [100, 50, 30, 20, 200],
        "is_total": [True, False, False, False, True],
    })


@pytest.fixture
def sample_all_negative():
    """All negative changes."""
    return pd.DataFrame({
        "step": ["Start", "Loss A", "Loss B", "Loss C", "Total"],
        "value": [1000, -200, -150, -100, 550],
        "is_total": [True, False, False, False, True],
    })


@pytest.fixture
def sample_mixed_sequence():
    """Mixed positive and negative in various patterns."""
    return pd.DataFrame({
        "item": ["Begin", "+100", "-50", "+75", "-25", "+50", "End"],
        "delta": [0, 100, -50, 75, -25, 50, 150],
        "total": [True, False, False, False, False, False, True],
    })


# --- Basic Functionality Tests ---


class TestBasicWaterfall:
    """Test basic waterfall chart generation."""

    def test_simple_waterfall(self, sample_revenue_bridge):
        """Test basic waterfall chart with totals."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
            title="Revenue Bridge",
        )

        assert config.chart_type == "waterfall"
        assert len(config.data) == 5
        assert config.title == "Revenue Bridge"

    def test_waterfall_without_totals(self, sample_cost_breakdown):
        """Test waterfall chart without explicit total markers."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_cost_breakdown,
            label_key="category",
            value_key="amount",
        )

        assert len(config.data) == 4
        # Without is_total column, all should be treated as incremental
        assert all(not item["is_total"] for item in config.data)

    def test_list_of_dicts_input(self):
        """Test waterfall chart with list of dicts input."""
        data = [
            {"step": "Start", "value": 100, "is_total": True},
            {"step": "Increase", "value": 50, "is_total": False},
            {"step": "End", "value": 150, "is_total": True},
        ]
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=data,
            label_key="step",
            value_key="value",
            is_total_key="is_total",
        )

        assert len(config.data) == 3
        assert config.data[0]["step"] == "Start"


# --- Cumulative Calculation Tests ---


class TestCumulativeLogic:
    """Test cumulative value calculations."""

    def test_cumulative_with_positives(self, sample_all_positive):
        """Test cumulative calculation with all positive changes."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_all_positive,
            label_key="step",
            value_key="value",
            is_total_key="is_total",
        )

        # Check cumulative values
        # Start: 100, +50 → 150, +30 → 180, +20 → 200, Total: 200
        cumulatives = [item["cumulative"] for item in config.data]
        assert cumulatives == [100, 150, 180, 200, 200]

    def test_cumulative_with_negatives(self, sample_all_negative):
        """Test cumulative calculation with negative changes."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_all_negative,
            label_key="step",
            value_key="value",
            is_total_key="is_total",
        )

        # Start: 1000, -200 → 800, -150 → 650, -100 → 550, Total: 550
        cumulatives = [item["cumulative"] for item in config.data]
        assert cumulatives == [1000, 800, 650, 550, 550]

    def test_cumulative_mixed_sequence(self, sample_mixed_sequence):
        """Test cumulative with mixed positive/negative."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_mixed_sequence,
            label_key="item",
            value_key="delta",
            is_total_key="total",
        )

        # Begin: 0, +100 → 100, -50 → 50, +75 → 125, -25 → 100, +50 → 150, End: 150
        cumulatives = [item["cumulative"] for item in config.data]
        assert cumulatives == [0, 100, 50, 125, 100, 150, 150]

    def test_values_preserved(self, sample_revenue_bridge):
        """Test that original values are preserved in data."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        # Original values should be in output
        values = [item["value"] for item in config.data]
        assert values == [1000, 200, -50, 100, 1250]


# --- Bar Position Tests ---


class TestBarPositioning:
    """Test floating bar start/end calculations."""

    def test_total_bar_positioning(self, sample_revenue_bridge):
        """Test that total bars start from 0."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        # Total bars (indices 0 and 4) should start from 0
        assert config.data[0]["start"] == 0
        assert config.data[0]["end"] == 1000
        assert config.data[4]["start"] == 0
        assert config.data[4]["end"] == 1250

    def test_positive_increment_positioning(self, sample_revenue_bridge):
        """Test positioning of positive incremental bars."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        # "New Sales" (+200): should float from 1000 to 1200
        new_sales = config.data[1]
        assert new_sales["start"] == 1000
        assert new_sales["end"] == 1200

        # "Price Increase" (+100): should float from 1150 to 1250
        price_increase = config.data[3]
        assert price_increase["start"] == 1150
        assert price_increase["end"] == 1250

    def test_negative_increment_positioning(self, sample_revenue_bridge):
        """Test positioning of negative incremental bars."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        # "Returns" (-50): should float from 1150 down to 1200
        returns = config.data[2]
        assert returns["start"] == 1150  # cumulative before + value
        assert returns["end"] == 1200  # cumulative before
        assert returns["value"] == -50

    def test_sequential_positioning(self):
        """Test that bars position correctly in sequence."""
        data = pd.DataFrame({
            "step": ["A", "B", "C"],
            "value": [100, 50, -30],
        })
        builder = WaterfallChartBuilder()
        config = builder.build(data=data, label_key="step", value_key="value")

        # A: 0 to 100
        assert config.data[0]["start"] == 0
        assert config.data[0]["end"] == 100

        # B: 100 to 150
        assert config.data[1]["start"] == 100
        assert config.data[1]["end"] == 150

        # C: 120 to 150 (negative, so start is lower)
        assert config.data[2]["start"] == 120
        assert config.data[2]["end"] == 150


# --- Color Assignment Tests ---


class TestColorCoding:
    """Test color assignment for positive/negative/total bars."""

    def test_default_colors(self, sample_revenue_bridge):
        """Test default color assignment."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        # Total bars (indices 0, 4) should use total_color
        assert config.data[0]["fill"] == KDSColors.PRIMARY
        assert config.data[4]["fill"] == KDSColors.PRIMARY

        # Positive increment (index 1, 3) should use positive_color
        assert config.data[1]["fill"] == KDSColors.CHART_PALETTE[9]
        assert config.data[3]["fill"] == KDSColors.CHART_PALETTE[9]

        # Negative increment (index 2) should use negative_color
        assert config.data[2]["fill"] == KDSColors.CHART_PALETTE[3]

    def test_custom_colors(self, sample_revenue_bridge):
        """Test custom color override."""
        custom_positive = "#D2D2D2"
        custom_negative = "#A5A6A5"
        custom_total = "#787878"

        builder = WaterfallChartBuilder(
            positive_color=custom_positive,
            negative_color=custom_negative,
            total_color=custom_total,
        )
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        # Check colors applied correctly
        assert config.data[0]["fill"] == custom_total  # Total
        assert config.data[1]["fill"] == custom_positive  # Positive
        assert config.data[2]["fill"] == custom_negative  # Negative

    def test_no_green_colors(self, sample_revenue_bridge):
        """Test that default colors don't include green."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        for item in config.data:
            color = item["fill"].lower()
            # No green hex values
            assert not color.startswith("#0") or "f" in color or "a" in color or "d" in color
            assert color not in ["#00ff00", "#008000", "#90ee90", "#00ff7f"]


# --- Data Labels and Connectors Tests ---


class TestLabelsAndConnectors:
    """Test data labels and connector line options."""

    def test_data_labels_enabled_by_default(self, sample_revenue_bridge):
        """Test that data labels are enabled by default."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        assert config.config["showDataLabels"] is True

    def test_data_labels_disabled(self, sample_revenue_bridge):
        """Test disabling data labels."""
        builder = WaterfallChartBuilder(show_data_labels=False)
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        assert config.config["showDataLabels"] is False

    def test_connectors_enabled_by_default(self, sample_revenue_bridge):
        """Test that connectors are enabled by default."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        assert config.config["showConnectors"] is True

    def test_connectors_disabled(self, sample_revenue_bridge):
        """Test disabling connector lines."""
        builder = WaterfallChartBuilder(show_connectors=False)
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        assert config.config["showConnectors"] is False


# --- Edge Cases Tests ---


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        builder = WaterfallChartBuilder()

        config = builder.build(
            data=empty_df,
            label_key="label",
            value_key="value",
        )

        assert len(config.data) == 0

    def test_single_bar(self):
        """Test waterfall chart with single bar."""
        single_bar = pd.DataFrame({
            "step": ["Total"],
            "value": [1000],
            "is_total": [True],
        })
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=single_bar,
            label_key="step",
            value_key="value",
            is_total_key="is_total",
        )

        assert len(config.data) == 1
        assert config.data[0]["start"] == 0
        assert config.data[0]["end"] == 1000
        assert config.data[0]["cumulative"] == 1000

    def test_two_bars(self):
        """Test waterfall chart with two bars."""
        two_bars = pd.DataFrame({
            "step": ["Start", "Change"],
            "value": [100, 50],
            "is_total": [True, False],
        })
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=two_bars,
            label_key="step",
            value_key="value",
            is_total_key="is_total",
        )

        assert len(config.data) == 2
        assert config.data[0]["cumulative"] == 100
        assert config.data[1]["cumulative"] == 150

    def test_zero_values(self):
        """Test waterfall with zero values."""
        with_zeros = pd.DataFrame({
            "step": ["Start", "No Change", "Change", "Total"],
            "value": [100, 0, 50, 150],
            "is_total": [True, False, False, True],
        })
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=with_zeros,
            label_key="step",
            value_key="value",
            is_total_key="is_total",
        )

        # Zero change should still create a bar
        zero_bar = config.data[1]
        assert zero_bar["value"] == 0
        assert zero_bar["start"] == 100
        assert zero_bar["end"] == 100

    def test_large_positive_values(self):
        """Test waterfall with large values."""
        large_values = pd.DataFrame({
            "step": ["A", "B", "C"],
            "value": [1000000, 500000, 250000],
        })
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=large_values,
            label_key="step",
            value_key="value",
        )

        assert config.data[-1]["cumulative"] == 1750000

    def test_large_negative_values(self):
        """Test waterfall with large negative values."""
        large_negatives = pd.DataFrame({
            "step": ["Start", "Big Loss", "Small Loss"],
            "value": [1000000, -750000, -100000],
            "is_total": [True, False, False],
        })
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=large_negatives,
            label_key="step",
            value_key="value",
            is_total_key="is_total",
        )

        assert config.data[-1]["cumulative"] == 150000

    def test_special_characters_in_labels(self):
        """Test handling of special characters in labels."""
        special_chars = pd.DataFrame({
            "label": ["Start ($)", "Change (%)", "End (€)"],
            "amount": [100, 50, 150],
            "total": [True, False, True],
        })
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=special_chars,
            label_key="label",
            value_key="amount",
            is_total_key="total",
        )

        assert config.data[0]["label"] == "Start ($)"
        assert config.data[1]["label"] == "Change (%)"
        assert config.data[2]["label"] == "End (€)"

    def test_all_incremental_no_totals(self):
        """Test waterfall with all incremental bars, no totals."""
        all_incremental = pd.DataFrame({
            "item": ["A", "B", "C", "D"],
            "change": [100, -50, 75, -25],
        })
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=all_incremental,
            label_key="item",
            value_key="change",
        )

        # Should calculate cumulative correctly
        assert config.data[0]["cumulative"] == 100
        assert config.data[1]["cumulative"] == 50
        assert config.data[2]["cumulative"] == 125
        assert config.data[3]["cumulative"] == 100


# --- KDS Compliance Tests ---


class TestKDSCompliance:
    """Test Kearney Design System compliance."""

    def test_no_gridlines(self, sample_revenue_bridge):
        """Test that gridlines are disabled (KDS requirement)."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        assert config.config["gridLines"] is False

    def test_no_axis_lines(self, sample_revenue_bridge):
        """Test that axis lines are disabled."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        assert config.config["axisLine"] is False
        assert config.config["tickLine"] is False

    def test_font_family(self, sample_revenue_bridge):
        """Test KDS font family."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        assert "Inter" in config.config["fontFamily"]

    def test_interactive_enabled(self, sample_revenue_bridge):
        """Test that charts are interactive."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        assert config.config["interactive"] is True


# --- Config Structure Tests ---


class TestConfigStructure:
    """Test waterfall configuration structure."""

    def test_config_keys_present(self, sample_revenue_bridge):
        """Test that config has all required keys."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        required_keys = [
            "xKey", "startKey", "endKey", "valueKey", "cumulativeKey",
            "showDataLabels", "showConnectors",
            "positiveColor", "negativeColor", "totalColor",
        ]

        for key in required_keys:
            assert key in config.config, f"Missing key: {key}"

    def test_data_item_structure(self, sample_revenue_bridge):
        """Test that each data item has correct structure."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        required_item_keys = ["step", "start", "end", "value", "cumulative", "fill", "is_total"]

        for item in config.data:
            for key in required_item_keys:
                assert key in item, f"Missing item key: {key}"


# --- JSON Serialization Tests ---


class TestJSONSerialization:
    """Test JSON export functionality."""

    def test_to_json_basic(self, sample_revenue_bridge, tmp_path):
        """Test basic JSON serialization."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
            title="Test Waterfall",
        )

        output_path = tmp_path / "waterfall.json"
        config.to_json(output_path)

        assert output_path.exists()

        # Verify JSON is valid
        with open(output_path) as f:
            data = json.load(f)

        assert data["type"] == "waterfall"
        assert data["title"] == "Test Waterfall"
        assert len(data["data"]) == 5

    def test_json_structure(self, sample_revenue_bridge):
        """Test JSON structure."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        json_str = json.dumps(config.to_dict())
        parsed = json.loads(json_str)

        assert "type" in parsed
        assert "data" in parsed
        assert "config" in parsed

    def test_json_preserves_calculations(self, sample_revenue_bridge, tmp_path):
        """Test that JSON preserves cumulative calculations."""
        builder = WaterfallChartBuilder()
        config = builder.build(
            data=sample_revenue_bridge,
            label_key="step",
            value_key="change",
            is_total_key="is_total",
        )

        output_path = tmp_path / "waterfall_calc.json"
        config.to_json(output_path)

        with open(output_path) as f:
            data = json.load(f)

        # Check cumulative values preserved
        for item in data["data"]:
            assert "cumulative" in item
            assert "start" in item
            assert "end" in item


# --- Convenience Function Tests ---


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""

    def test_waterfall_chart_function(self, sample_revenue_bridge):
        """Test waterfall_chart() convenience function."""
        config = waterfall_chart(
            data=sample_revenue_bridge,
            labels="step",
            values="change",
            is_total="is_total",
            title="Quick Waterfall",
        )

        assert config.chart_type == "waterfall"
        assert config.title == "Quick Waterfall"
        assert len(config.data) == 5

    def test_waterfall_chart_with_output(self, sample_revenue_bridge, tmp_path):
        """Test waterfall_chart() with file output."""
        output_path = tmp_path / "quick_waterfall.json"
        config = waterfall_chart(
            data=sample_revenue_bridge,
            labels="step",
            values="change",
            is_total="is_total",
            output_path=output_path,
        )

        assert output_path.exists()

    def test_convenience_function_kwargs(self, sample_revenue_bridge):
        """Test passing kwargs to convenience function."""
        config = waterfall_chart(
            data=sample_revenue_bridge,
            labels="step",
            values="change",
            is_total="is_total",
            show_data_labels=False,
            show_connectors=False,
        )

        assert config.config["showDataLabels"] is False
        assert config.config["showConnectors"] is False
