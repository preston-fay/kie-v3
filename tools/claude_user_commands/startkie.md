# /startkie - Bootstrap KIE Project

Bootstrap a new KIE project in the current directory.

## Instructions

Run the KIE bootstrap command to scaffold a new project:

```bash
python3 -m kie.cli startkie
```

This creates:
- `data/` - Place your data files here
- `outputs/` - Generated deliverables
- `exports/` - Final client-ready exports
- `project_state/` - KIE state files (spec.yaml, etc.)
- `CLAUDE.md` - Project-specific instructions
- `README.md` - Project documentation
- `.gitignore` - Standard ignores

After scaffolding, begin conversational requirements gathering to understand the project needs.
