# /help

---
name: help
description: Show available commands
---

Display KIE commands and usage.

## Commands

| Command | Description |
|---------|-------------|
| `/interview` | Gather project requirements |
| `/analyze` | Analyze data and generate insights |
| `/build` | Create presentations, reports, dashboards |
| `/preview` | Preview deliverables in browser |
| `/status` | Show project status |
| `/help` | Show this help |

## Quick Start

```
1. /interview              # Tell KIE what you need
2. /analyze data/file.csv  # Analyze your data
3. /build presentation     # Create deliverable
4. /preview                # Review output
```

## Project Types

- **analytics**: Data analysis, charts, insights
- **presentation**: Slide decks
- **dashboard**: Interactive visualizations
- **modeling**: ML/statistical models
- **proposal**: RFP responses
- **research**: Market analysis
- **data_engineering**: ETL pipelines
- **webapp**: Tools and prototypes

## Core Engines

```python
from core.brand import load_design_system
from core.interview import ConversationalInterviewer
from core.charts import Chart
from core.slides import Presentation
from core.insights import InsightEngine
from core.preview import PreviewEngine
```

## Brand Rules

1. Primary: #7823DC (Kearney Purple)
2. NO green colors
3. Dark mode default
4. No emojis
5. Text on dark: use light purple or white
