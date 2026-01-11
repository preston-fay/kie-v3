---
name: map
description: Create geographic visualizations from location data
---

## GUARDRAIL: Execution Mode Enforcement

**Rails Mode (default)** - Off-rails execution is FORBIDDEN:
- ❌ NEVER write ad-hoc Python scripts outside KIE
- ❌ NEVER use matplotlib/seaborn/plotly
- ❌ NEVER run arbitrary bash/python beyond KIE CLI commands
- ❌ NEVER create non-KIE artifacts

**If user requests custom analysis:** Respond with:
"This requires Freeform Mode. Run /freeform enable to allow custom scripts."
and STOP execution.

**Only proceed with ad-hoc analysis after /freeform enable is set.**

---

```bash
# Check for KIE workspace
if [ ! -d ".kie/src" ]; then
  echo "❌ Not in a KIE workspace"
  echo "Run /startkie to bootstrap first"
  exit 1
fi

# Route to project CLI
PYTHONPATH=".kie/src" python3 -m kie.cli map
```
