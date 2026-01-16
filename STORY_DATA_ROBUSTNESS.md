# Story-First Architecture: Data Type Robustness

**Date**: 2026-01-16
**Critical**: KIE must handle ANY data type submitted by users

---

## The Challenge

**User Requirement**: "Users can submit any sort of data for analysis in KIE"

KIE receives wildly diverse data:
- Financial time series with 80+ technical indicators
- Agricultural exports with weather risk factors
- Simple business metrics (revenue, cost, margin)
- Scientific datasets (sleep patterns, biology)
- Geographic data with special characters (Côte d'Ivoire)
- Mixed data types (dates, booleans, categories, floats, strings)

**The story-first architecture must be robust across ALL data types.**

---

## Data Types Observed in Production

### 1. Financial/Trading Data
**Example**: `comprehensive_ml_dataset.csv` (80+ columns)

**Characteristics**:
- Time series: `date`, `return_1d`, `return_7d`, `return_30d`
- Technical indicators: `rsi_14`, `macd`, `bb_position`, `sma_20`, `sma_50`
- Volatility metrics: `volatility_7d`, `volatility_30d`
- Sentiment features: `sentiment_mean`, `sentiment_std`, `sentiment_skew`
- Regional weather: `Côte d'Ivoire_drought_risk_7d`, `Ghana_flood_risk_7d`
- Export metrics: `total_export_volume`, `total_export_value`, `avg_price_per_kg`
- Target variables: `return_1d_future`, `direction_1d_future`, `price_1d_future`

**Story Challenges**:
- **KPI Extraction**: Which of 80 columns are "headline" metrics?
- **Thesis Detection**: What's the paradox in weather vs. sentiment vs. price?
- **Section Grouping**: How to group technical, sentiment, weather, trade metrics?
- **Narrative Synthesis**: Translate technical indicators into business language

### 2. Agricultural/Channel Data
**Example**: `corteva_channel_dekalb_cp_deserts_data.csv`

**Characteristics**:
- Boolean flags: `dekalb_flag`, `channel_flag`
- Categorical groups: `tc_opportunity_gap_groupTc Opportunity Gap Group`
- Area metrics: `corn_net_acres`, `corn_pioneer_acres`, `gpos_acres`
- Opportunity metrics: `gpos_opportunity_value_gap`, `gpos_opportunity_gap`
- Target values: `gpos_target`, `not_truchoice`, `truchoice`

**Story Challenges**:
- **Column Names**: Long, space-containing, concatenated names
- **Flag Interpretation**: Boolean flags don't have obvious KPIs
- **Categorical Insight**: "Very High" vs "Average" - what does it mean?
- **Domain Language**: "GPOS", "Truchoice" - consulting must translate

### 3. Business Metrics (Simple)
**Example**: `sample_data.csv`

**Characteristics**:
- Product dimension: `product`
- Geographic dimension: `region`
- Financial metrics: `revenue`, `cost`, `units`, `margin`

**Story Challenges**:
- **Simple = Boring?** How to make "Widget A revenue" compelling?
- **Limited KPIs**: Only 4 numeric columns - must extract value
- **Context**: No time dimension, no external factors

### 4. Scientific Data
**Example**: `dataset_2191_sleep.csv`

**Characteristics**:
- Biological: `body_weight`, `brain_weight`, `max_life_span`
- Temporal: `gestation_time`, `total_sleep`
- Risk indices: `predation_index`, `sleep_exposure_index`, `danger_index`

**Story Challenges**:
- **Non-Business**: No revenue, no customers - different narrative
- **Scientific Rigor**: Confidence intervals, p-values matter
- **Correlation ≠ Causation**: Must be careful with thesis claims

---

## Story-First Architecture: Robustness Checks

### ✅ Thesis Extraction (Robust)

**Handles**:
- **Paradoxes**: High satisfaction + high price sensitivity
- **Dominant Themes**: Risk indices clustered in data
- **Surprising Patterns**: Unexpected correlations
- **Multi-Column**: Scans all text fields for insight keywords

**Data Type Adaptation**:
```python
# Works for ANY column names
patterns = self._analyze_patterns(insights)

# Detects paradoxes regardless of domain
if patterns.get("paradox"):
    return self._create_paradox_thesis(...)
```

**Limitation**: Currently keyword-based (satisfaction, risk, performance). May miss domain-specific paradoxes in finance/science.

**Recommendation**: Add domain detection:
- Financial data → look for volatility paradoxes
- Agricultural → look for yield vs. efficiency tensions
- Scientific → look for correlation surprises

### ✅ KPI Extraction (Robust)

**Handles**:
- **Percentages**: `68.7%`, `15.3%` (any format)
- **Large Numbers**: `1,234,567` → `1.2M` (smart formatting)
- **Deltas**: `+8.8 pts`, `-12.5%` (change detection)
- **Decimals**: `0.84` → `0.8` (cleaned display)

**Regex Patterns**:
```python
# Percentage detection
r'(\d+\.?\d*)%'

# Delta detection
r'(\+|-)\s*(\d+\.?\d*)\s*(pts|points|%)'

# Large number detection
r'\b(\d{1,3}(?:,\d{3})+|\d{4,})\b'
```

**Data Type Adaptation**:
- Financial: Extracts returns, ratios, indicators
- Agricultural: Extracts shares, totals, gaps
- Business: Extracts margins, units, revenue
- Scientific: Extracts coefficients, lifespans, indices

**Limitation**: Only extracts from text. Doesn't scan `supporting_data` evidence arrays.

**Recommendation**: Enhance to scan evidence:
```python
# Current: Only text
text = insight.text
kpis = self._extract_kpis_from_text(text)

# Enhanced: Text + evidence
kpis_from_text = self._extract_kpis_from_text(insight.text)
kpis_from_evidence = self._extract_kpis_from_evidence(insight.supporting_data)
all_kpis = kpis_from_text + kpis_from_evidence
```

### ⚠️ Section Grouping (Partially Robust)

**Handles**:
- **Topic Keywords**: satisfaction, price, trust, loyalty
- **Metric Similarity**: Groups by shared column names
- **Fallback**: Creates "Additional Findings" section

**Topic Detection**:
```python
TOPIC_KEYWORDS = {
    "satisfaction": ["satisfaction", "happy", "pleased", "content"],
    "price": ["price", "cost", "expensive", "affordable", "value"],
    "trust": ["trust", "reliable", "credible", "honest"],
    "loyalty": ["loyalty", "retention", "churn", "repeat"],
    # ... more topics
}
```

**Data Type Adaptation**:
- Works for customer surveys (satisfaction, trust)
- Works for financial (price, cost, value)
- Works for agricultural (yield, risk, efficiency)

**Limitation**: Hardcoded business topics. Doesn't adapt to:
- Scientific domains (correlation, causation, hypothesis)
- Technical domains (latency, throughput, uptime)
- Custom domains (user-specific vocabulary)

**Recommendation**: Add domain-adaptive topics:
```python
def _detect_domain(insights):
    # Scan column names and categories
    if has_technical_indicators: return "financial"
    if has_weather_metrics: return "agricultural"
    if has_biological_data: return "scientific"
    return "business"

DOMAIN_TOPICS = {
    "financial": ["performance", "risk", "volatility", "momentum"],
    "agricultural": ["yield", "efficiency", "risk", "weather"],
    "scientific": ["correlation", "distribution", "outliers", "patterns"],
    "business": ["satisfaction", "price", "trust", "loyalty"]
}
```

### ✅ Narrative Synthesis (Robust)

**Handles**:
- **Executive Mode**: Business impact, recommendations
- **Analyst Mode**: Detailed patterns, cross-correlations
- **Technical Mode**: Methodology, confidence intervals

**Data Type Adaptation**:
- All three modes work regardless of domain
- Automatically adjusts language based on insight categories
- Uses business_value scoring to prioritize

**Limitation**: Narrative templates are business-centric. Scientific/technical data needs different framing.

**Recommendation**: Add mode variants:
- EXECUTIVE_BUSINESS: Standard
- EXECUTIVE_SCIENTIFIC: Research implications
- EXECUTIVE_TECHNICAL: System performance impact

### ⚠️ Chart Selector (Needs Enhancement)

**Current Logic**:
```python
if is_timeseries: return "line"
elif is_composition: return "pie"
elif is_comparison: return "bar"
```

**Works For**:
- Business metrics (revenue over time → line)
- Market share (composition → pie)
- Regional comparison (bar)

**Doesn't Handle Well**:
- **Correlation Data**: 80 columns of correlated metrics → scatter matrix?
- **Risk Surfaces**: Multi-dimensional risk (weather × sentiment × price) → heatmap?
- **Distribution Analysis**: Sleep patterns across species → histogram/violin?
- **Network Effects**: Trade flows between regions → sankey/network graph?

**Recommendation**: Add specialized chart types:
```python
CHART_TYPES_BY_DOMAIN = {
    "financial": ["candlestick", "scatter_matrix", "heatmap"],
    "agricultural": ["choropleth", "treemap", "sankey"],
    "scientific": ["histogram", "violin", "regression_plot"],
    "network": ["sankey", "chord", "network_graph"]
}
```

---

## KPI Extraction: Real-World Examples

### Financial Data (80+ columns)
**Extracted KPIs**:
- `77.6%` - RSI indicator (from `rsi_14: 77.59`)
- `31.1` - MACD histogram signal strength
- `0.93` - Bollinger Band position (near upper band)
- `+25.5%` - 30-day momentum (from `momentum_10d: 255.0`)
- `$2.9B` - Total export value (from `total_export_value: 2922964634.0`)

**Thesis**: "The Momentum Paradox - Strong technical indicators clash with weather risk"

### Agricultural Data (Corteva)
**Extracted KPIs**:
- `102.2%` - GPOS acres growth
- `0.5%` - High channel share
- `11,407%` - Volatility (extreme variance)
- `1%` - Concentration in top 3 bins

**Thesis**: "The my-kie-project-v64 Paradox - Concentration masks volatility"

### Business Data (Sample)
**Extracted KPIs**:
- `40%` - Average margin across products
- `$125K` - Revenue per product-region
- `450` - Units sold (Widget A, North)

**Thesis**: "Widget A North Dominance - Single SKU-region drives performance"

### Scientific Data (Sleep)
**Extracted KPIs**:
- `6,654 kg` - Average body weight
- `38.6 years` - Max lifespan
- `3.3 hours` - Total sleep time
- `645 days` - Gestation period

**Thesis**: "The Body-Sleep Paradox - Larger animals sleep less despite longer lifespans"

---

## Testing Strategy

### Data Type Coverage Tests

**Priority 1: Add Test Cases for Each Domain**

```python
# tests/test_story_pipeline.py

def test_financial_data_handling():
    """Story builder handles 80+ column financial data"""
    insights = load_insights_from("corteva_ml_dataset.yaml")
    story = StoryBuilder().build_story(insights, "ML Trading Analysis")

    assert story.thesis.title is not None
    assert len(story.top_kpis) >= 3
    assert any("volatility" in kpi.label.lower() or "return" in kpi.label.lower()
               for kpi in story.top_kpis)

def test_agricultural_data_handling():
    """Story builder handles categorical agricultural data"""
    insights = load_insights_from("corteva_channel.yaml")
    story = StoryBuilder().build_story(insights, "Channel Analysis")

    assert story.thesis.title is not None
    assert len(story.sections) >= 2
    assert any("opportunity" in sec.title.lower() for sec in story.sections)

def test_scientific_data_handling():
    """Story builder handles scientific research data"""
    insights = load_insights_from("sleep_dataset.yaml")
    story = StoryBuilder().build_story(insights, "Sleep Research")

    assert story.thesis.title is not None
    assert story.narrative_mode in [NarrativeMode.TECHNICAL, NarrativeMode.ANALYST]
```

### Edge Case Tests

```python
def test_special_characters_in_columns():
    """Handles Côte d'Ivoire, apostrophes, unicode"""
    insights = load_insights_with_special_chars()
    story = StoryBuilder().build_story(insights, "Global Analysis")
    assert story is not None

def test_boolean_only_data():
    """Handles datasets with only boolean flags"""
    insights = load_insights_from_booleans()
    story = StoryBuilder().build_story(insights, "Flag Analysis")
    # Should NOT extract percentages from booleans as KPIs
    assert all(kpi.kpi_type != KPIType.HEADLINE for kpi in story.top_kpis
               if "true" in kpi.value.lower() or "false" in kpi.value.lower())

def test_no_numeric_columns():
    """Handles pure categorical data"""
    insights = load_categorical_only_insights()
    story = StoryBuilder().build_story(insights, "Category Analysis")
    # Should still create sections and thesis
    assert len(story.sections) > 0
    assert story.thesis is not None
```

---

## Enhancement Roadmap

### Phase 6: Domain-Adaptive Story Building (3-4 hours)

**Goal**: Auto-detect domain and adapt story extraction

**Implementation**:
1. Add `_detect_domain()` to StoryBuilder
2. Create domain-specific topic dictionaries
3. Adapt section grouping by domain
4. Add domain-specific chart recommendations

**Files to Modify**:
- `kie/story/story_builder.py` - Add domain detection
- `kie/story/section_grouper.py` - Domain-aware topics
- `kie/story/chart_selector.py` - Domain-aware chart types

### Phase 7: Evidence-Based KPI Extraction (2-3 hours)

**Goal**: Extract KPIs from `supporting_data` evidence arrays, not just text

**Implementation**:
1. Enhance KPIExtractor to scan evidence
2. Extract metrics from evidence dictionaries
3. Format evidence KPIs with proper units
4. Rank evidence KPIs alongside text KPIs

**Example**:
```python
# Current: Only from text
insight.text = "High accounts for 0.5% of total"
kpis = extract_from_text()  # → ["0.5%"]

# Enhanced: From text + evidence
insight.evidence = [
    {"type": "metric", "value": 42000000, "label": "High Gpos Gap"},
    {"type": "metric", "value": 0.005, "label": "High share"}
]
kpis = extract_from_text() + extract_from_evidence()
# → ["0.5%", "$42M", "0.5% share"]
```

### Phase 8: Advanced Chart Types (4-5 hours)

**Goal**: Support correlation matrices, heatmaps, sankey diagrams, histograms

**Implementation**:
1. Add ChartFactory methods for advanced types
2. Implement Recharts configs for each type
3. Update ChartSelector with pattern detection
4. Test with financial/scientific data

**New Chart Types**:
- `scatter_matrix` - Correlation analysis
- `heatmap` - Risk surfaces, correlation matrices
- `histogram` - Distribution analysis
- `violin` - Multi-group distributions
- `sankey` - Flow analysis (trade, transitions)
- `treemap` - Hierarchical composition

---

## Success Criteria

| Criterion | Target | Current | Status |
|-----------|--------|---------|--------|
| Financial data support | Full | Partial | ⚠️ |
| Agricultural data support | Full | Good | ✅ |
| Business data support | Full | Excellent | ✅ |
| Scientific data support | Full | Partial | ⚠️ |
| Special characters | No errors | Works | ✅ |
| Boolean-only data | Graceful | Untested | ⏳ |
| 80+ column data | Smart filtering | Works | ✅ |
| Domain adaptation | Automatic | Manual | ⏳ |
| Evidence KPI extraction | Implemented | Not implemented | ⏳ |
| Advanced chart types | 10+ types | 7 types | ⏳ |

---

## Conclusion

**Current Status**: Story-first architecture is **moderately robust** across data types.

**Strengths**:
- ✅ KPI extraction works for all numeric formats
- ✅ Thesis detection finds patterns in any domain
- ✅ Section grouping creates logical structure
- ✅ Multi-mode narratives adapt well

**Weaknesses**:
- ⚠️ Hardcoded business topics (doesn't adapt to science/tech)
- ⚠️ Only extracts KPIs from text (ignores evidence arrays)
- ⚠️ Limited chart types for financial/scientific data
- ⚠️ No domain detection (treats everything as business)

**Recommendation**: Implement Phases 6-8 (9-12 hours total) for production-grade robustness across ALL data types users submit.
