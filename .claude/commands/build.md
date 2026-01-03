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
from kie.powerpoint import SlideBuilder
from kie.insights import InsightCatalog

# Load insights
catalog = InsightCatalog.load("outputs/insights.yaml")

# Create presentation
builder = SlideBuilder()
builder.add_title_slide("Q4 Analysis", "Revenue Performance")

# Add findings
for insight in catalog.get_key_insights():
    builder.add_content_slide(
        title=insight.headline,
        content=[insight.supporting_text]
    )

# Add recommendations
for rec in catalog.get_recommendations():
    builder.add_content_slide(
        title=rec.headline,
        content=[rec.supporting_text]
    )

builder.save("exports/analysis.pptx")
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

Use `/preview` command to view outputs in React dashboard:

```bash
# In project root
/preview
# Opens React dashboard at http://localhost:5173
```

## Next Steps

```
/preview  # View all outputs
/export   # Package for delivery
```
