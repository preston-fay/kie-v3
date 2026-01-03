# /analyze

---
name: analyze
description: Analyze data and generate insights
agent: @analyst
---

Analyze data files and generate structured insights.

## Usage

```
/analyze                           # Analyze data from spec
/analyze data/sales.csv            # Analyze specific file
/analyze --auto                    # Auto-extract all insights
/analyze --correlations            # Focus on correlations
/analyze --trends                  # Focus on time series
```

## Workflow

1. **Load Data**: Read CSV, Excel, or database
2. **Profile**: Generate descriptive statistics
3. **Detect**: Find patterns, outliers, correlations
4. **Extract**: Create structured insights
5. **Visualize**: Generate supporting charts

## Using KIE Engines

```python
from kie.insights import InsightEngine, StatisticalAnalyzer
from kie.charts import ChartFactory
import pandas as pd

# Load and analyze
df = pd.read_csv("data/sales.csv")
engine = InsightEngine()

# Auto-extract insights
insights = engine.auto_extract(
    df,
    value_column="revenue",
    group_column="region",
    time_column="quarter"
)

# Build catalog
catalog = engine.build_catalog(insights, "What drives revenue?")
catalog.save("outputs/insights.yaml")
```

## Output

- Insights catalog: `outputs/insights.yaml`
- Charts: `outputs/charts/`
- Preview: Opens in browser

## Next Steps

```
/build    # Create presentation from insights
/preview  # View insights in browser
```
