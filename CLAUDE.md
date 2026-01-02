# KIE v3 - Project Instructions for Claude

**You are working on KIE v3** - a complete rewrite with modern architecture and 100% KDS compliance.

---

## Critical Context

### This is v3 - NOT v2

- ✅ **Package name**: `kie` (NOT `core` or `core_v3`)
- ✅ **No matplotlib** - Charts use Recharts (React) only
- ✅ **JSON configs** - Python generates configs, React renders
- ✅ **Modern architecture** - Clean separation of concerns

### Never reference v2

- ❌ Do NOT import from `core` package (doesn't exist here)
- ❌ Do NOT mention `core_v3` (renamed to `kie`)
- ❌ Do NOT use matplotlib (use chart builders → JSON → Recharts)

---

## Directory Structure

```
kie/           # Python backend (was core_v3)
web/           # React frontend (was web_v3)
tests/         # Integration tests
examples/      # Usage examples
docs/          # Documentation
```

## Development Rules

### 1. KDS Compliance First

**ALL outputs must be KDS-compliant:**
- No gridlines (`axisLine: false`, `tickLine: false`)
- Kearney Purple #7823DC for primary elements
- 10-color KDS palette in order
- Inter font family
- Responsive grids (4-col → 2-col → 1-col)

**Use validation pipeline**:
```python
from kie.validation import validate_chart
result = validate_chart(config)
```

### 2. Chart Generation Pattern

```python
from kie.charts import ChartFactory

# Generate chart config
config = ChartFactory.bar(data, x="region", y=["revenue"])

# Export to JSON for React
config.to_json("web/public/charts/revenue.json")
```

**React consumption**:
```tsx
import { ChartLoader } from './components/charts';

<ChartLoader configPath="/charts/revenue.json" />
```

### 3. Testing Requirements

**Every feature needs tests**:
```bash
pytest tests/test_*.py -v
```

Current status: 11/11 tests passing ✅

### 4. Type Hints Required

Use Pydantic for schemas:
```python
from pydantic import BaseModel

class ChartConfig(BaseModel):
    type: str
    data: List[Dict[str, Any]]
    config: Dict[str, Any]
```

---

## Common Tasks

### Generate Chart

```python
from kie.charts import ChartFactory

data = [{"x": 1, "y": 100}, {"x": 2, "y": 200}]
config = ChartFactory.bar(data, x="x", y=["y"], title="My Chart")
config.to_json("output.json")
```

### Validate Output

```python
from kie.validation import validate_chart

result = validate_chart(config.to_dict())
if not result.compliant:
    print(f"Violations: {result.violations}")
```

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_charts.py -v -k bar_chart
```

### Build Web Dashboard

```bash
cd web
npm install
npm run build
```

---

## Architecture Principles

### Python Backend (kie/)

**Responsibilities**:
- Generate KDS-compliant chart configs (JSON)
- Validate outputs against KDS rules
- Provide CLI and API interfaces
- Handle data processing and analysis

**Does NOT**:
- Render charts directly (React does that)
- Use matplotlib (v2 only)
- Mix concerns (clean separation)

### React Frontend (web/)

**Responsibilities**:
- Consume JSON configs from Python
- Render KDS-compliant dashboards
- Provide interactive UI
- Theme management (dark/light)

**Does NOT**:
- Generate chart data (Python does that)
- Validate compliance (Python does that)
- Make backend calls during render

---

## File Locations

### Core Systems

| System | Location | Description |
|--------|----------|-------------|
| Chart builders | `kie/charts/builders/` | Generate chart configs |
| Validation | `kie/validation/` | QC pipeline |
| Brand system | `kie/brand/` | KDS colors & compliance |
| Interview | `kie/interview/` | Requirements gathering |
| Workflow | `kie/workflow/` | Orchestration |

### React Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Chart renderers | `web/src/components/charts/` | Render JSON configs |
| Dashboard layouts | `web/src/components/dashboard/` | KDS grids |
| Theme system | `web/src/contexts/ThemeContext.tsx` | Dark/light modes |

---

## Testing Checklist

Before committing:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Type checking: `mypy kie/`
- [ ] Linting: `ruff check kie/`
- [ ] Web builds: `cd web && npm run build`
- [ ] Validation passes on generated outputs

---

## Common Pitfalls

### ❌ Wrong: Using matplotlib

```python
import matplotlib.pyplot as plt
plt.bar(x, y)  # NO - v2 only
```

### ✅ Right: Using chart factory

```python
from kie.charts import ChartFactory
config = ChartFactory.bar(data, x="x", y=["y"])
```

### ❌ Wrong: Importing from old package

```python
from core.charts import Chart  # NO - doesn't exist
from core_v3.charts import Chart  # NO - renamed
```

### ✅ Right: Using new package name

```python
from kie.charts import ChartFactory  # YES
```

### ❌ Wrong: Hardcoding colors

```python
bar_config = {"fill": "#00FF00"}  # NO - green forbidden
```

### ✅ Right: Using KDS colors

```python
from kie.brand.colors import KDSColors
colors = KDSColors.get_chart_colors(1)  # Returns KDS palette
```

---

## Documentation

- **README.md** - Quick start guide
- **docs/KIE_V3_ARCHITECTURE.md** - System design
- **docs/KDS_COMPLIANCE_REPORT_V3.md** - Full KDS audit
- **docs/DASHBOARD_UI_COMPLETE.md** - React components
- **docs/ROADMAP.md** - Development timeline

---

## Getting Help

1. **Check tests**: `tests/test_v3_integration.py` shows usage patterns
2. **Check examples**: `examples/` has working code
3. **Check docs**: `docs/` has detailed guides
4. **Run validation**: Use `kie.validation` to check outputs

---

**Version**: 3.0.0
**Status**: Production Ready ✅
**Tests**: 11/11 Passing ✅
**KDS Compliance**: 100% ✅
