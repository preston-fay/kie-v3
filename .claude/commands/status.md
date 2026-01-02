# /status

---
name: status
description: Show current project status
---

Display the current state of the KIE project.

## Usage

```
/status              # Full status
/status --brief      # One-line summary
```

## Status Display

```
PROJECT STATUS
==============

Specification: project_state/spec.yaml
  - Project: Q4 Revenue Analysis
  - Type: analytics
  - Client: Acme Corp
  - Status: Complete

Insights: outputs/insights.yaml
  - 8 insights (3 key, 5 supporting)
  - 2 recommendations

Outputs:
  - Charts: 4 files in outputs/charts/
  - Presentation: exports/analysis.pptx (12 slides)

Next Step: /build presentation
```

## Checking Status

```python
from pathlib import Path
import yaml

# Check spec
spec_path = Path("project_state/spec.yaml")
if spec_path.exists():
    spec = yaml.safe_load(spec_path.read_text())
    print(f"Project: {spec['project']['name']}")

# Check insights
insights_path = Path("outputs/insights.yaml")
if insights_path.exists():
    from core.insights import InsightCatalog
    catalog = InsightCatalog.load(str(insights_path))
    print(f"Insights: {catalog.summary}")

# Check outputs
charts = list(Path("outputs/charts").glob("*.png"))
print(f"Charts: {len(charts)} files")
```

## Project Structure

```
project_state/
  spec.yaml          # Requirements (source of truth)

outputs/
  charts/            # Generated charts
  insights.yaml      # Insight catalog

exports/
  *.pptx             # Presentations
  *.docx             # Reports
  dashboard/         # Dashboard files
```
