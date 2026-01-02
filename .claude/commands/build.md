# /build

---
name: build
description: Create deliverables from insights
agent: @builder
---

Build presentations, reports, or dashboards from analyzed insights.

## Usage

```
/build                           # Build based on spec type
/build presentation              # Create PPTX deck
/build report                    # Create document
/build dashboard                 # Create interactive dashboard
/build --preview                 # Build with live preview
```

## Deliverable Types

### Presentation (`/build presentation`)

```python
from core.slides import Presentation
from core.insights import InsightCatalog

# Load insights
catalog = InsightCatalog.load("outputs/insights.yaml")

# Create presentation
pres = Presentation()
pres.add_title("Q4 Analysis", "Revenue Performance")
pres.add_agenda("Agenda", ["Findings", "Analysis", "Recommendations"])

# Add findings
pres.add_section("Key Findings", section_number=1)
for insight in catalog.get_key_insights():
    pres.add_content(insight.headline, [insight.supporting_text])

# Add recommendations
pres.add_section("Recommendations", section_number=2)
for rec in catalog.get_recommendations():
    pres.add_key_takeaway(rec.headline, rec.supporting_text)

pres.add_closing("Questions?")
pres.save("exports/analysis.pptx")
```

### Dashboard (`/build dashboard`)

Creates Streamlit or HTML dashboard with interactive charts.

### Report (`/build report`)

Creates Word document with executive summary, findings, and appendix.

## Brand Requirements

- Use design system colors (no green)
- Text on dark: light purple or white, never primary
- No emojis
- Action titles (insight as headline)
- 1 idea per slide

## Output Locations

| Type | Location |
|------|----------|
| Presentation | `exports/*.pptx` |
| Report | `exports/*.docx` |
| Dashboard | `exports/dashboard/` |
| Charts | `outputs/charts/` |

## Preview

Use `--preview` flag to open live preview while building:

```python
from core.preview import PreviewEngine

preview = PreviewEngine()
preview.add_slide(spec)
preview.open_in_browser()
```

## Next Steps

```
/preview  # View all outputs
/export   # Package for delivery
```
