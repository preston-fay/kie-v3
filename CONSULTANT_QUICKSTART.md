# KIE v3 - How Consultants Start a New Project

## One-Time Setup (5 minutes)

```bash
# Install KIE
pip install -e /path/to/kie-v3-v11

# Verify installation
python -m kie.cli doctor
```

## Starting a New Project (30 seconds)

```bash
# 1. Create project folder
mkdir ~/projects/acme-q1-analysis
cd ~/projects/acme-q1-analysis

# 2. Initialize KIE workspace
python -m kie.cli init
# or: kie init

# 3. Open in Claude Code
# (drag folder to Claude Code or use 'code .')
```

That's it. You now have:
- data/ folder (drop your files here)
- outputs/ folder (charts appear here)
- exports/ folder (final deliverables here)
- project_state/ folder (project tracking)
- .claude/commands/ with /interview, /build, /review

## Using KIE

### Step 1: Gather Requirements
```
You: /interview
```

Claude will have a natural conversation to understand:
- What deliverable you need
- Who the audience is
- What data you have
- Any specific requirements

This creates `project_state/spec.yaml`.

### Step 2: Add Your Data
- Drop data file into the chat, OR
- Put it in the `data/` folder

### Step 3: Build Deliverables
```
You: /build
```

KIE analyzes your data and creates:
- Brand-compliant charts (Kearney purple, no gridlines)
- PowerPoint decks (dark theme, white text)
- Dashboards (interactive HTML)
- Reports (insights and recommendations)

All following Kearney brand standards automatically.

### Step 4: Review (Optional)
```
You: /review
```

KIE checks brand compliance:
- Colors (no green, proper purple)
- Charts (no gridlines, data labels outside)
- Typography (Inter/Arial)
- Contrast (WCAG AA)

### Step 5: Get Your Files
Final deliverables appear in `exports/`:
- presentation.pptx
- dashboard.html
- report.pdf

## Example Session

```
Consultant: /interview

Claude: What are you working on today?

Consultant: I need to create a Q1 sales analysis deck for Acme Corp's 
            leadership team. I have their sales data in a CSV.

Claude: Got it! Here's what I captured:
        - Client: Acme Corp
        - Deliverable: Executive presentation
        - Audience: Leadership team
        - Timeframe: Q1

        Drop your CSV file when ready.

Consultant: [drops acme_q1_sales.csv]

Claude: Received. Run /build when ready to create the deck.

Consultant: /build

Claude: Creating brand-compliant presentation...
        ✓ Analyzed 15,000 sales records
        ✓ Generated 8 insights
        ✓ Created 6 charts (Kearney purple, dark theme)
        ✓ Built 12-slide deck

        Saved to: exports/acme_q1_presentation.pptx

Consultant: /review

Claude: Brand compliance review:
        ✓ All colors compliant (Kearney purple #7823DC)
        ✓ No green colors detected
        ✓ Charts: no gridlines, data labels outside
        ✓ Typography: Arial
        ✓ Dark backgrounds (#1E1E1E) with white text
        ✓ WCAG AA contrast met

        Status: PASS - Ready to export!
```

## Troubleshooting

### Command Not Found
```bash
# If /interview doesn't work:
python -m kie.cli doctor

# Should show:
# ✓ .claude/commands/ exists
# ✓ Found 4 command files
```

### Missing Dependencies
```bash
pip install -e /path/to/kie-v3-v11
```

### Start Fresh
```bash
# In your project folder:
rm -rf .claude data outputs exports project_state
python -m kie.cli init
```

## Multiple Projects

Each project is independent:

```bash
# Project 1
mkdir ~/projects/acme-q1
cd ~/projects/acme-q1
kie init
# Work on Acme Q1...

# Project 2 (separate folder)
mkdir ~/projects/globex-strategy
cd ~/projects/globex-strategy
kie init
# Work on Globex strategy...
```

No conflicts. Each workspace is isolated.

## What Gets Created

After `kie init`:

```
your-project/
├── .claude/
│   └── commands/          # Slash commands
│       ├── interview.md
│       ├── build.md
│       ├── review.md
│       └── startkie.md
├── data/                  # Your data files
├── outputs/               # Generated charts
├── exports/               # Final deliverables
├── project_state/         # Project tracking
│   └── spec.yaml         # (created by /interview)
├── CLAUDE.md             # KIE instructions
├── README.md             # Quick reference
└── .gitignore            # Git config
```

## Brand Rules (Automatic)

KIE enforces Kearney standards automatically:

**Colors:**
- Primary: #7823DC (Kearney Purple)
- FORBIDDEN: All greens
- Dark BG: #1E1E1E
- Text: White (#FFFFFF) on dark

**Charts:**
- No gridlines
- Data labels OUTSIDE bars/slices
- Dark background
- Kearney purple bars

**Typography:**
- Inter font (Arial fallback)
- White text on dark slides

**No Emojis**

You don't have to remember these - KIE enforces them.

## That's It

Three steps:
1. `kie init` (once per project)
2. `/interview` (gather requirements)
3. `/build` (create deliverables)

Clean, fast, brand-compliant.

---

**Questions?** Run `python -m kie.cli doctor` to diagnose issues.
