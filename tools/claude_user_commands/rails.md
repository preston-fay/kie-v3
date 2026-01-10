---
name: rails
description: Show Rails workflow progress and suggest next command
---

```bash
# Check for KIE workspace
if [ ! -d ".kie/src" ]; then
  echo "❌ Not in a KIE workspace"
  echo "Run /startkie to bootstrap first"
  exit 1
fi
```

You are in a KIE workspace with Rails workflow tracking.

**IMPORTANT:** This command shows status only. DO NOT auto-run the suggested next command.

Run these commands and report the output:

```bash
PYTHONPATH=".kie/src" python3 -m kie.cli status
```

After showing the status output, STOP.
