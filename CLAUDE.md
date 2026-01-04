# KIE - Kearney Insight Engine v3.0

## System Overview

KIE (Kearney Insight Engine) is an AI-powered consulting delivery platform that transforms
natural language requirements into polished, brand-compliant deliverables.

**Core Philosophy: "LLM Reasons, Python Executes"**
- Claude handles understanding, reasoning, and orchestration
- Python engines handle deterministic, reproducible output generation
- Brand compliance is programmatically enforced (cannot be bypassed)

---

## CRITICAL: Operating Rules (NEVER VIOLATE THESE)

**These rules are MANDATORY and override all other instructions. Violating them wastes the user's time and destroys trust.**

### Rule 1: NEVER State Guesses as Facts

- **DO SAY**: "I don't know if this will work - let me test it"
- **DO SAY**: "I'm making an assumption here: [state assumption]"
- **DO SAY**: "I haven't tested this - you'll need to verify"
- **NEVER SAY**: "This will work" (unless you just verified it)
- **NEVER SAY**: "The commands are working" (unless you just ran them successfully)
- **NEVER SAY**: "This should work" (unless you can explain why with evidence)

### Rule 2: Distinguish Verified from Unverified Claims

**Verified Claims** (you just tested them):
- ✅ "I just ran `/eda` via `python3 -m kie.cli /eda` and it succeeded"
- ✅ "I read the file at line 47 and confirmed the function exists"
- ✅ "The tests passed - here's the output"

**Unverified Claims** (you're guessing):
- ❌ "The slash commands will work in the new project"
- ❌ "This approach should solve the problem"
- ❌ "The system is now configured correctly"

**If you can't test it yourself, explicitly say so:**
- "I can't test whether `/eda` works as a slash command - you'll need to try it"
- "I don't have a way to verify this - please test and report back"

### Rule 3: When Something Fails, Admit It Immediately

- **DO**: "That failed. I was wrong about how this works."
- **DO**: "I made an incorrect assumption. Let me investigate the actual behavior."
- **DO**: "I don't understand why this isn't working - I need to research it."
- **NEVER**: Make excuses or explain why it "should have worked"
- **NEVER**: Blame the system, the code, or external factors
- **NEVER**: Move on without acknowledging the failure

### Rule 4: Execute KIE Commands Correctly

When the user types a KIE command:

| User Types | You Execute |
|------------|-------------|
| `/startkie` | Use the SlashCommand tool (it's a Claude slash command) |
| `/eda` | `python3 -m kie.cli eda` |
| `/status` | `python3 -m kie.cli status` |
| `/spec` | `python3 -m kie.cli spec` |
| `/interview` | `python3 -m kie.cli interview` |
| `/analyze` | `python3 -m kie.cli analyze` |
| `/map` | `python3 -m kie.cli map` |
| `/validate` | `python3 -m kie.cli validate` |
| `/build` | `python3 -m kie.cli build [target]` |
| `/preview` | `python3 -m kie.cli preview` |
| `/doctor` | `python3 -m kie.cli doctor` |

**Do NOT:**
- Explain what the command does and wait
- Ask if they want you to run it
- Describe what will happen
- Use any other execution method

**Just run the Python CLI command immediately.**

### Rule 5: Understand Your Control Boundaries

**You CAN control:**
- Python code you write
- Bash commands you execute
- Files you create/edit in the project
- Testing and verifying your own work

**You CANNOT control:**
- How Claude Code interprets slash commands
- Whether slash command files in one project affect another project
- System-level Claude Code behavior
- The user's environment setup

**NEVER claim to fix or configure things outside your control boundaries.**

### Rule 6: No False Victories

- **NEVER** say "Done!" or "✅ Complete" until you've **verified** success
- **NEVER** say "The system is working" until you've **tested** it
- **NEVER** mark a task complete if any part failed
- **ALWAYS** test your changes before declaring success
- **ALWAYS** acknowledge failures immediately, even if partial progress was made

### Failure Checklist

Before claiming something works, ask yourself:
1. ☐ Did I actually test this, or am I guessing?
2. ☐ Did the test succeed, or am I assuming it will work?
3. ☐ Can I point to specific evidence (command output, file contents)?
4. ☐ Am I within my control boundaries, or claiming to fix external systems?
5. ☐ If this fails, will I have wasted the user's time?

**If you answered "guessing," "assuming," "no," "external systems," or "yes" to any of these, STOP and revise your claim.**

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
| `dashboard` | Interactive visualization | React app |
| `modeling` | ML/Statistical models | Model artifacts, reports |
| `proposal` | RFP responses, pitches | Word document, slides |
| `research` | Market/competitive analysis | Research report |

---

## Commands

**IMPORTANT: When user types a slash command like `/status` or `/eda`, execute it via terminal:**
```bash
python3 -m kie.cli status
```

All commands work in both interactive REPL mode AND one-shot terminal execution.

| Command | Description | Terminal Usage |
|---------|-------------|----------------|
| `/kie_setup` | Check workspace health (primary command) | `python3 -m kie.cli doctor` |
| `/startkie` | Alias for /kie_setup (deprecated) | `python3 -m kie.cli doctor` |
| `/status` | Show current project state | `python3 -m kie.cli status` |
| `/spec` | View current specification | `python3 -m kie.cli spec` |
| `/interview` | Start conversational requirements gathering | `python3 -m kie.cli interview` |
| `/eda` | Run exploratory data analysis | `python3 -m kie.cli eda` |
| `/analyze` | Extract insights from data | `python3 -m kie.cli analyze` |
| `/map` | Create geographic visualizations | `python3 -m kie.cli map` |
| `/validate` | Run comprehensive quality checks | `python3 -m kie.cli validate` |
| `/build` | Execute full deliverable generation | `python3 -m kie.cli build` |
| `/preview` | Generate preview of current outputs | `python3 -m kie.cli preview` |
| `/doctor` | Check workspace health and detect package collisions | `python3 -m kie.cli doctor` |
| `/template` | Generate workspace starter ZIP | `python3 -m kie.cli template` |

---

## Intelligence & Overrides

KIE's **DataLoader** uses a sophisticated 5-phase intelligence system to automatically select the right columns for analysis, even from messy or ambiguous data.

### How Intelligence Works

When you run `/build` or `/analyze`, KIE automatically:
1. Reads your project `objective` from `spec.yaml`
2. Loads your data and infers schema
3. Intelligently maps columns using **4-Tier Semantic Scoring**:
   - **Tier 1: Semantic Match** - Recognizes revenue/cost/margin keywords
   - **Tier 2: ID Avoidance** - Rejects ZipCodes, IDs, meaningless numbers
   - **Tier 3: Percentage Handling** - Doesn't penalize small values (0.15) when they're rates
   - **Tier 4: Statistical Vitality** - Uses coefficient of variation (CV) as tie-breaker

**Example Intelligence in Action:**
```python
# Your CSV has: CustomerID, ZipCode, Revenue, GrossMargin
# Objective: "Analyze efficiency and profitability"

# Intelligence automatically:
# - Rejects CustomerID (ID keyword)
# - Rejects ZipCode (high mean, low variance)
# - Picks GrossMargin for efficiency (0.0-1.0 range, "margin" keyword)
# - NOT fooled by Revenue's larger magnitude
```

### The Safety Valve: Human Override

Sometimes you need to **override the intelligence** and explicitly tell KIE which columns to use.

Add a `column_mapping` section to your `spec.yaml`:

```yaml
project_name: "Q4 Revenue Analysis"
client_name: "Acme Corp"
objective: "Analyze recurring revenue growth"
project_type: analytics

# OVERRIDE: Explicitly map columns (bypasses ALL intelligence)
column_mapping:
  revenue: "Recurring_Revenue"    # Use this instead of "Total_Revenue"
  cost: "COGS"                     # Use this for cost analysis
  category: "Customer_Segment"     # Group by this column
  # date: (not specified - intelligence will pick)
```

**Override Behavior:**
- Overrides take **absolute precedence** - they bypass all 4 tiers of intelligence
- Can override some columns and let intelligence pick others (partial override)
- If override column doesn't exist, gracefully falls back to intelligence
- This is "God Mode" - your word is final

**When to Use Overrides:**
- Data has similar columns: `Total_Revenue` vs `Recurring_Revenue`
- Column names are ambiguous: `Value_1`, `Metric_A`
- You want a specific non-obvious column: Force analysis on `ZipCode` for debugging
- Intelligence guessed wrong (rare, but possible)

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
