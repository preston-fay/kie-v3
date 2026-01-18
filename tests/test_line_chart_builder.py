"""
Tests for LineChartBuilder

Comprehensive test suite covering:
- Basic line charts
- Multiple series
- Missing data points
- Date handling
- Curve types
- Dot markers
- Data labels
- Color handling
- KDS compliance
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json
from datetime import datetime

from kie.charts.builders.line import LineChartBuilder, line_chart
from kie.base import RechartsConfig
from kie.brand.colors import KDSColors


class TestLineChartBuilderBasics:
    """Test basic line chart generation."""

    def test_basic_line_chart(self):
        """Test basic single-series line chart."""
        data = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar', 'Apr'],
            'sales': [1200, 1350, 1180, 1420]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='month', y_keys='sales', title='Monthly Sales')

        assert config.chart_type == 'line'
        assert len(config.data) == 4
        assert config.title == 'Monthly Sales'
        assert config.data[0]['Month'] == 'Jan'
        assert config.data[0]['Sales'] == 1200

    def test_line_chart_with_list_of_dicts(self):
        """Test line chart with list of dicts input."""
        data = [
            {'week': 'W1', 'revenue': 100},
            {'week': 'W2', 'revenue': 120},
            {'week': 'W3', 'revenue': 115}
        ]

        builder = LineChartBuilder()
        config = builder.build(data, x_key='week', y_keys='revenue')

        assert config.chart_type == 'line'
        assert len(config.data) == 3
        assert config.data[1]['Revenue'] == 120

    def test_multi_series_line_chart(self):
        """Test line chart with multiple series."""
        data = pd.DataFrame({
            'quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
            'revenue': [1000, 1200, 1100, 1500],
            'cost': [600, 700, 650, 800],
            'profit': [400, 500, 450, 700]
        })

        builder = LineChartBuilder()
        config = builder.build(
            data,
            x_key='quarter',
            y_keys=['revenue', 'cost', 'profit'],
            title='Financial Metrics'
        )

        assert config.chart_type == 'line'
        assert len(config.data) == 4

        # Check that three lines are configured
        lines = config.config.get('lines', [])
        assert len(lines) == 3
        assert lines[0]['dataKey'] == 'Revenue'
        assert lines[1]['dataKey'] == 'Cost'
        assert lines[2]['dataKey'] == 'Profit'

    def test_single_y_key_as_string(self):
        """Test that single y_key can be passed as string."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')  # String, not list

        lines = config.config['lines']
        assert len(lines) == 1
        assert lines[0]['dataKey'] == 'Y'


class TestCurveTypes:
    """Test different curve interpolation types."""

    def test_monotone_curve(self):
        """Test monotone curve (smooth, default)."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder(curve_type='monotone')
        config = builder.build(data, x_key='x', y_keys='y')

        # Curve type is stored in builder, not exported to config
        # (Recharts uses type prop on Line component)
        assert builder.curve_type == 'monotone'

    def test_linear_curve(self):
        """Test linear curve (straight lines between points)."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder(curve_type='linear')
        config = builder.build(data, x_key='x', y_keys='y')

        assert builder.curve_type == 'linear'

    def test_step_curve(self):
        """Test step curve (staircase pattern)."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder(curve_type='step')
        config = builder.build(data, x_key='x', y_keys='y')

        assert builder.curve_type == 'step'

    def test_natural_curve(self):
        """Test natural curve (cubic spline)."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder(curve_type='natural')
        config = builder.build(data, x_key='x', y_keys='y')

        assert builder.curve_type == 'natural'


class TestDotMarkers:
    """Test data point marker configuration."""

    def test_dots_enabled(self):
        """Test that dots are shown when enabled."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder(show_dots=True)
        config = builder.build(data, x_key='x', y_keys='y')

        lines = config.config['lines']
        assert lines[0]['dot'] is not False
        assert isinstance(lines[0]['dot'], dict)
        assert lines[0]['dot']['r'] == 4  # Radius

    def test_dots_disabled(self):
        """Test that dots are hidden when disabled."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder(show_dots=False)
        config = builder.build(data, x_key='x', y_keys='y')

        lines = config.config['lines']
        assert lines[0]['dot'] is False

    def test_active_dot_always_present(self):
        """Test that activeDot (hover state) is always configured."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder(show_dots=False)
        config = builder.build(data, x_key='x', y_keys='y')

        lines = config.config['lines']
        assert 'activeDot' in lines[0]
        assert lines[0]['activeDot']['r'] == 6


class TestStrokeWidthConfiguration:
    """Test line stroke width settings."""

    def test_default_stroke_width(self):
        """Test default stroke width."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        lines = config.config['lines']
        assert lines[0]['strokeWidth'] == 2

    def test_custom_stroke_width(self):
        """Test custom stroke width."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = LineChartBuilder(stroke_width=4)
        config = builder.build(data, x_key='x', y_keys='y')

        lines = config.config['lines']
        assert lines[0]['strokeWidth'] == 4

    def test_thin_line(self):
        """Test thin line (stroke_width=1)."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = LineChartBuilder(stroke_width=1)
        config = builder.build(data, x_key='x', y_keys='y')

        lines = config.config['lines']
        assert lines[0]['strokeWidth'] == 1


class TestDataLabels:
    """Test data label configuration."""

    def test_data_labels_enabled(self):
        """Test that data labels are configured when enabled."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder(show_data_labels=True)
        config = builder.build(data, x_key='x', y_keys='y')

        lines = config.config['lines']
        assert lines[0]['label'] is not None
        assert lines[0]['label']['position'] == 'top'
        assert lines[0]['label']['fontSize'] == 11

    def test_data_labels_disabled(self):
        """Test that data labels are not configured when disabled."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder(show_data_labels=False)
        config = builder.build(data, x_key='x', y_keys='y')

        lines = config.config['lines']
        # When disabled, label key should not be present (exclude_none=True)
        assert 'label' not in lines[0]


class TestLegend:
    """Test legend configuration."""

    def test_legend_single_series(self):
        """Test that legend is not shown for single series."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder(show_legend=True)
        config = builder.build(data, x_key='x', y_keys='y')

        # Legend should not be present for single series (exclude_none=True)
        assert 'legend' not in config.config

    def test_legend_multi_series(self):
        """Test that legend is shown for multiple series."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y1': [10, 20, 15],
            'y2': [15, 25, 20]
        })

        builder = LineChartBuilder(show_legend=True)
        config = builder.build(data, x_key='x', y_keys=['y1', 'y2'])

        assert config.config['legend'] is not None

    def test_legend_disabled(self):
        """Test that legend can be disabled even for multi-series."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y1': [10, 20, 15],
            'y2': [15, 25, 20]
        })

        builder = LineChartBuilder(show_legend=False)
        config = builder.build(data, x_key='x', y_keys=['y1', 'y2'])

        # Legend should not be present when disabled (exclude_none=True)
        assert 'legend' not in config.config


class TestColorHandling:
    """Test color assignment and validation."""

    def test_default_kds_colors(self):
        """Test that default colors come from KDS palette."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 30]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        lines = config.config['lines']
        line_color = lines[0]['stroke']

        # Should be first color in KDS palette
        assert line_color == KDSColors.CHART_PALETTE[0]

    def test_multiple_series_colors(self):
        """Test that multiple series get different KDS colors."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y1': [10, 20],
            'y2': [15, 25],
            'y3': [12, 22]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys=['y1', 'y2', 'y3'])

        lines = config.config['lines']
        colors = [line['stroke'] for line in lines]

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
        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y', colors=[custom_color])

        lines = config.config['lines']
        assert lines[0]['stroke'] == custom_color

    def test_insufficient_custom_colors(self):
        """Test that KDS colors extend insufficient custom colors."""
        data = pd.DataFrame({
            'x': ['A'],
            'y1': [10],
            'y2': [20],
            'y3': [30]
        })

        # Only provide 1 custom color for 3 series
        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys=['y1', 'y2', 'y3'], colors=['#7823DC'])

        lines = config.config['lines']
        assert lines[0]['stroke'] == '#7823DC'
        # Remaining should come from KDS palette
        assert lines[1]['stroke'] in KDSColors.CHART_PALETTE
        assert lines[2]['stroke'] in KDSColors.CHART_PALETTE

    def test_dot_colors_match_line_colors(self):
        """Test that dot markers use the same color as their line."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y1': [10, 20],
            'y2': [15, 25]
        })

        builder = LineChartBuilder(show_dots=True)
        config = builder.build(data, x_key='x', y_keys=['y1', 'y2'])

        lines = config.config['lines']
        # Dot fill should match stroke
        assert lines[0]['dot']['fill'] == lines[0]['stroke']
        assert lines[1]['dot']['fill'] == lines[1]['stroke']


class TestKDSCompliance:
    """Test KDS design system compliance."""

    def test_no_gridlines(self):
        """Test that gridLines is always False (KDS requirement)."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert config.config['gridLines'] is False

    def test_font_family(self):
        """Test that Inter font is used (KDS requirement)."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        font_family = config.config.get('fontFamily', '')
        assert 'Inter' in font_family

    def test_tooltip_present(self):
        """Test that tooltip is configured (KDS requirement for interactivity)."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert config.config['tooltip'] is not None

    def test_interactive_enabled(self):
        """Test that interactive mode is enabled."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert config.config['interactive'] is True


class TestDateHandling:
    """Test handling of date/time data on x-axis."""

    def test_date_strings(self):
        """Test line chart with date strings."""
        data = pd.DataFrame({
            'date': ['2024-01-01', '2024-02-01', '2024-03-01'],
            'value': [100, 120, 110]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='date', y_keys='value', title='Time Series')

        assert config.chart_type == 'line'
        assert config.data[0]['Date'] == '2024-01-01'

    def test_datetime_objects(self):
        """Test line chart with datetime objects."""
        data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='D'),
            'metric': [50, 60, 55, 70, 65]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='timestamp', y_keys='metric')

        # Datetime objects should be serializable
        assert len(config.data) == 5
        # First value should be timestamp (may be serialized as string)
        assert 'Timestamp' in config.data[0]

    def test_month_names_x_axis(self):
        """Test typical monthly trend chart."""
        data = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'revenue': [100, 110, 105, 120, 130, 125]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='month', y_keys='revenue', title='Monthly Revenue Trend')

        assert len(config.data) == 6
        assert config.title == 'Monthly Revenue Trend'


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        data = pd.DataFrame()

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert config.data == []

    def test_single_data_point(self):
        """Test chart with single data point."""
        data = pd.DataFrame({
            'x': ['A'],
            'y': [100]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert len(config.data) == 1
        assert config.data[0]['Y'] == 100

    def test_two_data_points(self):
        """Test chart with two data points (minimum for a line)."""
        data = pd.DataFrame({
            'x': ['A', 'B'],
            'y': [10, 20]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert len(config.data) == 2

    def test_missing_column_handled(self):
        """Test that missing columns are handled gracefully."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder()
        # Reference non-existent column
        config = builder.build(data, x_key='x', y_keys='nonexistent')

        # Should still build config (column will be missing in data)
        assert config.chart_type == 'line'

    def test_zero_values(self):
        """Test handling of zero values."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C', 'D'],
            'y': [0, 10, 0, 20]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert len(config.data) == 4
        assert config.data[0]['Y'] == 0
        assert config.data[2]['Y'] == 0

    def test_negative_values(self):
        """Test handling of negative values."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C', 'D'],
            'y': [-10, 20, -5, 15]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert config.data[0]['Y'] == -10
        assert config.data[2]['Y'] == -5

    def test_large_dataset(self):
        """Test handling of large dataset."""
        data = pd.DataFrame({
            'x': [f'Point{i}' for i in range(200)],
            'y': list(range(200))
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        assert len(config.data) == 200

    def test_missing_data_points_in_series(self):
        """Test handling of None/NaN values in data."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C', 'D', 'E'],
            'y': [10, None, 15, None, 20]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y')

        # Should preserve data structure (None values will be in data)
        assert len(config.data) == 5
        assert config.data[0]['Y'] == 10


class TestJSONSerialization:
    """Test JSON output and serialization."""

    def test_to_json_string(self):
        """Test conversion to JSON string."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y', title='Test Line Chart')

        json_str = config.to_json()

        # Parse to verify valid JSON
        parsed = json.loads(json_str)
        assert parsed['type'] == 'line'
        assert parsed['title'] == 'Test Line Chart'
        assert len(parsed['data']) == 3

    def test_to_json_file(self):
        """Test saving to JSON file."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'charts' / 'test_line.json'

            builder = LineChartBuilder()
            config = builder.build(data, x_key='x', y_keys='y')
            config.to_json(output_path)

            assert output_path.exists()

            # Verify content
            with open(output_path) as f:
                parsed = json.load(f)

            assert parsed['type'] == 'line'
            assert len(parsed['data']) == 3

    def test_convenience_function_with_output_path(self):
        """Test line_chart convenience function with output path."""
        data = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar'],
            'sales': [100, 120, 110]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_line.json'

            config = line_chart(
                data,
                x='month',
                y='sales',
                title='Sales Trend',
                output_path=output_path
            )

            assert output_path.exists()
            assert config.title == 'Sales Trend'


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_line_chart_function(self):
        """Test line_chart convenience function."""
        data = pd.DataFrame({
            'week': ['W1', 'W2', 'W3', 'W4'],
            'value': [100, 110, 105, 120]
        })

        config = line_chart(data, x='week', y='value', title='Weekly Trend')

        assert config.chart_type == 'line'
        assert config.title == 'Weekly Trend'
        assert len(config.data) == 4

    def test_line_chart_with_kwargs(self):
        """Test line_chart with additional kwargs."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        config = line_chart(
            data,
            x='x',
            y='y',
            curve_type='linear',
            show_dots=False,
            stroke_width=3
        )

        lines = config.config['lines']
        assert lines[0]['strokeWidth'] == 3
        assert lines[0]['dot'] is False


class TestSubtitleSupport:
    """Test subtitle configuration."""

    def test_subtitle_present(self):
        """Test that subtitle is included when provided."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder()
        config = builder.build(
            data,
            x_key='x',
            y_keys='y',
            title='Main Title',
            subtitle='Subtitle Text'
        )

        assert config.title == 'Main Title'
        assert config.subtitle == 'Subtitle Text'
        assert config.config['subtitle'] == 'Subtitle Text'

    def test_no_subtitle(self):
        """Test that subtitle is optional."""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [10, 20, 15]
        })

        builder = LineChartBuilder()
        config = builder.build(data, x_key='x', y_keys='y', title='Title Only')

        assert config.title == 'Title Only'
        assert config.subtitle is None
