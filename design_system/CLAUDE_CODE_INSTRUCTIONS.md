# INSTRUCTIONS FOR CLAUDE CODE (Desktop)

## 🎯 Goal
Upload the complete Kearney Design System (74 files) from Figma Make to a public GitHub Gist.

## 📋 Context
I've been working with Figma Make to build a comprehensive design system. All 74 files exist in the Figma Make environment but there's no export button. I need your help transferring these files to a GitHub Gist.

## ✅ What You Need to Do

### Step 1: Get the Files from Figma Make
I'll paste the file manifest below. Each file exists in my Figma Make session at the paths shown.

### Step 2: Create Local Project Structure
Create a new directory: `kearney-design-system/`

With this structure:
```
kearney-design-system/
├── src/
│   ├── app/
│   │   └── components/
│   │       ├── kearney/       (18 files)
│   │       └── ui/             (48 files)
│   ├── styles/                 (4 files)
│   └── assets/
│       └── logos/              (3 files)
├── KDS_AI_GUIDELINES.md
├── README.md
└── package.json
```

### Step 3: Request File Contents from User
Ask me to paste the contents of each file, starting with:
1. KDS_AI_GUIDELINES.md (most important)
2. Kearney components (18 files)
3. UI components (can be batched)
4. Styles (4 files)
5. Logo SVGs (3 files)

### Step 4: Create the GitHub Gist
Once you have all files locally, run:

```bash
cd kearney-design-system

gh gist create --public \
  --description "Kearney Design System - Production-ready React component library for consulting deliverables. Built with React, Tailwind CSS 4.0, and Recharts. January 2026." \
  src/app/components/kearney/*.tsx \
  src/app/components/ui/*.tsx \
  src/styles/*.css \
  src/assets/logos/*.svg \
  KDS_AI_GUIDELINES.md \
  README.md \
  package.json
```

### Step 5: Return the Gist URL
Give me the URL so I can share it.

---

## 📦 File Manifest (74 Files)

### Priority 1: Documentation (1 file)
- KDS_AI_GUIDELINES.md - Complete design system documentation

### Priority 2: Kearney Components (18 files)
- src/app/components/kearney/AnnotatedChartsExample.tsx
- src/app/components/kearney/ChartCard.tsx
- src/app/components/kearney/ChartsShowcase.tsx
- src/app/components/kearney/ColorPalette.tsx
- src/app/components/kearney/ComponentsShowcase.tsx
- src/app/components/kearney/DashboardExample.tsx
- src/app/components/kearney/DataCard.tsx
- src/app/components/kearney/DataTable.tsx
- src/app/components/kearney/DataVisualizationGuide.tsx
- src/app/components/kearney/DesignSystemOverview.tsx
- src/app/components/kearney/GradientsShowcase.tsx
- src/app/components/kearney/InsightCard.tsx
- src/app/components/kearney/KPIGrid.tsx
- src/app/components/kearney/Logo.tsx
- src/app/components/kearney/SlideExample.tsx
- src/app/components/kearney/SlideLayout.tsx
- src/app/components/kearney/StatusBadge.tsx
- src/app/components/kearney/TypographyShowcase.tsx

### Priority 3: Logo Assets (3 files)
- src/assets/logos/kearney-logo-purple.svg
- src/assets/logos/kearney-logo-slate.svg
- src/assets/logos/kearney-logo-white.svg

### Priority 4: Styles (4 files)
- src/styles/fonts.css
- src/styles/index.css
- src/styles/tailwind.css
- src/styles/theme.css

### Priority 5: UI Components (48 files - can be batched)
- src/app/components/ui/accordion.tsx
- src/app/components/ui/alert-dialog.tsx
- src/app/components/ui/alert.tsx
- src/app/components/ui/aspect-ratio.tsx
- src/app/components/ui/avatar.tsx
- src/app/components/ui/badge.tsx
- src/app/components/ui/breadcrumb.tsx
- src/app/components/ui/button.tsx
- src/app/components/ui/calendar.tsx
- src/app/components/ui/card.tsx
- src/app/components/ui/carousel.tsx
- src/app/components/ui/chart.tsx
- src/app/components/ui/checkbox.tsx
- src/app/components/ui/collapsible.tsx
- src/app/components/ui/command.tsx
- src/app/components/ui/context-menu.tsx
- src/app/components/ui/dialog.tsx
- src/app/components/ui/drawer.tsx
- src/app/components/ui/dropdown-menu.tsx
- src/app/components/ui/form.tsx
- src/app/components/ui/hover-card.tsx
- src/app/components/ui/input-otp.tsx
- src/app/components/ui/input.tsx
- src/app/components/ui/label.tsx
- src/app/components/ui/menubar.tsx
- src/app/components/ui/navigation-menu.tsx
- src/app/components/ui/pagination.tsx
- src/app/components/ui/popover.tsx
- src/app/components/ui/progress.tsx
- src/app/components/ui/radio-group.tsx
- src/app/components/ui/resizable.tsx
- src/app/components/ui/scroll-area.tsx
- src/app/components/ui/select.tsx
- src/app/components/ui/separator.tsx
- src/app/components/ui/sheet.tsx
- src/app/components/ui/sidebar.tsx
- src/app/components/ui/skeleton.tsx
- src/app/components/ui/slider.tsx
- src/app/components/ui/sonner.tsx
- src/app/components/ui/switch.tsx
- src/app/components/ui/table.tsx
- src/app/components/ui/tabs.tsx
- src/app/components/ui/textarea.tsx
- src/app/components/ui/toggle-group.tsx
- src/app/components/ui/toggle.tsx
- src/app/components/ui/tooltip.tsx
- src/app/components/ui/use-mobile.ts
- src/app/components/ui/utils.ts

---

## 💡 Tips for Efficiency

**Batching Strategy:**
- Request 5-10 files at a time
- UI components can often be requested as "all button-related" or "all form-related"
- Some files might be standard shadcn/ui components you can generate yourself

**Alternative Approach:**
If the user can't easily paste all files, you could:
1. Ask them to share their Figma Make session/project URL
2. See if Figma Make has an API or sharing mechanism
3. Generate standard UI components yourself (many are from shadcn/ui)

---

## 🆘 If This Doesn't Work

Alternative: Create a curated subset with just the essential files:
- KDS_AI_GUIDELINES.md (documentation)
- All 18 Kearney components
- Logo SVGs (3 files)
- Core theme.css file

This would be ~23 files instead of 74, which is more manageable.

---

**Ready to start?** Ask me for the first batch of files!
