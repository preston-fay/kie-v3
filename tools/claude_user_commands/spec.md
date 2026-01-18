---
name: spec
description: View current project specification
---

```bash
# Check for KIE workspace
if [ ! -f "project_state/spec.yaml" ] && [ ! -d "project_state" ]; then
  echo "❌ Not in a KIE workspace"
  echo "Run /startkie to bootstrap first"
  exit 1
fi

# Route to project CLI
python3 -m kie.cli spec
```
