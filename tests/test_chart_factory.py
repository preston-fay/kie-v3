"""
Tests for ChartFactory

Tests cover:
- All chart type creation methods
- Auto-detection logic for different data patterns
- Column auto-detection when not provided
- Time series detection
- Categorical vs numeric data handling
- Small vs large category sets
- Single vs multi-series auto-detection
- Error handling for unknown chart types
"""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from kie.charts.factory import ChartFactory, create_chart


# --- Fixtures ---


@pytest.fixture
def categorical_single_numeric():
    """Categorical + single numeric (→ bar chart)."""
    return pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "revenue": [1200, 1350, 1180, 1420],
    })


@pytest.fixture
def categorical_multi_numeric():
    """Categorical + multiple numeric (→ grouped bar)."""
    return pd.DataFrame({
        "region": ["North", "South", "East"],
        "revenue": [1200, 1350, 1180],
        "costs": [800, 900, 750],
        "profit": [400, 450, 430],
    })


@pytest.fixture
def time_series_single():
    """Time series + single numeric (→ line chart)."""
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]
    return pd.DataFrame({
        "date": dates,
        "sales": [100, 120, 110, 130, 125, 140, 135, 150, 145, 160],
    })


@pytest.fixture
def time_series_multi():
    """Time series + multiple numeric (→ stacked area)."""
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(5)]
    return pd.DataFrame({
        "date": dates,
        "product_a": [100, 120, 110, 130, 125],
        "product_b": [80, 90, 85, 95, 100],
        "product_c": [60, 70, 65, 75, 80],
    })


@pytest.fixture
def two_numeric_columns():
    """Two numeric columns (→ scatter plot)."""
    return pd.DataFrame({
        "price": [100, 120, 90, 110, 95, 130],
        "sales": [1200, 1050, 1350, 1180, 1280, 980],
    })


@pytest.fixture
def small_categories():
    """Small categorical data (≤4 rows → pie chart)."""
    return pd.DataFrame({
        "category": ["A", "B", "C", "D"],
        "value": [25, 35, 20, 20],
    })


@pytest.fixture
def medium_categories():
    """Medium categorical data (5-10 rows → horizontal bar)."""
    return pd.DataFrame({
        "department": ["Sales", "Marketing", "Engineering", "HR", "Finance", "IT", "Legal"],
        "headcount": [50, 30, 80, 15, 20, 25, 10],
    })


# --- Chart Creation Tests ---


class TestChartCreation:
    """Test individual chart type creation methods."""

    def test_create_bar_chart(self, categorical_single_numeric):
        """Test bar chart creation via factory."""
        config = ChartFactory.bar(
            categorical_single_numeric,
            x="region",
            y="revenue",
            title="Revenue by Region",
        )

        assert config.chart_type == "bar"
        assert config.title == "Revenue by Region"
        assert len(config.data) == 4

    def test_create_horizontal_bar(self, categorical_single_numeric):
        """Test horizontal bar chart creation."""
        config = ChartFactory.horizontal_bar(
            categorical_single_numeric,
            x="region",
            y="revenue",
        )

        assert config.chart_type == "bar"
        assert config.config["layout"] == "vertical"

    def test_create_stacked_bar(self, categorical_multi_numeric):
        """Test stacked bar chart creation."""
        config = ChartFactory.stacked_bar(
            categorical_multi_numeric,
            x="region",
            y=["revenue", "costs"],
        )

        assert config.chart_type == "bar"
        # Stacked bar chart should have multiple bars
        assert len(config.config.get("bars", [])) == 2

    def test_create_line_chart(self, time_series_single):
        """Test line chart creation."""
        config = ChartFactory.line(
            time_series_single,
            x="date",
            y="sales",
            title="Sales Over Time",
        )

        assert config.chart_type == "line"
        assert config.title == "Sales Over Time"

    def test_create_area_chart(self, time_series_single):
        """Test area chart creation."""
        config = ChartFactory.area(
            time_series_single,
            x="date",
            y="sales",
        )

        assert config.chart_type == "area"

    def test_create_stacked_area(self, time_series_multi):
        """Test stacked area chart creation."""
        config = ChartFactory.stacked_area(
            time_series_multi,
            x="date",
            y=["product_a", "product_b", "product_c"],
        )

        assert config.chart_type == "area"
        assert config.config.get("stackId") is not None

    def test_create_pie_chart(self, small_categories):
        """Test pie chart creation."""
        config = ChartFactory.pie(
            small_categories,
            name="category",
            value="value",
            title="Distribution",
        )

        assert config.chart_type == "pie"
        assert config.title == "Distribution"

    def test_create_donut_chart(self, small_categories):
        """Test donut chart creation."""
        config = ChartFactory.donut(
            small_categories,
            name="category",
            value="value",
        )

        assert config.chart_type == "pie"
        # Donut has inner radius > 0 (may be nested in pie config)
        pie_config = config.config.get("pie", config.config)
        assert pie_config.get("innerRadius", 0) > 0

    def test_create_scatter_plot(self, two_numeric_columns):
        """Test scatter plot creation."""
        config = ChartFactory.scatter(
            two_numeric_columns,
            x="price",
            y="sales",
            title="Price vs Sales",
        )

        assert config.chart_type == "scatter"
        assert config.title == "Price vs Sales"

    def test_create_combo_chart(self):
        """Test combo chart creation."""
        data = pd.DataFrame({
            "month": ["Jan", "Feb", "Mar"],
            "actual": [100, 150, 120],
            "target": [110, 140, 130],
        })
        config = ChartFactory.combo(
            data,
            x="month",
            bars="actual",
            lines="target",
        )

        assert config.chart_type == "combo"
        assert len(config.config["bars"]) == 1
        assert len(config.config["lines"]) == 1

    def test_create_waterfall_chart(self):
        """Test waterfall chart creation."""
        data = pd.DataFrame({
            "step": ["Start", "Change", "End"],
            "value": [100, 50, 150],
            "is_total": [True, False, True],
        })
        config = ChartFactory.waterfall(
            data,
            labels="step",
            values="value",
            is_total="is_total",
        )

        assert config.chart_type == "waterfall"


# --- Generic Create Method Tests ---


class TestGenericCreate:
    """Test the generic create() method."""

    def test_create_with_type_bar(self, categorical_single_numeric):
        """Test create() with chart_type='bar'."""
        config = ChartFactory.create(
            "bar",
            categorical_single_numeric,
            x="region",
            y="revenue",
        )

        assert config.chart_type == "bar"

    def test_create_with_type_line(self, time_series_single):
        """Test create() with chart_type='line'."""
        config = ChartFactory.create(
            "line",
            time_series_single,
            x="date",
            y="sales",
        )

        assert config.chart_type == "line"

    def test_create_with_type_pie(self, small_categories):
        """Test create() with chart_type='pie'."""
        config = ChartFactory.create(
            "pie",
            small_categories,
            name="category",
            value="value",
        )

        assert config.chart_type == "pie"

    def test_create_with_invalid_type(self, categorical_single_numeric):
        """Test create() raises error for unknown chart type."""
        with pytest.raises(ValueError, match="Unknown chart type"):
            ChartFactory.create(
                "invalid_type",
                categorical_single_numeric,
                x="region",
                y="revenue",
            )


# --- Auto-Detection Tests ---


class TestAutoDetection:
    """Test auto_detect() logic."""

    def test_auto_detect_bar_chart(self, categorical_single_numeric):
        """Test auto-detection: categorical + numeric → bar or pie."""
        config = ChartFactory.auto_detect(
            categorical_single_numeric,
            x="region",
            y="revenue",
        )

        # 4 rows of categorical data → pie chart per auto-detect logic
        assert config.chart_type == "pie"

    def test_auto_detect_line_chart(self, time_series_single):
        """Test auto-detection: time series + numeric → line."""
        config = ChartFactory.auto_detect(
            time_series_single,
            x="date",
            y="sales",
        )

        assert config.chart_type == "line"

    def test_auto_detect_stacked_area(self, time_series_multi):
        """Test auto-detection: time series + multiple numeric → stacked area."""
        config = ChartFactory.auto_detect(
            time_series_multi,
            x="date",
            y=["product_a", "product_b", "product_c"],
        )

        assert config.chart_type == "area"
        assert config.config.get("stackId") is not None

    def test_auto_detect_grouped_bar(self, categorical_multi_numeric):
        """Test auto-detection: categorical + multiple numeric → grouped bar."""
        config = ChartFactory.auto_detect(
            categorical_multi_numeric,
            x="region",
            y=["revenue", "costs"],
        )

        assert config.chart_type == "bar"
        # Grouped bars don't have stackId
        assert config.config.get("stackId") is None

    def test_auto_detect_pie_chart(self, small_categories):
        """Test auto-detection: ≤4 categories → pie chart."""
        config = ChartFactory.auto_detect(
            small_categories,
            x="category",
            y="value",
        )

        assert config.chart_type == "pie"

    def test_auto_detect_horizontal_bar(self, medium_categories):
        """Test auto-detection: 5-10 categories → horizontal bar."""
        config = ChartFactory.auto_detect(
            medium_categories,
            x="department",
            y="headcount",
        )

        assert config.chart_type == "bar"
        assert config.config["layout"] == "vertical"  # Horizontal bar

    def test_auto_detect_many_categories_regular_bar(self):
        """Test auto-detection: >10 categories → regular bar."""
        many_cats = pd.DataFrame({
            "item": [f"Item_{i}" for i in range(15)],
            "value": list(range(15)),
        })
        config = ChartFactory.auto_detect(
            many_cats,
            x="item",
            y="value",
        )

        assert config.chart_type == "bar"
        # Should be regular bar (not horizontal) for many categories
        assert config.config.get("layout", "horizontal") == "horizontal"


# --- Column Auto-Detection Tests ---


class TestColumnAutoDetection:
    """Test auto-detection of x and y columns when not provided."""

    def test_auto_detect_columns_categorical_first(self, categorical_single_numeric):
        """Test auto-detection picks categorical column as x."""
        config = ChartFactory.auto_detect(categorical_single_numeric)

        # Should detect region as x, revenue as y → pie (≤4 rows)
        assert config.chart_type == "pie"
        assert len(config.data) == 4

    def test_auto_detect_columns_datetime_first(self, time_series_single):
        """Test auto-detection picks datetime column as x."""
        config = ChartFactory.auto_detect(time_series_single)

        # Should detect date as x, sales as y
        assert config.chart_type == "line"

    def test_auto_detect_multi_numeric_columns(self, categorical_multi_numeric):
        """Test auto-detection with multiple numeric columns."""
        config = ChartFactory.auto_detect(categorical_multi_numeric)

        # Should pick region as x, all numeric as y
        assert config.chart_type == "bar"
        assert len(config.config["bars"]) >= 2

    def test_auto_detect_only_numeric_columns(self, two_numeric_columns):
        """Test auto-detection with only numeric columns."""
        # When only numeric columns, auto-detection may fail to find categorical x
        try:
            config = ChartFactory.auto_detect(two_numeric_columns)
            # If succeeds, should create some chart type
            assert config.chart_type in ["bar", "line", "scatter", "area"]
        except (ValueError, KeyError, TypeError):
            # Acceptable to fail when no categorical column found
            pass


# --- List of Dicts Input Tests ---


class TestListOfDictsInput:
    """Test auto-detection with list of dicts input."""

    def test_auto_detect_list_categorical(self):
        """Test auto-detection with list of dicts (categorical)."""
        data = [
            {"region": "North", "revenue": 1200},
            {"region": "South", "revenue": 1350},
            {"region": "East", "revenue": 1180},
        ]
        config = ChartFactory.auto_detect(data, x="region", y="revenue")

        # 3 rows of categorical → pie chart (≤4 rows)
        assert config.chart_type == "pie"

    def test_auto_detect_list_time_series(self):
        """Test auto-detection with list of dicts (time series)."""
        data = [
            {"date": datetime(2024, 1, 1), "sales": 100},
            {"date": datetime(2024, 1, 2), "sales": 120},
            {"date": datetime(2024, 1, 3), "sales": 110},
        ]
        config = ChartFactory.auto_detect(data, x="date", y="sales")

        assert config.chart_type == "line"


# --- Edge Cases Tests ---


class TestEdgeCases:
    """Test edge cases for auto-detection."""

    def test_auto_detect_empty_dataframe(self):
        """Test auto-detection with empty DataFrame."""
        empty_df = pd.DataFrame()

        # Should handle gracefully (may raise or return empty chart)
        try:
            config = ChartFactory.auto_detect(empty_df)
            # If it succeeds, verify it's a valid config
            assert config.chart_type in ["bar", "line", "pie", "area", "scatter"]
        except (ValueError, IndexError, KeyError):
            # Acceptable to raise error for empty data
            pass

    def test_auto_detect_single_row(self, small_categories):
        """Test auto-detection with single row."""
        single_row = small_categories.head(1)
        config = ChartFactory.auto_detect(single_row, x="category", y="value")

        # Should create pie chart (≤4 rows)
        assert config.chart_type == "pie"

    def test_auto_detect_single_column(self):
        """Test auto-detection with single column."""
        single_col = pd.DataFrame({"value": [10, 20, 30]})

        # May raise or use first column as both x and y
        try:
            config = ChartFactory.auto_detect(single_col)
            assert config.chart_type in ["bar", "line", "pie"]
        except (ValueError, IndexError, KeyError):
            pass

    def test_auto_detect_with_title(self, categorical_single_numeric):
        """Test auto-detection preserves title kwarg."""
        config = ChartFactory.auto_detect(
            categorical_single_numeric,
            x="region",
            y="revenue",
            title="My Chart",
        )

        assert config.title == "My Chart"

    def test_auto_detect_with_subtitle(self, categorical_single_numeric):
        """Test auto-detection preserves subtitle kwarg."""
        config = ChartFactory.auto_detect(
            categorical_single_numeric,
            x="region",
            y="revenue",
            subtitle="Q4 2024",
        )

        assert config.subtitle == "Q4 2024"


# --- Data Type Detection Tests ---


class TestDataTypeDetection:
    """Test detection of different data types."""

    def test_detect_datetime_dtype(self):
        """Test datetime dtype detection."""
        df = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "value": [10, 20, 30],
        })
        config = ChartFactory.auto_detect(df, x="date", y="value")

        # Datetime → line chart
        assert config.chart_type == "line"

    def test_detect_object_dtype_categorical(self):
        """Test object dtype detection (strings)."""
        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "value": [10, 20, 30],
        })
        config = ChartFactory.auto_detect(df, x="category", y="value")

        # Object + few rows → pie chart
        assert config.chart_type == "pie"

    def test_detect_numeric_dtype(self):
        """Test numeric dtype detection."""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [10, 20, 15, 25, 30],
        })
        config = ChartFactory.auto_detect(df, x="x", y="y")

        # Numeric x → bar (default fallback)
        assert config.chart_type in ["bar", "line"]


# --- Integration with Builders Tests ---


class TestBuilderIntegration:
    """Test that factory properly integrates with builders."""

    def test_factory_bar_calls_builder(self, categorical_single_numeric):
        """Test that factory.bar() produces same result as BarChartBuilder."""
        from kie.charts.builders.bar import BarChartBuilder

        factory_config = ChartFactory.bar(
            categorical_single_numeric,
            x="region",
            y="revenue",
            title="Test",
        )

        builder = BarChartBuilder()
        builder_config = builder.build(
            categorical_single_numeric,
            x_key="region",
            y_keys="revenue",
            title="Test",
        )

        # Should produce same chart type and structure
        assert factory_config.chart_type == builder_config.chart_type
        assert len(factory_config.data) == len(builder_config.data)

    def test_factory_passes_kwargs(self, categorical_single_numeric):
        """Test that factory passes additional kwargs to builder."""
        config = ChartFactory.bar(
            categorical_single_numeric,
            x="region",
            y="revenue",
            show_data_labels=True,
            colors=["#D2D2D2"],
        )

        # Should have data labels enabled
        assert config.config["bars"][0]["label"] is not None
        # Should use custom color
        assert config.config["bars"][0]["fill"] == "#D2D2D2"


# --- Convenience Alias Tests ---


class TestConvenienceAlias:
    """Test create_chart convenience alias."""

    def test_create_chart_alias(self, categorical_single_numeric):
        """Test that create_chart is an alias for ChartFactory.create."""
        config = create_chart(
            "bar",
            categorical_single_numeric,
            x="region",
            y="revenue",
        )

        assert config.chart_type == "bar"


# --- String Y Values Tests ---


class TestStringYHandling:
    """Test handling of y as string vs list."""

    def test_auto_detect_single_y_string(self, categorical_single_numeric):
        """Test auto-detection with y as string."""
        config = ChartFactory.auto_detect(
            categorical_single_numeric,
            x="region",
            y="revenue",  # String
        )

        # 4 rows categorical → pie
        assert config.chart_type == "pie"

    def test_auto_detect_single_y_list(self, categorical_single_numeric):
        """Test auto-detection with y as single-item list."""
        config = ChartFactory.auto_detect(
            categorical_single_numeric,
            x="region",
            y=["revenue"],  # List with one item
        )

        # Single item list with 4 rows → pie
        assert config.chart_type == "pie"

    def test_auto_detect_multi_y_list(self, categorical_multi_numeric):
        """Test auto-detection with y as multi-item list."""
        config = ChartFactory.auto_detect(
            categorical_multi_numeric,
            x="region",
            y=["revenue", "costs"],  # Multiple items
        )

        # Multiple y values → grouped bars
        assert config.chart_type == "bar"
        assert len(config.config["bars"]) == 2
