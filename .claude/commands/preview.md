# /preview

---
name: preview
description: Preview deliverables in browser
---

Open live preview of charts, slides, and insights.

## Usage

```
/preview                     # Preview all outputs
/preview charts              # Preview charts only
/preview slides              # Preview slide deck
/preview insights            # Preview insight catalog
/preview --serve             # Start live server
```

## Quick Preview

```python
from core.preview import PreviewEngine
from core.insights import InsightCatalog

# Create preview
preview = PreviewEngine()

# Add items
preview.add_chart("outputs/charts/revenue.png", title="Revenue Chart")
preview.add_insight(insight)
preview.add_slide({"title": "Key Findings", "bullets": ["Point 1"]})

# Open in browser
preview.open_in_browser()
```

## Live Server

Start a server for auto-refreshing preview:

```python
from core.preview import PreviewServer

server = PreviewServer(preview)
server.start(port=8080)  # Opens browser

# Add more items while server runs
preview.add_chart(another_chart)
# Browser auto-refreshes

server.stop()
```

## What's Previewed

| Item | Display |
|------|---------|
| Charts | Embedded images |
| Slides | HTML mockup |
| Insights | Formatted cards |
| Tables | HTML tables |

## Styling

Preview uses design system colors:
- Dark background (#1E1E1E)
- Light purple accents (#9B4DCA)
- Brand-compliant styling
