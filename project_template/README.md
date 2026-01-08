# KIE Workspace - Quick Start

## Available Commands

All slash commands live in `.claude/commands/` - each command is a minimal wrapper that executes the corresponding KIE CLI function.

To see all available commands:
- Run `/railscheck` and read the enumerated list in the output
- Or browse `.claude/commands/*.md` to see what's available

⚠️ **Commands are case-sensitive.** Use `/eda` not `/EDA`

## Recommended Workflows

### Option 1: I Have Data, Need Quick Analysis
1. Drop your data file (CSV/Excel/Parquet/JSON) in `data/` folder
2. Run `/eda` to profile your data
3. Run `/analyze` to extract insights

### Option 2: Need Formal Deliverable (Presentation/Dashboard)
1. Run `/interview` to gather requirements
2. Choose express (6 questions) or full (11 questions)
3. Follow the guided workflow

### Option 3: Just Exploring KIE
1. Sample data is in `data/sample_data.csv`
2. Run `/eda` to see how analysis works
3. Run `/analyze` to see insight extraction

---

## Folder Structure

```
data/           - Put your data files here
outputs/        - Generated charts, tables, maps
exports/        - Final deliverables (PPTX, PDF, etc.)
project_state/  - Project tracking and validation reports
```

## Tips

- Just describe what you need naturally
- Say "preview" to see what's been generated
- Say "export" when ready for final deliverables
- KIE enforces Kearney brand standards automatically
- All outputs are validated before delivery
