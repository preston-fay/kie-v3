---
name: startkie
description: Bootstrap a new KIE workspace in current folder
---

I'll initialize a KIE workspace in the current directory.

```bash
python3 -m kie.cli startkie
```

This creates:
- Folder structure (data/, outputs/, exports/, project_state/)
- README.md and CLAUDE.md
- .gitignore
- Slash commands in .claude/commands/
- Sample dataset in data/sample_data.csv

---

After initialization completes, I'll show you the available commands and next steps:

## Available Commands

| Command | What It Does |
|---------|-------------|
| `/eda` | Exploratory data analysis - profiles your data, finds patterns |
| `/analyze` | Extract insights - identifies key trends, comparisons, outliers |
| `/interview` | Start requirements gathering (express or full mode) |
| `/map` | Create geographic visualizations from location data |
| `/build` | Generate deliverables (dashboard/presentation) |
| `/status` | Show current project state and progress |
| `/spec` | View your project specification |
| `/preview` | Preview current outputs |
| `/validate` | Run quality checks on outputs |

## Recommended Next Steps

**Option 1: Quick Start (Use Sample Data)**
1. I'll run `/eda` on the sample data to show you how it works
2. Then run `/analyze` to see insights
3. You can explore the outputs in the `outputs/` folder

**Option 2: Use Your Own Data**
1. Drop your CSV file in the `data/` folder
2. Run `/eda` to profile it
3. Run `/analyze` to extract insights
4. Run `/interview` if you want to create a formal deliverable

**Option 3: Formal Project (Deliverable Needed)**
1. Run `/interview` to start requirements gathering
2. Choose express (6 questions) or full (11 questions) mode
3. I'll guide you through the rest

Which option would you like?
