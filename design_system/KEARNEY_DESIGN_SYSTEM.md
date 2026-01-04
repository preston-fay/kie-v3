# Kearney Design System

## Overview

This is a comprehensive design system for creating beautiful, consistent deliverables across all Kearney formats: data visualizations, reports, slides, applications, and dashboards. It provides a complete reference for LLMs to generate on-brand Kearney content.

## Core Principles

1. **Brand-First Color System**: All colors are anchored in official Kearney brand palette
2. **Light & Dark Themes**: Full support for both themes with optimized legibility
3. **Clean Data Visualization**: No gridlines, minimal decoration, maximum insight clarity
4. **Professional Icons Only**: Use Lucide icons in Kearney colors - never use emoticons
5. **Typography**: Primary font is **Inter**, followed by Arial, sans-serif
6. **Accessibility**: WCAG AA compliant (4.5:1 contrast ratio minimum)
7. **Value-First Charts**: Prefer value labels on data points; hide axis values when labels make them clear

---

## Color Palette

### Main Colors

| Color | Hex | RGB | Usage |
|-------|-----|-----|-------|
| Kearney Black | `#1E1E1E` | RGB 30 30 30 | Primary text, dark backgrounds |
| Kearney White | `#FFFFFF` | RGB 255 255 255 | Light backgrounds, text on dark |
| Kearney Gray | `#A5A5A5` | RGB 165 165 165 | Secondary text, subtle elements |
| Kearney Purple | `#7823DC` | RGB 120 35 220 | Primary brand color, CTAs, emphasis |

### Chart Colors (Use in Order 1-10)

**CRITICAL**: Always use these colors in the specified order for multi-series data visualizations.

1. `#D2D2D2` - RGB 210 210 210
2. `#A5A6A5` - RGB 165 165 165
3. `#787878` - RGB 120 120 120
4. `#E0D2FA` - RGB 224 210 250
5. `#C8A5F0` - RGB 200 165 240
6. `#AF7DEB` - RGB 175 125 235
7. `#4B4B4B` - RGB 75 75 75
8. `#1E1E1E` - RGB 30 30 30
9. `#9150E1` - RGB 145 80 225
10. `#7823DC` - RGB 120 35 220

**Example**: For 3 data series, use colors 1, 2, and 3. For 5 series, use colors 1-5.

### Additional Colors (Use Sparingly)

**Grays**:
- Gray 100: `#F5F5F5` - RGB 245 245 245
- Gray 200: `#E6E6E6` - RGB 230 230 230
- Gray 300: `#B9B9B9` - RGB 185 185 185
- Gray 400: `#8C8C8C` - RGB 140 140 140
- Gray 500: `#5F5F5F` - RGB 95 95 95
- Gray 600: `#323232` - RGB 50 50 50

**Purples**:
- Purple 100: `#D7BEF5` - RGB 215 190 245
- Purple 200: `#B991EB` - RGB 185 145 235
- Purple 300: `#A064E6` - RGB 160 100 230
- Purple 400: `#8737E1` - RGB 135 55 225

---

## Gradients

All gradients must be anchored in valid Kearney colors. Two types: progressive and divergent.

### Progressive Gradients

Directional flow for showing movement, intensity, or transformation.

```css
/* Purple Intensity */
background: linear-gradient(135deg, #E0D2FA 0%, #7823DC 100%);

/* Purple Depth */
background: linear-gradient(135deg, #9150E1 0%, #1E1E1E 100%);

/* Gray to Purple */
background: linear-gradient(135deg, #A5A5A5 0%, #7823DC 100%);

/* Three-point Purple */
background: linear-gradient(135deg, #D7BEF5 0%, #9150E1 50%, #7823DC 100%);
```

### Divergent Gradients

Center-focused or edge-focused, for heatmaps and highlighting ranges.

```css
/* Purple Divergent */
background: linear-gradient(90deg, #7823DC 0%, #FFFFFF 50%, #7823DC 100%);

/* Gray to Purple Divergent */
background: linear-gradient(90deg, #A5A5A5 0%, #E0D2FA 50%, #7823DC 100%);
```

### Overlay Gradients

Semi-transparent, for layering over images or backgrounds.

```css
/* Purple Vignette */
background: radial-gradient(circle, transparent 0%, rgba(120, 35, 220, 0.1) 100%);

/* Dark Edge Fade */
background: linear-gradient(to bottom, transparent 0%, rgba(30, 30, 30, 0.3) 100%);
```

---

## Typography

### Type Scale

| Element | Size | Weight | Line Height | Usage |
|---------|------|--------|-------------|-------|
| H1 | 40px (2.5rem) | Bold (700) | 1.2 | Page titles, primary headlines |
| H2 | 32px (2rem) | Bold (700) | 1.3 | Section headers, slide titles |
| H3 | 24px (1.5rem) | Semibold (600) | 1.4 | Subsections, card titles |
| H4 | 20px (1.25rem) | Semibold (600) | 1.4 | Component titles, list headers |
| H5 | 16px (1rem) | Semibold (600) | 1.5 | Small headers, data labels |
| H6 | 14px (0.875rem) | Semibold (600) | 1.5 | Metadata, captions |
| Body Large | 18px (1.125rem) | Normal (400) | 1.6 | Lead text, introductions |
| Body Regular | 16px (1rem) | Normal (400) | 1.6 | Default paragraphs |
| Body Small | 14px (0.875rem) | Normal (400) | 1.5 | Secondary info, captions |
| Body XS | 12px (0.75rem) | Normal (400) | 1.4 | Fine print, timestamps |

### Font Weights

- **Normal (400)**: Default body text
- **Medium (500)**: Labels, buttons
- **Semibold (600)**: Headers, callouts
- **Bold (700)**: Major headlines

### Chart Typography

- **Chart Title**: 18-24px
- **Axis Labels**: 12-14px
- **Data Labels**: 12-14px
- **Legend**: 12px
- **Tooltips**: 12-13px
- **Annotations**: 11-12px

---

## Data Visualization Rules

### FORBIDDEN

❌ **Never use gridlines** - No exceptions
❌ **Avoid pie charts** - Use only when absolutely necessary (2-4 segments max)
❌ **Gauge charts sparingly** - Only when appropriate for the data
❌ **No 3D effects** - They distort perception
❌ **No dual y-axes** - Very confusing

### RECOMMENDED

✅ **Bar Charts**: Comparing discrete categories or time periods
✅ **Line Charts**: Continuous trends over time
✅ **Area Charts**: Emphasizing volume or magnitude
✅ **Stacked Bars**: Showing composition across categories
✅ **Scatter Plots**: Exploring correlations
✅ **Heatmaps**: Patterns across two dimensions

### Chart Configuration

All charts should:
- Have no gridlines (axisLine: false, tickLine: false)
- Use Kearney color palette in order (1-10)
- Have clear, readable axis labels (12-14px)
- Include tooltips for detailed values
- Maintain consistent spacing and padding

### Example Chart Config (Recharts)

```tsx
<BarChart data={data}>
  <XAxis 
    dataKey="category"
    axisLine={false}
    tickLine={false}
    tick={{ fill: 'currentColor', fontSize: 12 }}
  />
  <YAxis 
    axisLine={false}
    tickLine={false}
    tick={{ fill: 'currentColor', fontSize: 12 }}
  />
  <Tooltip 
    contentStyle={{ 
      backgroundColor: 'hsl(var(--card))',
      border: '1px solid hsl(var(--border))',
      borderRadius: '8px'
    }}
  />
  <Bar dataKey="value" fill="#7823DC" radius={[4, 4, 0, 0]} />
</BarChart>
```

---

## Component Patterns

### Buttons

```tsx
// Primary action
<Button>Analyze</Button>

// Secondary action
<Button variant="outline">Export</Button>

// With icon
<Button>
  <TrendingUp className="w-4 h-4 mr-2" />
  View Insights
</Button>
```

### Cards

```tsx
// Standard card
<Card className="p-6">
  <h4>Title</h4>
  <p className="text-muted-foreground">Description</p>
</Card>

// Highlighted card
<Card className="p-6 border-primary bg-gradient-to-br from-primary/5 to-primary/10">
  <h4>Important Content</h4>
</Card>
```

### Status Badges

```tsx
<Badge className="bg-green-600">On Track</Badge>
<Badge className="bg-yellow-600">At Risk</Badge>
<Badge className="bg-red-600">Delayed</Badge>
```

### KPI Cards

```tsx
<Card className="p-6">
  <p className="text-sm text-muted-foreground mb-1">Total Revenue</p>
  <h2 className="mb-1">$2.4M</h2>
  <div className="flex items-center gap-1">
    <TrendingUp className="w-4 h-4 text-green-600" />
    <span className="text-sm text-green-600">+12.5%</span>
  </div>
  <Progress value={78} className="mt-4 h-2" />
</Card>
```

---

## Dashboard Layout Patterns

### KPI Grid (Top)

4-column grid on desktop, 2-column on tablet, 1-column on mobile.

```tsx
<div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
  {kpiData.map((kpi) => (
    <Card key={kpi.label} className="p-6">
      {/* KPI content */}
    </Card>
  ))}
</div>
```

### Chart Sections

2-column grid for main charts, 3-column for secondary metrics.

```tsx
<div className="grid lg:grid-cols-2 gap-6">
  <Card className="p-6">
    {/* Primary chart */}
  </Card>
  <Card className="p-6">
    {/* Secondary chart */}
  </Card>
</div>
```

### Data Tables

Clean tables with hover states, proper alignment.

```tsx
<table className="w-full text-sm">
  <thead>
    <tr className="border-b">
      <th className="text-left py-3 px-4">Metric</th>
      <th className="text-right py-3 px-4">Value</th>
    </tr>
  </thead>
  <tbody>
    <tr className="border-b hover:bg-muted/50">
      <td className="py-4 px-4">Revenue</td>
      <td className="text-right py-4 px-4">$2.4M</td>
    </tr>
  </tbody>
</table>
```

---

## Slide Layout Patterns

### Aspect Ratio

Always use **16:9** aspect ratio for slides.

### Margins

- **Outer margins**: 64px on all sides
- **Content area**: Maximum 75% of slide
- **Footer**: 48px height with slide number and footer text

### Slide Types

1. **Title Slide**: Large headline (3rem), subtitle, metadata
2. **Key Message**: 2-3 highlighted cards with main points
3. **Data Slide**: Chart with title, description, key insight
4. **Bullet Points**: Maximum 6 bullets, use numbered sections
5. **Timeline**: Vertical timeline with phases and milestones
6. **Closing**: Next steps and contact information

### Example Slide Structure

```tsx
<div className="relative bg-card" style={{ aspectRatio: '16/9' }}>
  <div className="h-full p-16">
    <h2 className="mb-8">Slide Title</h2>
    {/* Content */}
  </div>
  <div className="absolute bottom-0 left-0 right-0 px-16 py-6 border-t">
    <div className="flex justify-between text-sm text-muted-foreground">
      <span>Footer Text</span>
      <span>1 / 12</span>
    </div>
  </div>
</div>
```

---

## Theme Variables

### Light Theme

```css
--background: #FFFFFF;
--foreground: #1E1E1E;
--primary: #7823DC;
--primary-foreground: #FFFFFF;
--secondary: #F5F5F5;
--muted: #E6E6E6;
--muted-foreground: #787878;
--border: #E6E6E6;
```

### Dark Theme

```css
--background: #1E1E1E;
--foreground: #FFFFFF;
--primary: #9150E1;
--primary-foreground: #FFFFFF;
--secondary: #323232;
--muted: #4B4B4B;
--muted-foreground: #A5A5A5;
--border: #4B4B4B;
```

---

## Accessibility Checklist

- [ ] Text contrast ratio ≥ 4.5:1 (WCAG AA)
- [ ] Works in both light and dark themes
- [ ] Colorblind-friendly palette (no red/green reliance)
- [ ] Text size ≥ 12px for all labels
- [ ] Keyboard navigable (for interactive elements)
- [ ] Screen reader friendly with proper ARIA labels
- [ ] No critical information conveyed by color alone

---

## Quick Reference: Do's & Don'ts

### Do's ✓

- Use Kearney Purple (#7823DC) for primary actions
- Follow chart color sequence (1-10) consistently
- Start y-axis at zero for bar charts
- Label axes clearly with units
- Use direct labeling when possible
- Sort categories meaningfully
- Include data sources and timestamps
- Test in both light and dark modes
- Ensure generous whitespace

### Don'ts ✗

- Never use gridlines
- Never use dual y-axes
- Don't use pie charts for more than 4 segments
- Don't use 3D effects or shadows
- Don't truncate y-axis to exaggerate differences
- Don't use more than 7-8 series in one chart
- Don't rely solely on color to differentiate
- Don't use rainbow color schemes
- Don't clutter with unnecessary decoration
- Don't use colors outside the official palette

---

## Usage for LLMs

When generating Kearney deliverables:

1. **Always reference this design system** for colors, typography, and component patterns
2. **Use exact hex codes** - never approximate or modify colors
3. **Follow chart color order strictly** - colors 1-10 in sequence
4. **No gridlines** - this is a hard rule for all visualizations
5. **Test legibility** - ensure text works on both light and dark backgrounds
6. **Maintain consistency** - use the same patterns throughout a deliverable
7. **Prioritize clarity** - remove any element that doesn't add understanding

---

## Examples Included

This design system includes complete examples of:

- **Color Palette**: All colors with hex codes and usage guidelines
- **Gradients**: Progressive, divergent, and overlay gradient patterns
- **Typography**: Complete type scale with usage examples
- **Components**: Buttons, forms, cards, badges, alerts, tables
- **Charts**: Bar, line, area, scatter, radar, composed charts
- **Dashboard**: Full executive dashboard with KPIs and visualizations
- **Slides**: Multiple slide layouts for presentations
- **Data Viz Guide**: Comprehensive best practices and guidelines

---

## Version

**Version**: 1.0  
**Date**: January 1, 2026  
**Status**: Production-ready

---

© 2026 Kearney Design System - Comprehensive reference for all deliverables