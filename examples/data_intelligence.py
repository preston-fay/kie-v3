#!/usr/bin/env python3
"""
Data Intelligence Examples for KIE v3

This script demonstrates KIE's intelligent column mapping system and manual
overrides. Shows how ChartFactory.auto_detect() works and when to use explicit
column mappings to bypass intelligence.
"""

import pandas as pd
from pathlib import Path
from kie.charts.factory import ChartFactory
from kie.charts.builders.bar import BarChartBuilder
from kie.charts.builders.line import LineChartBuilder

# Create output directory
OUTPUT_DIR = Path("outputs/examples/intelligence")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def example_auto_detection():
    """Demonstrate automatic chart type detection."""
    print("🧠 Example 1: Automatic Chart Type Detection\n")

    # Time series data → should detect line chart
    time_data = pd.DataFrame({
        'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'sales': [120000, 135000, 148000, 142000, 165000, 178000],
        'target': [130000, 130000, 145000, 145000, 160000, 160000]
    })

    print("Time series data:")
    print(time_data.head(3))

    config = ChartFactory.auto_detect(
        data=time_data,
        title='Auto-Detected Time Series'
    )

    print(f"\n✓ Detected chart type: {config.chart_type}")
    print("  Reasoning: Sequential data with multiple metrics")

    config.to_json(OUTPUT_DIR / 'auto_timeseries.json')

    # Categorical data → should detect bar chart
    cat_data = pd.DataFrame({
        'region': ['North', 'South', 'East', 'West'],
        'revenue': [1200000, 980000, 1450000, 1100000]
    })

    print("\nCategorical data:")
    print(cat_data)

    config = ChartFactory.auto_detect(
        data=cat_data,
        title='Auto-Detected Categorical'
    )

    print(f"\n✓ Detected chart type: {config.chart_type}")
    print("  Reasoning: Small number of categories with single metric\n")

    config.to_json(OUTPUT_DIR / 'auto_categorical.json')
    print(f"✅ Auto-detection examples saved to: {OUTPUT_DIR}\n")


def example_manual_override():
    """Demonstrate explicit column mapping to override intelligence."""
    print("🧠 Example 2: Manual Column Override\n")

    # Data with multiple similar columns
    data = pd.DataFrame({
        'region': ['North', 'South', 'East', 'West'],
        'total_revenue': [1000000, 1500000, 1200000, 1800000],
        'recurring_revenue': [800000, 1200000, 950000, 1400000],
        'one_time_revenue': [200000, 300000, 250000, 400000]
    })

    print("Data with multiple revenue columns:")
    print(list(data.columns))

    # Option 1: Let auto-detection choose
    print("\nOption 1: Auto-detection (will pick first metric)")
    config_auto = ChartFactory.auto_detect(
        data=data,
        title='Auto-Selected Revenue'
    )
    print(f"  → Used default intelligence selection")

    # Option 2: Explicit override
    print("\nOption 2: Manual override (specify exact column)")
    builder = BarChartBuilder()
    config_manual = builder.build(
        data=data,
        x_key='region',
        y_keys=['recurring_revenue'],  # EXPLICIT choice
        title='Manual Override: Recurring Revenue Only'
    )
    print(f"  → Forced 'recurring_revenue' column")

    # Option 3: Multiple metrics explicitly
    print("\nOption 3: Multiple explicit metrics")
    config_multi = builder.build(
        data=data,
        x_key='region',
        y_keys=['recurring_revenue', 'one_time_revenue'],  # EXPLICIT multiple
        title='Recurring vs One-Time Revenue'
    )
    print(f"  → Forced comparison of 2 specific metrics")

    config_manual.to_json(OUTPUT_DIR / 'manual_override_single.json')
    config_multi.to_json(OUTPUT_DIR / 'manual_override_multi.json')

    print(f"\n✅ Manual override examples saved to: {OUTPUT_DIR}")
    print("\nKey Takeaway: Explicit parameters ALWAYS override intelligence\n")


def example_time_series_detection():
    """Demonstrate time series vs categorical detection."""
    print("🧠 Example 3: Time Series vs Categorical Detection\n")

    # Sequential time data
    time_data = pd.DataFrame({
        'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'value': [100, 105, 110, 108, 115, 120, 118, 125, 130, 128, 135, 140]
    })

    print("Time series with dates:")
    print(f"  {len(time_data)} data points over time")

    config_time = ChartFactory.auto_detect(
        data=time_data,
        title='Time Series Data'
    )

    print(f"  → Detected: {config_time.chart_type} (good for trends)\n")

    # Categorical comparison
    cat_data = pd.DataFrame({
        'product': ['Product A', 'Product B', 'Product C', 'Product D'],
        'sales': [45000, 67000, 34000, 89000]
    })

    print("Categorical data:")
    print(f"  {len(cat_data)} discrete categories")

    config_cat = ChartFactory.auto_detect(
        data=cat_data,
        title='Product Comparison'
    )

    print(f"  → Detected: {config_cat.chart_type} (good for comparison)\n")

    config_time.to_json(OUTPUT_DIR / 'timeseries_detected.json')
    config_cat.to_json(OUTPUT_DIR / 'categorical_detected.json')

    print(f"✅ Detection examples saved to: {OUTPUT_DIR}\n")


def example_forcing_chart_types():
    """Demonstrate forcing specific chart types regardless of data."""
    print("🧠 Example 4: Forcing Specific Chart Types\n")

    data = pd.DataFrame({
        'quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
        'revenue': [1200000, 1350000, 1450000, 1600000],
        'cost': [800000, 900000, 950000, 1000000]
    })

    print("Same data, different chart types:")

    # Force bar chart
    bar_builder = BarChartBuilder()
    config_bar = bar_builder.build(
        data=data,
        x_key='quarter',
        y_keys=['revenue', 'cost'],
        title='Forced Bar Chart'
    )
    print("  ✓ Bar chart (comparison focus)")

    # Force line chart
    line_builder = LineChartBuilder()
    config_line = line_builder.build(
        data=data,
        x_key='quarter',
        y_keys=['revenue', 'cost'],
        title='Forced Line Chart'
    )
    print("  ✓ Line chart (trend focus)")

    config_bar.to_json(OUTPUT_DIR / 'forced_bar.json')
    config_line.to_json(OUTPUT_DIR / 'forced_line.json')

    print(f"\n✅ Forced chart types saved to: {OUTPUT_DIR}")
    print("\nKey Takeaway: Use specific builders to force chart types\n")


def main():
    """Run all data intelligence examples."""
    print("\n" + "="*60)
    print("KIE v3 - Data Intelligence & Override Examples")
    print("="*60 + "\n")

    try:
        example_auto_detection()
        print("-" * 60 + "\n")

        example_manual_override()
        print("-" * 60 + "\n")

        example_time_series_detection()
        print("-" * 60 + "\n")

        example_forcing_chart_types()

        print("=" * 60)
        print("✅ All intelligence examples completed!")
        print(f"📁 Outputs saved to: {OUTPUT_DIR}")
        print("=" * 60 + "\n")

        print("Summary:")
        print("1. ChartFactory.auto_detect() chooses chart type automatically")
        print("2. Use specific builders (BarChartBuilder, etc.) to force types")
        print("3. Explicit column parameters override all intelligence")
        print("4. Auto-detection analyzes data shape and column names")
        print("5. Manual override is recommended for ambiguous data\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == '__main__':
    main()
