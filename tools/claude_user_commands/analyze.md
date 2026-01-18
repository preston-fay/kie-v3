---
name: analyze
description: Extract insights from data - find key patterns and recommendations
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
if [ ! -f "project_state/spec.yaml" ] && [ ! -d "project_state" ]; then
  echo "❌ Not in a KIE workspace"
  echo "Run /startkie to bootstrap first"
  exit 1
fi

# Route to project CLI
python3 -m kie.cli analyze
```
