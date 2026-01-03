# Start KIE in Current Folder

Bootstrap a KIE (Kearney Insight Engine) project right here, right now.

## What This Does

When you run `/startkie`, Claude will:
1. Create the KIE folder structure (data/, outputs/, exports/, project_state/, .claude/commands/)
2. Copy all slash command files from kie-v3 repo
3. Generate CLAUDE.md with all KIE instructions
4. Generate README.md with quick reference
5. Create .gitignore for proper file handling
6. Begin conversational requirements gathering

## Usage

Just type `/startkie` in any folder and you're ready to work.

## Detection Logic

This command will NOT run if:
- A CLAUDE.md already exists with "KIE Project" in it (already a KIE project)
- You're in the KIE repository itself (project_template/ exists)

In those cases, you'll get a message explaining why.

## Bootstrap Code

Execute this EXACT Python code:

```python
from pathlib import Path

# Create folder structure including .claude/commands
folders = ['data', 'outputs', 'exports', 'project_state', '.claude/commands']
for folder in folders:
    Path(folder).mkdir(parents=True, exist_ok=True)
    print(f"✓ Created {folder}/")

# Create .gitignore
gitignore_content = """# Data files
data/*
!data/.gitkeep

# Outputs
outputs/*
!outputs/.gitkeep

# Exports
exports/*
!exports/.gitkeep

# Python
__pycache__/
*.pyc
.venv/
"""

Path('.gitignore').write_text(gitignore_content)
print("✓ Created .gitignore")

print("\n✓ KIE folder structure created!")
```

Then copy slash commands:

```bash
cp /Users/pfay01/Projects/kie-v3/.claude/commands/*.md .claude/commands/
```

## What Happens Next

After setup completes, Claude will greet you and ask:
- What client/project are you working on?
- What type of deliverable do you need? (presentation, dashboard, analysis, etc.)
- What data do you have?

Then you're off and running with full KIE capabilities.
