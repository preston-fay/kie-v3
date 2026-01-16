# KIE v3 Codebase Structure

## Top-Level Directories

```
kie/                # Python backend (core engine)
web/                # React frontend (dashboard UI)
tests/              # Integration tests (1338 tests)
examples/           # Usage examples
docs/               # Architecture & compliance docs
project_template/   # Workspace scaffolding template
scripts/            # Utility scripts
```

## kie/ Module Structure

### Core Modules
- **kie/base.py**: Core data models (RechartsConfig, Insight, etc.)
- **kie/cli.py**: CLI entry point (KIEClient class)
- **kie/commands/handler.py**: CommandHandler - orchestrates all slash commands

### Key Subsystems

#### Data & Analysis
- **kie/data/**: DataLoader - intelligent column mapping, schema inference
- **kie/insights/engine.py**: InsightEngine - auto-extract insights from data
- **kie/formatting/**: Number, currency, percentage formatters

#### Charts & Visualization
- **kie/charts/**: ChartFactory - generates KDS-compliant Recharts configs
  - ChartBuilder classes (bar, line, area, pie, etc.)
  - svg_renderer.py - Pygal-based SVG generation for PowerPoint
- **kie/brand/**: KDS color system, validation rules
- **kie/validation/**: Multi-level QC pipeline

#### Skills (Rails Architecture)
- **kie/skills/**: Skill-based architecture (analyze stage)
  - base.py: Skill, SkillContext, SkillResult
  - registry.py: Skill registration system
  - insight_triage.py: Filters top insights
  - visualization_planner.py: Plans chart types
  - visual_storyboard.py: Creates storyboard sections
  - story_manifest.py: Final manifest for PowerPoint

#### Output Generation
- **kie/powerpoint/**: PPT generation engine
- **kie/export/**: Export utilities
- **kie/reports/**: HTML report generation
- **kie/geo/**: Geographic visualization (maps)

#### Workflow & State
- **kie/workflow/**: Orchestration logic
- **kie/state/**: Project state management
- **kie/interview/**: Conversational requirements gathering

#### Configuration
- **kie/config/**: Configuration management
- **kie/templates/**: Project templates
- **kie/workspace/**: Workspace utilities

## Critical Files
- **CLAUDE.md**: AI agent instructions (operating rules)
- **RAILS_ARCHITECTURE.md**: Phased implementation plan
- **pyproject.toml**: Python packaging & dependencies
