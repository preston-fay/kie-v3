# KIE v3 Examples

This directory contains comprehensive examples demonstrating KIE's chart generation and data intelligence capabilities.

## Quick Start

```bash
# Run basic chart examples
python3 examples/basic_charts.py

# Run advanced chart examples
python3 examples/advanced_charts.py

# Run data intelligence examples
python3 examples/data_intelligence.py

# Run validation example
python3 examples/validation_example.py
```

## Examples Overview

### 1. Basic Charts (`basic_charts.py`)

Demonstrates fundamental chart generation:

- **Bar Charts** - Simple and stacked bar charts for categorical comparisons
- **Line Charts** - Time series and multi-series trend analysis
- **Pie Charts** - Proportional composition visualization
- **Auto-Detection** - Automatic chart type selection based on data patterns

**Use this when:**
- Learning KIE chart generation basics
- Building simple visualizations
- Understanding KDS color palette usage

### 2. Advanced Charts (`advanced_charts.py`)

Shows advanced chart types and features:

- **Scatter Plots** - Correlation analysis and outlier detection
- **Waterfall Charts** - Cumulative change visualization
- **Combo Charts** - Mixed line + bar with dual axes
- **Area Charts** - Stacked composition over time
- **Multi-Series** - Complex comparisons with different scales
- **Custom Theming** - Dark/light theme customization

**Use this when:**
- Building complex analytical dashboards
- Combining multiple chart types
- Customizing chart appearance

### 3. Data Intelligence (`data_intelligence.py`)

Explains KIE's 4-tier semantic scoring system:

- **Tier 1: Semantic Matching** - Keyword recognition (revenue, cost, margin)
- **Tier 2: ID Avoidance** - Automatic rejection of IDs, zip codes
- **Tier 3: Percentage Handling** - Recognition of ratios in [0,1] range
- **Tier 4: Statistical Vitality** - Coefficient of variation (CV) tie-breaking
- **Manual Overrides** - Explicit column mapping to bypass intelligence

**Use this when:**
- Understanding how column selection works
- Debugging unexpected column choices
- Learning when to use manual overrides

### 4. Validation (`validation_example.py`)

Demonstrates the comprehensive validation system:

- **Brand Compliance** - KDS color palette, no green colors, gridline detection
- **Data Quality** - Synthetic data detection, null handling, duplicate checks
- **Content Safety** - Placeholder detection, profanity filter, accessibility
- **Multi-Level QC** - ERROR, WARNING, INFO severity levels

**Use this when:**
- Ensuring deliverable quality before client delivery
- Understanding validation failure reasons
- Building custom validation workflows

## Chart Types Reference

| Chart Type | Best For | Example File |
|------------|----------|--------------|
| Bar | Categorical comparisons | `basic_charts.py` |
| Line | Time series, trends | `basic_charts.py` |
| Pie | Proportions, composition | `basic_charts.py` |
| Scatter | Correlation, outliers | `advanced_charts.py` |
| Waterfall | Cumulative changes | `advanced_charts.py` |
| Combo | Multi-metric dashboards | `advanced_charts.py` |
| Area | Stacked composition over time | `advanced_charts.py` |

## KDS Compliance

All examples follow Kearney Design System (KDS) guidelines:

- ✅ Official KDS 10-color palette
- ✅ Kearney Purple (#7823DC) as primary brand color
- ❌ NO green colors (brand violation)
- ✅ No gridlines in charts
- ✅ Data labels outside bars/slices
- ✅ WCAG 2.1 AA contrast compliance

## Output Structure

Charts are saved as JSON configs in:

```
outputs/examples/
├── charts/               # Basic chart outputs
├── advanced_charts/      # Advanced chart outputs
└── intelligence/         # Data intelligence examples
```

These JSON configs are rendered by the React frontend (`web/`) for final display.

## Common Patterns

### Pattern 1: Simple Chart Generation

```python
from kie.charts.builders.bar import BarChartBuilder
import pandas as pd

data = pd.DataFrame({
    'category': ['A', 'B', 'C'],
    'value': [100, 200, 150]
})

builder = BarChartBuilder()
config = builder.build(
    data=data,
    x='category',
    y=['value'],
    title='My Chart'
)

config.to_json('outputs/my_chart.json')
```

### Pattern 2: Auto-Detection

```python
from kie.charts.factory import ChartFactory

# Let KIE pick the best chart type
config = ChartFactory.auto_detect(
    data=data,
    title='Auto-Generated Chart'
)
```

### Pattern 3: Manual Override

```python
# Bypass intelligence with explicit column mapping
config = builder.build(
    data=data,
    x='specific_column',      # Force this column
    y=['exact_metric'],       # Force this metric
    title='Override Example'
)
```

### Pattern 4: Validation

```python
from kie.validation import validate_chart_output

report = validate_chart_output(
    data=data,
    chart_config=config.to_dict(),
    output_path=output_path,
    strict=True  # Warnings also fail
)

if not report.passed:
    print(report.format_text_report())
```

## Troubleshooting

### Intelligence picking wrong column?

1. Check your `objective` parameter - it drives semantic matching
2. Use explicit column mapping to override
3. Verify column names match expected keywords (revenue, cost, margin)

### Validation failing?

1. Check for green colors (`#00FF00`, `#008000`, etc.) - KDS violation
2. Ensure using official KDS palette from `kie.brand.colors`
3. Verify no gridlines in chart config
4. Check for synthetic/test data (names like "John Doe", sequential IDs)

### Charts not rendering?

1. Verify JSON config saved to `outputs/` directory
2. Check React frontend is running (`npm start` in `web/`)
3. Ensure config follows `RechartsConfig` schema

## Next Steps

1. **Modify examples** - Change data and parameters to fit your needs
2. **Run validation** - Always validate before client delivery
3. **Review CLAUDE.md** - Full system documentation
4. **Explore source** - Check `kie/charts/` and `kie/validation/`

## Questions?

- See `CLAUDE.md` for full system documentation
- Check `kie/` source code for implementation details
- Run tests: `python3 -m pytest tests/`

---

**KIE v3.0** - Kearney Insight Engine
