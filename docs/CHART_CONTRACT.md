# KIE v3 Chart Contract

**Version**: 3.0
**Last Updated**: 2026-01-15
**Status**: Authoritative

---

## Overview

This document defines the **single authoritative JSON contract** for chart data exchange between:
- **Python Backend** (`kie/` package): Generates chart JSON configs
- **React Frontend** (`web/` package): Renders charts from JSON configs

**Critical Rule**: All chart JSON must conform to this contract. No custom formats.

---

## Contract Structure

### Top-Level Schema

Every chart JSON file MUST have this structure:

```json
{
  "type": "bar" | "line" | "area" | "pie" | "scatter" | "combo",
  "data": [...],
  "config": {...},
  "title": "Optional Chart Title",
  "subtitle": "Optional Subtitle"
}
```

**Fields**:
- `type` (string, required): Chart type identifier (see supported types below)
- `data` (array, required): Array of data objects
- `config` (object, required): Chart configuration (type-specific structure)
- `title` (string, optional): Chart title
- `subtitle` (string, optional): Chart subtitle

---

## Supported Chart Types

### 1. Bar Chart (`type: "bar"`)

**Use Cases**: Comparisons, rankings, categorical data

**Data Format**:
```json
[
  {"category": "North", "Revenue": 125000, "Cost": 80000},
  {"category": "South", "Revenue": 98000, "Cost": 65000}
]
```

**Config Structure**:
```json
{
  "xAxis": {
    "dataKey": "category",
    "axisLine": false,
    "tickLine": false,
    "tick": {"fill": "currentColor", "fontSize": 12}
  },
  "yAxis": {
    "dataKey": "value",
    "axisLine": false,
    "tickLine": false,
    "tick": {"fill": "currentColor", "fontSize": 12}
  },
  "bars": [
    {
      "dataKey": "Revenue",
      "fill": "#7823DC",
      "radius": [4, 4, 0, 0],
      "label": {
        "position": "top",
        "fill": "currentColor",
        "fontSize": 12,
        "fontWeight": 500
      }
    }
  ],
  "layout": "horizontal",
  "barSize": null,
  "barGap": 4,
  "barCategoryGap": "20%",
  "legend": {
    "verticalAlign": "bottom",
    "align": "center",
    "iconType": "square"
  },
  "tooltip": {
    "contentStyle": {"backgroundColor": "#2D2D2D", "border": "none"},
    "labelStyle": {"color": "#FFFFFF", "fontWeight": 600}
  },
  "gridLines": false,
  "fontFamily": "Inter, sans-serif"
}
```

**Backend**: `kie.charts.builders.bar.BarChartBuilder`
**Frontend**: `web/src/components/charts/BarChart.tsx`

---

### 2. Line Chart (`type: "line"`)

**Use Cases**: Trends over time, time-series data

**Data Format**:
```json
[
  {"date": "2024-01", "Revenue": 125000},
  {"date": "2024-02", "Revenue": 142000}
]
```

**Config Structure**:
```json
{
  "xAxis": {"dataKey": "date", "axisLine": false, "tickLine": false},
  "yAxis": {"dataKey": "value", "axisLine": false, "tickLine": false},
  "lines": [
    {
      "dataKey": "Revenue",
      "stroke": "#7823DC",
      "strokeWidth": 2,
      "dot": {"r": 4},
      "activeDot": {"r": 6}
    }
  ],
  "legend": {...},
  "tooltip": {...},
  "gridLines": false
}
```

**Backend**: `kie.charts.builders.line.LineChartBuilder`
**Frontend**: `web/src/components/charts/LineChart.tsx`

---

### 3. Area Chart (`type: "area"`)

**Use Cases**: Cumulative trends, volume over time

**Config Structure**:
```json
{
  "xAxis": {...},
  "yAxis": {...},
  "areas": [
    {
      "dataKey": "Revenue",
      "fill": "#7823DC",
      "stroke": "#7823DC",
      "strokeWidth": 2,
      "fillOpacity": 0.6
    }
  ],
  "stackId": null
}
```

**Backend**: `kie.charts.builders.area.AreaChartBuilder`
**Frontend**: `web/src/components/charts/AreaChart.tsx`

---

### 4. Pie Chart (`type: "pie"`)

**Use Cases**: Part-to-whole relationships (2-4 segments only per KDS)

**Data Format**:
```json
[
  {"name": "North", "value": 45},
  {"name": "South", "value": 30},
  {"name": "East", "value": 25}
]
```

**Config Structure**:
```json
{
  "pie": {
    "dataKey": "value",
    "nameKey": "name",
    "cx": "50%",
    "cy": "50%",
    "innerRadius": 0,
    "outerRadius": 80,
    "paddingAngle": 2,
    "label": {"position": "outside", "fontSize": 12}
  },
  "colors": ["#7823DC", "#9150E1", "#AF7DEB", "#C8A5F0"]
}
```

**Backend**: `kie.charts.builders.pie.PieChartBuilder`
**Frontend**: `web/src/components/charts/PieChart.tsx`

---

### 5. Scatter Chart (`type: "scatter"`)

**Use Cases**: Correlation, distribution analysis

**Config Structure**:
```json
{
  "xAxis": {...},
  "yAxis": {...},
  "scatter": {
    "dataKey": "Revenue",
    "fill": "#7823DC",
    "shape": "circle"
  }
}
```

**Backend**: `kie.charts.builders.scatter.ScatterChartBuilder`
**Frontend**: `web/src/components/charts/ScatterChart.tsx`

---

### 6. Combo Chart (`type: "combo"`)

**Use Cases**: Multi-dimensional comparisons (bar + line)

**Config Structure**:
```json
{
  "xAxis": {...},
  "yAxis": {...},
  "bars": [{...}],
  "lines": [{...}]
}
```

**Backend**: `kie.charts.builders.combo.ComboChartBuilder`
**Frontend**: `web/src/components/charts/ComboChart.tsx`

---

## KDS Compliance Requirements

**MANDATORY for ALL charts**:

1. **No Gridlines**: `config.gridLines` MUST be `false`
2. **No Axis Lines**: `xAxis.axisLine` and `yAxis.axisLine` MUST be `false`
3. **No Tick Lines**: `xAxis.tickLine` and `yAxis.tickLine` MUST be `false`
4. **KDS Colors Only**: Use colors from `kie.brand.colors.KDSColors`
5. **Inter Font**: `config.fontFamily` MUST include "Inter"
6. **Pie Chart Segments**: Max 4 segments (KDS rule)

**Validator**: `kie.brand.validator.ChartBrandValidator`

---

## Smart Number Formatting

**Backend Integration**:
```python
from kie.charts.formatting import format_number, format_currency, format_percentage

# Attach formatters to config
config["formatters"] = {
    "xAxis": {"type": "number", "abbreviate": True},
    "yAxis": {"type": "currency", "currency": "$"},
    "tooltip": {"type": "percentage"}
}
```

**Frontend Integration**:
```typescript
// React component reads formatters from config
const formatValue = (value: number) => {
  if (config.formatters?.yAxis?.type === "currency") {
    return formatCurrency(value);
  }
  // ...
};
```

**See**: `kie/charts/formatting.py`, `web/src/utils/formatters.ts`

---

## Validation

### Schema Validation

```python
from kie.charts.schema import BarChartConfig, RechartsSchema

# Validate config structure
config = BarChartConfig(**config_dict)
chart_json = RechartsSchema(
    type="bar",
    data=data,
    config=config.model_dump()
)
```

### Brand Validation

```python
from kie.brand.validator import ChartBrandValidator

validator = ChartBrandValidator()
result = validator.validate(chart_json.model_dump())

if not result["compliant"]:
    raise ValueError(f"KDS violations: {result['violations']}")
```

---

## Backend Usage

```python
from kie.charts import ChartFactory
import pandas as pd

# Create data
data = pd.DataFrame({
    'region': ['North', 'South', 'East'],
    'revenue': [125000, 98000, 142000]
})

# Build chart
chart = ChartFactory.bar(
    data=data,
    x='region',
    y=['revenue'],
    title='Q3 Revenue by Region'
)

# Save JSON (contract-compliant)
chart.to_json('outputs/charts/revenue.json')
```

---

## Frontend Usage

```tsx
import { ChartRenderer } from '@/components/charts/ChartRenderer';

function Dashboard() {
  return (
    <ChartRenderer
      configPath="/charts/revenue.json"
      fallback={<ChartSkeleton />}
    />
  );
}
```

**ChartRenderer** reads `type` field and routes to correct component:
- `type: "bar"` → `<BarChart />`
- `type: "line"` → `<LineChart />`
- etc.

---

## File Locations

### Backend (`kie/` package)
- **Contract Definition**: `kie/base.py` (`RechartsConfig` class)
- **Schema Types**: `kie/charts/schema.py`
- **Builders**: `kie/charts/builders/*.py`
- **Factory**: `kie/charts/__init__.py` (`ChartFactory`)
- **Formatters**: `kie/charts/formatting.py`
- **Validator**: `kie/brand/validator.py`

### Frontend (`web/` package)
- **Chart Components**: `web/src/components/charts/*.tsx`
- **Router**: `web/src/components/charts/ChartRenderer.tsx`
- **Formatters**: `web/src/utils/formatters.ts`
- **Types**: `web/src/types/charts.ts`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2026-01-15 | Initial contract definition |

---

## References

- **KDS Guidelines**: `kds/KDS_AI_GUIDELINES.md`
- **Chart Excellence Plan**: `docs/KIE_V3_ROADMAP.md` (section 3)
- **Backend Architecture**: `kie/charts/README.md`
- **Frontend Architecture**: `web/README.md`
