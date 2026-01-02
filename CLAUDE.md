# KIE - Kearney Insight Engine v3.0

## System Overview

KIE (Kearney Insight Engine) is an AI-powered consulting delivery platform that transforms
natural language requirements into polished, brand-compliant deliverables.

**Core Philosophy: "LLM Reasons, Python Executes"**
- Claude handles understanding, reasoning, and orchestration
- Python engines handle deterministic, reproducible output generation
- Brand compliance is programmatically enforced (cannot be bypassed)

---

## Bootstrap Detection (Auto-Setup)

**IMPORTANT**: When you detect you're in a folder that needs KIE setup, automatically bootstrap it.

### Detection Triggers

Bootstrap a KIE project if ALL of these are true:
1. Current working directory does NOT contain `CLAUDE.md` with "KIE Project" in it
2. Current working directory does NOT contain `kie/` or `web/` folders (you're not in the KIE v3 repo)
3. User requests indicate Kearney/KIE work with phrases like:
   - "KIE project"
   - "Kearney analysis"
   - "consulting deliverable"
   - "need a presentation/dashboard/analysis"
   - Any mention of Acme, client work, or business analysis
   - User types `/startkie`

### Bootstrap Process

When triggered, use the Python CommandHandler:

```python
from pathlib import Path
from kie.commands.handler import CommandHandler

handler = CommandHandler(project_root=Path.cwd())
result = handler.handle_startkie()

if result['success']:
    print(f"✅ {result['message']}")
    print(f"Created: {', '.join(result['folders_created'])}")
else:
    print(f"❌ {result['message']}")
```

This will create:
- Folder structure (data/, outputs/, exports/, project_state/)
- .gitignore
- README.md
- CLAUDE.md (project-specific instructions)

After bootstrapping, begin conversational requirements gathering.

---

## Architecture

KIE v3 uses modern separation of concerns:

```
Python Backend (kie/)    →  Generates JSON configs
React Frontend (web/)    →  Renders charts from JSON
Validation System        →  Ensures 100% KDS compliance
```

**Key Differences from v2:**
- ✅ No matplotlib - Charts use Recharts (React) only
- ✅ JSON configs - Python generates, React renders
- ✅ Enhanced validation - Multi-level QC system
- ✅ Theme support - Dark and light modes

---

## Conversational Requirements

Use **natural conversation** to gather requirements - never rigid questionnaires:

```
User: "I need a sales dashboard for Acme Corp showing Q3 performance"

You: "Got it - I've captured:
     - Client: Acme Corp
     - Deliverable: Dashboard
     - Timeframe: Q3

     What data do you have? (drop a file, or I can mock sample data)"
```

Extract structured requirements from natural language. Only ask targeted follow-ups for missing critical info.

---

## Brand Rules (Non-Negotiable)

**ALWAYS enforce these - no exceptions:**

| Rule | Requirement |
|------|-------------|
| Primary Color | Kearney Purple `#7823DC` |
| Forbidden Colors | ALL greens (no #00FF00, #008000, #90EE90, etc.) |
| Typography | Inter font (Arial fallback) |
| Charts | No gridlines. Data labels outside bars/slices. |
| Text on Dark | Use white `#FFFFFF` or light purple `#9B4DCA` - NEVER primary purple |
| Dark Mode | Background `#1E1E1E` |
| Accessibility | WCAG 2.1 AA contrast minimum |
| No Emojis | Never in deliverables |

**Kearney Color Palette (KDS 10-color chart palette):**
```
1. #D2D2D2  (Light Gray)
2. #A5A6A5  (Medium Gray)
3. #787878  (Dark Gray)
4. #E0D2FA  (Light Purple)
5. #C8A5F0  (Medium Light Purple)
6. #AF7DEB  (Medium Purple)
7. #4B4B4B  (Charcoal)
8. #1E1E1E  (Kearney Black)
9. #9150E1  (Bright Purple)
10. #7823DC (Kearney Purple / primary brand color)
```

---

## Project Types

| Type | Description | Primary Outputs |
|------|-------------|-----------------|
| `analytics` | Data analysis & insights | Charts, insights catalog |
| `presentation` | Executive slides | PowerPoint deck |
| `dashboard` | Interactive visualization | HTML/Streamlit/React app |
| `modeling` | ML/Statistical models | Model artifacts, reports |
| `proposal` | RFP responses, pitches | Word document, slides |
| `research` | Market/competitive analysis | Research report |

---

## Commands

| Command | Description |
|---------|-------------|
| `/startkie` | Bootstrap new KIE project in current folder |
| `/interview` | Start conversational requirements gathering |
| `/status` | Show current project state |
| `/validate` | Run comprehensive quality checks |
| `/build` | Execute full deliverable generation |
| `/preview` | Generate preview of current outputs |

---

## Chart Generation (v3 Pattern)

```python
from kie.charts import ChartFactory
import pandas as pd

# Your data
data = pd.DataFrame({
    'region': ['North', 'South', 'East', 'West'],
    'revenue': [1250000, 980000, 1450000, 1100000]
})

# Generate chart (creates JSON config)
chart_config = ChartFactory.bar(
    data=data,
    x='region',
    y=['revenue'],
    title='Q3 Revenue by Region'
)

# Save for React rendering
chart_config.to_json('outputs/charts/revenue_by_region.json')
```

**React consumption (automatic in dashboard)**:
```tsx
import { ChartRenderer } from './components/charts';

<ChartRenderer configPath="/charts/revenue_by_region.json" />
```

---

## Validation (Critical Safety Layer)

**NEVER deliver outputs to consultants without validation!**

```python
from kie.validation import validate_chart_output

# Validate before delivery
report = validate_chart_output(
    data=data,
    chart_config=chart_config.to_dict(),
    output_path=output_path,
    strict=True  # Warnings also block output
)

if not report.passed:
    print("❌ Validation failed - cannot deliver!")
    print(report.format_text_report())
```

Validation prevents:
- Synthetic/fake data (test names, sequential IDs)
- Brand violations (green colors, gridlines)
- Data quality issues (nulls, duplicates, errors)
- Content problems (placeholders, profanity)
- Calculation errors (infinity, overflow)
- Accessibility violations (contrast, font size)

---

## State Management

```
project_state/
  spec.yaml               # Requirements (source of truth)
  interview_state.yaml    # Interview progress
  status.json             # Build status
  validation_reports/     # QC reports
```

---

## Tool Usage Rules

### Charts
```python
from kie.charts import ChartFactory

# Create chart
config = ChartFactory.bar(data, x="region", y=["revenue"])
config.to_json('outputs/charts/revenue.json')
```

### Interview
```python
from kie.interview import InterviewEngine

interview = InterviewEngine()
response = interview.process_message("I need a sales dashboard")
```

### Validation
```python
from kie.validation import ValidationPipeline, ValidationConfig

pipeline = ValidationPipeline(ValidationConfig(strict=True))
summary = pipeline.get_pipeline_summary()
```

---

## Package Information

**Package name**: `kie` (version 3.0.0)
**Installation**: `pip install -e ".[all]"`

**Critical**: NEVER import from `core` or `core_v3` - those are v2 only. Always use `kie`:

```python
# ✅ Correct
from kie.charts import ChartFactory
from kie.validation import validate_chart_output

# ❌ Wrong
from core.charts import Chart  # v2 only
from core_v3.charts import ChartFactory  # old name
```

---

## Non-Goals

- User authentication (uses Claude Code security)
- Multi-tenant features
- Arbitrary code execution outside kie/
- Mobile layouts
- External API integrations (unless specified)

---

**Version**: 3.0.0
**Status**: Production Ready ✅
**Tests**: 11/11 Passing ✅
**KDS Compliance**: 100% ✅
