# KIE Chart Type Audit

**Date**: 2026-01-13
**Issue**: Chart types without clear use cases detected during remediation

---

## Current State

### Chart Types in ChartFactory (11 total)

| Chart Type | Status | Use Case | InsightType Mapping |
|------------|--------|----------|---------------------|
| `bar` | ✅ ACTIVE | Comparison, concentration, outliers, benchmarks | COMPARISON, CONCENTRATION, OUTLIER, BENCHMARK |
| `horizontal_bar` | ❓ UNUSED | Unknown | None |
| `stacked_bar` | ❓ UNUSED | Unknown | None |
| `line` | ✅ ACTIVE | Trends over time | TREND |
| `area` | ❓ UNUSED | Unknown | None |
| `stacked_area` | ❓ UNUSED | Unknown | None |
| `pie` | ❓ UNUSED | Unknown | None |
| `donut` | ❓ UNUSED | Unknown | None |
| `scatter` | ✅ ACTIVE | Correlation, relationships | CORRELATION |
| `combo` | ❓ UNUSED | Unknown | None |
| `waterfall` | ❓ UNUSED | Unknown | None |

### Chart Types in VisualizationPlanner (4 total)

| Type | Purpose | Works? |
|------|---------|--------|
| `bar` | Comparison, concentration | ✅ YES |
| `line` | Trend | ✅ YES |
| `scatter` | Correlation/risk | ✅ YES |
| `histogram` | Distribution | ⚠️ **NO** - Not in ChartFactory |

---

## Problems

### Problem 1: Histogram Mismatch
- VisualizationPlanner maps DISTRIBUTION → "histogram"
- ChartFactory has NO "histogram" type
- **Impact**: Distribution insights fail to render

### Problem 2: Unused Chart Types (7 types)
- horizontal_bar, stacked_bar, area, stacked_area, pie, donut, combo, waterfall
- Built but never selected by VisualizationPlanner
- **Impact**: Dead code, maintenance burden

### Problem 3: No Clear Business Use Cases
- Which consulting scenarios need stacked_area vs line?
- When would consultants prefer waterfall vs bar?
- Are pie/donut charts KDS-compliant? (4 slice max rule?)

---

## Recommended Actions

### HIGH PRIORITY: Fix Histogram Mismatch

**Option A**: Map DISTRIBUTION → bar (histogram-style)
```python
InsightType.DISTRIBUTION: ("bar", "distribution"),  # Bar chart formatted as histogram
```

**Option B**: Add "histogram" to ChartFactory
```python
ChartType = Literal[
    "bar", "horizontal_bar", "stacked_bar",
    "line", "area", "stacked_area",
    "pie", "donut",
    "scatter",
    "combo",
    "waterfall",
    "histogram"  # NEW
]
```

**Recommendation**: Option A (use bar with histogram styling) - simpler, no new chart type needed

### MEDIUM PRIORITY: Define Use Cases for Existing Types

**Stacked Bar**:
- Use case: Show composition within categories (e.g., Revenue by Region + Product Line)
- InsightType mapping: COMPOSITION (new type?) or CONCENTRATION with grouping
- KDS rules: Max 4 stack segments, labeled

**Horizontal Bar**:
- Use case: Long category names (>15 chars), many categories (>8)
- InsightType mapping: COMPARISON (auto-switch when >8 categories)
- KDS rules: Same as bar, rotated

**Area Chart**:
- Use case: Emphasize magnitude of trend (cumulative effect)
- InsightType mapping: TREND with emphasis="magnitude"
- KDS rules: Semi-transparent fill, KDS purple

**Stacked Area**:
- Use case: Show composition over time (e.g., Revenue by Product Line over quarters)
- InsightType mapping: TREND + COMPOSITION
- KDS rules: Max 4 series, KDS palette order

**Pie/Donut**:
- Use case: Show part-to-whole (STRICT: max 4 slices per KDS)
- InsightType mapping: CONCENTRATION when <5 categories
- KDS rules: Max 4 slices, KDS palette, data labels outside

**Combo Chart**:
- Use case: Two different scales (e.g., Revenue bars + Margin% line)
- InsightType mapping: DUAL_METRIC (new type?) or COMPARISON with secondary metric
- KDS rules: Primary on bars, secondary on line, clear legend

**Waterfall**:
- Use case: Show cumulative effect of sequential changes (Budget → Actual)
- InsightType mapping: DRIVER or CONTRIBUTION
- KDS rules: Green for positive, purple for negative (exception to no-green rule?)

### LOW PRIORITY: Remove Truly Unused Types

If no use cases emerge:
- Consider deprecating: stacked_area, combo, waterfall
- Focus on consultant-essential charts: bar, line, scatter

---

## Next Steps

1. **Immediate**: Fix histogram mismatch (Option A)
2. **Short-term**: Document use cases for each chart type
3. **Medium-term**: Add InsightType mappings for all kept types
4. **Long-term**: Deprecate/remove charts with no consulting use cases

---

**Status**: OPEN - Requires product decision on chart portfolio strategy
