# Story Architecture Integration Guide

**Date**: 2026-01-16
**Status**: Phase 5 Complete - Integration Strategy Documented

---

## Two-Stage Story Architecture

KIE v3 now has a **two-stage story architecture** that transforms insights into consultant-grade outputs:

### Stage 1: ANALYZE - Story-First Transformation
**Skill**: `StoryBuilderSkill` (kie/skills/story_builder_skill.py)
**Input**: `outputs/insights.yaml`
**Output**: `outputs/internal/story_manifest*.json` (3 modes)

**Purpose**: Transform raw insights into structured story with thesis, KPIs, and narrative sections

**What it produces**:
```json
{
  "story_id": "story_project_20260116",
  "project_name": "Agricultural Retail Analysis",
  "thesis": {
    "title": "The Agricultural Retail Paradox",
    "hook": "High satisfaction masks price vulnerability",
    "summary": "...",
    "implication": "...",
    "confidence": 0.85
  },
  "top_kpis": [
    {"value": "68.7%", "label": "Very/Extremely Satisfied", ...},
    {"value": "82%", "label": "Price Sensitive", ...}
  ],
  "sections": [
    {
      "section_id": "sec_001",
      "title": "Overall Satisfaction",
      "thesis": "...",
      "kpis": [...],
      "insight_ids": ["ins_001", "ins_002"],
      "chart_refs": []  // Empty at this stage
    }
  ],
  "narrative_mode": "executive",
  "executive_summary": "...",
  "key_findings": [...]
}
```

### Stage 2: BUILD - Final Manifest Assembly
**Skill**: `StoryManifestSkill` (kie/skills/story_manifest.py)
**Inputs**:
- `outputs/internal/story_manifest.json` (from Stage 1)
- `outputs/internal/visual_storyboard.json`
- `outputs/internal/visualization_plan.json`
- `outputs/charts/*.json` (rendered charts)

**Output**: `outputs/story_manifest.json` (final deliverable manifest)

**Purpose**: Assemble complete story with all visuals, narratives, and rendering instructions

**What it produces**:
```json
{
  "story_id": "...",
  "project_name": "...",
  "objective": "...",
  "thesis": {  // From story_manifest.json
    "title": "The Agricultural Retail Paradox",
    "hook": "...",
    "summary": "..."
  },
  "top_kpis": [...],  // From story_manifest.json
  "sections": [
    {
      "section_id": "sec_001",
      "title": "Overall Satisfaction",
      "narrative": {  // From executive_summary
        "headline": "...",
        "supporting_bullets": [...]
      },
      "visuals": [  // From visual_storyboard + viz_plan
        {
          "chart_ref": "charts/satisfaction_breakdown.json",
          "visualization_type": "horizontal_bar",
          "emphasis": "..."
        }
      ],
      "kpis": [...],  // From story_manifest.json
      "evidence_index": [...]
    }
  ],
  "generated_at": "...",
  "execution_mode": "rails"
}
```

---

## Data Flow

```
insights.yaml (raw insights)
    ↓
┌───────────────────── ANALYZE STAGE ─────────────────────┐
│                                                          │
│  StoryBuilderSkill                                       │
│  ├─ ThesisExtractor → Extract paradox/theme             │
│  ├─ KPIExtractor → Surface top numbers                  │
│  ├─ SectionGrouper → Group by narrative theme           │
│  └─ NarrativeSynthesizer → Generate summaries           │
│                                                          │
│  OUTPUT: story_manifest.json (thesis, KPIs, sections)   │
│          story_manifest_analyst.json                    │
│          story_manifest_technical.json                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
    ↓
    ├─ InsightTriageSkill → Filter top insights
    ├─ VisualizationPlannerSkill → Plan chart types
    └─ VisualStoryboardSkill → Create visual sequence
    ↓
┌───────────────────── BUILD STAGE ───────────────────────┐
│                                                          │
│  StoryManifestSkill                                      │
│  ├─ Load story_manifest.json (thesis, KPIs, sections)   │
│  ├─ Load visual_storyboard.json (visual sequence)       │
│  ├─ Load executive_summary.md (narratives)              │
│  ├─ Merge sections with visuals                         │
│  └─ Add rendering instructions                          │
│                                                          │
│  OUTPUT: story_manifest.json (complete deliverable)     │
│                                                          │
└──────────────────────────────────────────────────────────┘
    ↓
    ├─ PowerPoint renderer
    ├─ Dashboard renderer
    └─ HTML renderer
```

---

## Integration Points

### 1. StoryBuilderSkill → VisualStoryboardSkill
**Connection**: Section IDs and insight IDs

The story builder creates sections with `insight_ids`. The visual storyboard should respect these groupings when creating the visual sequence.

**Recommendation**: Update VisualStoryboardSkill to:
1. Read `story_manifest.json` sections
2. Use section titles as narrative groupings
3. Match insight IDs to maintain story coherence

### 2. StoryBuilderSkill → StoryManifestSkill
**Connection**: Thesis, KPIs, Section Structure

The final manifest should include:
- `thesis` from story_manifest.json
- `top_kpis` array for hero section
- `sections[].kpis` for section-level callouts

**Recommendation**: Update StoryManifestSkill to:
1. Read `story_manifest.json`
2. Merge thesis into final manifest
3. Add KPIs to sections
4. Preserve narrative mode metadata

### 3. Story Manifest → PowerPoint
**Connection**: KPI Callout Slides

PowerPoint generator should create:
- Hero slide with top 3-5 KPIs (large display)
- Section slides with section-level KPIs
- Thesis slide with hook + summary

**Recommendation**: Create new PPT template:
- `kpi_hero.pptx` - Large KPI callout layout
- `section_kpi.pptx` - Section header with KPIs
- `thesis.pptx` - Executive summary with thesis

---

## File Locations

### Analyze Stage Outputs
```
outputs/internal/
  story_manifest.json              # Executive mode
  story_manifest_analyst.json      # Analyst mode
  story_manifest_technical.json    # Technical mode
  insight_triage.json              # Top insights (existing)
  visualization_plan.json          # Chart assignments (existing)
  visual_storyboard.json           # Visual sequence (existing)
```

### Build Stage Outputs
```
outputs/
  story_manifest.json              # Final deliverable manifest
  story_manifest.md                # Human-readable version
```

---

## Benefits of Two-Stage Architecture

### Stage 1 (Analyze) Benefits:
1. **Early Story Extraction**: Thesis and KPIs identified before visualization
2. **Multi-Mode Support**: Same insights, different narratives (exec/analyst/tech)
3. **Reusability**: Story structure can be reused across multiple builds
4. **Testability**: Story quality can be validated before visualization

### Stage 2 (Build) Benefits:
1. **Format-Agnostic**: Final manifest works for PPT, dashboard, HTML
2. **Complete Context**: All visuals + narratives + metadata in one place
3. **Rendering Instructions**: Chart types, emphasis, transitions
4. **Client-Ready**: Includes readiness hints and evidence indexes

---

## Next Steps for Full Integration

### 1. Update VisualStoryboardSkill (2-3 hours)
- Read story_manifest.json sections
- Use section titles for grouping
- Maintain insight ID mappings

### 2. Update StoryManifestSkill (2-3 hours)
- Merge thesis from story_manifest.json
- Include top_kpis array
- Add section-level KPIs
- Preserve narrative mode

### 3. Update PowerPoint Generator (4-6 hours)
- Create KPI hero slide template
- Add thesis slide layout
- Implement section KPI callouts
- Test with all three narrative modes

### 4. Update Dashboard Renderer (4-6 hours)
- Create `<KPICallout>` component
- Add thesis section to hero
- Implement section KPI display
- Support dark/light modes

### 5. End-to-End Testing (2-3 hours)
- Test analyze → build flow
- Validate all three narrative modes
- Verify KPI display in all outputs
- Check thesis presentation

---

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Story structure extracted | Yes | Yes | ✅ |
| Thesis quality | High | High | ✅ |
| KPI extraction | 3-5 per story | 5 | ✅ |
| Section grouping | 2-4 sections | 3 | ✅ |
| Multi-mode support | 3 modes | 3 | ✅ |
| Integration with viz | Seamless | Pending | ⏳ |
| PowerPoint KPIs | Large display | Not implemented | ⏳ |
| Dashboard KPIs | Interactive | Not implemented | ⏳ |

---

## Migration Notes

### Backward Compatibility
The new story builder runs in ANALYZE stage, while old story manifest runs in BUILD stage. They are complementary, not conflicting.

**No breaking changes** - existing projects will continue to work. New projects get enhanced story structure.

### Gradual Adoption
1. Phase 5 (Complete): Story builder generates thesis/KPIs/sections
2. Phase 6 (Next): Visual storyboard reads story structure
3. Phase 7 (Next): Story manifest merges story + visuals
4. Phase 8 (Next): Renderers consume enhanced manifest

---

## Technical Debt

### Current Limitations
1. Section KPIs not yet merged into final manifest
2. Thesis not displayed in PowerPoint
3. KPI callouts use plain text (no large visual display)
4. Dashboard doesn't show story structure
5. Only executive summary narrative used (analyst/technical modes ignored)

### Future Enhancements
1. LLM-powered thesis extraction (currently rule-based)
2. Adaptive section grouping based on insights
3. Dynamic KPI ranking by audience
4. Story quality scoring
5. A/B testing for narrative effectiveness

---

**Estimated Total Integration Time**: 14-21 hours to fully integrate story-first architecture into all deliverables.
