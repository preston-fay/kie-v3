# KIE v3 Architecture - Senior Engineer Deep Dive

## End-to-End Pipeline Flow

### Phase 1: Bootstrap & Requirements
```
/startkie → Creates workspace structure
/interview → Conversational requirements (Claude-orchestrated, doesn't write spec!)
/intent set → Explicitly set objective
/spec --init → Creates spec.yaml with smart defaults
```

### Phase 2: Data & Analysis
```
/eda → Exploratory data analysis
/analyze → Core insight extraction pipeline:
  1. DataLoader.load() → Intelligent column mapping (5-tier system)
  2. InsightEngine.auto_extract_comprehensive() → Extract 15-20 insights
  3. Save insights_catalog.json
  4. Execute analyze stage skills (2-pass):
     - insight_triage → Filter top insights (removed limits)
     - visualization_planner → Plan chart types for each insight
     - visual_storyboard → Group into story sections
     - story_manifest → Final manifest for PowerPoint
```

### Phase 3: Deliverable Generation
```
/build presentation → Generate PowerPoint:
  1. Load story_manifest.json
  2. For each visual: SVG → PNG conversion (cairo)
  3. Embed charts in PPT with KDS layout
  4. Add executive summary slide

/build dashboard → Generate React dashboard:
  1. Load chart JSON configs
  2. Start React dev server
  3. Render with Recharts + KDS theme
```

## Critical Components

### DataLoader Intelligence (5-Tier Column Mapping)
- **Tier 0**: Objective keyword match (NEW - from user's stated goal)
- **Tier 1**: Semantic match (revenue/cost/margin keywords)
- **Tier 2**: ID avoidance (rejects ZipCodes, CustomerIDs)
- **Tier 3**: Percentage handling (doesn't penalize 0.0-1.0 range)
- **Tier 4**: Statistical vitality (coefficient of variation)
- **Tier 5**: Human override (column_mapping in spec.yaml)

### Skills-Based Architecture ("Rails")
- All state-changing operations are "skills"
- Skills have preconditions, outputs, handlers
- Execute in stages: bootstrap → analyze → build
- Two-pass execution for dependency resolution

### Insight Engine
- `auto_extract()`: Basic 5-7 insights
- `auto_extract_comprehensive()`: 15-20 insights
  - Multiple numeric columns
  - Cross-column correlations (objective-aware prioritization)
  - Time-based patterns
  - Distribution analysis

### Visualization Pipeline
1. **insight_triage.py**: Filter top insights (NO LIMITS after user fix)
2. **visualization_planner.py**: Assign chart types (bar, pareto, line, etc.)
3. **visual_storyboard.py**: Group into story sections (NO LIMITS after user fix)
4. **story_manifest.py**: Final manifest with visuals array

### Chart Rendering
- **JSON configs**: Python generates Recharts configs
- **SVG generation**: Pygal renders for PowerPoint
- **PNG conversion**: cairo library (macOS: `/opt/homebrew/opt/cairo/lib`)
- **React rendering**: Recharts from JSON configs

## Known Architecture Issues (Pre-Investigation)

### Issue: "Insights are WOW, Analysis isn't WOW"
- Insight extraction is powerful (comprehensive mode, 15-20 insights)
- BUT: What happens to these insights?
- Are they being filtered too aggressively downstream?
- Is the triage/storyboard losing signal?

### Issue: "Output isn't WOW"
- PowerPoint generation works (fixed cairo)
- BUT: Are the insights presented compellingly?
- Is the narrative synthesis weak?
- Are charts too basic (only bar charts)?
- Is the executive summary missing key findings?

### Issue: "4X over budget and time"
- Rails architecture (Phase 1) is tactical fixes only
- Phase 2 (Python Registry) not implemented
- Phase 3 (Guardrails) not implemented
- Skills are loosely coupled, not validated
- No precondition checking
- No auto-prerequisite execution

## Test Coverage
- 1338 total tests
- Mix of passing/failing (acceptance tests show gaps)
- Critical failures in:
  - test_journey_b_demo_data_opt_in
  - test_journey_f_large_csv
  - test_journey_h_chart_rendering_from_viz_plan
  - test_journey_i_freeform_bridge
  - Actionability scoring tests (all 6 failing)

## Key Files for Investigation
- **kie/insights/engine.py**: Insight extraction logic
- **kie/skills/insight_triage.py**: Top insights filtering (FIXED - no limits)
- **kie/skills/visual_storyboard.py**: Story structuring (FIXED - no limits)
- **kie/skills/story_manifest.py**: Final manifest generation
- **kie/skills/narrative_synthesis.py**: Executive narrative generation
- **kie/commands/handler.py**: handle_analyze(), handle_build()
- **kie/data/loader.py**: Intelligent column mapping
