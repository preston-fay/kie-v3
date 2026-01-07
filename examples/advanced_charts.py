#!/usr/bin/env python3
"""
Advanced Chart Generation Examples for KIE v3

This script demonstrates advanced chart features including:
- Scatter plots with outliers
- Waterfall charts with cumulative totals
- Combo charts (mixed line + bar)
- Area charts with stacking
- Custom styling and themes
"""

import pandas as pd
import numpy as np
from pathlib import Path
from kie.charts.builders.scatter import ScatterPlotBuilder
from kie.charts.builders.waterfall import WaterfallChartBuilder
from kie.charts.builders.combo import ComboChartBuilder
from kie.charts.builders.area import AreaChartBuilder

# Create output directory
OUTPUT_DIR = Path("outputs/examples/advanced_charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def example_scatter_plot():
    """Generate scatter plot with correlation analysis."""
    print("📊 Generating scatter plot...")

    # Generate sample data with correlation
    np.random.seed(42)
    x_vals = np.random.normal(100, 20, 50)
    y_vals = x_vals * 0.8 + np.random.normal(0, 10, 50)

    data = pd.DataFrame({
        'marketing_spend': x_vals,
        'revenue': y_vals,
        'region': np.random.choice(['North', 'South', 'East', 'West'], 50)
    })

    builder = ScatterPlotBuilder()
    config = builder.build(
        data=data,
        x_key='marketing_spend',
        y_key='revenue',
        category_key='region',
        title='Marketing Spend vs Revenue'
    )

    output_path = OUTPUT_DIR / 'scatter_plot_example.json'
    config.to_json(output_path)
    print(f"✅ Scatter plot saved to: {output_path}")
    return config


def example_waterfall_chart():
    """Generate waterfall chart showing cumulative changes."""
    print("💧 Generating waterfall chart...")

    data = pd.DataFrame({
        'category': ['Starting Revenue', 'New Sales', 'Upsells',
                     'Churn', 'Discounts', 'Ending Revenue'],
        'value': [1000000, 250000, 150000, -180000, -80000, 1140000],
        'type': ['total', 'increase', 'increase',
                 'decrease', 'decrease', 'total']
    })

    builder = WaterfallChartBuilder()
    config = builder.build(
        data=data,
        label_key='category',
        value_key='value',
        is_total_key='type',
        title='Q3 Revenue Waterfall Analysis'
    )

    output_path = OUTPUT_DIR / 'waterfall_example.json'
    config.to_json(output_path)
    print(f"✅ Waterfall chart saved to: {output_path}")
    return config


def example_combo_chart():
    """Generate combo chart with line and bar elements."""
    print("📊 Generating combo chart...")

    data = pd.DataFrame({
        'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'revenue': [1200000, 1350000, 1280000, 1450000, 1520000, 1600000],
        'units': [4500, 4800, 4600, 5100, 5300, 5500],
        'margin': [0.32, 0.35, 0.33, 0.36, 0.37, 0.38]
    })

    builder = ComboChartBuilder()
    config = builder.build(
        data=data,
        x_key='month',
        bar_keys=['revenue', 'units'],
        line_keys=['margin'],
        title='Revenue, Units & Margin Analysis'
    )

    output_path = OUTPUT_DIR / 'combo_chart_example.json'
    config.to_json(output_path)
    print(f"✅ Combo chart saved to: {output_path}")
    return config


def example_area_chart():
    """Generate stacked area chart showing composition over time."""
    print("📈 Generating area chart...")

    data = pd.DataFrame({
        'quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
        'product_a': [300000, 320000, 350000, 380000],
        'product_b': [250000, 280000, 290000, 310000],
        'product_c': [200000, 220000, 240000, 260000],
        'product_d': [150000, 180000, 190000, 210000]
    })

    builder = AreaChartBuilder(stacked=True)
    config = builder.build(
        data=data,
        x_key='quarter',
        y_keys=['product_a', 'product_b', 'product_c', 'product_d'],
        title='Product Revenue Mix Over Time'
    )

    output_path = OUTPUT_DIR / 'area_chart_example.json'
    config.to_json(output_path)
    print(f"✅ Area chart saved to: {output_path}")
    return config


def example_multi_series_comparison():
    """Generate chart comparing multiple data series with different scales."""
    print("📊 Generating multi-series comparison...")

    data = pd.DataFrame({
        'week': [f'W{i}' for i in range(1, 13)],
        'conversion_rate': [0.045, 0.048, 0.051, 0.049, 0.053, 0.056,
                            0.054, 0.058, 0.061, 0.059, 0.063, 0.065],
        'sessions': [25000, 27000, 26500, 28000, 29500, 31000,
                     30000, 32500, 34000, 33500, 35500, 37000],
        'revenue': [1125000, 1296000, 1351500, 1372000, 1563500, 1736000,
                    1620000, 1885000, 2074000, 1976500, 2236500, 2405000]
    })

    builder = ComboChartBuilder()
    config = builder.build(
        data=data,
        x_key='week',
        bar_keys=['sessions'],
        line_keys=['conversion_rate', 'revenue'],
        title='E-commerce Performance Dashboard'
    )

    output_path = OUTPUT_DIR / 'multi_series_example.json'
    config.to_json(output_path)
    print(f"✅ Multi-series chart saved to: {output_path}")
    return config


def example_custom_theming():
    """Demonstrate custom theme options."""
    print("🎨 Generating custom themed charts...")

    data = pd.DataFrame({
        'category': ['Category A', 'Category B', 'Category C', 'Category D'],
        'value': [45, 67, 34, 89]
    })

    from kie.charts.builders.bar import BarChartBuilder

    # Dark theme example
    builder = BarChartBuilder()
    config_dark = builder.build(
        data=data,
        x_key='category',
        y_keys=['value'],
        title='Dark Theme Example'
    )
    config_dark.to_json(OUTPUT_DIR / 'custom_theme_dark.json')

    # Light theme example
    config_light = builder.build(
        data=data,
        x_key='category',
        y_keys=['value'],
        title='Light Theme Example'
    )
    config_light.to_json(OUTPUT_DIR / 'custom_theme_light.json')

    print(f"✅ Custom themed charts saved to: {OUTPUT_DIR}")


def main():
    """Run all advanced chart examples."""
    print("\n" + "="*60)
    print("KIE v3 - Advanced Chart Generation Examples")
    print("="*60 + "\n")

    try:
        example_scatter_plot()
        example_waterfall_chart()
        example_combo_chart()
        example_area_chart()
        example_multi_series_comparison()
        example_custom_theming()

        print("\n" + "="*60)
        print("✅ All advanced examples completed successfully!")
        print(f"📁 Charts saved to: {OUTPUT_DIR}")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == '__main__':
    main()
