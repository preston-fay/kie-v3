"""
Tests for ScatterPlotBuilder

Tests cover:
- Basic scatter plots
- Multi-category scatter plots with color coding
- Point sizes
- Outlier handling
- Large datasets
- Empty data edge cases
- Axis labeling
- KDS color compliance
- JSON serialization
- Convenience functions
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from kie.brand.colors import KDSColors
from kie.charts.builders.scatter import ScatterPlotBuilder, scatter_plot


# --- Fixtures ---


@pytest.fixture
def sample_data_simple():
    """Simple scatter plot data."""
    return pd.DataFrame({
        "price": [100, 120, 90, 110, 95, 130, 85, 105],
        "sales": [1200, 1050, 1350, 1180, 1280, 980, 1420, 1150],
    })


@pytest.fixture
def sample_data_with_categories():
    """Scatter plot data with categories."""
    return pd.DataFrame({
        "price": [100, 120, 90, 110, 95, 130, 85, 105, 125, 80],
        "sales": [1200, 1050, 1350, 1180, 1280, 980, 1420, 1150, 1100, 1380],
        "region": ["North", "North", "South", "South", "East", "East", "West", "West", "North", "South"],
    })


@pytest.fixture
def sample_data_outliers():
    """Data with outliers."""
    return pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 100],  # 100 is outlier
        "y": [10, 20, 30, 40, 50, 500],  # 500 is outlier
    })


@pytest.fixture
def sample_data_zeros():
    """Data with zero values."""
    return pd.DataFrame({
        "x": [0, 1, 2, 3, 0],
        "y": [10, 0, 20, 30, 0],
    })


@pytest.fixture
def sample_data_negatives():
    """Data with negative values."""
    return pd.DataFrame({
        "temperature": [-10, -5, 0, 5, 10, 15],
        "energy_usage": [850, 780, 650, 520, 480, 450],
    })


# --- Basic Functionality Tests ---


class TestBasicScatter:
    """Test basic scatter plot generation."""

    def test_simple_scatter(self, sample_data_simple):
        """Test basic scatter plot with two variables."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
            title="Price vs Sales",
        )

        assert config.chart_type == "scatter"
        assert len(config.data) == 8
        assert config.title == "Price vs Sales"
        assert config.config["xAxis"]["dataKey"] == "price"
        assert config.config["yAxis"]["dataKey"] == "sales"

    def test_scatter_with_categories(self, sample_data_with_categories):
        """Test scatter plot with category-based coloring."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_with_categories,
            x_key="price",
            y_key="sales",
            category_key="region",
            title="Price vs Sales by Region",
        )

        assert len(config.data) == 10
        # Each point should have a fill color assigned
        for point in config.data:
            assert "fill" in point
            assert point["fill"] in KDSColors.CHART_PALETTE

    def test_list_of_dicts_input(self):
        """Test scatter plot with list of dicts input."""
        data = [
            {"x": 1, "y": 10},
            {"x": 2, "y": 20},
            {"x": 3, "y": 15},
        ]
        builder = ScatterPlotBuilder()
        config = builder.build(data=data, x_key="x", y_key="y")

        assert len(config.data) == 3
        assert config.data[0]["x"] == 1
        assert config.data[0]["y"] == 10

    def test_scatter_config_structure(self, sample_data_simple):
        """Test scatter config has correct structure."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        assert "scatter" in config.config
        assert config.config["scatter"]["dataKey"] == "sales"
        assert config.config["scatter"]["shape"] == "circle"
        assert config.config["scatter"]["r"] == 6  # default size


# --- Point Size Tests ---


class TestPointSizing:
    """Test point size configuration."""

    def test_default_point_size(self, sample_data_simple):
        """Test default point size."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        assert config.config["scatter"]["r"] == 6

    def test_custom_point_size(self, sample_data_simple):
        """Test custom point size."""
        builder = ScatterPlotBuilder(point_size=10)
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        assert config.config["scatter"]["r"] == 10

    def test_small_point_size(self, sample_data_simple):
        """Test small point size."""
        builder = ScatterPlotBuilder(point_size=3)
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        assert config.config["scatter"]["r"] == 3

    def test_large_point_size(self, sample_data_simple):
        """Test large point size."""
        builder = ScatterPlotBuilder(point_size=12)
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        assert config.config["scatter"]["r"] == 12


# --- Category Tests ---


class TestCategoryHandling:
    """Test category-based color coding."""

    def test_no_category_single_color(self, sample_data_simple):
        """Test that without categories, all points get same color."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        # All points should have same fill color
        first_color = config.data[0]["fill"]
        assert all(point["fill"] == first_color for point in config.data)

    def test_category_color_mapping(self, sample_data_with_categories):
        """Test that categories get distinct colors."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_with_categories,
            x_key="price",
            y_key="sales",
            category_key="region",
        )

        # Group points by region
        region_colors = {}
        for point in config.data:
            region = point["region"]
            color = point["fill"]
            if region not in region_colors:
                region_colors[region] = color
            else:
                # All points in same region should have same color
                assert region_colors[region] == color

        # Should have 4 distinct regions
        assert len(region_colors) == 4

    def test_category_uses_kds_colors(self, sample_data_with_categories):
        """Test that category colors come from KDS palette."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_with_categories,
            x_key="price",
            y_key="sales",
            category_key="region",
        )

        for point in config.data:
            assert point["fill"] in KDSColors.CHART_PALETTE

    def test_many_categories(self):
        """Test handling many categories (more than palette colors)."""
        data = pd.DataFrame({
            "x": list(range(15)),
            "y": list(range(15)),
            "cat": [f"Category_{i}" for i in range(15)],
        })
        builder = ScatterPlotBuilder()
        config = builder.build(data=data, x_key="x", y_key="y", category_key="cat")

        # Should still assign colors (cycling through palette)
        for point in config.data:
            assert "fill" in point
            assert point["fill"] in KDSColors.CHART_PALETTE


# --- Color Tests ---


class TestScatterColors:
    """Test color assignment and KDS compliance."""

    def test_default_single_color(self, sample_data_simple):
        """Test default color is Kearney Purple."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        # Default should be Kearney Purple (index 9)
        assert config.data[0]["fill"] == KDSColors.CHART_PALETTE[9]

    def test_custom_colors_single_series(self, sample_data_simple):
        """Test custom color for single series."""
        custom_color = "#D2D2D2"
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
            colors=[custom_color],
        )

        assert config.data[0]["fill"] == custom_color

    def test_custom_colors_categories(self, sample_data_with_categories):
        """Test custom colors for categories."""
        custom_colors = ["#D2D2D2", "#A5A6A5", "#787878", "#4B4B4B"]
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_with_categories,
            x_key="price",
            y_key="sales",
            category_key="region",
            colors=custom_colors,
        )

        # All colors should be from custom list
        used_colors = {point["fill"] for point in config.data}
        assert used_colors.issubset(set(custom_colors))

    def test_no_green_colors(self, sample_data_with_categories):
        """Test that KDS colors never include green."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_with_categories,
            x_key="price",
            y_key="sales",
            category_key="region",
        )

        for point in config.data:
            color = point["fill"].lower()
            # Check for common green hex patterns
            assert not color.startswith("#0") or "f" in color or "a" in color or "d" in color
            assert color not in ["#00ff00", "#008000", "#90ee90", "#00ff7f"]


# --- Axis Configuration Tests ---


class TestAxisConfiguration:
    """Test axis labeling and configuration."""

    def test_axis_labels_default(self, sample_data_simple):
        """Test that axis labels are created from column names."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        x_label = config.config["xAxis"]["label"]["value"]
        y_label = config.config["yAxis"]["label"]["value"]

        assert x_label == "Price"
        assert y_label == "Sales"

    def test_axis_labels_with_underscores(self):
        """Test that underscores in column names are replaced."""
        data = pd.DataFrame({
            "customer_age": [25, 30, 35],
            "lifetime_value": [1000, 2000, 1500],
        })
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=data,
            x_key="customer_age",
            y_key="lifetime_value",
        )

        x_label = config.config["xAxis"]["label"]["value"]
        y_label = config.config["yAxis"]["label"]["value"]

        assert x_label == "Customer Age"
        assert y_label == "Lifetime Value"

    def test_y_axis_label_rotation(self, sample_data_simple):
        """Test that y-axis label is rotated."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        assert config.config["yAxis"]["label"]["angle"] == -90
        assert config.config["yAxis"]["label"]["position"] == "left"


# --- Edge Cases Tests ---


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        builder = ScatterPlotBuilder()

        config = builder.build(
            data=empty_df,
            x_key="x",
            y_key="y",
        )

        assert len(config.data) == 0

    def test_single_point(self):
        """Test scatter plot with single data point."""
        single_point = pd.DataFrame({
            "x": [100],
            "y": [200],
        })
        builder = ScatterPlotBuilder()
        config = builder.build(data=single_point, x_key="x", y_key="y")

        assert len(config.data) == 1
        assert config.data[0]["x"] == 100
        assert config.data[0]["y"] == 200

    def test_two_points(self):
        """Test scatter plot with two points."""
        two_points = pd.DataFrame({
            "x": [1, 2],
            "y": [10, 20],
        })
        builder = ScatterPlotBuilder()
        config = builder.build(data=two_points, x_key="x", y_key="y")

        assert len(config.data) == 2

    def test_zero_values(self, sample_data_zeros):
        """Test scatter plot with zero values."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_zeros,
            x_key="x",
            y_key="y",
        )

        assert len(config.data) == 5
        # Check zeros are preserved
        zero_x_points = [p for p in config.data if p["x"] == 0]
        assert len(zero_x_points) == 2
        zero_y_points = [p for p in config.data if p["y"] == 0]
        assert len(zero_y_points) == 2

    def test_negative_values(self, sample_data_negatives):
        """Test scatter plot with negative values."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_negatives,
            x_key="temperature",
            y_key="energy_usage",
        )

        assert len(config.data) == 6
        # Check negative values preserved
        negative_temp = [p for p in config.data if p["temperature"] < 0]
        assert len(negative_temp) == 2

    def test_outliers(self, sample_data_outliers):
        """Test scatter plot with outliers."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_outliers,
            x_key="x",
            y_key="y",
            title="Data with Outliers",
        )

        assert len(config.data) == 6
        # Outliers should be included
        assert any(p["x"] == 100 for p in config.data)
        assert any(p["y"] == 500 for p in config.data)

    def test_large_dataset(self):
        """Test scatter plot with large dataset."""
        large_data = pd.DataFrame({
            "x": list(range(1000)),
            "y": [i * 2 + 100 for i in range(1000)],
        })
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=large_data,
            x_key="x",
            y_key="y",
        )

        assert len(config.data) == 1000

    def test_duplicate_points(self):
        """Test scatter plot with duplicate points."""
        duplicate_data = pd.DataFrame({
            "x": [1, 1, 2, 2, 3],
            "y": [10, 10, 20, 20, 30],
        })
        builder = ScatterPlotBuilder()
        config = builder.build(data=duplicate_data, x_key="x", y_key="y")

        # Duplicates should be preserved
        assert len(config.data) == 5

    def test_special_characters_in_columns(self):
        """Test handling of special characters in column names."""
        data = pd.DataFrame({
            "Price ($)": [100, 120, 90],
            "Sales (Units)": [1200, 1050, 1350],
        })
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=data,
            x_key="Price ($)",
            y_key="Sales (Units)",
        )

        assert config.config["xAxis"]["dataKey"] == "Price ($)"
        assert config.config["yAxis"]["dataKey"] == "Sales (Units)"


# --- KDS Compliance Tests ---


class TestKDSCompliance:
    """Test Kearney Design System compliance."""

    def test_no_gridlines(self, sample_data_simple):
        """Test that gridlines are disabled (KDS requirement)."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        assert config.config["gridLines"] is False

    def test_font_family(self, sample_data_simple):
        """Test KDS font family."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        assert "Inter" in config.config["fontFamily"]

    def test_interactive_enabled(self, sample_data_simple):
        """Test that charts are interactive."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        assert config.config["interactive"] is True

    def test_tooltip_present(self, sample_data_simple):
        """Test that tooltip is configured."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        assert config.config["tooltip"] is not None


# --- JSON Serialization Tests ---


class TestJSONSerialization:
    """Test JSON export functionality."""

    def test_to_json_basic(self, sample_data_simple, tmp_path):
        """Test basic JSON serialization."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
            title="Test Scatter",
        )

        output_path = tmp_path / "scatter.json"
        config.to_json(output_path)

        assert output_path.exists()

        # Verify JSON is valid
        with open(output_path) as f:
            data = json.load(f)

        assert data["type"] == "scatter"
        assert data["title"] == "Test Scatter"
        assert len(data["data"]) == 8

    def test_json_structure(self, sample_data_simple):
        """Test JSON structure matches Recharts schema."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_simple,
            x_key="price",
            y_key="sales",
        )

        json_str = json.dumps(config.to_dict())
        parsed = json.loads(json_str)

        assert "type" in parsed
        assert "data" in parsed
        assert "config" in parsed
        assert "scatter" in parsed["config"]
        assert "xAxis" in parsed["config"]
        assert "yAxis" in parsed["config"]

    def test_json_preserves_fill_colors(self, sample_data_with_categories, tmp_path):
        """Test that JSON preserves fill colors for categorized data."""
        builder = ScatterPlotBuilder()
        config = builder.build(
            data=sample_data_with_categories,
            x_key="price",
            y_key="sales",
            category_key="region",
        )

        output_path = tmp_path / "scatter_categories.json"
        config.to_json(output_path)

        with open(output_path) as f:
            data = json.load(f)

        # Check all points have fill colors
        for point in data["data"]:
            assert "fill" in point
            assert point["fill"] in KDSColors.CHART_PALETTE


# --- Convenience Function Tests ---


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""

    def test_scatter_plot_function(self, sample_data_simple):
        """Test scatter_plot() convenience function."""
        config = scatter_plot(
            data=sample_data_simple,
            x="price",
            y="sales",
            title="Quick Scatter",
        )

        assert config.chart_type == "scatter"
        assert config.title == "Quick Scatter"
        assert len(config.data) == 8

    def test_scatter_plot_with_output(self, sample_data_simple, tmp_path):
        """Test scatter_plot() with file output."""
        output_path = tmp_path / "quick_scatter.json"
        config = scatter_plot(
            data=sample_data_simple,
            x="price",
            y="sales",
            output_path=output_path,
        )

        assert output_path.exists()

    def test_scatter_plot_with_category(self, sample_data_with_categories):
        """Test scatter_plot() with category."""
        config = scatter_plot(
            data=sample_data_with_categories,
            x="price",
            y="sales",
            category="region",
            title="Price vs Sales by Region",
        )

        assert len(config.data) == 10
        # Check categories were applied
        for point in config.data:
            assert "fill" in point

    def test_convenience_function_kwargs(self, sample_data_simple):
        """Test passing kwargs to convenience function."""
        config = scatter_plot(
            data=sample_data_simple,
            x="price",
            y="sales",
            point_size=10,
            show_legend=False,
        )

        assert config.config["scatter"]["r"] == 10
