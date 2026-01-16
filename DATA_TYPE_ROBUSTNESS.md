# Story-First Architecture: Data Type Robustness

**Date**: 2026-01-16
**Critical**: Story architecture must handle ANY data type users submit

---

## The Challenge

**User Requirement**: "Users can submit any sort of data for analysis in KIE"

KIE must handle diverse data sources:
- Financial data (revenue, costs, margins, P&L statements)
- Sales data (transactions, customers, products, territories)
- Operational data (supply chain, logistics, manufacturing metrics)
- HR data (headcount, turnover, compensation, performance)
- Survey data (satisfaction scores, NPS, qualitative responses)
- Market data (competitors, market share, pricing)
- Time-series data (trends, seasonality, forecasts)
- Geospatial data (regions, locations, lat/lon coordinates)
- Mixed data (boolean flags, categories, IDs, metrics)

---

## Current Story Architecture Data Assumptions

### 1. Thesis Extraction (thesis_extractor.py)
**Assumptions**:
- Looks for paradoxes (high satisfaction + high churn)
- Detects dominant themes from insight categories
- Identifies surprise patterns (unexpected correlations)

**Risk**: Overly focused on satisfaction/loyalty patterns
**Example Issue**: Financial P&L data won't have "satisfaction" paradoxes

**Robustness Check**: ✅ Theme detection is category-agnostic
```python
def _create_theme_thesis(self, theme, insights, project_name):
    # Uses insight.category (generic: "finding", "comparison", "trend")
    # NOT hardcoded to "satisfaction" or "loyalty"
```

### 2. KPI Extraction (kpi_extractor.py)
**Assumptions**:
- Extracts percentages (68.7%, 82%)
- Extracts deltas (+15 pts, -8.2%)
- Extracts large numbers (1.2M, 42K)
- Formats using smart numbering (K/M/B abbreviations)

**Risk**: May miss domain-specific KPIs
**Examples**:
- Manufacturing: Yield rates, defect rates, OEE
- HR: Turnover rates, time-to-hire, headcount ratios
- Supply chain: Days of inventory, fill rates, lead times

**Robustness Check**: ✅ Regex-based extraction is format-agnostic
```python
# Matches ANY percentage pattern
percentage_pattern = r'(\d+\.?\d*)%'
# Matches ANY large number
large_num_pattern = r'\b(\d{1,3}(?:,\d{3})+|\d{4,})\b'
```

**Enhancement Needed**: Add domain-specific KPI type detection
```python
# Add to KPIType enum:
RATE = "rate"        # Yield, fill rate, defect rate
RATIO = "ratio"      # Revenue/employee, EBITDA margin
DURATION = "duration" # Days, hours, lead time
INDEX = "index"      # NPS, satisfaction index
```

### 3. Section Grouper (section_grouper.py)
**Assumptions**:
- Groups by topic keywords (satisfaction, price, trust, loyalty)
- Groups by metric similarity
- Falls back to generic sections if no matches

**Risk**: Hardcoded topic keywords are satisfaction-focused
**Example Issue**: Won't recognize "COGS", "gross margin", "EBITDA" sections

**Robustness Check**: ⚠️ Partially robust
```python
# Current topic keywords (satisfaction-biased):
"satisfaction", "loyalty", "price", "trust", "demographics"

# Missing topics:
"revenue", "profitability", "operations", "efficiency",
"growth", "market", "competition", "risk", "compliance"
```

**Enhancement Needed**: Make topic detection data-driven
```python
def _detect_topics_from_insights(self, insights):
    """Extract topics from insight text using frequency analysis"""
    # Count noun phrases in insight text
    # Cluster similar terms (revenue/sales/income)
    # Create sections based on discovered topics
```

### 4. Narrative Synthesizer (narrative_synthesizer.py)
**Assumptions**:
- Executive mode focuses on business impact
- Analyst mode focuses on patterns
- Technical mode focuses on methodology

**Risk**: Generic language may not resonate with domain experts
**Example**: Supply chain exec expects "inventory turns", not "efficiency metrics"

**Robustness Check**: ✅ Mode-based framing is domain-agnostic
```python
# Executive mode synthesizes business implications
# Works for ANY domain (finance, ops, HR, sales)
```

**Enhancement Needed**: Add domain-aware language
```python
# Detect domain from objective or column names
# Use domain-specific terminology in narratives
domain_vocab = {
    "finance": ["EBITDA", "gross margin", "ROI", "burn rate"],
    "supply_chain": ["inventory turns", "fill rate", "lead time"],
    "hr": ["attrition", "time-to-hire", "span of control"],
}
```

---

## Test Data Diversity Analysis

### Current Test Data: Agricultural Retail (Corteva)
```
Columns: R_INCA, dekalb_flag, channel_flag, tc_opportunity_gap_group,
         corn_net_acres, corn_pioneer_acres, gpos_acres,
         gpos_opportunity_value_gap, gpos_opportunity_gap, gpos_target

Data Types:
- Boolean flags (dekalb_flag, channel_flag)
- Categorical (tc_opportunity_gap_group: "High", "Average", "Very High")
- Numeric metrics (acres, opportunity values)
- ID columns (R_INCA)
```

**Story Architecture Handling**:
- ✅ Thesis: "The my-kie-project-v64 Paradox" (generic, works)
- ✅ KPIs: "102.2%", "0.5%", "1%" (extracted successfully)
- ✅ Sections: "Price & Value Perception", "Additional Findings" (reasonable)
- ⚠️ Domain terminology: Uses "Price & Value" for agricultural opportunity data

### Missing Test Coverage: Critical Data Types

#### 1. Financial P&L Data
```csv
account,category,value,prior_year_value
Revenue,Income,1250000,1100000
COGS,Expense,750000,680000
Gross_Profit,Income,500000,420000
Operating_Expenses,Expense,350000,330000
EBITDA,Income,150000,90000
```

**Expected Story**:
- Thesis: "Revenue Growth Masking Margin Compression"
- KPIs: "$1.25M Revenue", "40% Gross Margin", "+$60K EBITDA"
- Sections: "Revenue Performance", "Cost Structure", "Profitability"

**Test**: Does thesis extractor recognize "growth + margin compression"?

#### 2. Time-Series Data
```csv
date,metric,value,forecast
2024-01-01,sales,42500,40000
2024-02-01,sales,45200,43000
2024-03-01,sales,39800,46000
```

**Expected Story**:
- Thesis: "Sales Volatility Exceeding Forecast Accuracy"
- KPIs: "+6.4% Growth", "-13.7% Miss in March"
- Sections: "Growth Trends", "Forecast Accuracy", "Seasonality"

**Test**: Does section grouper create time-based sections?

#### 3. Survey/NPS Data
```csv
respondent_id,question,score,segment
101,satisfaction,8,enterprise
102,satisfaction,9,smb
103,nps,9,enterprise
104,nps,6,smb
```

**Expected Story**:
- Thesis: "Enterprise Satisfaction Hides NPS Detractor Risk"
- KPIs: "8.5 Satisfaction", "NPS 40", "33% Detractors"
- Sections: "Overall Satisfaction", "NPS Analysis", "Segment Differences"

**Test**: Does KPI extractor handle non-percentage scores (1-10 scale)?

#### 4. Geospatial Data
```csv
territory,lat,lon,sales,target
Northeast,42.36,-71.06,125000,150000
Southeast,33.75,-84.39,98000,100000
```

**Expected Story**:
- Thesis: "Geographic Performance Gap Concentrated in Northeast"
- KPIs: "83% to Target", "$27K Gap", "2 Territories"
- Sections: "Regional Performance", "Target Achievement", "Geographic Risk"

**Test**: Does chart selector suggest map visualizations?

#### 5. HR Headcount Data
```csv
department,headcount,attrition_rate,avg_tenure_months
Engineering,45,12.5,28
Sales,32,22.3,18
Operations,18,8.1,42
```

**Expected Story**:
- Thesis: "Sales Attrition Creating Institutional Knowledge Drain"
- KPIs: "22.3% Attrition", "18mo Tenure", "95 Total Headcount"
- Sections: "Retention Challenges", "Department Comparison", "Tenure Analysis"

**Test**: Does narrative use HR-specific terminology?

---

## Robustness Enhancement Plan

### Phase 1: Topic Detection (2-3 hours)
**Goal**: Make section grouping data-driven

```python
# In section_grouper.py
def _extract_topics_from_data(self, insights, data_columns):
    """
    Detect topics from:
    1. Column names (revenue, headcount, inventory)
    2. Insight text frequency (what words appear most?)
    3. Objective keywords (from spec.yaml)
    """
    topics = []

    # Extract from column names
    for col in data_columns:
        if 'revenue' in col.lower():
            topics.append('revenue_performance')
        elif 'cost' in col.lower():
            topics.append('cost_structure')
        elif 'margin' in col.lower():
            topics.append('profitability')

    # Extract from insight text
    insight_text = " ".join([i.text for i in insights])
    # Use frequency analysis + noun phrase extraction

    return topics
```

### Phase 2: Domain-Aware KPI Types (1-2 hours)
**Goal**: Recognize domain-specific KPI patterns

```python
# In kpi_extractor.py
class KPIType(Enum):
    HEADLINE = "headline"
    SUPPORTING = "supporting"
    DELTA = "delta"
    COUNT = "count"
    # NEW:
    RATE = "rate"          # 12.5% attrition rate
    RATIO = "ratio"        # 3.2:1 inventory turns
    DURATION = "duration"  # 18 days lead time
    INDEX = "index"        # NPS 42, CSAT 8.5
    CURRENCY = "currency"  # $1.2M (already formatted)

def _detect_kpi_type(self, value_str, context):
    """Detect KPI type from value and context"""
    if 'rate' in context.lower():
        return KPIType.RATE
    elif ':' in value_str:
        return KPIType.RATIO
    # ... more heuristics
```

### Phase 3: Domain Vocabulary (2-3 hours)
**Goal**: Use domain-specific terminology in narratives

```python
# In narrative_synthesizer.py
DOMAIN_VOCABULARY = {
    "finance": {
        "metrics": ["EBITDA", "gross margin", "burn rate", "ROI"],
        "verbs": ["drove", "compressed", "expanded", "eroded"],
        "themes": ["profitability", "efficiency", "leverage"]
    },
    "supply_chain": {
        "metrics": ["inventory turns", "fill rate", "lead time", "OEE"],
        "verbs": ["optimized", "streamlined", "constrained", "exceeded"],
        "themes": ["efficiency", "capacity", "bottlenecks"]
    },
    "hr": {
        "metrics": ["attrition", "time-to-hire", "span of control"],
        "verbs": ["retained", "recruited", "developed", "churned"],
        "themes": ["retention", "talent", "productivity"]
    }
}

def _detect_domain(self, insights, objective):
    """Detect domain from objective and column names"""
    # Check objective keywords
    # Check column name patterns
    # Default to "general"
```

### Phase 4: Chart Type Intelligence (1-2 hours)
**Goal**: Suggest domain-appropriate visualizations

```python
# In chart_selector.py
def _suggest_domain_charts(self, insight, data, domain):
    """Domain-specific chart suggestions"""
    if domain == "geospatial" and has_lat_lon(data):
        return "map", {"center": auto_detect_center()}
    elif domain == "time_series":
        return "line", {"show_forecast": True}
    elif domain == "survey" and has_likert_scale(data):
        return "stacked_bar", {"diverging": True}
```

### Phase 5: Comprehensive Testing (3-4 hours)
**Goal**: Validate robustness across data types

Test suite expansions:
- `tests/test_story_financial_data.py`
- `tests/test_story_timeseries_data.py`
- `tests/test_story_survey_data.py`
- `tests/test_story_geospatial_data.py`
- `tests/test_story_hr_data.py`

---

## Success Criteria

| Data Type | Thesis Quality | KPI Extraction | Section Grouping | Domain Language |
|-----------|---------------|----------------|------------------|-----------------|
| Financial P&L | High | High | High | Medium |
| Time-Series | High | High | Medium | High |
| Survey/NPS | High | Medium | High | High |
| Geospatial | Medium | High | Medium | Low |
| HR Headcount | High | High | Medium | Medium |
| Agricultural | ✅ High | ✅ High | ✅ High | ⚠️ Medium |

**Current Status**: Story architecture works for agricultural data, needs enhancements for full data type coverage.

**Risk Mitigation**: Fallback to generic language ensures graceful degradation for unknown domains.

---

## Immediate Actions

### 1. Document Data Type Requirements (Complete ✅)
This document serves as the spec.

### 2. Create Data Type Test Matrix (Next Step)
```python
# In tests/test_story_data_types.py
@pytest.mark.parametrize("data_type,expected_thesis_pattern", [
    ("financial", r".*margin.*profitability"),
    ("timeseries", r".*trend.*forecast"),
    ("survey", r".*satisfaction.*nps"),
    ("geospatial", r".*region.*territory"),
    ("hr", r".*attrition.*retention"),
])
def test_story_handles_data_type(data_type, expected_thesis_pattern):
    # Load fixture for data_type
    # Run story builder
    # Assert thesis matches expected pattern
```

### 3. Prioritize Enhancements by User Need
**High Priority** (next 2-3 days):
- Topic detection from data (Phase 1)
- Domain vocabulary (Phase 3)

**Medium Priority** (next week):
- Domain-aware KPI types (Phase 2)
- Comprehensive testing (Phase 5)

**Low Priority** (future):
- Chart type intelligence (Phase 4)

---

## Conclusion

The story-first architecture is **fundamentally robust** because:
1. ✅ Pattern detection is regex-based (works on any text)
2. ✅ Section grouping has fallbacks (generic sections when needed)
3. ✅ Smart formatting works universally (K/M/B for any number)
4. ✅ Multi-mode narratives adapt to any domain

**Enhancement needed** for:
1. ⚠️ Domain-specific terminology (HR, finance, ops language)
2. ⚠️ Topic detection from data (not hardcoded satisfaction keywords)
3. ⚠️ Advanced KPI type recognition (rates, ratios, indices)

**Estimated effort**: 8-12 hours to achieve 95%+ robustness across all data types.
