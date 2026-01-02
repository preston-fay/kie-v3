# KIE - Kearney Insight Engine v3

**AI-powered consulting delivery platform that transforms natural language requirements into polished, KDS-compliant deliverables.**

![Version](https://img.shields.io/badge/version-3.0.0-purple)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![KDS](https://img.shields.io/badge/KDS-100%25%20Compliant-success)
![Tests](https://img.shields.io/badge/tests-11%2F11%20passing-success)

---

## Overview

KIE v3 is a complete rewrite focusing on:
- ✅ **100% KDS Compliance** (enforced programmatically)
- ✅ **Modern Architecture** (Python backend + React frontend)
- ✅ **Validation Pipeline** (blocks non-compliant outputs)
- ✅ **Production Ready** (11/11 tests passing)

## Quick Start

```bash
# Install
pip install -e ".[all]"

# Generate a chart
python -c "
from kie.charts import ChartFactory
data = [{'region': 'North', 'revenue': 125000}, ...]
config = ChartFactory.bar(data, x='region', y=['revenue'])
config.to_json('chart.json')
"

# Start dashboard (requires Node 20+)
cd web && npm install && npm run dev
```

## Architecture

```
kie/                # Python backend
├── brand/          # KDS color system & validation
├── charts/         # Chart generation (JSON configs)
├── validation/     # QC pipeline
├── interview/      # Conversational requirements
└── workflow/       # Orchestration

web/                # React frontend
├── src/components/
│   ├── charts/     # Chart renderers (Recharts)
│   └── dashboard/  # KDS layouts (KPI, insights)
└── package.json

tests/              # Integration tests (11/11 passing)
examples/           # Usage examples
docs/               # Architecture & compliance docs
```

## KDS Compliance

**100% compliant by design** - violations are impossible:

| Requirement | Implementation | Enforced |
|-------------|----------------|----------|
| No gridlines | `axisLine: false, tickLine: false` | Schema level ✅ |
| Kearney Purple | `#7823DC` | Default color ✅ |
| 10-color palette | `#D2D2D2, #A5A6A5, ...` | Exact order ✅ |
| Inter font | `fontFamily: "Inter, sans-serif"` | All charts ✅ |
| Responsive grids | `sm:grid-cols-2 lg:grid-cols-4` | Dashboard layouts ✅ |

See `docs/KDS_COMPLIANCE_REPORT_V3.md` for full audit.

## Key Features

### Chart Generation
```python
from kie.charts import ChartFactory

# Bar chart
config = ChartFactory.bar(data, x="region", y=["revenue"])

# Line chart
config = ChartFactory.line(data, x="month", y=["value"])

# Area chart
config = ChartFactory.area(data, x="date", y=["sales"])

# All charts are KDS-compliant by default
config.to_json("output.json")
```

### Dashboard UI
```tsx
import { DashboardLayout, KPICard, ChartRenderer } from './components';

<DashboardLayout
  kpis={<KPICard label="Revenue" value="$478K" trend="up" />}
  charts={<ChartRenderer config={chartConfig} />}
/>
```

### Validation Pipeline
```python
from kie.validation import validate_chart

result = validate_chart(config)
# CRITICAL: Blocks gridlines, forbidden colors
# WARNING: Flags synthetic data
# INFO: Suggests improvements
```

## Documentation

- **[ARCHITECTURE](docs/KIE_V3_ARCHITECTURE.md)** - System design & philosophy
- **[ROADMAP](docs/KIE_V3_ROADMAP.md)** - Development timeline
- **[KDS_COMPLIANCE](docs/KDS_COMPLIANCE_REPORT_V3.md)** - Full KDS audit
- **[DASHBOARD_UI](docs/DASHBOARD_UI_COMPLETE.md)** - React components guide
- **[THEME_SYSTEM](docs/THEME_SYSTEM.md)** - Dark/light mode

## Testing

```bash
# Python tests (11/11 passing)
pytest tests/ -v

# Web build
cd web && npm run build

# Type checking
mypy kie/

# Linting
ruff check kie/
```

## Development

```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v --cov=kie
```

## Examples

See `examples/` for:
- Chart generation with validation
- Dashboard creation
- End-to-end workflows

## Requirements

- **Python**: 3.11+
- **Node.js**: 20+ (for web dashboard)
- **Dependencies**: See `pyproject.toml`

## License

Proprietary - © 2024 Kearney & Company

---

**Status**: Production Ready ✅
**Version**: 3.0.0
**Last Updated**: 2026-01-02
