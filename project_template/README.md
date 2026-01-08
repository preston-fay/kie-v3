# KIE Workspace - Quick Start

## Available Commands (case-sensitive, lowercase only!)

| Command | What It Does |
|---------|-------------|
| `/eda` | Exploratory data analysis - profile your data |
| `/analyze` | Extract insights - find key patterns |
| `/interview` | Start requirements gathering (express or full) |
| `/map` | Create geographic visualizations |
| `/build` | Generate deliverables (presentation/dashboard) |
| `/status` | Show current project state |
| `/spec` | View your specification |
| `/preview` | Preview current outputs |
| `/validate` | Run quality checks |
| `/railscheck` | Verify Rails configuration |

⚠️ **Commands are case-sensitive.** Use `/startkie` not `/STARTKIE`

## Recommended Workflows

### Option 1: I Have Data, Need Quick Analysis
1. Drop your CSV file in `data/` folder
2. Type `/eda` to profile your data
3. Type `/analyze` to extract insights

### Option 2: Need Formal Deliverable (Presentation/Dashboard)
1. Type `/interview` to gather requirements
2. Choose express (6 questions) or full (11 questions)
3. Follow the guided workflow

### Option 3: Just Exploring KIE
1. Sample data is in `data/sample_data.csv`
2. Type `/eda` to see how analysis works
3. Type `/analyze` to see insight extraction

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
