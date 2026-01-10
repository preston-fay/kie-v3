# Claude Code Slash Commands for KIE

This document explains how KIE slash commands work in Claude Code and why user-level installation is needed.

## Why User-Level Commands?

**Claude Code limitation:** CC loads slash commands only at session start from:
- `~/.claude/commands/` (user-level)
- `.claude/commands/` (project-level)

**The problem:** Commands created mid-session (e.g., by `/startkie` bootstrap) aren't recognized until CC restarts.

**The solution:** Install KIE commands at user level (`~/.claude/commands/`) so they're available when CC starts, eliminating the need to restart after `/startkie`.

## Installation

### One-Time Setup

After installing KIE, run once:

```bash
python3 -m kie.cli install_commands
```

This installs 12 KIE slash commands to `~/.claude/commands/`:
- `/eda` - Exploratory data analysis
- `/analyze` - Extract insights from data
- `/build` - Generate deliverables
- `/preview` - Preview outputs
- `/rails` - Show workflow progress
- `/go` - Execute next workflow step
- `/spec` - Manage project specification
- `/status` - Show project status
- `/validate` - Run quality checks
- `/interview` - Requirements gathering
- `/map` - Geographic visualizations
- `/doctor` - Workspace health check

**After installation:** Restart Claude Code once to load the commands.

### Automatic Installation

The `/startkie` bootstrap script automatically checks for user-level commands:
- **First time:** Runs `install_commands` and prompts one-time CC restart
- **Already installed:** No restart needed - commands work immediately

## Usage Flow

### First Project (One-Time Restart)

```
1. Open Claude Code in empty folder
2. Type: /startkie
   → Bootstrap runs
   → Installs user commands if missing
   → Message: "ONE-TIME: Restart Claude Code to load slash commands"
3. Restart Claude Code (once)
4. Type: /eda, /rails, /go, etc. → Works immediately
```

### Subsequent Projects (Zero Restart)

```
1. Open Claude Code in new folder
2. Type: /startkie
   → Bootstrap runs
   → Detects commands already installed
   → Message: "No restart needed - slash commands are ready to use"
3. Type: /eda, /rails, /go, etc. → Works immediately
```

## How Commands Work

Each user-level command:

1. **Detects workspace:** Checks for `.kie/src` directory
2. **Routes to CLI:** Runs `PYTHONPATH=".kie/src" python3 -m kie.cli <command>`
3. **Friendly errors:** If not in KIE workspace, shows: "Run /startkie to bootstrap first"

### Example: /eda Command

```markdown
---
name: eda
description: Exploratory data analysis - profile data, find patterns
---

```bash
# Check for KIE workspace
if [ ! -d ".kie/src" ]; then
  echo "❌ Not in a KIE workspace"
  echo "Run /startkie to bootstrap first"
  exit 1
fi

# Route to project CLI
PYTHONPATH=".kie/src" python3 -m kie.cli eda
```
```

## Project-Level Commands

KIE still creates `.claude/commands/` in each workspace for portability:
- Allows workspace to be shared without requiring user-level install
- Project commands override user commands if names conflict
- Both approaches coexist

## Troubleshooting

### Commands Don't Show in /help

**Symptom:** After `install_commands`, slash commands don't appear in `/help` or autocomplete.

**Solution:** Restart Claude Code. CC only loads commands at session start.

### Commands Say "Not in a KIE workspace"

**Symptom:** `/eda` or `/rails` says "Not in a KIE workspace" even though you ran `/startkie`.

**Possible causes:**
1. `/startkie` didn't complete successfully - check output
2. `.kie/src` directory missing - run `/startkie` again
3. You're in wrong directory - `cd` to project root

**Solution:** Verify `.kie/src` exists:
```bash
ls -la .kie/src
```

### Need to Reinstall Commands

**Symptom:** Want to update commands after pulling new KIE version.

**Solution:** Reinstall to get latest versions:
```bash
python3 -m kie.cli install_commands
# Restart Claude Code
```

### Conflicts with Custom /startkie

**Protection:** `install_commands` never overwrites `~/.claude/commands/startkie.md` if it already exists.

If you have a custom `/startkie`, your version is preserved.

## Technical Details

### Installation Metadata

Each installed command includes a header:

```markdown
<!--
installed_from_repo: preston-fay/kie-v3
installed_at: 2026-01-10T08:20:54.452055
source_commit: 64e6fd2f
-->
```

This tracks:
- Source repository
- Installation timestamp
- Git commit (for version tracking)

### File Locations

```
~/.claude/commands/         User-level (always loaded)
├── eda.md                 ✓ Installed by install_commands
├── rails.md               ✓ Installed by install_commands
├── ...                    ✓ (12 total KIE commands)
└── startkie.md            ⚠ User-managed (not overwritten)

project/.claude/commands/   Project-level (optional, for portability)
├── eda.md                 ✓ Created by /startkie
├── rails.md               ✓ Created by /startkie
└── ...                    ✓ (13 total, including startkie)
```

### Cross-Platform Compatibility

The installer uses `Path.home()` to detect user home directory:
- **macOS/Linux:** `~/.claude/commands`
- **Windows:** `%USERPROFILE%\.claude\commands`

## FAQ

**Q: Do I need to reinstall commands for each project?**
A: No. Install once, use everywhere.

**Q: What if I delete a command file?**
A: Run `install_commands` again to restore.

**Q: Can I customize installed commands?**
A: Yes, edit files in `~/.claude/commands/`. Changes persist until you reinstall.

**Q: What about `/startkie`?**
A: It's separately managed (not part of `install_commands`). Keep your existing version.

**Q: Do commands work offline?**
A: Yes. Commands route to vendored `.kie/src` in your workspace (no network needed).

**Q: How do I uninstall?**
A: Delete `~/.claude/commands/*.md` files (keep `startkie.md` if you use it elsewhere).

## Summary

- **Install once:** `python3 -m kie.cli install_commands` + restart CC
- **Zero restart after that:** `/startkie` works immediately in new projects
- **Commands auto-detect** workspace and route to project CLI
- **Coexists** with project-level commands for portability
