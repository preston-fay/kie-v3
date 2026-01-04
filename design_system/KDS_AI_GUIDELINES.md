# Kearney Design System (KDS) - AI Assistant Guidelines

**Version**: 1.1  
**Last Updated**: January 2, 2026  
**Status**: Production-ready

> **GitHub Gist**: [View complete component code examples →](https://gist.github.com/YOUR_USERNAME/YOUR_GIST_ID)
> 
> Replace with your actual Gist URL after uploading component files from `/src/app/components/kearney/`

---

## 🎯 Quick Start - Critical Rules (READ FIRST)

Copy and paste this section when starting conversations with AI assistants:

```
You MUST follow the Kearney Design System (KDS) guidelines:

COLORS: Only use these exact hex codes
- Kearney Purple: #7823DC
- Kearney Black: #1E1E1E  
- Kearney White: #FFFFFF
- Kearney Gray: #A5A5A5
- Chart sequence: #D2D2D2, #A5A6A5, #787878, #E0D2FA, #C8A5F0, #AF7DEB, #4B4B4B, #1E1E1E, #9150E1, #7823DC

TYPOGRAPHY: font-family: Inter, Arial, sans-serif

CHARTS: 
- NO gridlines ever (axisLine: false, tickLine: false)
- MUST include value labels on data points where possible
- Use annotations for key insights
- Hide Y-axis values when labels make them clear

MAPS:
- Use Kearney colors ONLY for all map elements
- Sequential scale for choropleth: #F5F5F5 → #7823DC
- Minimal base maps (light gray or white)
- Always include legend and scale
- No unnecessary detail (roads, labels unless critical)

ICONS: 
- Lucide-react ONLY
- Must be colored with KDS colors (#7823DC, #1E1E1E, etc.)
- NO emoticons EVER

FORBIDDEN:
❌ Gridlines on any chart
❌ Non-Kearney colors or gradients (including on maps!)
❌ Emoticons
❌ Pie charts (except 2-4 segments, sparingly)
❌ Gauge charts (only when appropriate)
❌ Rainbow color scales on maps
```

---

## 📋 Table of Contents

1. [Core Principles](#core-principles)
2. [Logo Usage](#logo-usage)
3. [Color System](#color-system)
4. [Typography](#typography)
5. [Data Visualization Rules](#data-visualization-rules)
6. [Component Patterns](#component-patterns)
7. [Dashboard Layouts](#dashboard-layouts)
8. [Slide Layouts](#slide-layouts)
9. [Theme Configuration](#theme-configuration)
10. [Mapping & Geospatial Analytics](#mapping--geospatial-analytics)
11. [Common Mistakes & Anti-Patterns](#common-mistakes--anti-patterns)
12. [Code Examples](#code-examples)
13. [Decision Trees](#decision-trees)

---

## Core Principles

This design system supports professional consulting deliverables across:
- Data visualizations
- Executive dashboards
- Presentation slides
- Reports and applications

### Key Principles

1. **Brand-First Color System** - All colors anchored in official Kearney palette
2. **Light & Dark Theme Support** - Full legibility in both modes
3. **Clean Data Visualization** - No gridlines, minimal decoration, maximum insight
4. **Professional Icons Only** - Lucide icons in Kearney colors, never emoticons
5. **Typography Hierarchy** - Inter primary font, followed by Arial, sans-serif
6. **Accessibility** - WCAG AA compliant (4.5:1 contrast minimum)
7. **Value-First Charts** - Prefer value labels on data points; hide axis values when labels are clear

---

## Logo Usage

### Official Kearney Logo Component

**CRITICAL**: Always use the official Kearney logo from the Logo component.

The logo is available in three variants:
- **slate** (#1E1E1E) - For light backgrounds
- **white** (#FFFFFF) - For dark backgrounds
- **purple** (#7823DC) - For brand emphasis

### Logo Component Code

```tsx
import { Logo } from './components/kearney/Logo';

// Default - Slate on light background
<Logo variant="slate" size="md" />

// White on dark background
<Logo variant="white" size="lg" />

// Purple for emphasis
<Logo variant="purple" size="sm" />

// Sizes available: sm (80px), md (120px), lg (160px), xl (200px)
```

### Logo Usage Guidelines

**Minimum Size**: 60px width
**Clear Space**: Minimum 16px on all sides
**Backgrounds**: Use appropriate variant for background color

```tsx
// Light background
<div className="bg-white p-6">
  <Logo variant="slate" size="md" />
</div>

// Dark background
<div className="bg-kearney-black p-6">
  <Logo variant="white" size="md" />
</div>

// Purple background
<div className="bg-primary p-6">
  <Logo variant="white" size="md" />
</div>
```

### Header Usage

```tsx
import { Logo } from './components/kearney/Logo';

<header className="border-b p-6">
  <div className="flex items-center justify-between">
    <Logo variant="slate" size="sm" />
    <nav>{/* Navigation */}</nav>
  </div>
</header>
```

### Slide Usage

```tsx
<div className="relative bg-card" style={{ aspectRatio: '16/9' }}>
  <div className="h-full p-16">
    <Logo variant="slate" size="md" className="mb-8" />
    <h1>Slide Title</h1>
    {/* Content */}
  </div>
</div>
```

### Dashboard Usage

```tsx
<header className="sticky top-0 border-b bg-background p-4">
  <div className="flex items-center gap-3">
    <Logo variant="slate" size="sm" />
    <span className="text-sm text-muted-foreground">Design System</span>
  </div>
</header>
```

**DON'T:**
- ❌ Distort or stretch the logo
- ❌ Change logo colors to non-Kearney colors
- ❌ Add effects (shadows, outlines, gradients)
- ❌ Rotate or skew the logo
- ❌ Use logo smaller than 60px
- ❌ Place logo on busy backgrounds without proper contrast

**DO:**
- ✅ Use the Logo component
- ✅ Choose appropriate variant for background
- ✅ Maintain clear space around logo
- ✅ Use approved sizes (sm, md, lg, xl)
- ✅ Ensure adequate contrast

---

## Color System

### Main Brand Colors

**CRITICAL**: These are the ONLY colors you can use. Never approximate or create variations.

```typescript
const KEARNEY_COLORS = {
  // Brand Colors
  black: '#1E1E1E',      // RGB 30, 30, 30
  white: '#FFFFFF',      // RGB 255, 255, 255
  gray: '#A5A5A5',       // RGB 165, 165, 165
  purple: '#7823DC',     // RGB 120, 35, 220
};
```

### Chart Colors (Use in Sequence 1-10)

**RULE**: Always use these colors in this exact order for multi-series visualizations.

```typescript
const CHART_COLORS = [
  '#D2D2D2',  // 1 - Light Gray
  '#A5A6A5',  // 2 - Medium Gray
  '#787878',  // 3 - Dark Gray
  '#E0D2FA',  // 4 - Light Purple
  '#C8A5F0',  // 5 - Medium Light Purple
  '#AF7DEB',  // 6 - Medium Purple
  '#4B4B4B',  // 7 - Charcoal
  '#1E1E1E',  // 8 - Black
  '#9150E1',  // 9 - Bright Purple
  '#7823DC',  // 10 - Kearney Purple (primary)
];
```

**Usage Example**: 
- 3 data series → Use colors 1, 2, 3
- 5 data series → Use colors 1, 2, 3, 4, 5
- Single emphasis → Use color 10 (#7823DC)

### Additional Palette (Use Sparingly)

```typescript
// Grays
const GRAYS = {
  100: '#F5F5F5',
  200: '#E6E6E6',
  300: '#B9B9B9',
  400: '#8C8C8C',
  500: '#5F5F5F',
  600: '#323232',
};

// Purples
const PURPLES = {
  100: '#D7BEF5',
  200: '#B991EB',
  300: '#A064E6',
  400: '#8737E1',
};
```

### Gradients (All Must Use Kearney Colors)

```css
/* Progressive: Purple Intensity */
background: linear-gradient(135deg, #E0D2FA 0%, #7823DC 100%);

/* Progressive: Purple Depth */
background: linear-gradient(135deg, #9150E1 0%, #1E1E1E 100%);

/* Progressive: Gray to Purple */
background: linear-gradient(135deg, #A5A5A5 0%, #7823DC 100%);

/* Divergent: Purple Center */
background: linear-gradient(90deg, #7823DC 0%, #FFFFFF 50%, #7823DC 100%);

/* Overlay: Purple Vignette */
background: radial-gradient(circle, transparent 0%, rgba(120, 35, 220, 0.1) 100%);
```

---

## Typography

### Font Stack

```css
font-family: Inter, Arial, sans-serif;
```

**CRITICAL**: Always specify Inter first, then Arial, then sans-serif fallback.

### Type Scale

| Element | Size | Weight | Line Height | Usage |
|---------|------|--------|-------------|-------|
| **H1** | 40px (2.5rem) | Bold (700) | 1.2 | Page titles |
| **H2** | 32px (2rem) | Bold (700) | 1.3 | Section headers |
| **H3** | 24px (1.5rem) | Semibold (600) | 1.4 | Subsections |
| **H4** | 20px (1.25rem) | Semibold (600) | 1.4 | Component titles |
| **H5** | 16px (1rem) | Semibold (600) | 1.5 | Data labels |
| **H6** | 14px (0.875rem) | Semibold (600) | 1.5 | Captions |
| **Body Large** | 18px (1.125rem) | Normal (400) | 1.6 | Lead text |
| **Body** | 16px (1rem) | Normal (400) | 1.6 | Default text |
| **Body Small** | 14px (0.875rem) | Normal (400) | 1.5 | Secondary info |
| **Body XS** | 12px (0.75rem) | Normal (400) | 1.4 | Fine print |

### Chart Typography

```typescript
const CHART_TYPE_SIZES = {
  title: '18-24px',
  axisLabel: '12-14px',
  dataLabel: '12-14px',
  legend: '12px',
  tooltip: '12-13px',
  annotation: '11-12px',
};
```

---

## Data Visualization Rules

### FORBIDDEN ❌

1. **NO GRIDLINES** - This is absolute. Never add gridlines to any chart.
2. **NO PIE CHARTS** - Except when absolutely necessary (2-4 segments max)
3. **NO GAUGE CHARTS** - Only when specifically appropriate for data
4. **NO 3D EFFECTS** - They distort perception
5. **NO DUAL Y-AXES** - Very confusing for readers
6. **NO NON-KEARNEY COLORS** - Only use the official palette

### REQUIRED ✅

1. **Value Labels** - Include on data points where they enhance clarity
2. **Annotations** - Add callouts for key insights
3. **No Gridlines** - Set `axisLine={false}` and `tickLine={false}`
4. **Proper Color Sequence** - Use chart colors 1-10 in order
5. **Clean Axes** - Hide Y-axis values when data labels make them clear
6. **Tooltips** - Always provide for detailed information

### RECOMMENDED Chart Types

```typescript
const CHART_RECOMMENDATIONS = {
  'comparing-categories': 'Bar Chart',
  'time-series': 'Line Chart',
  'volume-over-time': 'Area Chart',
  'composition': 'Stacked Bar Chart',
  'correlation': 'Scatter Plot',
  'two-dimensional-patterns': 'Heatmap',
  'single-value': 'KPI Card',
  'progress': 'Progress Bar (not gauge)',
};
```

### Recharts Configuration Template

**CRITICAL**: All Recharts components must follow this pattern:

```tsx
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, Tooltip, Legend, ResponsiveContainer,
  LabelList
} from 'recharts';

// Bar Chart Example
<ResponsiveContainer width="100%" height={300}>
  <BarChart data={data}>
    <XAxis 
      dataKey="category"
      axisLine={false}        // ← REQUIRED: No axis line
      tickLine={false}        // ← REQUIRED: No tick marks
      tick={{ fill: 'currentColor', fontSize: 12 }}
    />
    <YAxis 
      axisLine={false}        // ← REQUIRED: No axis line
      tickLine={false}        // ← REQUIRED: No tick marks
      tick={false}            // ← Hide values when labels present
    />
    <Tooltip 
      contentStyle={{ 
        backgroundColor: 'hsl(var(--card))',
        border: '1px solid hsl(var(--border))',
        borderRadius: '8px'
      }}
    />
    <Bar 
      dataKey="value" 
      fill="#7823DC"          // ← Use Kearney colors
      radius={[4, 4, 0, 0]}
    >
      <LabelList             // ← RECOMMENDED: Add value labels
        dataKey="value"
        position="top"
        style={{ fill: 'currentColor', fontSize: 12 }}
      />
    </Bar>
  </BarChart>
</ResponsiveContainer>
```

### Line Chart with Annotations

```tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, 
         ResponsiveContainer, ReferenceLine, Label } from 'recharts';
import { TrendingUp } from 'lucide-react';

<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    <XAxis 
      dataKey="month"
      axisLine={false}
      tickLine={false}
      tick={{ fill: 'currentColor', fontSize: 12 }}
    />
    <YAxis 
      axisLine={false}
      tickLine={false}
      tick={{ fill: 'currentColor', fontSize: 12 }}
    />
    <Tooltip />
    
    {/* Reference line for target */}
    <ReferenceLine 
      y={100} 
      stroke="#7823DC" 
      strokeDasharray="3 3"
    >
      <Label 
        value="Target" 
        position="insideTopRight"
        style={{ fill: '#7823DC', fontSize: 11 }}
      />
    </ReferenceLine>
    
    <Line 
      type="monotone"
      dataKey="value"
      stroke="#7823DC"
      strokeWidth={2}
      dot={{ fill: '#7823DC', r: 4 }}
    />
  </LineChart>
</ResponsiveContainer>
```

---

## Component Patterns

### KPI/Data Card

```tsx
import { Card } from './components/ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';

<Card className="p-6">
  <p className="text-sm text-muted-foreground mb-3 uppercase tracking-wide">
    Total Revenue
  </p>
  <div className="flex items-baseline gap-3 mb-2">
    <h2>$2.4M</h2>
    <span className="text-sm font-semibold" style={{ color: '#7823DC' }}>
      +12.5%
    </span>
  </div>
  <div className="flex items-center gap-1 mt-2">
    <TrendingUp 
      className="w-4 h-4" 
      style={{ color: '#7823DC' }}  // ← REQUIRED: Color icons
    />
    <span className="text-xs text-muted-foreground">
      vs last quarter
    </span>
  </div>
</Card>
```

### Chart Card

```tsx
import { Card } from './components/ui/card';
import { Download } from 'lucide-react';
import { Button } from './components/ui/button';

<Card className="p-6">
  <div className="flex items-start justify-between mb-6">
    <div>
      <h3 className="font-semibold mb-1">Revenue Trends</h3>
      <p className="text-sm text-muted-foreground">
        Quarterly performance 2024
      </p>
    </div>
    <Button variant="outline" size="sm">
      <Download className="w-4 h-4 mr-2" style={{ color: '#7823DC' }} />
      Export
    </Button>
  </div>
  <div className="w-full">
    {/* Chart component here */}
  </div>
</Card>
```

### Insight Card with Annotation

```tsx
import { Card } from './components/ui/card';
import { Lightbulb } from 'lucide-react';

<Card className="p-6 border-l-4" style={{ borderLeftColor: '#7823DC' }}>
  <div className="flex gap-4">
    <div className="p-3 rounded-lg" style={{ backgroundColor: '#E0D2FA' }}>
      <Lightbulb className="w-5 h-5" style={{ color: '#7823DC' }} />
    </div>
    <div>
      <h4 className="mb-2">Key Insight</h4>
      <p className="text-sm text-muted-foreground">
        Revenue increased 12.5% QoQ, driven primarily by digital 
        transformation engagements (+34%) and operational excellence 
        projects (+28%).
      </p>
    </div>
  </div>
</Card>
```

### Status Badge

```tsx
import { Badge } from './components/ui/badge';

// Predefined status colors
<Badge style={{ backgroundColor: '#7823DC' }}>On Track</Badge>
<Badge style={{ backgroundColor: '#FFA726' }}>At Risk</Badge>
<Badge style={{ backgroundColor: '#EF5350' }}>Delayed</Badge>
```

### Data Table

```tsx
<div className="rounded-lg border">
  <table className="w-full text-sm">
    <thead>
      <tr className="border-b bg-muted/50">
        <th className="text-left py-3 px-4 font-semibold">Metric</th>
        <th className="text-right py-3 px-4 font-semibold">Value</th>
        <th className="text-right py-3 px-4 font-semibold">Change</th>
      </tr>
    </thead>
    <tbody>
      <tr className="border-b hover:bg-muted/50 transition-colors">
        <td className="py-4 px-4">Revenue</td>
        <td className="text-right py-4 px-4 font-medium">$2.4M</td>
        <td className="text-right py-4 px-4" style={{ color: '#7823DC' }}>
          +12.5%
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### Button Variants

```tsx
import { Button } from './components/ui/button';
import { Download, Share } from 'lucide-react';

// Primary action
<Button>Analyze</Button>

// Secondary action
<Button variant="outline">Export</Button>

// With icon (MUST color the icon)
<Button>
  <Download className="w-4 h-4 mr-2" style={{ color: 'currentColor' }} />
  Download Report
</Button>

// Ghost variant for subtle actions
<Button variant="ghost">
  <Share className="w-4 h-4 mr-2" />
  Share
</Button>
```

---

## Dashboard Layouts

### KPI Grid (Responsive)

```tsx
<div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
  {kpiData.map((kpi) => (
    <Card key={kpi.id} className="p-6">
      <p className="text-sm text-muted-foreground mb-3 uppercase">
        {kpi.label}
      </p>
      <h2>{kpi.value}</h2>
      <div className="flex items-center gap-1 mt-2">
        <TrendingUp className="w-4 h-4" style={{ color: '#7823DC' }} />
        <span className="text-sm" style={{ color: '#7823DC' }}>
          {kpi.change}
        </span>
      </div>
    </Card>
  ))}
</div>
```

### Chart Grid (2-Column)

```tsx
<div className="grid lg:grid-cols-2 gap-6">
  <Card className="p-6">
    <h3 className="font-semibold mb-6">Primary Chart</h3>
    {/* Chart component */}
  </Card>
  <Card className="p-6">
    <h3 className="font-semibold mb-6">Secondary Chart</h3>
    {/* Chart component */}
  </Card>
</div>
```

### Full Dashboard Structure

```tsx
<div className="min-h-screen bg-background">
  {/* Header */}
  <header className="border-b p-6">
    <div className="flex items-center justify-between">
      <div>
        <h1>Executive Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">Q4 2024 Performance</p>
      </div>
      <div className="flex gap-2">
        <Button variant="outline">Export</Button>
        <Button>Share</Button>
      </div>
    </div>
  </header>

  {/* Main Content */}
  <main className="p-6 space-y-6">
    {/* KPI Grid */}
    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* KPI cards */}
    </div>

    {/* Charts */}
    <div className="grid lg:grid-cols-2 gap-6">
      {/* Chart cards */}
    </div>

    {/* Insights */}
    <div className="grid lg:grid-cols-3 gap-6">
      {/* Insight cards */}
    </div>
  </main>
</div>
```

---

## Slide Layouts

### Aspect Ratio & Margins

```typescript
const SLIDE_SPECS = {
  aspectRatio: '16:9',
  outerMargin: '64px',
  contentMaxWidth: '75%',
  footerHeight: '48px',
};
```

### Slide Template

```tsx
<div 
  className="relative bg-card" 
  style={{ aspectRatio: '16/9' }}
>
  {/* Content Area */}
  <div className="h-full p-16">
    <h2 className="mb-8">Slide Title</h2>
    
    {/* Slide content */}
    <div className="space-y-6">
      {/* Content here */}
    </div>
  </div>

  {/* Footer */}
  <div className="absolute bottom-0 left-0 right-0 px-16 py-6 border-t">
    <div className="flex justify-between text-sm text-muted-foreground">
      <span>© Kearney 2026</span>
      <span>1 / 12</span>
    </div>
  </div>
</div>
```

### Title Slide

```tsx
<div className="relative bg-card" style={{ aspectRatio: '16/9' }}>
  <div className="h-full flex items-center justify-center p-16">
    <div className="text-center max-w-3xl">
      <h1 className="mb-4" style={{ fontSize: '3rem' }}>
        Strategic Initiative Review
      </h1>
      <p className="text-xl text-muted-foreground mb-8">
        Q4 2024 Performance Analysis
      </p>
      <div className="flex items-center justify-center gap-8 text-sm text-muted-foreground">
        <span>December 2024</span>
        <span>•</span>
        <span>Executive Summary</span>
      </div>
    </div>
  </div>
  
  {/* Footer */}
  <div className="absolute bottom-0 left-0 right-0 px-16 py-6 border-t">
    <div className="flex justify-between text-sm text-muted-foreground">
      <span>© Kearney 2026</span>
      <span>1 / 12</span>
    </div>
  </div>
</div>
```

### Data Slide with Chart

```tsx
<div className="relative bg-card" style={{ aspectRatio: '16/9' }}>
  <div className="h-full p-16">
    <div className="mb-8">
      <h2 className="mb-2">Revenue Growth Trends</h2>
      <p className="text-sm text-muted-foreground">
        Quarterly performance showing 12.5% YoY growth
      </p>
    </div>

    <div className="grid grid-cols-3 gap-6 h-[calc(100%-200px)]">
      {/* Chart takes 2/3 */}
      <div className="col-span-2">
        <ResponsiveContainer width="100%" height="100%">
          {/* Chart component */}
        </ResponsiveContainer>
      </div>

      {/* Key insights 1/3 */}
      <div className="space-y-4">
        <Card className="p-4 border-l-4" style={{ borderLeftColor: '#7823DC' }}>
          <h4 className="mb-2">Key Finding</h4>
          <p className="text-sm text-muted-foreground">
            Digital transformation driving growth
          </p>
        </Card>
      </div>
    </div>
  </div>

  {/* Footer */}
  <div className="absolute bottom-0 left-0 right-0 px-16 py-6 border-t">
    <div className="flex justify-between text-sm text-muted-foreground">
      <span>© Kearney 2026</span>
      <span>5 / 12</span>
    </div>
  </div>
</div>
```

---

## Theme Configuration

### Light Theme (Default)

```css
:root {
  --background: #FFFFFF;
  --foreground: #1E1E1E;
  --primary: #7823DC;
  --primary-foreground: #FFFFFF;
  --secondary: #F5F5F5;
  --secondary-foreground: #1E1E1E;
  --muted: #E6E6E6;
  --muted-foreground: #787878;
  --card: #FFFFFF;
  --card-foreground: #1E1E1E;
  --border: #E6E6E6;
  --accent: #E0D2FA;
  --accent-foreground: #1E1E1E;
}
```

### Dark Theme

```css
.dark {
  --background: #1E1E1E;
  --foreground: #FFFFFF;
  --primary: #9150E1;
  --primary-foreground: #FFFFFF;
  --secondary: #323232;
  --secondary-foreground: #FFFFFF;
  --muted: #4B4B4B;
  --muted-foreground: #A5A5A5;
  --card: #323232;
  --card-foreground: #FFFFFF;
  --border: #4B4B4B;
  --accent: #7823DC;
  --accent-foreground: #FFFFFF;
}
```

### Using Theme Variables

```tsx
// In Tailwind classes
<div className="bg-background text-foreground">
  <h1 className="text-primary">Title</h1>
  <p className="text-muted-foreground">Description</p>
</div>

// In inline styles (for charts)
<Bar fill="hsl(var(--primary))" />

// For specific Kearney purple
<Bar fill="#7823DC" />
```

---

## Mapping & Geospatial Analytics

### Core Mapping Principles

Maps and geospatial visualizations in Kearney deliverables must follow KDS brand standards while maintaining geographic accuracy and clarity.

**CRITICAL RULES:**
1. **Use Kearney Colors Only** - All map elements must use the official KDS palette
2. **Minimal Base Maps** - Keep base layers subtle to emphasize data overlays
3. **No Unnecessary Detail** - Remove visual clutter (roads, labels) unless critical to analysis
4. **Data-First Approach** - Data overlays should be immediately visible and dominant
5. **Clear Legends** - Always include scale bars, color legends, and units
6. **Annotations** - Mark key geographic insights with callouts
7. **Proper Projections** - Use appropriate map projections for the geographic scope

---

### Recommended Mapping Libraries

```typescript
const APPROVED_MAP_LIBRARIES = {
  interactive: 'react-leaflet',      // Open source, lightweight, easiest to implement
  advanced: 'mapbox-gl',             // Premium features, custom styling, best performance
  simple: 'react-simple-maps',       // Static SVG maps, perfect for slides
  geospatial: '@deck.gl/react',      // 3D visualization layers, advanced analytics
};
```

**Installation:**

```bash
# Leaflet (recommended for most use cases)
npm install react-leaflet leaflet
npm install @types/leaflet --save-dev

# Mapbox GL (advanced interactive maps)
npm install mapbox-gl react-map-gl

# Simple Maps (slides/static visualizations)
npm install react-simple-maps

# Deck.gl (3D/advanced geospatial)
npm install deck.gl @deck.gl/react
```

---

### Map Configuration Standards

```typescript
// Base map configuration for light and dark themes
const KDS_MAP_CONFIG = {
  light: {
    style: 'mapbox://styles/mapbox/light-v11',
    backgroundColor: '#FFFFFF',
    waterColor: '#E6E6E6',          // Light gray water
    landColor: '#F5F5F5',           // Off-white land
    borderColor: '#D2D2D2',         // Gray borders
    labelColor: '#1E1E1E',          // Black labels
  },
  dark: {
    style: 'mapbox://styles/mapbox/dark-v11',
    backgroundColor: '#1E1E1E',
    waterColor: '#323232',
    landColor: '#4B4B4B',
    borderColor: '#787878',
    labelColor: '#FFFFFF',
  },
};

// Standard zoom levels for different analysis scales
const ZOOM_LEVELS = {
  global: 2,           // World view
  continent: 4,        // Continental view
  country: 6,          // National view
  region: 8,           // State/province view
  metro: 10,           // Metropolitan area
  city: 12,            // City view
  neighborhood: 15,    // District/neighborhood
  street: 18,          // Street level
};
```

---

### Choropleth Maps (Regions with Color Scales)

**Use Case:** Market size by region, sales by territory, performance by district

```tsx
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { Card } from './components/ui/card';
import 'leaflet/dist/leaflet.css';

// Kearney color scale for choropleth (sequential: low to high)
const CHOROPLETH_SCALE = [
  '#F5F5F5',  // 0-12.5% - Very low (lightest gray)
  '#E6E6E6',  // 12.5-25% - Low
  '#D2D2D2',  // 25-37.5% - Medium-low
  '#E0D2FA',  // 37.5-50% - Medium (light purple)
  '#C8A5F0',  // 50-62.5% - Medium-high
  '#AF7DEB',  // 62.5-75% - High
  '#9150E1',  // 75-87.5% - Very high
  '#7823DC',  // 87.5-100% - Highest (Kearney purple)
];

// Function to assign color based on value
function getColor(value: number, min: number, max: number): string {
  const normalized = (value - min) / (max - min);
  const index = Math.floor(normalized * (CHOROPLETH_SCALE.length - 1));
  return CHOROPLETH_SCALE[Math.max(0, Math.min(index, CHOROPLETH_SCALE.length - 1))];
}

// GeoJSON styling function
function style(feature: any, minValue: number, maxValue: number) {
  const value = feature.properties.revenue;
  return {
    fillColor: getColor(value, minValue, maxValue),
    weight: 1,
    opacity: 1,
    color: '#787878',         // Border color - gray
    fillOpacity: 0.85,
  };
}

export function ChoroplethMap({ data, geoJson }: Props) {
  const values = data.map(d => d.revenue);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="mb-1">Revenue by Territory</h3>
          <p className="text-sm text-muted-foreground">
            Q4 2024 Performance ($M)
          </p>
        </div>
      </div>
      
      <div className="relative" style={{ height: '500px' }}>
        <MapContainer
          center={[39.8283, -98.5795]}  // US center
          zoom={4}
          style={{ height: '100%', width: '100%', borderRadius: '8px' }}
          scrollWheelZoom={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
            attribution='&copy; OpenStreetMap contributors, CARTO'
          />
          <GeoJSON 
            data={geoJson} 
            style={(feature) => style(feature, minValue, maxValue)} 
          />
        </MapContainer>

        {/* Legend */}
        <div className="absolute bottom-4 right-4 bg-background/95 backdrop-blur p-4 rounded-lg border shadow-lg">
          <h4 className="text-sm font-semibold mb-2">Revenue ($M)</h4>
          <div className="space-y-1">
            {CHOROPLETH_SCALE.map((color, i) => {
              const rangeValue = minValue + ((maxValue - minValue) * i / (CHOROPLETH_SCALE.length - 1));
              return (
                <div key={i} className="flex items-center gap-2">
                  <div 
                    className="w-8 h-4 rounded border"
                    style={{ backgroundColor: color, borderColor: '#787878' }}
                  />
                  <span className="text-xs font-medium">
                    ${rangeValue.toFixed(0)}M
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Card>
  );
}
```

---

### Point/Marker Maps (Locations)

**Use Case:** Store locations, office locations, client sites, facility placement

```tsx
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { MapPin, TrendingUp } from 'lucide-react';

const locations = [
  { lat: 40.7128, lng: -74.0060, name: 'New York', revenue: 250, type: 'primary' },
  { lat: 34.0522, lng: -118.2437, name: 'Los Angeles', revenue: 180, type: 'secondary' },
  { lat: 41.8781, lng: -87.6298, name: 'Chicago', revenue: 150, type: 'secondary' },
  { lat: 29.7604, lng: -95.3698, name: 'Houston', revenue: 120, type: 'tertiary' },
];

// Size markers proportionally by value
function getMarkerRadius(value: number, max: number): number {
  const minRadius = 8;
  const maxRadius = 30;
  return minRadius + ((value / max) * (maxRadius - minRadius));
}

// Color by category
function getMarkerColor(type: string): string {
  const colors = {
    primary: '#7823DC',      // Kearney purple - top tier
    secondary: '#AF7DEB',    // Medium purple - mid tier
    tertiary: '#E0D2FA',     // Light purple - lower tier
    inactive: '#D2D2D2',     // Gray - inactive/closed
  };
  return colors[type] || colors.tertiary;
}

export function LocationMap() {
  const maxRevenue = Math.max(...locations.map(l => l.revenue));

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="mb-1">Office Network</h3>
          <p className="text-sm text-muted-foreground">
            Revenue by location ($M)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4" style={{ color: '#7823DC' }} />
          <span className="text-sm font-semibold">
            {locations.length} Locations
          </span>
        </div>
      </div>

      <div style={{ height: '500px', borderRadius: '8px', overflow: 'hidden' }}>
        <MapContainer
          center={[39.8283, -98.5795]}
          zoom={4}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; OpenStreetMap contributors'
          />
          
          {locations.map((loc, i) => (
            <CircleMarker
              key={i}
              center={[loc.lat, loc.lng]}
              radius={getMarkerRadius(loc.revenue, maxRevenue)}
              fillColor={getMarkerColor(loc.type)}
              fillOpacity={0.7}
              color="#FFFFFF"         // White border
              weight={2}
            >
              <Popup>
                <div className="p-2 min-w-[150px]">
                  <h4 className="font-semibold mb-1">{loc.name}</h4>
                  <p className="text-sm text-muted-foreground mb-2">
                    Revenue: ${loc.revenue}M
                  </p>
                  <div className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" style={{ color: '#7823DC' }} />
                    <span className="text-xs" style={{ color: '#7823DC' }}>
                      +12% YoY
                    </span>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
      
      {/* Legend */}
      <div className="mt-4 p-4 border rounded-lg">
        <h4 className="text-sm font-semibold mb-3">Location Tiers</h4>
        <div className="grid grid-cols-3 gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#7823DC' }} />
            <span className="text-xs">Primary</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#AF7DEB' }} />
            <span className="text-xs">Secondary</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#E0D2FA' }} />
            <span className="text-xs">Tertiary</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          Circle size represents revenue volume
        </p>
      </div>
    </Card>
  );
}
```

---

### Map Color Scales Reference

**Sequential Scale (Low to High):**
```typescript
// Use for single-variable visualizations (revenue, population, etc.)
const SEQUENTIAL_SCALE = [
  '#F5F5F5',  // 0-12.5% - Very low
  '#E6E6E6',  // 12.5-25% - Low
  '#D2D2D2',  // 25-37.5% - Medium-low
  '#E0D2FA',  // 37.5-50% - Medium
  '#C8A5F0',  // 50-62.5% - Medium-high
  '#AF7DEB',  // 62.5-75% - High
  '#9150E1',  // 75-87.5% - Very high
  '#7823DC',  // 87.5-100% - Highest
];
```

**Diverging Scale (Below/Above Target):**
```typescript
// Use for performance vs target visualizations
const DIVERGING_SCALE = {
  // Below target (red tones - use sparingly)
  low: ['#FFCDD2', '#FF8A80', '#EF5350'],
  // At target (neutral gray)
  neutral: '#E6E6E6',
  // Above target (purple tones - Kearney colors)
  high: ['#E0D2FA', '#AF7DEB', '#7823DC'],
};
```

**Categorical Colors:**
```typescript
// Use for different types/categories
const CATEGORICAL_COLORS = {
  primary: '#7823DC',      // Primary territories/locations
  secondary: '#AF7DEB',    // Secondary territories
  tertiary: '#E0D2FA',     // Tertiary territories
  inactive: '#D2D2D2',     // Inactive/closed locations
  competitor: '#EF5350',   // Competitor presence (use sparingly)
  opportunity: '#9150E1',  // New opportunity areas
};
```

---

### Static Maps for Slides (react-simple-maps)

**Use Case:** Presentation slides, static reports, printed materials

```tsx
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const markers = [
  { coordinates: [-74.006, 40.7128], name: "New York", value: 250 },
  { coordinates: [-118.2437, 34.0522], name: "Los Angeles", value: 180 },
  { coordinates: [-87.6298, 41.8781], name: "Chicago", value: 150 },
];

export function StaticWorldMap() {
  return (
    <div className="relative bg-card" style={{ aspectRatio: '16/9' }}>
      <div className="h-full p-16">
        <h2 className="mb-2">Global Office Network</h2>
        <p className="text-sm text-muted-foreground mb-8">
          Revenue by location ($M)
        </p>
        
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{ scale: 140, center: [-95, 40] }}
          style={{ width: '100%', height: 'calc(100% - 200px)' }}
        >
          <Geographies geography={geoUrl}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="#E6E6E6"           // Light gray land
                  stroke="#FFFFFF"         // White borders
                  strokeWidth={0.5}
                  style={{
                    default: { outline: 'none' },
                    hover: { 
                      fill: '#E0D2FA',     // Light purple on hover
                      outline: 'none' 
                    },
                  }}
                />
              ))
            }
          </Geographies>
          
          {markers.map(({ coordinates, name, value }, i) => (
            <Marker key={i} coordinates={coordinates}>
              {/* Marker circle */}
              <circle 
                r={6 + (value / 50)} 
                fill="#7823DC"
                stroke="#FFFFFF"
                strokeWidth={2}
              />
              {/* Label */}
              <text
                textAnchor="middle"
                y={-15}
                style={{ 
                  fontFamily: 'Inter, Arial, sans-serif',
                  fontSize: '12px',
                  fill: '#1E1E1E',
                  fontWeight: 600,
                }}
              >
                {name}
              </text>
              {/* Value label */}
              <text
                textAnchor="middle"
                y={-2}
                style={{ 
                  fontFamily: 'Inter, Arial, sans-serif',
                  fontSize: '10px',
                  fill: '#787878',
                }}
              >
                ${value}M
              </text>
            </Marker>
          ))}
        </ComposableMap>
      </div>
      
      {/* Slide footer */}
      <div className="absolute bottom-0 left-0 right-0 px-16 py-6 border-t">
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>© Kearney 2026</span>
          <span>8 / 12</span>
        </div>
      </div>
    </div>
  );
}
```

---

### Geospatial Analytics Best Practices

**DO ✅:**
- Use appropriate zoom level for the analysis scale
- Include scale bar and north arrow when needed
- Provide clear legend with units and color scale
- Use Kearney color scales exclusively for all data overlays
- Annotate key geographic insights with callouts
- Keep base maps minimal (light gray or white background)
- Label major cities/regions/territories
- Add interactive tooltips with detailed data
- Test choropleth scales for colorblind accessibility
- Provide data table alternative for accessibility

**DON'T ❌:**
- Use rainbow or traffic light color scales
- Overcrowd the map with labels
- Use 3D effects unless specifically needed for terrain
- Show unnecessary geographic detail (roads, buildings, water features)
- Use non-Kearney colors for any data visualization
- Forget to include a legend or scale
- Use fonts smaller than 11px
- Distort geographic projections without reason
- Use pie charts on maps (use proportional circles instead)
- Rely solely on color to convey critical information

---

### Common Consulting Map Use Cases

```typescript
const MAP_USE_CASES = {
  'market-sizing': {
    type: 'Choropleth map',
    description: 'Revenue or market potential by region',
    colors: 'Sequential scale (gray to purple)',
  },
  'store-locations': {
    type: 'Point map with sized markers',
    description: 'Locations with performance metrics',
    colors: 'Categorical + size by value',
  },
  'territory-planning': {
    type: 'Choropleth with boundaries',
    description: 'Sales territories with targets',
    colors: 'Diverging scale (below/above target)',
  },
  'customer-density': {
    type: 'Heatmap',
    description: 'Customer concentration analysis',
    colors: 'Sequential scale with transparency',
  },
  'supply-chain': {
    type: 'Flow map with routes',
    description: 'Distribution network visualization',
    colors: 'Line weight by volume, purple',
  },
  'site-selection': {
    type: 'Multi-criteria point map',
    description: 'Locations scored on multiple factors',
    colors: 'Categorical with size indicators',
  },
  'competitive-landscape': {
    type: 'Multi-category choropleth',
    description: 'Market share by region',
    colors: 'Categorical (primary/competitor)',
  },
  'demographic-analysis': {
    type: 'Choropleth with census data',
    description: 'Population characteristics by area',
    colors: 'Sequential scale',
  },
};
```

---

### Map Typography Standards

```typescript
const MAP_TYPOGRAPHY = {
  title: {
    fontSize: '18px',
    fontWeight: 600,
    fontFamily: 'Inter, Arial, sans-serif',
    color: '#1E1E1E',
  },
  subtitle: {
    fontSize: '14px',
    fontWeight: 400,
    fontFamily: 'Inter, Arial, sans-serif',
    color: '#787878',
  },
  cityLabel: {
    fontSize: '12px',
    fontWeight: 600,
    fontFamily: 'Inter, Arial, sans-serif',
    color: '#1E1E1E',
  },
  valueLabel: {
    fontSize: '11px',
    fontWeight: 400,
    fontFamily: 'Inter, Arial, sans-serif',
    color: '#787878',
  },
  legendTitle: {
    fontSize: '12px',
    fontWeight: 600,
    fontFamily: 'Inter, Arial, sans-serif',
    color: '#1E1E1E',
  },
  legendLabels: {
    fontSize: '11px',
    fontWeight: 400,
    fontFamily: 'Inter, Arial, sans-serif',
    color: '#787878',
  },
};
```

**CRITICAL:** Never use fonts smaller than 11px on maps - they become illegible when printed or viewed on slides.

---

### Geospatial Data Formats

**Common formats for consulting work:**

1. **GeoJSON (most common, easiest to use):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-74, 40], [-73, 40], [-73, 41], [-74, 41], [-74, 40]]]
      },
      "properties": {
        "name": "Territory Northeast",
        "revenue": 2400000,
        "growth": 0.125,
        "category": "primary"
      }
    }
  ]
}
```

2. **CSV with coordinates:**
```csv
name,lat,lng,revenue,growth
"New York",40.7128,-74.0060,250,0.15
"Los Angeles",34.0522,-118.2437,180,0.08
"Chicago",41.8781,-87.6298,150,0.12
```

3. **Shapefile (.shp) conversion:**
- Use https://mapshaper.org/ to convert Shapefiles to GeoJSON
- Or use command line: `ogr2ogr -f GeoJSON output.json input.shp`

---

### Map Accessibility Checklist

Before delivering any map visualization:

- [ ] **Color Contrast**: All labels have ≥ 4.5:1 contrast ratio
- [ ] **Colorblind Safe**: Test with colorblind simulator (use coolors.co or similar)
- [ ] **Text Alternative**: Provide data table showing all map data
- [ ] **Keyboard Navigation**: Interactive maps have keyboard controls
- [ ] **Screen Reader Labels**: Add ARIA labels to map containers
- [ ] **Legend Clarity**: Color legend is clear without relying solely on hue
- [ ] **Font Size**: All text ≥ 11px
- [ ] **Touch Targets**: Interactive elements ≥ 44x44px on mobile
- [ ] **Zoom Controls**: Visible zoom in/out buttons
- [ ] **Scale Indicator**: Include scale bar for distance reference

```tsx
// Accessibility example
<div 
  role="img" 
  aria-label="Map showing revenue by territory. New York leads with $250M, followed by Los Angeles at $180M and Chicago at $150M."
  style={{ height: '500px' }}
>
  <MapContainer>
    {/* Map content */}
  </MapContainer>
</div>

{/* Provide accessible data table */}
<details className="mt-4">
  <summary className="text-sm font-semibold cursor-pointer hover:text-primary">
    View data table (accessible alternative)
  </summary>
  <table className="mt-2 w-full text-sm border">
    <thead>
      <tr className="bg-muted">
        <th className="text-left p-2">Territory</th>
        <th className="text-right p-2">Revenue</th>
        <th className="text-right p-2">Growth</th>
      </tr>
    </thead>
    <tbody>
      {data.map((item, i) => (
        <tr key={i} className="border-t">
          <td className="p-2">{item.name}</td>
          <td className="text-right p-2">${item.revenue}M</td>
          <td className="text-right p-2">{item.growth}%</td>
        </tr>
      ))}
    </tbody>
  </table>
</details>
```

---

### Package Dependencies for Maps

```json
{
  "dependencies": {
    "react-leaflet": "^4.x",
    "leaflet": "^1.9.x",
    "mapbox-gl": "^3.x",
    "react-map-gl": "^7.x",
    "react-simple-maps": "^3.x",
    "@deck.gl/react": "^8.x",
    "deck.gl": "^8.x"
  },
  "devDependencies": {
    "@types/leaflet": "^1.9.x"
  }
}
```

**Installation order:**
```bash
# Start with Leaflet (most common)
npm install react-leaflet leaflet
npm install @types/leaflet --save-dev

# Add Mapbox if needed
npm install mapbox-gl react-map-gl

# Add Simple Maps for slides
npm install react-simple-maps
```

---

## Common Mistakes & Anti-Patterns

### ❌ WRONG: Gridlines on Chart

```tsx
// DON'T DO THIS
<BarChart data={data}>
  <XAxis />  {/* Missing axisLine={false} */}
  <YAxis />  {/* Missing tickLine={false} */}
  <Bar dataKey="value" fill="#7823DC" />
</BarChart>
```

### ✅ CORRECT: No Gridlines

```tsx
// DO THIS
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
  <Bar dataKey="value" fill="#7823DC" />
</BarChart>
```

---

### ❌ WRONG: Non-Kearney Colors

```tsx
// DON'T DO THIS
<Bar dataKey="value" fill="#FF5733" />  // Random color
<TrendingUp className="w-4 h-4 text-blue-500" />  // Tailwind color
```

### ✅ CORRECT: Kearney Colors

```tsx
// DO THIS
<Bar dataKey="value" fill="#7823DC" />
<TrendingUp className="w-4 h-4" style={{ color: '#7823DC' }} />
```

---

### ❌ WRONG: Missing Value Labels

```tsx
// DON'T DO THIS
<Bar dataKey="value" fill="#7823DC" />
```

### ✅ CORRECT: With Value Labels

```tsx
// DO THIS
<Bar dataKey="value" fill="#7823DC">
  <LabelList 
    dataKey="value"
    position="top"
    style={{ fill: 'currentColor', fontSize: 12 }}
  />
</Bar>
```

---

### ❌ WRONG: Uncolored Icons

```tsx
// DON'T DO THIS
<TrendingUp className="w-4 h-4" />  // No color specified
```

### ✅ CORRECT: Properly Colored Icons

```tsx
// DO THIS
import { TrendingUp } from 'lucide-react';

<TrendingUp className="w-4 h-4" style={{ color: '#7823DC' }} />
```

---

### ❌ WRONG: Wrong Font Stack

```tsx
// DON'T DO THIS
<div style={{ fontFamily: 'Helvetica, sans-serif' }}>
<div className="font-roboto">
```

### ✅ CORRECT: Proper Font Stack

```tsx
// DO THIS
<div style={{ fontFamily: 'Inter, Arial, sans-serif' }}>

// Or rely on default CSS
<div>  {/* Uses theme font-family */}
```

---

### ❌ WRONG: Using Emoticons

```tsx
// DON'T DO THIS
<span>🚀 Revenue Increased</span>
<h2>Great Results! 🎉</h2>
```

### ✅ CORRECT: Use Lucide Icons

```tsx
// DO THIS
import { TrendingUp } from 'lucide-react';

<div className="flex items-center gap-2">
  <TrendingUp className="w-4 h-4" style={{ color: '#7823DC' }} />
  <span>Revenue Increased</span>
</div>
```

---

### ❌ WRONG: Wrong Chart Color Sequence

```tsx
// DON'T DO THIS - Random order
const colors = ['#FF5733', '#7823DC', '#00FF00'];

data.map((item, i) => (
  <Bar key={i} dataKey={item.key} fill={colors[i]} />
))
```

### ✅ CORRECT: Proper Sequence

```tsx
// DO THIS - Use chart colors 1-10 in order
const CHART_COLORS = [
  '#D2D2D2', '#A5A6A5', '#787878', '#E0D2FA', '#C8A5F0',
  '#AF7DEB', '#4B4B4B', '#1E1E1E', '#9150E1', '#7823DC'
];

data.map((item, i) => (
  <Bar 
    key={i} 
    dataKey={item.key} 
    fill={CHART_COLORS[i % CHART_COLORS.length]} 
  />
))
```

---

### ❌ WRONG: Pie Chart with Too Many Segments

```tsx
// DON'T DO THIS
<PieChart>
  <Pie data={dataWith10Segments} />  // Too many!
</PieChart>
```

### ✅ CORRECT: Use Bar Chart Instead

```tsx
// DO THIS
<BarChart data={data}>
  <XAxis dataKey="name" axisLine={false} tickLine={false} />
  <YAxis axisLine={false} tickLine={false} />
  <Bar dataKey="value" fill="#7823DC">
    <LabelList dataKey="value" position="top" />
  </Bar>
</BarChart>
```

---

## Code Examples

### Complete Bar Chart with All Requirements

```tsx
import { Card } from './components/ui/card';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, 
  ResponsiveContainer, LabelList 
} from 'recharts';
import { TrendingUp } from 'lucide-react';

const data = [
  { category: 'Digital', value: 34 },
  { category: 'Operations', value: 28 },
  { category: 'Strategy', value: 22 },
  { category: 'Technology', value: 16 },
];

export function RevenueChart() {
  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="font-semibold mb-1">Revenue by Service Line</h3>
          <p className="text-sm text-muted-foreground">
            Q4 2024 Performance ($M)
          </p>
        </div>
        <div className="flex items-center gap-1">
          <TrendingUp className="w-4 h-4" style={{ color: '#7823DC' }} />
          <span className="text-sm font-semibold" style={{ color: '#7823DC' }}>
            +15% YoY
          </span>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <XAxis 
            dataKey="category"
            axisLine={false}          // No axis line
            tickLine={false}          // No tick marks
            tick={{ fill: 'currentColor', fontSize: 12 }}
          />
          <YAxis 
            axisLine={false}          // No axis line
            tickLine={false}          // No tick marks
            tick={false}              // Hide values (labels show them)
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px'
            }}
          />
          <Bar 
            dataKey="value" 
            fill="#7823DC"             // Kearney purple
            radius={[4, 4, 0, 0]}     // Rounded top corners
          >
            <LabelList               // Value labels
              dataKey="value"
              position="top"
              style={{ fill: 'currentColor', fontSize: 12 }}
              formatter={(value) => `$${value}M`}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Insight */}
      <div className="mt-6 p-4 rounded-lg border-l-4" 
           style={{ 
             borderLeftColor: '#7823DC',
             backgroundColor: 'hsl(var(--muted))' 
           }}>
        <p className="text-sm text-muted-foreground">
          <strong>Key Insight:</strong> Digital transformation services 
          grew 34% QoQ, representing our strongest performing segment.
        </p>
      </div>
    </Card>
  );
}
```

### Complete Multi-Series Line Chart

```tsx
import { Card } from './components/ui/card';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, Label
} from 'recharts';

const data = [
  { month: 'Jan', actual: 1.8, forecast: 2.0, target: 2.2 },
  { month: 'Feb', actual: 2.1, forecast: 2.1, target: 2.2 },
  { month: 'Mar', actual: 2.3, forecast: 2.2, target: 2.2 },
  { month: 'Apr', actual: 2.0, forecast: 2.3, target: 2.2 },
  { month: 'May', actual: 2.5, forecast: 2.4, target: 2.2 },
  { month: 'Jun', actual: 2.4, forecast: 2.5, target: 2.2 },
];

const CHART_COLORS = ['#D2D2D2', '#A5A6A5', '#787878'];

export function RevenueComparison() {
  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="font-semibold mb-1">Revenue Comparison</h3>
        <p className="text-sm text-muted-foreground">
          Actual vs Forecast vs Target ($M)
        </p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <XAxis 
            dataKey="month"
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
          <Legend 
            wrapperStyle={{ fontSize: 12 }}
            iconType="line"
          />
          
          {/* Target reference line */}
          <ReferenceLine 
            y={2.2} 
            stroke="#7823DC" 
            strokeDasharray="3 3"
          >
            <Label 
              value="Target: $2.2M" 
              position="insideTopRight"
              style={{ fill: '#7823DC', fontSize: 11 }}
            />
          </ReferenceLine>

          {/* Lines using chart color sequence */}
          <Line 
            type="monotone"
            dataKey="actual"
            stroke={CHART_COLORS[0]}
            strokeWidth={2}
            dot={{ fill: CHART_COLORS[0], r: 4 }}
            name="Actual"
          />
          <Line 
            type="monotone"
            dataKey="forecast"
            stroke={CHART_COLORS[1]}
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: CHART_COLORS[1], r: 4 }}
            name="Forecast"
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
```

### Complete KPI Dashboard

```tsx
import { Card } from './components/ui/card';
import { TrendingUp, TrendingDown, DollarSign, Users, Target } from 'lucide-react';

const kpis = [
  { 
    label: 'Total Revenue', 
    value: '$2.4M', 
    change: '+12.5%', 
    trend: 'up',
    icon: DollarSign 
  },
  { 
    label: 'Active Clients', 
    value: '142', 
    change: '+8', 
    trend: 'up',
    icon: Users 
  },
  { 
    label: 'Target Achievement', 
    value: '94%', 
    change: '-2%', 
    trend: 'down',
    icon: Target 
  },
];

export function KPIDashboard() {
  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {kpis.map((kpi) => {
        const Icon = kpi.icon;
        const TrendIcon = kpi.trend === 'up' ? TrendingUp : TrendingDown;
        const trendColor = kpi.trend === 'up' ? '#7823DC' : '#EF5350';
        
        return (
          <Card key={kpi.label} className="p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-muted-foreground mb-3 uppercase tracking-wide">
                  {kpi.label}
                </p>
                <h2 className="mb-2">{kpi.value}</h2>
                <div className="flex items-center gap-1">
                  <TrendIcon 
                    className="w-4 h-4" 
                    style={{ color: trendColor }} 
                  />
                  <span 
                    className="text-sm font-semibold"
                    style={{ color: trendColor }}
                  >
                    {kpi.change}
                  </span>
                  <span className="text-xs text-muted-foreground ml-1">
                    vs last quarter
                  </span>
                </div>
              </div>
              <div 
                className="p-3 rounded-lg"
                style={{ backgroundColor: '#E0D2FA' }}
              >
                <Icon className="w-5 h-5" style={{ color: '#7823DC' }} />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
```

### Icon Import & Usage Pattern

```tsx
// ALWAYS verify icon exists before using!
// Check node_modules/lucide-react/dist/esm/icons/index.js

import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign,
  Users,
  Target,
  Lightbulb,
  AlertCircle,
  CheckCircle,
  Download,
  Share2,
  Filter,
  Search
} from 'lucide-react';

// Usage pattern - ALWAYS color the icon
<TrendingUp 
  className="w-4 h-4"           // Size
  style={{ color: '#7823DC' }}  // Kearney purple
/>

// Or use CSS variable for theme-aware coloring
<TrendingUp 
  className="w-4 h-4" 
  style={{ color: 'hsl(var(--primary))' }}
/>

// Common sizes
const ICON_SIZES = {
  xs: 'w-3 h-3',   // 12px
  sm: 'w-4 h-4',   // 16px
  md: 'w-5 h-5',   // 20px
  lg: 'w-6 h-6',   // 24px
  xl: 'w-8 h-8',   // 32px
};
```

---

## Decision Trees

### Chart Type Selection

```
START: What are you trying to show?

├─ Comparing categories?
│  ├─ Few categories (< 10)? → Bar Chart
│  ├─ Many categories? → Horizontal Bar Chart
│  └─ Showing composition? → Stacked Bar Chart
│
├─ Showing trends over time?
│  ├─ Continuous data? → Line Chart
│  ├─ Emphasizing volume? → Area Chart
│  └─ Multiple series? → Multi-line Chart (max 5 series)
│
├─ Showing relationship between variables?
│  ├─ Two variables? → Scatter Plot
│  └─ Pattern across dimensions? → Heatmap
│
├─ Showing single metric?
│  ├─ With trend? → KPI Card with sparkline
│  ├─ With target? → KPI Card with progress bar
│  └─ Simple value? → KPI Card
│
└─ Showing composition of whole?
   ├─ 2-4 segments ONLY? → Pie Chart (reluctantly)
   └─ More segments? → Stacked Bar Chart instead
```

### Component Selection

```
START: What element do you need?

├─ Displaying data?
│  ├─ Chart? → ChartCard wrapper + Recharts component
│  ├─ Table? → DataTable with hover states
│  ├─ Single metric? → DataCard/KPI Card
│  └─ List of items? → Vertical list in Card
│
├─ User interaction?
│  ├─ Primary action? → Button (default variant)
│  ├─ Secondary action? → Button variant="outline"
│  ├─ Filter/search? → Input with icon
│  └─ Settings? → Dropdown or Modal
│
├─ Information display?
│  ├─ Status? → StatusBadge
│  ├─ Insight? → InsightCard with icon
│  ├─ Alert? → Card with border-l-4
│  └─ Tooltip? → Built-in Recharts Tooltip
│
└─ Layout?
   ├─ Dashboard? → Grid layout with Cards
   ├─ Slide? → 16:9 aspect ratio container
   └─ Report? → Standard document flow
```

### Color Selection

```
START: What needs color?

├─ Chart with 1 data series?
│  └─ Use #7823DC (Kearney Purple)
│
├─ Chart with multiple series?
│  └─ Use CHART_COLORS[0..n-1] in sequence
│
├─ Icon?
│  ├─ Primary action? → #7823DC
│  ├─ Positive trend? → #7823DC
│  ├─ Negative trend? → #EF5350 (red)
│  └─ Neutral? → currentColor
│
├─ Background?
│  ├─ Light theme? → #FFFFFF
│  ├─ Dark theme? → #1E1E1E
│  ├─ Muted section? → hsl(var(--muted))
│  └─ Gradient? → Use approved Kearney gradients only
│
└─ Text?
   ├─ Primary? → currentColor (theme foreground)
   ├─ Secondary? → text-muted-foreground class
   └─ Emphasis? → #7823DC
```

---

## Accessibility Checklist

Before delivering any Kearney design system work, verify:

- [ ] **Color Contrast**: All text has ≥ 4.5:1 contrast ratio (WCAG AA)
- [ ] **Theme Support**: Works correctly in both light and dark themes
- [ ] **Colorblind Friendly**: No critical information conveyed by color alone
- [ ] **Text Size**: All labels ≥ 12px font size
- [ ] **Keyboard Navigation**: Interactive elements are keyboard accessible
- [ ] **Screen Readers**: Proper ARIA labels on interactive elements
- [ ] **Focus Indicators**: Visible focus states on all interactive elements
- [ ] **Touch Targets**: Buttons/links ≥ 44x44px on mobile

---

## Package Dependencies

### Required Packages

```json
{
  "dependencies": {
    "react": "^18.x",
    "recharts": "^2.x",
    "lucide-react": "latest",
    "tailwindcss": "^4.x"
  }
}
```

### Lucide Icon Verification

**CRITICAL**: Before using ANY Lucide icon, verify it exists:

```bash
# Check if icon exists in lucide-react
cat node_modules/lucide-react/dist/esm/icons/index.js | grep "IconName"
```

Common icons that exist:
- TrendingUp, TrendingDown
- DollarSign, Users, Target
- Lightbulb, AlertCircle, CheckCircle
- Download, Upload, Share2
- Filter, Search, Settings
- ArrowRight, ArrowLeft, ArrowUp, ArrowDown
- Plus, Minus, X, Check

---

## Version History

### Version 1.1 (January 2, 2026)
- **NEW: Comprehensive Mapping & Geospatial Analytics section**
- Added choropleth map color scales and examples
- Added point/marker map standards
- Added static map guidelines for slides
- Included map library recommendations (Leaflet, Mapbox, react-simple-maps)
- Added geospatial data format guidance
- Added map accessibility standards
- Created MapExample.tsx component with best practices
- Updated Quick Start guide to include mapping rules

### Version 1.0 (January 1, 2026)
- Initial release with complete design system
- All color palettes defined
- Chart configurations established
- Component patterns documented
- Dashboard and slide layouts included
- Accessibility guidelines added

---

## Quick Reference Card

**Copy this for rapid AI prompting:**

```
KEARNEY DESIGN SYSTEM ESSENTIALS:

COLORS (use EXACTLY):
- Primary: #7823DC
- Black: #1E1E1E
- White: #FFFFFF
- Gray: #A5A5A5
- Charts 1-10: #D2D2D2, #A5A6A5, #787878, #E0D2FA, #C8A5F0, #AF7DEB, #4B4B4B, #1E1E1E, #9150E1, #7823DC

FONTS:
- Stack: Inter, Arial, sans-serif
- Sizes: H1=40px, H2=32px, H3=24px, Body=16px, Small=14px, XS=12px

CHARTS MUST HAVE:
✓ axisLine={false} tickLine={false}
✓ Value labels (LabelList)
✓ Kearney colors only
✓ Tooltips
✓ Annotations for insights

NEVER USE:
✗ Gridlines
✗ Non-Kearney colors
✗ Emoticons
✗ Uncolored Lucide icons

ICONS:
- Import from 'lucide-react'
- Always style={{ color: '#7823DC' }}
- Verify icon exists first
```

---

## GitHub Gist Reference

**📦 Complete Component Library**: [View on GitHub Gist](https://gist.github.com/YOUR_USERNAME/YOUR_GIST_ID)

The Gist includes all React component implementations from `/src/app/components/kearney/`:

- `ChartCard.tsx` - Chart wrapper component
- `DataCard.tsx` - KPI/metric display
- `InsightCard.tsx` - Annotation cards
- `StatusBadge.tsx` - Status indicators
- `DataTable.tsx` - Styled tables
- `KPIGrid.tsx` - Dashboard KPI layout
- `ChartsShowcase.tsx` - All chart examples
- `AnnotatedChartsExample.tsx` - Charts with annotations
- `DashboardExample.tsx` - Complete dashboard
- `SlideExample.tsx` - Presentation slides
- And more...

**To create your Gist:**

1. Go to https://gist.github.com/
2. Create a new Gist
3. Add all `.tsx` files from `/src/app/components/kearney/`
4. Make it public
5. Copy the Gist URL
6. Replace `YOUR_USERNAME/YOUR_GIST_ID` in this document with your actual Gist URL

---

## Usage with AI Assistants

### For Chat Interfaces (ChatGPT, Claude, etc.)

1. **Start conversation**: Paste the "Quick Reference Card" section
2. **For detailed work**: Reference this full document
3. **For examples**: Point to the GitHub Gist

### For Code Editors (Cursor, GitHub Copilot)

1. **Add to workspace**: Save this file as `KDS_GUIDELINES.md` in project root
2. **Reference in prompts**: "Follow KDS_GUIDELINES.md for all styling"
3. **Component reference**: Link to Gist for implementation details

### For Figma Make

1. **Upload this file** at the start of your session
2. **Reference throughout**: "Use Kearney Design System from uploaded file"
3. **For charts**: "Create chart following KDS guidelines with no gridlines"

---

## Support & Questions

**Common Questions:**

**Q: Can I use a gradient that's not in the approved list?**  
A: No. All gradients must use only Kearney brand colors.

**Q: What if I need more than 10 chart colors?**  
A: Reconsider the visualization. 10+ series is too complex. Use grouping or multiple charts.

**Q: Can I use a different icon library?**  
A: No. Only Lucide-react is approved, and icons must be colored.

**Q: Are emoticons ever acceptable?**  
A: Absolutely not. Use Lucide icons instead.

**Q: What if my chart needs gridlines for clarity?**  
A: It doesn't. Use value labels, annotations, and reference lines instead.

---

## License

© 2026 Kearney Design System  
For use in professional consulting deliverables

---

**END OF GUIDELINES**

When sharing this document with AI assistants, you can either:
1. Paste the entire document
2. Paste the "Quick Reference Card" for rapid work
3. Reference specific sections by name (e.g., "See Chart Configuration section")
4. Point to the GitHub Gist for component implementations