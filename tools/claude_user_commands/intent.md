---
name: intent
description: Manage project intent - set objective, view status, or clear
---

```bash
# Check for KIE workspace
if [ ! -f "project_state/spec.yaml" ] && [ ! -d "project_state" ]; then
  echo "❌ Not in a KIE workspace"
  echo "Run /startkie to bootstrap first"
  exit 1
fi

# Parse subcommand and arguments (default: status)
SUBCOMMAND="${1:-status}"
shift || true

# Route to project CLI
python3 -m kie.cli intent "$SUBCOMMAND" "$@"
```
