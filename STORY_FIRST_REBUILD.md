# Story-First Architecture Rebuild

**Status**: Phase 1-5 Complete ✅ (Tests Passing 15/15)
**Date**: 2026-01-16
**Objective**: Transform KIE from insight-dump to consultant-grade story-first output

📊 **[View Phase 5 Completion Report](./PHASE_5_COMPLETE.md)** - Full validation results and real-world test

---

## Problem Statement

**Before**: KIE produced 13 identical bar charts with JSON/YAML file soup, no narrative, no KPIs, no story arc.

**Gap**: Consultant-grade examples show:
- Massive KPI callouts (68.7%, 82%, 60%)
- Interactive scrolling narrative with visual hierarchy
- Chart diversity (horizontal bars, grouped bars, demographic breakdowns)
- Story sections with clear thesis
- Executive/analyst/technical narrative modes

**Root Cause**: Pipeline was insight-first (generate insights → slap on slides) instead of story-first (extract thesis → build narrative → visualize story).

---

## Solution: Story-First Architecture

### New Module: `kie/story/`

Complete story-first pipeline that transforms insights into compelling narratives:

```
insights.yaml
    ↓
[ThesisExtractor] → StoryThesis ("The Agricultural Retail Paradox")
    ↓
[KPIExtractor] → StoryKPIs (68.7%, 82%, 60% with rankings)
    ↓
[SectionGrouper] → StorySections (grouped by theme)
    ↓
[NarrativeSynthesizer] → Narratives (executive/analyst/technical)
    ↓
[StoryBuilder] → StoryManifest (single source of truth)
    ↓
outputs/internal/story_manifest.json (ready for React/PPTX/HTML)
```

---

## What Was Built

### Phase 1: Story-First Data Models ✅

**Files Created:**
- `kie/story/__init__.py` - Module entry point
- `kie/story/models.py` - Core data models

**Key Components:**
```python
class NarrativeMode(Enum):
    EXECUTIVE   # Business impact, recommendations, ROI
    ANALYST     # Detailed findings, cross-correlations
    TECHNICAL   # Methodology, confidence, statistical rigor

class KPIType(Enum):
    HEADLINE    # Main story number (68.7%)
    SUPPORTING  # Secondary metric
    DELTA       # Change metric (+8.8 pts)
    COUNT       # Absolute count (419 of 511)

@dataclass
class StoryThesis:
    title: str              # "The Agricultural Retail Paradox"
    hook: str               # 1-sentence story hook
    summary: str            # 2-3 sentence executive summary
    implication: str        # "So what?" - business impact
    confidence: float       # 0.0-1.0
    supporting_insight_ids: list[str]

@dataclass
class StoryKPI:
    value: str              # "68.7%"
    label: str              # "Very/Extremely Satisfied"
    context: str            # "n=511 growers"
    kpi_type: KPIType
    rank: int               # Priority rank (1 = most important)
    insight_id: str | None

@dataclass
class StorySection:
    section_id: str
    title: str              # "Overall Satisfaction"
    subtitle: str | None
    thesis: str             # Section-level story
    kpis: list[StoryKPI]
    chart_refs: list[str]
    insight_ids: list[str]
    narrative_text: str | None
    order: int

@dataclass
class StoryManifest:
    story_id: str
    project_name: str
    thesis: StoryThesis
    top_kpis: list[StoryKPI]        # Top 3-5 KPIs for hero section
    sections: list[StorySection]
    narrative_mode: NarrativeMode
    executive_summary: str
    key_findings: list[str]
    metadata: dict[str, Any]
```

### Phase 2: Narrative Synthesis ✅

**Files Created:**
- `kie/story/thesis_extractor.py` - Extracts core narrative thesis/paradox
- `kie/story/kpi_extractor.py` - Surfaces most impactful numbers
- `kie/story/section_grouper.py` - Groups insights into narrative sections
- `kie/story/narrative_synthesizer.py` - Multi-mode narrative generation

**Key Features:**

**Thesis Extraction:**
- Detects paradoxes ("high satisfaction but high switching intent")
- Identifies dominant themes (most insights cluster around topic)
- Surfaces surprising patterns
- Generates business implications

**KPI Extraction & Ranking:**
- Extracts percentages, deltas, counts from insights
- 4-tier scoring system:
  - KPI type (HEADLINE > DELTA > SUPPORTING > COUNT)
  - Source insight business_value
  - Source insight confidence
  - Numeric magnitude
- Smart formatting (68.7%, +8.8 pts, 419 of 511)

**Section Grouping:**
- Topic clustering (satisfaction, price, trust, loyalty, quality)
- Metric similarity (revenue, cost, margin)
- Priority ordering by business value

**Narrative Synthesis:**
- **EXECUTIVE Mode**: Business impact, recommendations, ROI focus
- **ANALYST Mode**: Detailed findings, cross-correlations, patterns
- **TECHNICAL Mode**: Methodology, confidence intervals, statistical rigor

### Phase 3: Chart Intelligence ✅

**Files Modified:**
- `kie/charts/factory.py` - Added `grouped_bar()` method
- Updated `ChartType` literal to include "grouped_bar"

**Files Created:**
- `kie/story/chart_selector.py` - Smart chart type selection

**Chart Selection Decision Tree:**
```python
if is_timeseries:
    → line/area/stacked_area
elif is_composition (parts-of-whole):
    → pie/donut
elif is_change_flow:
    → waterfall
elif is_correlation:
    → scatter
elif is_comparison:
    if is_multi_series:
        → grouped_bar
    elif len(data) > 8:
        → horizontal_bar
    else:
        → bar
```

**Supported Chart Types (12 total):**
- Bar: bar, horizontal_bar, stacked_bar, grouped_bar
- Line/Area: line, area, stacked_area
- Pie: pie, donut
- Advanced: scatter, combo, waterfall

### Phase 4: Integration ✅

**Files Modified:**
- `kie/skills/__init__.py` - Registered StoryBuilderSkill

**Files Created:**
- `kie/skills/story_builder_skill.py` - New analyze-stage skill

**Integration Flow:**
```
/analyze command
    ↓
InsightEngine.auto_extract_comprehensive() → outputs/insights.yaml
    ↓
[Skills Pipeline - Pass 1]
    insight_triage skill → outputs/internal/insight_triage.json
    ↓
[Skills Pipeline - Pass 2]
    story_builder skill → outputs/internal/story_manifest.json
                       → outputs/internal/story_manifest_analyst.json
                       → outputs/internal/story_manifest_technical.json
```

**Key Design Decision:**
- New `StoryBuilderSkill` runs in **analyze stage** (NOT build stage)
- Generates story manifest **before** visualization planning
- Creates 3 manifests (executive/analyst/technical) for different audiences
- Skill is independent - doesn't break existing pipeline

---

## Architecture Comparison

### Old Flow (Insight-First):
```
insights → triage → viz_plan → charts → storyboard → pptx
                                                    ↓
                                           (monotonous output)
```

### New Flow (Story-First):
```
insights → THESIS → KPIs → SECTIONS → NARRATIVES → manifest
                                                        ↓
                                              (consultant-grade)
```

---

## Files Created/Modified

### New Files (10):
1. `kie/story/__init__.py`
2. `kie/story/models.py`
3. `kie/story/thesis_extractor.py`
4. `kie/story/kpi_extractor.py`
5. `kie/story/section_grouper.py`
6. `kie/story/narrative_synthesizer.py`
7. `kie/story/story_builder.py`
8. `kie/story/chart_selector.py`
9. `kie/skills/story_builder_skill.py`
10. `STORY_FIRST_REBUILD.md` (this file)

### Modified Files (2):
1. `kie/charts/factory.py` - Added grouped_bar support
2. `kie/skills/__init__.py` - Registered new skill

---

## Testing Status

### Unit Tests: ⏳ Pending
- Thesis extraction logic
- KPI ranking system
- Section grouping algorithm
- Narrative synthesis modes

### Integration Tests: ⏳ Pending
- Full pipeline: insights → story manifest
- Chart selector intelligence
- Multi-mode narrative generation

### Manual Testing: ⏳ Pending
- Run `/analyze` on real data
- Verify story_manifest.json structure
- Compare executive/analyst/technical narratives

---

## Next Steps

### Phase 5: Test Story Pipeline ✅
**Test Results**: 15/15 tests passing

```bash
$ python3 -m pytest tests/test_story_pipeline.py -v
============================== test session starts ==============================
collected 15 items

tests/test_story_pipeline.py::TestThesisExtraction::test_paradox_detection PASSED [  6%]
tests/test_story_pipeline.py::TestKPIExtraction::test_kpi_extraction PASSED [ 13%]
tests/test_story_pipeline.py::TestKPIExtraction::test_kpi_ranking_logic PASSED [ 20%]
tests/test_story_pipeline.py::TestSectionGrouping::test_section_creation PASSED [ 26%]
tests/test_story_pipeline.py::TestSectionGrouping::test_section_ordering PASSED [ 33%]
tests/test_story_pipeline.py::TestNarrativeSynthesis::test_executive_mode PASSED [ 40%]
tests/test_story_pipeline.py::TestNarrativeSynthesis::test_analyst_mode PASSED [ 46%]
tests/test_story_pipeline.py::TestNarrativeSynthesis::test_technical_mode PASSED [ 53%]
tests/test_story_pipeline.py::TestStoryBuilder::test_story_manifest_creation PASSED [ 60%]
tests/test_story_pipeline.py::TestStoryBuilder::test_multi_mode_generation PASSED [ 66%]
tests/test_story_pipeline.py::TestStoryBuilder::test_manifest_serialization PASSED [ 73%]
tests/test_story_pipeline.py::TestChartSelector::test_timeseries_detection PASSED [ 80%]
tests/test_story_pipeline.py::TestChartSelector::test_comparison_detection PASSED [ 86%]
tests/test_story_pipeline.py::TestChartSelector::test_composition_detection PASSED [ 93%]
tests/test_story_pipeline.py::TestIntegration::test_agricultural_retail_scenario PASSED [100%]

============================== 15 passed in 0.30s
```

**Validation Complete**:
- ✅ Thesis extraction detects paradoxes and themes
- ✅ KPI extraction and ranking works correctly
- ✅ Section grouping creates logical narrative structure
- ✅ Multi-mode narratives generate distinct outputs
- ✅ Chart selector intelligence identifies correct chart types
- ✅ End-to-end integration produces valid manifests
- ✅ Serialization to JSON preserves all data structures

### Phase 6: React Frontend Integration (Future)
- Build `<StoryRenderer>` component
- Parse story_manifest.json
- Render KPI callouts (large visual display)
- Implement scrolling narrative
- Add interactive charts

### Phase 7: PowerPoint Integration (Future)
- Build `StoryManifestToPPTX` converter
- Section-based slide generation
- KPI callout slides
- Chart embedding from manifest

---

## Key Design Principles

1. **Single Source of Truth**: StoryManifest drives all deliverables (React, PPTX, HTML)
2. **Mode-Specific Narratives**: Same insights, different framings for different audiences
3. **Data-Driven KPIs**: Automatic extraction and ranking (no manual curation)
4. **Thesis-First**: Every story has a clear thesis/paradox
5. **Section Grouping**: Insights organized narratively (not just listed)
6. **Chart Intelligence**: Right chart type for the data and insight pattern

---

## Success Metrics

### Before (Current KIE v3):
- ❌ 13 identical bar charts
- ❌ No narrative (just insights.yaml dump)
- ❌ No KPIs
- ❌ JSON/YAML file soup
- ❌ No story arc
- ❌ Consultant must handcraft everything

### After (Story-First):
- ✅ Diverse chart types (12 options with smart selection)
- ✅ Compelling narrative with thesis
- ✅ Ranked KPIs (68.7% style callouts)
- ✅ Story sections with clear themes
- ✅ 3 narrative modes (exec/analyst/tech)
- ✅ Single manifest → multiple deliverables

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Story-First Pipeline                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ insights.yaml    │
                    │ (from /analyze)  │
                    └────────┬─────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │  ThesisExtractor       │
                │  • Detect paradoxes    │
                │  • Find dominant theme │
                │  • Surface surprises   │
                └────────┬───────────────┘
                         │
                         ▼
                    StoryThesis
                    "The Agricultural
                     Retail Paradox"
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   KPIExtractor    SectionGrouper  ChartSelector
   • Extract %     • Topic cluster • Time-series?
   • Rank impact   • Group themes  • Composition?
   • Format        • Order priority• Correlation?
         │               │               │
         ▼               ▼               ▼
   [68.7%, 82%,    [Satisfaction,   [line, pie,
    60%, ...]       Price,           grouped_bar,
                    Loyalty]         ...]
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │ NarrativeSynthesizer  │
             │ • EXECUTIVE mode      │
             │ • ANALYST mode        │
             │ • TECHNICAL mode      │
             └───────────┬───────────┘
                         │
                         ▼
                ┌────────────────────┐
                │  StoryBuilder      │
                │  • Orchestrates    │
                │  • Builds manifest │
                │  • 3 output modes  │
                └────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
story_manifest.json  _analyst.json  _technical.json
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │   Deliverable Renderers│
             │   • React Dashboard   │
             │   • PowerPoint Deck   │
             │   • HTML Report       │
             └───────────────────────┘
```

---

## Timeline

- **Day 1 (2026-01-16)**: Phases 1-4 complete (architecture + integration)
- **Day 2 (TBD)**: Phase 5 (testing)
- **Day 3 (TBD)**: Phase 6-7 (React/PPTX integration)

**Estimated Total**: 2-3 days for full story-first transformation.

---

## Conclusion

The story-first architecture is **architecturally complete**. All core components are built and integrated:
- ✅ Data models for thesis, KPIs, sections, manifest
- ✅ Extraction engines for thesis, KPIs, sections
- ✅ Multi-mode narrative synthesis
- ✅ Chart intelligence & selection
- ✅ Skills pipeline integration

**Next**: Test the pipeline end-to-end with real data to validate that story manifests are generating as expected.
