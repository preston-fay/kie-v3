#!/usr/bin/env python3
"""
Basic Chart Generation Examples for KIE v3

This script demonstrates how to generate various chart types using the KIE
chart generation system with KDS (Kearney Design System) compliance.

All charts use the official KDS color palette and follow brand guidelines.
"""

import pandas as pd
from pathlib import Path
from kie.charts.factory import ChartFactory
from kie.charts.builders.bar import BarChartBuilder
from kie.charts.builders.line import LineChartBuilder
from kie.charts.builders.pie import PieChartBuilder

# Create output directory
OUTPUT_DIR = Path("outputs/examples/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def example_bar_chart():
    """Generate a basic bar chart showing regional revenue."""
    print("📊 Generating bar chart...")

    data = pd.DataFrame({
        'region': ['North', 'South', 'East', 'West'],
        'revenue': [1250000, 980000, 1450000, 1100000]
    })

    builder = BarChartBuilder()
    config = builder.build(
        data=data,
        x_key='region',
        y_keys=['revenue'],
        title='Q3 Revenue by Region'
    )

    output_path = OUTPUT_DIR / 'bar_chart_example.json'
    config.to_json(output_path)
    print(f"✅ Bar chart saved to: {output_path}")
    return config


def example_stacked_bar_chart():
    """Generate a stacked bar chart showing revenue and cost breakdown."""
    print("📊 Generating stacked bar chart...")

    data = pd.DataFrame({
        'quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
        'revenue': [1200000, 1350000, 1450000, 1600000],
        'cost': [800000, 900000, 950000, 1000000],
        'profit': [400000, 450000, 500000, 600000]
    })

    builder = BarChartBuilder(stacked=True)
    config = builder.build(
        data=data,
        x_key='quarter',
        y_keys=['revenue', 'cost', 'profit'],
        title='Quarterly Financial Performance'
    )

    output_path = OUTPUT_DIR / 'stacked_bar_example.json'
    config.to_json(output_path)
    print(f"✅ Stacked bar chart saved to: {output_path}")
    return config


def example_line_chart():
    """Generate a line chart showing time series data."""
    print("📈 Generating line chart...")

    data = pd.DataFrame({
        'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'sales': [120, 135, 148, 142, 165, 178],
        'target': [130, 130, 145, 145, 160, 160]
    })

    builder = LineChartBuilder()
    config = builder.build(
        data=data,
        x_key='month',
        y_keys=['sales', 'target'],
        title='Sales vs Target - H1 2024'
    )

    output_path = OUTPUT_DIR / 'line_chart_example.json'
    config.to_json(output_path)
    print(f"✅ Line chart saved to: {output_path}")
    return config


def example_pie_chart():
    """Generate a pie chart showing market share distribution."""
    print("🥧 Generating pie chart...")

    data = pd.DataFrame({
        'segment': ['Enterprise', 'Mid-Market', 'SMB', 'Consumer'],
        'revenue': [4500000, 2800000, 1900000, 800000]
    })

    builder = PieChartBuilder()
    config = builder.build(
        data=data,
        name_key='segment',
        value_key='revenue',
        title='Revenue by Customer Segment'
    )

    output_path = OUTPUT_DIR / 'pie_chart_example.json'
    config.to_json(output_path)
    print(f"✅ Pie chart saved to: {output_path}")
    return config


def example_auto_detect():
    """Demonstrate automatic chart type detection."""
    print("🤖 Demonstrating auto-detection...")

    # Time series data → should detect line chart
    time_data = pd.DataFrame({
        'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'value': [100, 105, 110, 108, 115, 120, 118, 125, 130, 128, 135, 140]
    })

    config = ChartFactory.auto_detect(
        data=time_data,
        title='Auto-Detected Time Series'
    )

    print(f"  → Detected chart type: {config.chart_type}")
    output_path = OUTPUT_DIR / 'auto_detect_timeseries.json'
    config.to_json(output_path)

    # Categorical data → should detect bar chart
    cat_data = pd.DataFrame({
        'category': ['A', 'B', 'C', 'D'],
        'value': [45, 67, 34, 89]
    })

    config = ChartFactory.auto_detect(
        data=cat_data,
        title='Auto-Detected Categorical Data'
    )

    print(f"  → Detected chart type: {config.chart_type}")
    output_path = OUTPUT_DIR / 'auto_detect_categorical.json'
    config.to_json(output_path)

    print(f"✅ Auto-detection examples saved to: {OUTPUT_DIR}")


def main():
    """Run all chart generation examples."""
    print("\n" + "="*60)
    print("KIE v3 - Chart Generation Examples")
    print("="*60 + "\n")

    try:
        example_bar_chart()
        example_stacked_bar_chart()
        example_line_chart()
        example_pie_chart()
        example_auto_detect()

        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print(f"📁 Charts saved to: {OUTPUT_DIR}")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == '__main__':
    main()
