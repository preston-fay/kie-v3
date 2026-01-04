# KIE Consultant Quick Start Guide

## Recommended Workflow: Use the Workspace Starter Template

**The easiest way to start a KIE project:**

1. **Get the workspace starter ZIP**
   - Ask your tech lead for `kie_workspace_starter.zip`
   - Or generate it: `python3 -m kie.cli template`

2. **Set up your project folder**
   - Unzip to a new folder (e.g., `acme-q4-analysis/`)
   - Rename the folder to match your project
   - Open the folder in Claude Code

3. **Verify setup**
   - Run `/kie_setup` in Claude Code
   - It should confirm slash commands are available

4. **Start working**
   - Run `/interview` to begin requirements gathering
   - Drop your data file in the chat or `data/` folder
   - Describe what you need in plain English

That's it! You're ready to work.

---

## What's Inside the Starter Template?

The ZIP contains a complete KIE workspace:

```
kie_workspace_starter/
├── .claude/
│   └── commands/          # Slash commands (/interview, /build, etc.)
├── data/                  # Put your data files here
├── outputs/
│   ├── charts/           # Generated charts
│   ├── tables/           # Table configurations
│   └── maps/             # Map visualizations
├── exports/              # Final deliverables (PPTX, etc.)
├── project_state/        # Project tracking
│   ├── spec.yaml         # Requirements (source of truth)
│   └── .kie_workspace    # Workspace marker
├── README.md             # Project-specific readme
├── CLAUDE.md             # Full KIE instructions
└── .gitignore            # Git configuration
```

---

## Available Commands

Once your workspace is set up, use these slash commands in Claude Code:

| Command | Description |
|---------|-------------|
| `/kie_setup` | Check workspace health (run this first) |
| `/interview` | Start requirements gathering |
| `/status` | Show project status |
| `/eda` | Run exploratory data analysis |
| `/analyze` | Extract insights from data |
| `/validate` | Run quality checks |
| `/build` | Build deliverables (presentation, dashboard) |
| `/preview` | Preview outputs |
| `/doctor` | Detailed workspace diagnostics |

---

## Fallback: Manual Initialization (Power Users Only)

If you don't have the starter template, you can initialize manually:

```bash
python3 -m kie.cli init
```

**Warning:** This requires terminal access and won't create slash commands automatically. The starter template is strongly recommended.

---

## Common Issues

### "Slash command not found"

**Problem:** You started in an empty folder without the starter template.

**Solution:**
1. Exit the empty folder
2. Use the workspace starter template (see above)
3. Open the template folder in Claude Code
4. Run `/kie_setup` to verify

### "Can't find data"

**Problem:** Data file is in the wrong location.

**Solution:**
- Drop the file directly in the Claude Code chat, OR
- Put it in the `data/` folder

### "Commands don't work"

**Problem:** You might be in the KIE product repo, not a workspace.

**Solution:**
- Use the workspace starter template in a **separate folder**
- Do not work inside `/Users/pfay01/Projects/kie-v3/`

---

## Tips for Success

1. **One workspace per project** - Each client/deliverable gets its own folder
2. **Describe naturally** - Just say what you need in plain English
3. **Use `/status` often** - Check progress at any time
4. **Trust the validation** - KIE enforces Kearney brand standards automatically
5. **Ask questions** - Claude (with KIE) can explain what it's doing

---

## Support

For issues or questions:
- Check `/doctor` for diagnostic information
- Ask your tech lead for help
- Reference `/Users/pfay01/Projects/kie-v3/CLAUDE.md` for detailed documentation
