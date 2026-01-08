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

After initialization completes, I'll run `/eda` on the sample data to verify everything works.

If you want to use your own data instead, drop a CSV file in the `data/` folder and I'll analyze that instead.
