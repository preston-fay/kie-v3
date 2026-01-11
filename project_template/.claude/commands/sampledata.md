---
name: sampledata
description: Manage sample/demo data - status, install, remove
---

```bash
# Check for KIE workspace
if [ ! -d ".kie/src" ]; then
  echo "❌ Not in a KIE workspace"
  echo "Run /startkie to bootstrap first"
  exit 1
fi

# Parse subcommand (default: status)
SUBCOMMAND="${1:-status}"

# Route to project CLI
PYTHONPATH=".kie/src" python3 -m kie.cli sampledata "$SUBCOMMAND"
```
