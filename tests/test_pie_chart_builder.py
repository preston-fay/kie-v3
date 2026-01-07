"""
Tests for PieChartBuilder and DonutChartBuilder

Comprehensive test suite covering:
- Basic pie charts
- Donut charts (hollow center)
- Small slices handling
- Empty data handling
- Single value handling
- Color handling
- Label and percentage display
- KDS compliance
- Legend configuration
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json

from kie.charts.builders.pie import PieChartBuilder, DonutChartBuilder, pie_chart, donut_chart
from kie.base import RechartsConfig
from kie.brand.colors import KDSColors


class TestPieChartBuilderBasics:
    """Test basic pie chart generation."""

    def test_basic_pie_chart(self):
        """Test basic pie chart generation."""
        data = pd.DataFrame({
            'category': ['Product A', 'Product B', 'Product C'],
            'sales': [4500, 3200, 2800]
        })

        builder = PieChartBuilder()
        config = builder.build(data, name_key='category', value_key='sales', title='Sales by Product')

        assert config.chart_type == 'pie'
        assert len(config.data) == 3
        assert config.title == 'Sales by Product'
        assert config.data[0]['category'] == 'Product A'
        assert config.data[0]['sales'] == 4500

    def test_pie_chart_with_list_of_dicts(self):
        """Test pie chart with list of dicts input."""
        data = [
            {'category': 'A', 'value': 100},
            {'category': 'B', 'value': 200},
            {'category': 'C', 'value': 150}
        ]

        builder = PieChartBuilder()
        config = builder.build(data, name_key='category', value_key='value')

        assert config.chart_type == 'pie'
        assert len(config.data) == 3
        assert config.data[1]['value'] == 200

    def test_pie_chart_with_subtitle(self):
        """Test pie chart with title and subtitle."""
        data = pd.DataFrame({
            'region': ['North', 'South'],
            'revenue': [1000000, 800000]
        })

        builder = PieChartBuilder()
        config = builder.build(
            data,
            name_key='region',
            value_key='revenue',
            title='Revenue Distribution',
            subtitle='Q3 2024'
        )

        assert config.title == 'Revenue Distribution'
        assert config.subtitle == 'Q3 2024'


class TestDonutChartBuilder:
    """Test donut chart (pie with hollow center)."""

    def test_basic_donut_chart(self):
        """Test basic donut chart generation."""
        data = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [100, 200, 150]
        })

        builder = DonutChartBuilder()
        config = builder.build(data, name_key='category', value_key='value', title='Donut Chart')

        assert config.chart_type == 'pie'
        # Donut has inner_radius > 0
        assert config.config['pie']['innerRadius'] == 40
        assert config.config['pie']['outerRadius'] == 80

    def test_donut_vs_pie_inner_radius(self):
        """Test that donut has inner radius while pie doesn't."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        pie_builder = PieChartBuilder()
        pie_config = pie_builder.build(data, name_key='x', value_key='y')

        donut_builder = DonutChartBuilder()
        donut_config = donut_builder.build(data, name_key='x', value_key='y')

        # Pie has innerRadius = 0
        assert pie_config.config['pie']['innerRadius'] == 0
        # Donut has innerRadius > 0
        assert donut_config.config['pie']['innerRadius'] == 40

    def test_custom_donut_radius(self):
        """Test custom inner and outer radius for donut."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = DonutChartBuilder(inner_radius=50, outer_radius=100)
        config = builder.build(data, name_key='x', value_key='y')

        assert config.config['pie']['innerRadius'] == 50
        assert config.config['pie']['outerRadius'] == 100


class TestPercentageCalculation:
    """Test percentage calculation and display."""

    def test_percentages_calculated(self):
        """Test that percentages are calculated correctly."""
        data = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [100, 200, 200]  # Total = 500
        })

        builder = PieChartBuilder(show_percentages=True)
        config = builder.build(data, name_key='category', value_key='value')

        # A: 100/500 = 20%
        assert config.data[0]['percentage'] == 20.0
        # B: 200/500 = 40%
        assert config.data[1]['percentage'] == 40.0
        # C: 200/500 = 40%
        assert config.data[2]['percentage'] == 40.0

    def test_percentages_sum_to_100(self):
        """Test that all percentages sum to approximately 100%."""
        data = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [33, 33, 34]
        })

        builder = PieChartBuilder(show_percentages=True)
        config = builder.build(data, name_key='category', value_key='value')

        total_percentage = sum(item['percentage'] for item in config.data)
        # Allow small rounding error
        assert 99.9 <= total_percentage <= 100.1

    def test_percentages_disabled(self):
        """Test that percentages are not calculated when disabled."""
        data = pd.DataFrame({
            'category': ['A', 'B'],
            'value': [100, 200]
        })

        builder = PieChartBuilder(show_percentages=False)
        config = builder.build(data, name_key='category', value_key='value')

        # Percentages should not be in data
        assert 'percentage' not in config.data[0]
        assert 'percentage' not in config.data[1]


class TestColorHandling:
    """Test color assignment and validation."""

    def test_default_kds_colors(self):
        """Test that default colors come from KDS palette."""
        data = pd.DataFrame({
            'cat': ['A', 'B', 'C'],
            'val': [10, 20, 30]
        })

        builder = PieChartBuilder()
        config = builder.build(data, name_key='cat', value_key='val')

        # Check that colors are assigned to data
        assert 'fill' in config.data[0]
        assert 'fill' in config.data[1]
        assert 'fill' in config.data[2]

        # Should use KDS palette
        assert config.data[0]['fill'] == KDSColors.CHART_PALETTE[0]
        assert config.data[1]['fill'] == KDSColors.CHART_PALETTE[1]
        assert config.data[2]['fill'] == KDSColors.CHART_PALETTE[2]

    def test_custom_colors(self):
        """Test custom color assignment."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 30]
        })

        custom_colors = ['#7823DC', '#9150E1', '#AF7DEB']
        builder = PieChartBuilder()
        config = builder.build(data, name_key='x', value_key='y', colors=custom_colors)

        assert config.data[0]['fill'] == '#7823DC'
        assert config.data[1]['fill'] == '#9150E1'
        assert config.data[2]['fill'] == '#AF7DEB'

    def test_insufficient_custom_colors(self):
        """Test that KDS colors extend insufficient custom colors."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C', 'D'],
            'y': [10, 20, 30, 40]
        })

        # Only provide 2 custom colors for 4 slices
        custom_colors = ['#7823DC', '#9150E1']
        builder = PieChartBuilder()
        config = builder.build(data, name_key='x', value_key='y', colors=custom_colors)

        # First two use custom colors
        assert config.data[0]['fill'] == '#7823DC'
        assert config.data[1]['fill'] == '#9150E1'
        # Remaining use KDS palette
        assert config.data[2]['fill'] in KDSColors.CHART_PALETTE
        assert config.data[3]['fill'] in KDSColors.CHART_PALETTE

    def test_color_cycling(self):
        """Test that colors cycle when more slices than colors."""
        data = pd.DataFrame({
            'x': [f'Item{i}' for i in range(12)],  # More than 10 KDS colors
            'y': [10] * 12
        })

        builder = PieChartBuilder()
        config = builder.build(data, name_key='x', value_key='y')

        # 11th item should cycle back to first color
        assert config.data[10]['fill'] == config.data[0]['fill']


class TestLabels:
    """Test label configuration."""

    def test_labels_enabled(self):
        """Test that labels are configured when enabled."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder(show_labels=True)
        config = builder.build(data, name_key='x', value_key='y')

        pie_config = config.config['pie']
        assert pie_config['label'] is not None
        assert pie_config['label']['position'] == 'outside'

    def test_labels_disabled(self):
        """Test that labels are not configured when disabled."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder(show_labels=False)
        config = builder.build(data, name_key='x', value_key='y')

        pie_config = config.config['pie']
        # When disabled, label should not be present (exclude_none=True)
        assert 'label' not in pie_config


class TestLegend:
    """Test legend configuration."""

    def test_legend_enabled(self):
        """Test that legend is shown when enabled."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 30]
        })

        builder = PieChartBuilder(show_legend=True)
        config = builder.build(data, name_key='x', value_key='y')

        assert config.config['legend'] is not None
        assert config.config['legend']['verticalAlign'] == 'bottom'
        assert config.config['legend']['align'] == 'center'

    def test_legend_disabled(self):
        """Test that legend can be disabled."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 30]
        })

        builder = PieChartBuilder(show_legend=False)
        config = builder.build(data, name_key='x', value_key='y')

        # Legend should be None when disabled (exclude_none removes it)
        assert 'legend' not in config.config


class TestKDSCompliance:
    """Test KDS design system compliance."""

    def test_no_gridlines(self):
        """Test that gridLines is always False (KDS requirement)."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder()
        config = builder.build(data, name_key='x', value_key='y')

        assert config.config['gridLines'] is False

    def test_font_family(self):
        """Test that Inter font is used (KDS requirement)."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder()
        config = builder.build(data, name_key='x', value_key='y')

        font_family = config.config.get('fontFamily', '')
        assert 'Inter' in font_family

    def test_interactive_enabled(self):
        """Test that interactive mode is enabled."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder()
        config = builder.build(data, name_key='x', value_key='y')

        assert config.config['interactive'] is True

    def test_padding_angle(self):
        """Test that slices have padding (KDS styling)."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder()
        config = builder.build(data, name_key='x', value_key='y')

        assert config.config['pie']['paddingAngle'] == 2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        data = pd.DataFrame()

        builder = PieChartBuilder()
        config = builder.build(data, name_key='x', value_key='y')

        assert config.data == []

    def test_single_slice(self):
        """Test pie chart with single slice (100%)."""
        data = pd.DataFrame({
            'category': ['Only One'],
            'value': [100]
        })

        builder = PieChartBuilder(show_percentages=True)
        config = builder.build(data, name_key='category', value_key='value')

        assert len(config.data) == 1
        assert config.data[0]['value'] == 100
        assert config.data[0]['percentage'] == 100.0

    def test_two_slices(self):
        """Test pie chart with two slices."""
        data = pd.DataFrame({
            'category': ['A', 'B'],
            'value': [60, 40]
        })

        builder = PieChartBuilder(show_percentages=True)
        config = builder.build(data, name_key='category', value_key='value')

        assert len(config.data) == 2
        assert config.data[0]['percentage'] == 60.0
        assert config.data[1]['percentage'] == 40.0

    def test_small_slices(self):
        """Test handling of very small slices."""
        data = pd.DataFrame({
            'category': ['Large', 'Tiny1', 'Tiny2'],
            'value': [1000, 1, 1]
        })

        builder = PieChartBuilder(show_percentages=True)
        config = builder.build(data, name_key='category', value_key='value')

        assert len(config.data) == 3
        # Large slice: 1000/1002 ≈ 99.8%
        assert config.data[0]['percentage'] > 99
        # Tiny slices: 1/1002 ≈ 0.1%
        assert config.data[1]['percentage'] < 1
        assert config.data[2]['percentage'] < 1

    def test_zero_values(self):
        """Test handling of zero values."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 0, 20]
        })

        builder = PieChartBuilder(show_percentages=True)
        config = builder.build(data, name_key='x', value_key='y')

        # B has 0 value, should be 0%
        assert config.data[1]['percentage'] == 0.0

    def test_all_equal_slices(self):
        """Test pie chart where all slices are equal."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C', 'D'],
            'y': [25, 25, 25, 25]
        })

        builder = PieChartBuilder(show_percentages=True)
        config = builder.build(data, name_key='x', value_key='y')

        # All should be 25%
        for item in config.data:
            assert item['percentage'] == 25.0

    def test_large_dataset(self):
        """Test handling of many slices."""
        data = pd.DataFrame({
            'x': [f'Slice{i}' for i in range(20)],
            'y': [10] * 20
        })

        builder = PieChartBuilder(show_percentages=True)
        config = builder.build(data, name_key='x', value_key='y')

        assert len(config.data) == 20
        # Each slice should be 5% (10/200)
        for item in config.data:
            assert item['percentage'] == 5.0

    def test_missing_column_raises_error(self):
        """Test that missing columns raise KeyError."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder()
        # Reference non-existent column should raise KeyError
        with pytest.raises(KeyError):
            builder.build(data, name_key='x', value_key='nonexistent')


class TestJSONSerialization:
    """Test JSON output and serialization."""

    def test_to_json_string(self):
        """Test conversion to JSON string."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder()
        config = builder.build(data, name_key='x', value_key='y', title='Test Chart')

        json_str = config.to_json()

        # Parse to verify valid JSON
        parsed = json.loads(json_str)
        assert parsed['type'] == 'pie'
        assert parsed['title'] == 'Test Chart'
        assert len(parsed['data']) == 2

    def test_to_json_file(self):
        """Test saving to JSON file."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'charts' / 'test_pie.json'

            builder = PieChartBuilder()
            config = builder.build(data, name_key='x', value_key='y')
            config.to_json(output_path)

            assert output_path.exists()

            # Verify content
            with open(output_path) as f:
                parsed = json.load(f)

            assert parsed['type'] == 'pie'
            assert len(parsed['data']) == 2


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_pie_chart_function(self):
        """Test pie_chart convenience function."""
        data = pd.DataFrame({
            'product': ['A', 'B', 'C'],
            'sales': [100, 200, 150]
        })

        config = pie_chart(data, name='product', value='sales', title='Product Sales')

        assert config.chart_type == 'pie'
        assert config.title == 'Product Sales'
        assert len(config.data) == 3

    def test_donut_chart_function(self):
        """Test donut_chart convenience function."""
        data = pd.DataFrame({
            'category': ['X', 'Y', 'Z'],
            'amount': [50, 75, 100]
        })

        config = donut_chart(data, name='category', value='amount', title='Category Distribution')

        assert config.chart_type == 'pie'
        assert config.title == 'Category Distribution'
        # Should have inner radius > 0
        assert config.config['pie']['innerRadius'] > 0

    def test_pie_chart_with_output_path(self):
        """Test pie_chart convenience function with output path."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.json'

            config = pie_chart(data, name='x', value='y', title='Test', output_path=output_path)

            assert output_path.exists()
            assert config.title == 'Test'

    def test_pie_chart_with_kwargs(self):
        """Test pie_chart with additional kwargs."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        config = pie_chart(
            data,
            name='x',
            value='y',
            show_labels=False,
            show_legend=False
        )

        # When disabled, label should not be present (exclude_none=True)
        assert 'label' not in config.config['pie']
        assert 'legend' not in config.config

    def test_donut_chart_with_output_path(self):
        """Test donut_chart convenience function with output path."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'donut.json'

            config = donut_chart(data, name='x', value='y', output_path=output_path)

            assert output_path.exists()
            assert config.config['pie']['innerRadius'] > 0


class TestTooltip:
    """Test tooltip configuration."""

    def test_tooltip_present(self):
        """Test that tooltip is configured."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder()
        config = builder.build(data, name_key='x', value_key='y')

        assert 'tooltip' in config.config
        assert config.config['tooltip'] is not None


class TestBuilderConfiguration:
    """Test various builder configurations."""

    def test_custom_radius_values(self):
        """Test custom inner and outer radius."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder(inner_radius=30, outer_radius=90)
        config = builder.build(data, name_key='x', value_key='y')

        assert config.config['pie']['innerRadius'] == 30
        assert config.config['pie']['outerRadius'] == 90

    def test_all_options_disabled(self):
        """Test builder with all optional features disabled."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder(
            show_labels=False,
            show_legend=False,
            show_percentages=False
        )
        config = builder.build(data, name_key='x', value_key='y')

        # When disabled, label should not be present (exclude_none=True)
        assert 'label' not in config.config['pie']
        assert 'legend' not in config.config
        assert 'percentage' not in config.data[0]

    def test_all_options_enabled(self):
        """Test builder with all optional features enabled."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = PieChartBuilder(
            show_labels=True,
            show_legend=True,
            show_percentages=True
        )
        config = builder.build(data, name_key='x', value_key='y')

        assert config.config['pie']['label'] is not None
        assert config.config['legend'] is not None
        assert 'percentage' in config.data[0]
