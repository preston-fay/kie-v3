---
name: intent
description: Manage project intent - set objective, view status, or clear
---

```bash
# Check for KIE workspace
if [ ! -d ".kie/src" ]; then
  echo "❌ Not in a KIE workspace"
  echo "Run /startkie to bootstrap first"
  exit 1
fi

# Parse subcommand and arguments (default: status)
SUBCOMMAND="${1:-status}"
shift || true

# Route to project CLI
PYTHONPATH=".kie/src" python3 -m kie.cli intent "$SUBCOMMAND" "$@"
```
