---
name: go
description: Execute next workflow step (Golden Path)
---

```bash
# Check for KIE workspace
if [ ! -d ".kie/src" ]; then
  echo "❌ Not in a KIE workspace"
  echo "Run /startkie to bootstrap first"
  exit 1
fi

# Route to project CLI
PYTHONPATH=".kie/src" python3 -m kie.cli go
```
