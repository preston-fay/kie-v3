# Bootstrap KIE Project

Transform this folder into a KIE (Kearney Insight Engine) project with one command.

## Instructions

You are about to bootstrap a KIE project in the current directory.

**First, check if bootstrap is needed:**

1. Check if `CLAUDE.md` exists and contains "KIE Project" → If yes, say "This is already a KIE project. Ready to start working!"
2. Check if `kie/` exists (Python package) → If yes, say "You're in the KIE repo. Use this folder for client projects instead."
3. Otherwise, proceed with bootstrap

**Bootstrap Process:**

Call the KIE initializer using Python:

```python
import sys
from pathlib import Path

# Try to import and use the installed KIE package
try:
    from kie.cli.workspace import initialize_workspace

    # Initialize in current directory
    success, message = initialize_workspace(Path.cwd())

    if success:
        print(message)
        print("\n✓ KIE workspace initialized!")
    else:
        print(f"✗ Initialization failed: {message}")
        sys.exit(1)

except ImportError:
    print("✗ KIE package not found. Install with: pip install -e /path/to/kie-v3")
    sys.exit(1)
```

**Verify initialization:**

After running init, verify:
- `.claude/commands/interview.md` exists
- `project_state/` exists
- `data/` exists
- At least 3 slash commands present

If verification fails:
"KIE workspace initialization failed. Missing: <items>. Run 'python -m kie.cli init' or reinstall KIE."

**After successful init, say:**

"I've set up KIE in this folder! Let's get started.

What are you working on? Tell me about:
- Your client or project
- What deliverable you need (presentation, dashboard, analysis, etc.)
- What data you have (or if you need sample data)"
