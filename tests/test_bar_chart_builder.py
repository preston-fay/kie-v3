"""
Tests for BarChartBuilder

Comprehensive test suite covering:
- Basic bar charts
- Grouped and stacked bars
- Horizontal bars
- Empty data handling
- Invalid column handling
- Color handling
- KDS compliance
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json

from kie.charts.builders.bar import BarChartBuilder, bar_chart, horizontal_bar_chart
from kie.base import RechartsConfig
from kie.brand.colors import KDSColors


class TestBarChartBuilderBasics:
    """Test basic bar chart generation."""

    def test_basic_bar_chart(self):
        """Test basic single-series bar chart."""
        data = pd.DataFrame({
            'region': ['North', 'South', 'East', 'West'],
            'revenue': [1200000, 980000, 1450000, 1100000]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='region', y_keys='revenue', title='Revenue by Region')

        assert config.chart_type == 'bar'
        assert len(config.data) == 4
        assert config.title == 'Revenue by Region'
        assert config.data[0]['Region'] == 'North'
        assert config.data[0]['Revenue'] == 1200000

    def test_bar_chart_with_list_of_dicts(self):
        """Test bar chart with list of dicts input."""
        data = [
            {'category': 'A', 'value': 100},
            {'category': 'B', 'value': 200},
            {'category': 'C', 'value': 150}
        ]

        builder = BarChartBuilder()
        config = builder.build(data, x_key='category', y_keys='value')

        assert config.chart_type == 'bar'
        assert len(config.data) == 3
        assert config.data[1]['Value'] == 200

    def test_multi_series_bar_chart(self):
        """Test bar chart with multiple series (grouped bars)."""
        data = pd.DataFrame({
            'quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
            'revenue': [1000, 1200, 1100, 1500],
            'cost': [600, 700, 650, 800]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='quarter', y_keys=['revenue', 'cost'], title='Revenue vs Cost')

        assert config.chart_type == 'bar'
        assert len(config.data) == 4
        assert 'Revenue' in config.data[0]
        assert 'Cost' in config.data[0]

        # Check that two bars are configured
        bars = config.config.get('bars', [])
        assert len(bars) == 2
        assert bars[0]['dataKey'] == 'Revenue'
        assert bars[1]['dataKey'] == 'Cost'


class TestBarChartLayouts:
    """Test different bar chart layouts."""

    def test_horizontal_layout(self):
        """Test horizontal (vertical bars) layout."""
        data = pd.DataFrame({
            'product': ['A', 'B', 'C'],
            'sales': [100, 200, 150]
        })

        builder = BarChartBuilder(layout='horizontal')
        config = builder.build(data, x_key='product', y_keys='sales')

        assert config.config['layout'] == 'horizontal'

        # Check bar radius for vertical bars (top corners rounded)
        bars = config.config['bars']
        assert bars[0]['radius'] == [4, 4, 0, 0]

    def test_vertical_layout(self):
        """Test vertical (horizontal bars) layout."""
        data = pd.DataFrame({
            'product': ['A', 'B', 'C'],
            'sales': [100, 200, 150]
        })

        builder = BarChartBuilder(layout='vertical')
        config = builder.build(data, x_key='product', y_keys='sales')

        assert config.config['layout'] == 'vertical'

        # Check bar radius for horizontal bars (right corners rounded)
        bars = config.config['bars']
        assert bars[0]['radius'] == [0, 4, 4, 0]

    def test_horizontal_bar_chart_convenience(self):
        """Test horizontal_bar_chart convenience function."""
        data = pd.DataFrame({
            'item': ['X', 'Y', 'Z'],
            'value': [50, 75, 100]
        })

        config = horizontal_bar_chart(data, x='item', y='value', title='Test')

        assert config.config['layout'] == 'vertical'
        assert config.title == 'Test'


class TestStackedBars:
    """Test stacked bar charts."""

    def test_stacked_bar_chart(self):
        """Test stacked bar chart generation."""
        data = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar'],
            'product_a': [100, 120, 110],
            'product_b': [80, 90, 85]
        })

        builder = BarChartBuilder(stacked=True)
        config = builder.build(data, x_key='month', y_keys=['product_a', 'product_b'])

        assert config.chart_type == 'bar'

        # Stacked charts should have legend
        assert config.config['legend'] is not None

    def test_build_stacked_method(self):
        """Test build_stacked convenience method."""
        data = pd.DataFrame({
            'category': ['A', 'B'],
            'value1': [10, 20],
            'value2': [15, 25]
        })

        builder = BarChartBuilder()
        config = builder.build_stacked(data, x_key='category', y_keys=['value1', 'value2'], title='Stacked')

        assert config.title == 'Stacked'
        assert config.config['legend'] is not None


class TestGroupedBars:
    """Test grouped bar charts."""

    def test_grouped_bar_chart(self):
        """Test grouped bar chart (multiple series side by side)."""
        data = pd.DataFrame({
            'region': ['North', 'South'],
            'q1': [100, 120],
            'q2': [110, 130],
            'q3': [120, 140]
        })

        builder = BarChartBuilder()
        config = builder.build_grouped(data, x_key='region', y_keys=['q1', 'q2', 'q3'], title='Quarterly Sales')

        assert config.chart_type == 'bar'
        bars = config.config['bars']
        assert len(bars) == 3


class TestColorHandling:
    """Test color assignment and validation."""

    def test_default_kds_colors(self):
        """Test that default colors come from KDS palette."""
        data = pd.DataFrame({
            'cat': ['A', 'B', 'C'],
            'val': [10, 20, 30]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='cat', y_keys='val')

        bars = config.config['bars']
        bar_color = bars[0]['fill']

        # Should be first color in KDS palette
        assert bar_color == KDSColors.CHART_PALETTE[0]

    def test_multiple_series_colors(self):
        """Test that multiple series get different KDS colors."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y1': [10, 20],
            'y2': [15, 25],
            'y3': [12, 22]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys=['y1', 'y2', 'y3'])

        bars = config.config['bars']
        colors = [bar['fill'] for bar in bars]

        # Should get first 3 colors from palette
        assert colors[0] == KDSColors.CHART_PALETTE[0]
        assert colors[1] == KDSColors.CHART_PALETTE[1]
        assert colors[2] == KDSColors.CHART_PALETTE[2]

        # All colors should be unique
        assert len(set(colors)) == 3

    def test_custom_colors(self):
        """Test custom color assignment."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        custom_color = '#7823DC'  # Kearney Purple
        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y', colors=[custom_color])

        bars = config.config['bars']
        assert bars[0]['fill'] == custom_color

    def test_insufficient_custom_colors(self):
        """Test that KDS colors extend insufficient custom colors."""
        data = pd.DataFrame({
            'x': ['A'],
            'y1': [10],
            'y2': [20],
            'y3': [30]
        })

        # Only provide 1 custom color for 3 series
        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys=['y1', 'y2', 'y3'], colors=['#7823DC'])

        bars = config.config['bars']
        assert bars[0]['fill'] == '#7823DC'
        # Remaining should come from KDS palette
        assert bars[1]['fill'] in KDSColors.CHART_PALETTE
        assert bars[2]['fill'] in KDSColors.CHART_PALETTE


class TestDataLabels:
    """Test data label configuration."""

    def test_data_labels_enabled(self):
        """Test that data labels are configured when enabled."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = BarChartBuilder(show_data_labels=True)
        config = builder.build(data, x_key='x', y_keys='y')

        bars = config.config['bars']
        assert bars[0]['label'] is not None
        assert bars[0]['label']['position'] == 'top'

    def test_data_labels_disabled(self):
        """Test that data labels are not configured when disabled."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = BarChartBuilder(show_data_labels=False)
        config = builder.build(data, x_key='x', y_keys='y')

        bars = config.config['bars']
        # When disabled, label key should not be present (exclude_none=True)
        assert 'label' not in bars[0]

    def test_data_label_position_horizontal(self):
        """Test data label position for horizontal layout (vertical bars)."""
        data = pd.DataFrame({'x': ['A'], 'y': [10]})

        builder = BarChartBuilder(layout='horizontal', show_data_labels=True)
        config = builder.build(data, x_key='x', y_keys='y')

        bars = config.config['bars']
        assert bars[0]['label']['position'] == 'top'

    def test_data_label_position_vertical(self):
        """Test data label position for vertical layout (horizontal bars)."""
        data = pd.DataFrame({'x': ['A'], 'y': [10]})

        builder = BarChartBuilder(layout='vertical', show_data_labels=True)
        config = builder.build(data, x_key='x', y_keys='y')

        bars = config.config['bars']
        assert bars[0]['label']['position'] == 'right'


class TestLegend:
    """Test legend configuration."""

    def test_legend_single_series(self):
        """Test that legend is not shown for single series."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = BarChartBuilder(show_legend=True)
        config = builder.build(data, x_key='x', y_keys='y')

        # Legend should not be present for single series (exclude_none=True)
        assert 'legend' not in config.config

    def test_legend_multi_series(self):
        """Test that legend is shown for multiple series."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y1': [10, 20],
            'y2': [15, 25]
        })

        builder = BarChartBuilder(show_legend=True)
        config = builder.build(data, x_key='x', y_keys=['y1', 'y2'])

        assert config.config['legend'] is not None

    def test_legend_disabled(self):
        """Test that legend can be disabled even for multi-series."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y1': [10, 20],
            'y2': [15, 25]
        })

        builder = BarChartBuilder(show_legend=False)
        config = builder.build(data, x_key='x', y_keys=['y1', 'y2'])

        # Legend should not be present when disabled (exclude_none=True)
        assert 'legend' not in config.config


class TestKDSCompliance:
    """Test KDS design system compliance."""

    def test_no_gridlines(self):
        """Test that gridLines is always False (KDS requirement)."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert config.config['gridLines'] is False

    def test_font_family(self):
        """Test that Inter font is used (KDS requirement)."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        font_family = config.config.get('fontFamily', '')
        assert 'Inter' in font_family

    def test_no_axis_lines(self):
        """Test that axis lines are disabled (KDS requirement)."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert config.config['xAxis']['axisLine'] is False
        assert config.config['yAxis']['axisLine'] is False
        assert config.config['xAxis']['tickLine'] is False
        assert config.config['yAxis']['tickLine'] is False

    def test_rounded_corners(self):
        """Test that bars have rounded corners (KDS styling)."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        bars = config.config['bars']
        # Should have radius defined
        assert bars[0]['radius'] is not None
        assert len(bars[0]['radius']) == 4


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        data = pd.DataFrame()

        builder = BarChartBuilder()
        # Should not crash - check behavior
        config = builder.build(data, x_key='x', y_keys='y')

        assert config.data == []

    def test_single_data_point(self):
        """Test chart with single data point."""
        data = pd.DataFrame({
            'x': ['A'],
            'y': [100]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert len(config.data) == 1
        assert config.data[0]['Y'] == 100

    def test_missing_column_handled(self):
        """Test that missing columns are handled gracefully."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = BarChartBuilder()
        # Reference non-existent column
        config = builder.build(data, x_key='x', y_keys='nonexistent')

        # Should still build config (column will be missing in data)
        assert config.chart_type == 'bar'

    def test_zero_values(self):
        """Test handling of zero values."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [0, 10, 0]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert len(config.data) == 3
        assert config.data[0]['Y'] == 0

    def test_negative_values(self):
        """Test handling of negative values."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [-10, 20, -5]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert config.data[0]['Y'] == -10
        assert config.data[2]['Y'] == -5

    def test_large_dataset(self):
        """Test handling of large dataset."""
        data = pd.DataFrame({
            'x': [f'Item{i}' for i in range(100)],
            'y': list(range(100))
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert len(config.data) == 100


class TestJSONSerialization:
    """Test JSON output and serialization."""

    def test_to_json_string(self):
        """Test conversion to JSON string."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = BarChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y', title='Test Chart')

        json_str = config.to_json()

        # Parse to verify valid JSON
        parsed = json.loads(json_str)
        assert parsed['type'] == 'bar'
        assert parsed['title'] == 'Test Chart'
        assert len(parsed['data']) == 2

    def test_to_json_file(self):
        """Test saving to JSON file."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'charts' / 'test_chart.json'

            builder = BarChartBuilder()
            config = builder.build(data, x_key='x', y_keys='y')
            config.to_json(output_path)

            assert output_path.exists()

            # Verify content
            with open(output_path) as f:
                parsed = json.load(f)

            assert parsed['type'] == 'bar'
            assert len(parsed['data']) == 2

    def test_convenience_function_with_output_path(self):
        """Test bar_chart convenience function with output path."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.json'

            config = bar_chart(data, x='x', y='y', title='Test', output_path=output_path)

            assert output_path.exists()
            assert config.title == 'Test'


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_bar_chart_function(self):
        """Test bar_chart convenience function."""
        data = pd.DataFrame({
            'region': ['A', 'B', 'C'],
            'sales': [100, 200, 150]
        })

        config = bar_chart(data, x='region', y='sales', title='Sales by Region')

        assert config.chart_type == 'bar'
        assert config.title == 'Sales by Region'
        assert len(config.data) == 3

    def test_bar_chart_with_kwargs(self):
        """Test bar_chart with additional kwargs."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        config = bar_chart(data, x='x', y='y', layout='vertical', stacked=False)

        assert config.config['layout'] == 'vertical'
