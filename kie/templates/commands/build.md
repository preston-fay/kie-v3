# Build Command

You are running the KIE build process. Create brand-compliant deliverables based on the project specification.

## Pre-flight Checks

1. Verify `project_state/spec.yaml` exists
   - If missing: "Run /interview first to create a project specification"

2. Check for data files in `data/`
   - If missing: Ask if they want to proceed with mock data

## Build Process

Based on project_type in spec.yaml:

### Analytics Projects
1. Load and analyze data
2. Generate insights
3. Create brand-compliant charts (matplotlib)
4. Save charts to `outputs/`
5. Create insight catalog

### Presentation Projects
1. Load data and analyze
2. Identify key messages
3. Create charts
4. Build PowerPoint deck (python-pptx)
5. Save to `exports/presentation.pptx`

### Dashboard Projects
1. Analyze data structure
2. Design dashboard layout
3. Create interactive HTML dashboard
4. Save to `exports/dashboard.html`

### Other Project Types
Follow similar patterns based on deliverable type.

## Brand Compliance (MANDATORY)

Every output MUST follow these rules:

**Colors:**
- Primary: #7823DC (Kearney Purple)
- Accent: #9B4DCA (light purple)
- Dark background: #1E1E1E
- Text on dark: #FFFFFF (white) or #9B4DCA (light purple) - NEVER primary purple
- NO GREEN COLORS - forbidden

**Charts (matplotlib):**
```python
import matplotlib.pyplot as plt

plt.style.use('dark_background')
plt.rcParams['figure.facecolor'] = '#1E1E1E'
plt.rcParams['axes.facecolor'] = '#1E1E1E'
plt.rcParams['axes.grid'] = False  # NO GRIDLINES
plt.rcParams['font.family'] = 'Arial'

KEARNEY_COLORS = ['#7823DC', '#9B4DCA', '#C4A6E8', '#5B1BA9', '#FF6B6B', '#4ECDC4']

# Data labels OUTSIDE bars/slices
for i, v in enumerate(values):
    ax.text(i, v + 0.5, f'{v:,.0f}', ha='center', color='white')
```

**PowerPoint (python-pptx):**
```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RgbColor

# Dark slide background
background = slide.background
fill = background.fill
fill.solid()
fill.fore_color.rgb = RgbColor(0x1E, 0x1E, 0x1E)

# White text on dark
p.font.color.rgb = RgbColor(0xFF, 0xFF, 0xFF)
```

## Quality Checklist

Before completing, verify:
- [ ] No green colors
- [ ] Primary purple (#7823DC) used appropriately
- [ ] White/light purple text on dark backgrounds
- [ ] No gridlines on charts
- [ ] Data labels outside bars/slices
- [ ] Arial font (Inter fallback)
- [ ] No emojis
- [ ] WCAG AA contrast

## Completion

After building:
1. List what was created
2. Show file paths
3. Suggest: "Run /review to check brand compliance"
