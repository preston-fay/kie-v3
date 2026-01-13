# KIE Chart Excellence Plan
**Mission**: Make KIE charts consultant-grade impressive, not just functional

**Date**: 2026-01-13
**Status**: PROPOSED - Ready for implementation

---

## Philosophy: Multiple Versions + User Choice

**Problem**: We've been too conservative - only generating ONE chart per insight
**Solution**: Generate MULTIPLE versions and let consultants choose the best

### Multi-Version Output Strategy

**For SVG/PNG exports** (presentations, reports):
- Generate 2-3 versions of each chart automatically
- Save all versions with suffixes: `_bar.json`, `_horizontal.json`, `_combo.json`
- Let consultant pick the most impactful version

**For dashboards**:
- Present radio buttons: "View as: [Bar] [Horizontal] [Stacked]"
- Real-time switching without re-render
- Remember user preference per insight

**For CLI**:
- `/build --preview` shows thumbnails of all versions
- User selects: "Use version 2 for Insight A, version 1 for Insight B"
- Interactive selection mode

---

## Full Chart Type Portfolio with Clear Use Cases

### Tier 1: Always Active (Core 4)

#### 1. Bar Chart (Vertical)
**Use Case**: Standard comparison, <8 categories, short labels
**InsightType**: COMPARISON, CONCENTRATION, OUTLIER, BENCHMARK
**When to Auto-Select**: Default for comparisons
**Example**: "Q3 Revenue by Region" - 4 regions

#### 2. Line Chart
**Use Case**: Trends over time, sequential data
**InsightType**: TREND
**When to Auto-Select**: Any time-series data detected
**Example**: "Monthly Sales Growth (Jan-Dec)"

#### 3. Scatter Plot
**Use Case**: Correlation, relationships, risk analysis
**InsightType**: CORRELATION
**When to Auto-Select**: Two continuous variables
**Example**: "Marketing Spend vs Revenue"

#### 4. Horizontal Bar Chart
**Use Case**: Comparison with long labels OR many categories (>8)
**InsightType**: COMPARISON, CONCENTRATION (auto-switch from bar)
**When to Auto-Select**: Category labels >15 chars OR >8 categories
**Example**: "Revenue by Customer Name" - 12 customers with long names

---

### Tier 2: Situational Enhancements (Add Sophistication)

#### 5. Stacked Bar Chart
**Use Case**: Show composition within categories (part-to-whole by category)
**InsightType**: COMPOSITION (NEW), CONCENTRATION with grouping
**When to Auto-Select**: 2 dimensions detected (e.g., Region + Product Line)
**KDS Rules**: Max 4 stack segments, labeled
**Example**: "Revenue by Region" stacked by "Product Line" (4 product lines)
**Multi-Version**: Generate BOTH vertical bar AND stacked bar

#### 6. Area Chart
**Use Case**: Emphasize magnitude/volume of trend (cumulative effect)
**InsightType**: TREND with `emphasis="magnitude"`
**When to Auto-Select**: Growth trends, cumulative metrics
**KDS Rules**: Semi-transparent fill (0.7 opacity), KDS purple
**Example**: "Cumulative Sales Growth YTD"
**Multi-Version**: Generate BOTH line AND area for trend insights

#### 7. Stacked Area Chart
**Use Case**: Show composition over time (how parts contribute to whole across time)
**InsightType**: TREND + COMPOSITION
**When to Auto-Select**: Time series WITH breakdown (e.g., Revenue by Product Line over Quarters)
**KDS Rules**: Max 4 series, KDS palette order
**Example**: "Quarterly Revenue by Product Line (Q1-Q4)"
**Multi-Version**: Generate line, area, AND stacked area

#### 8. Pie Chart
**Use Case**: Simple part-to-whole, max 4 categories
**InsightType**: CONCENTRATION (when ≤4 categories)
**When to Auto-Select**: Exactly 3-4 categories, asking "what's the share?"
**KDS Rules**: STRICT max 4 slices, data labels outside, KDS palette
**Example**: "Market Share by Top 4 Competitors"
**Multi-Version**: Generate BOTH pie AND bar

#### 9. Donut Chart
**Use Case**: Part-to-whole with emphasis on total in center
**InsightType**: CONCENTRATION (when ≤4 categories, with total emphasis)
**When to Auto-Select**: Same as pie, but when total value matters
**KDS Rules**: STRICT max 4 slices, center shows total/key metric
**Example**: "Revenue Mix (Total: $4.2M)" - 4 product lines
**Multi-Version**: Generate pie, donut, AND bar

#### 10. Combo Chart (Bar + Line)
**Use Case**: Two different scales (absolute vs rate, volume vs efficiency)
**InsightType**: DUAL_METRIC (NEW) or COMPARISON with secondary metric
**When to Auto-Select**: Two metrics detected: one absolute (revenue) + one rate (margin%)
**KDS Rules**: Primary metric on bars, secondary on line, clear legend, dual Y-axes
**Example**: "Revenue (bars) vs Gross Margin % (line)" by quarter
**Multi-Version**: Generate bar only, line only, AND combo

#### 11. Waterfall Chart
**Use Case**: Show cumulative effect of sequential changes (bridge analysis)
**InsightType**: DRIVER, CONTRIBUTION, VARIANCE
**When to Auto-Select**: "Budget vs Actual", "Starting → Ending", "Variance breakdown"
**KDS Rules**:
  - **EXCEPTION**: Use green for positive, red for negative (override no-green rule for this chart ONLY)
  - Connecting lines between bars
  - Start/End bars in different color (purple)
**Example**: "Budget $10M → Actual $8.5M" (Labor -$1M, Materials -$0.8M, Overhead +$0.3M)
**Multi-Version**: Generate waterfall AND stacked bar

---

## New InsightType Values (Expand Vocabulary)

Add to `kie/insights/schema.py`:

```python
class InsightType(Enum):
    """Types of insights that can be generated."""
    COMPARISON = "comparison"          # Existing
    TREND = "trend"                    # Existing
    DISTRIBUTION = "distribution"      # Existing
    CORRELATION = "correlation"        # Existing
    OUTLIER = "outlier"               # Existing
    CONCENTRATION = "concentration"    # Existing
    VARIANCE = "variance"             # Existing
    BENCHMARK = "benchmark"           # Existing

    # NEW (for sophisticated charts)
    COMPOSITION = "composition"        # Part-to-whole by category (stacked bar/pie)
    DUAL_METRIC = "dual_metric"       # Two scales (combo chart)
    CONTRIBUTION = "contribution"      # Sequential changes (waterfall)
    DRIVER = "driver"                 # What drives the outcome (waterfall, scatter)
```

---

## Implementation: Multi-Version Generation

### Phase 1: Expand VisualizationPlanner Mappings

```python
# FILE: kie/skills/visualization_planner.py

INSIGHT_TYPE_TO_CHART_TYPE = {
    InsightType.COMPARISON: [
        ("bar", "comparison"),                    # Primary
        ("horizontal_bar", "comparison"),         # Alternative (if long labels)
    ],
    InsightType.TREND: [
        ("line", "trend"),                        # Primary
        ("area", "trend"),                        # Alternative (emphasis on magnitude)
    ],
    InsightType.DISTRIBUTION: [
        ("bar", "distribution"),                  # Primary (histogram-style)
    ],
    InsightType.CORRELATION: [
        ("scatter", "risk"),                      # Primary
    ],
    InsightType.CONCENTRATION: [
        ("bar", "concentration"),                 # Primary
        ("pie", "concentration"),                 # Alternative (if ≤4 categories)
        ("donut", "concentration"),               # Alternative (if ≤4 categories, total matters)
    ],
    InsightType.OUTLIER: [
        ("bar", "comparison"),                    # Primary (with highlighting)
    ],
    InsightType.VARIANCE: [
        ("bar", "distribution"),                  # Primary
    ],
    InsightType.BENCHMARK: [
        ("bar", "comparison"),                    # Primary
    ],

    # NEW InsightTypes
    InsightType.COMPOSITION: [
        ("stacked_bar", "composition"),           # Primary
        ("pie", "composition"),                   # Alternative (if ≤4 categories)
        ("donut", "composition"),                 # Alternative (if ≤4 categories)
    ],
    InsightType.DUAL_METRIC: [
        ("combo", "dual_metric"),                 # Primary
        ("bar", "comparison"),                    # Alternative (primary metric only)
    ],
    InsightType.CONTRIBUTION: [
        ("waterfall", "contribution"),            # Primary
        ("stacked_bar", "composition"),           # Alternative
    ],
}
```

### Phase 2: Modify ChartRenderer to Generate Multiple Versions

```python
# FILE: kie/charts/renderer.py

def render_charts(self, generate_alternatives: bool = True) -> dict:
    """
    Render charts from visualization plan.

    Args:
        generate_alternatives: If True, generate 2-3 versions per insight

    Returns:
        {
            "primary_charts": [...],
            "alternative_charts": [...],  # NEW
            "versions_by_insight": {      # NEW
                "insight-1": ["bar", "horizontal_bar"],
                "insight-2": ["line", "area"]
            }
        }
    """
    # For each insight, generate PRIMARY + ALTERNATIVES
    for insight in insights:
        chart_types = planner.get_chart_types(insight)  # Returns list

        for i, (chart_type, purpose) in enumerate(chart_types):
            suffix = "" if i == 0 else f"_alt{i}"
            chart_config = ChartFactory.create(
                chart_type=chart_type,
                data=data,
                **config
            )

            output_path = charts_dir / f"{insight_id}{suffix}.json"
            chart_config.to_json(output_path)
```

### Phase 3: Add Interactive Selection to CLI

```python
# FILE: kie/commands/handler.py

def handle_build(self, preview: bool = False, interactive: bool = False):
    """
    Build deliverables.

    Args:
        preview: Show thumbnails of all chart versions
        interactive: Let user select preferred version
    """
    if preview or interactive:
        # Generate all versions
        result = renderer.render_charts(generate_alternatives=True)

        # Show thumbnails (ASCII art or base64 preview)
        self._show_chart_previews(result["versions_by_insight"])

        if interactive:
            # Prompt user to select versions
            selections = self._prompt_version_selection(result["versions_by_insight"])
            # Use selected versions only
            self._apply_selections(selections)
```

---

## Auto-Selection Intelligence (When to Use Each Chart)

### Horizontal Bar Auto-Switch Logic

```python
def _should_use_horizontal_bar(data: pd.DataFrame, x_column: str) -> bool:
    """Decide if horizontal bar is better than vertical."""
    # Check label length
    max_label_length = data[x_column].astype(str).str.len().max()
    if max_label_length > 15:
        return True  # Long labels -> horizontal

    # Check category count
    if len(data) > 8:
        return True  # Many categories -> horizontal

    return False
```

### Stacked Bar Auto-Detection

```python
def _detect_stacked_opportunity(insight: dict, data: pd.DataFrame) -> bool:
    """Detect if stacked bar would add value."""
    # Check for 2D structure: Category + Sub-category
    if "grouping" in insight and insight["grouping"]:
        unique_groups = data[insight["grouping"]].nunique()
        if 2 <= unique_groups <= 4:  # KDS max 4 stacks
            return True

    return False
```

### Pie/Donut Auto-Qualification

```python
def _qualifies_for_pie(data: pd.DataFrame) -> bool:
    """Check if data qualifies for pie chart (KDS rules)."""
    num_categories = len(data)
    if num_categories < 2 or num_categories > 4:
        return False  # KDS: 2-4 slices only

    # Check if percentages sum to ~100%
    if "percentage" in data.columns:
        total = data["percentage"].sum()
        if abs(total - 100) < 5:  # Within 5% of 100
            return True

    return False
```

### Combo Chart Detection

```python
def _detect_dual_metric(insight: dict) -> tuple[str | None, str | None]:
    """Detect if insight has two metrics on different scales."""
    evidence = insight.get("evidence", [])

    metrics = []
    for e in evidence:
        if e.get("evidence_type") == "metric":
            metrics.append((e.get("label"), e.get("value")))

    if len(metrics) == 2:
        # Heuristic: One is absolute (>1000), one is rate (<10)
        m1_val = metrics[0][1]
        m2_val = metrics[1][1]

        if abs(m1_val) > 1000 and abs(m2_val) < 10:
            return metrics[0][0], metrics[1][0]  # (primary, secondary)

    return None, None
```

### Waterfall Triggers

```python
def _should_use_waterfall(insight: dict, title: str) -> bool:
    """Detect waterfall chart scenarios."""
    waterfall_keywords = [
        "budget vs actual", "variance", "bridge",
        "starting", "ending", "contribution", "driver",
        "what explains", "breakdown of change"
    ]

    text = (title + " " + insight.get("why_it_matters", "")).lower()
    return any(kw in text for kw in waterfall_keywords)
```

---

## Waterfall Chart: Green Exception Policy

**Special KDS Exception for Waterfall Only:**

```python
# FILE: kie/brand/colors.py

class KDSColors:
    # ... existing colors ...

    # Waterfall-specific colors (ONLY EXCEPTION to no-green rule)
    WATERFALL_POSITIVE = "#00AA66"  # Muted green (positive variance)
    WATERFALL_NEGATIVE = "#DC143C"  # Crimson red (negative variance)
    WATERFALL_TOTAL = PRIMARY        # Kearney purple (start/end bars)
```

**Rationale**:
- Waterfall charts are universally understood as green=good, red=bad
- This is a **consulting convention** - breaking it would confuse clients
- **STRICT SCOPE**: Only waterfall charts, no other chart type
- Still uses KDS purple for start/end/total bars

---

## Preview & Selection UX

### CLI Preview Mode

```bash
$ python3 -m kie.cli build --preview

📊 Chart Preview - Insight 1: "Q3 Revenue by Region"

[1] Vertical Bar        [2] Horizontal Bar      [3] Stacked Bar (by Product)
   |█  |█                 North ████████         |███|██  |████
   |██ |██                South ██████           |██ |███ |██
   |███|█                 East ██████████        |███|█   |███
   |██ |███               West ████              |██ |██  |██
   CA TX NY FL            $0M    $1M             CA TX NY FL

Which version(s) do you want? [1,2,3] (default: 1): 1,3

✅ Selected: Vertical Bar + Stacked Bar
```

### Dashboard Radio Buttons

```tsx
// web/src/components/ChartSelector.tsx

<ChartControls>
  <VersionSelector>
    View as:
    <RadioButton value="bar" checked>Bar</RadioButton>
    <RadioButton value="horizontal_bar">Horizontal</RadioButton>
    <RadioButton value="stacked_bar">Stacked</RadioButton>
  </VersionSelector>
</ChartControls>
```

---

## Implementation Sequence

### Sprint 1: Foundation (Week 1)
- [ ] Add new InsightType values (COMPOSITION, DUAL_METRIC, CONTRIBUTION)
- [ ] Expand INSIGHT_TYPE_TO_CHART_TYPE to return lists
- [ ] Implement auto-detection functions (horizontal, stacked, pie, combo, waterfall)
- [ ] Update tests

### Sprint 2: Multi-Version Generation (Week 2)
- [ ] Modify ChartRenderer to generate alternatives
- [ ] Add suffix logic (_alt1, _alt2, etc.)
- [ ] Create version manifest JSON
- [ ] Test with real data

### Sprint 3: Selection UX (Week 3)
- [ ] Add --preview flag to CLI
- [ ] Create ASCII chart previews
- [ ] Add --interactive flag for selection
- [ ] Dashboard radio buttons

### Sprint 4: Waterfall + Polish (Week 4)
- [ ] Implement waterfall chart builder
- [ ] Add green/red exception for waterfall
- [ ] Combo chart builder
- [ ] Stacked variants (bar, area)
- [ ] Final testing & battery update

---

## Success Criteria

**Consultant Delight Metrics:**
- ✅ Every InsightType has 2-3 chart options
- ✅ User can preview all versions before building
- ✅ Interactive selection reduces "that's not what I wanted" moments
- ✅ Waterfall charts look professional (green/red convention)
- ✅ Combo charts handle dual scales correctly
- ✅ Stacked charts respect KDS 4-segment max
- ✅ Pie/donut auto-qualify only when appropriate (≤4 categories)

**Technical Quality:**
- ✅ All 11 chart types have documented use cases
- ✅ Auto-detection works 80% of the time (user override available)
- ✅ Multi-version generation doesn't slow build >20%
- ✅ Battery tests cover all chart types

---

## Chart Type Usage Summary (After Plan)

| Chart Type | Status | Use Case | Auto-Selected When |
|------------|--------|----------|-------------------|
| `bar` | ✅ ACTIVE | Standard comparison | Default for COMPARISON |
| `horizontal_bar` | ✅ ACTIVE | Long labels, many categories | >8 categories OR labels >15 chars |
| `stacked_bar` | ✅ ACTIVE | Composition by category | 2D data (Category + Subcategory) |
| `line` | ✅ ACTIVE | Time trends | TREND InsightType |
| `area` | ✅ ACTIVE | Magnitude emphasis | TREND with growth/cumulative |
| `stacked_area` | ✅ ACTIVE | Composition over time | Time series + breakdown |
| `pie` | ✅ ACTIVE | Part-to-whole (≤4 slices) | CONCENTRATION with 2-4 categories |
| `donut` | ✅ ACTIVE | Part-to-whole + total | CONCENTRATION with 2-4 categories + total matters |
| `scatter` | ✅ ACTIVE | Correlation | CORRELATION InsightType |
| `combo` | ✅ ACTIVE | Dual scales | DUAL_METRIC (absolute + rate) |
| `waterfall` | ✅ ACTIVE | Sequential changes | CONTRIBUTION, budget vs actual |

**ALL 11 CHART TYPES ACTIVATED** ✅

---

**Status**: READY FOR IMPLEMENTATION
**Estimated Effort**: 4 weeks (4 sprints)
**Impact**: Transform KIE from functional to consultant-impressive
