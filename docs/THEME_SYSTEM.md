

# KIE v3 Theme System

Complete dark and light theme support for all outputs.

---

## Overview

KIE v3 supports **both dark and light themes** to accommodate consultant preferences. All outputs (charts, maps, slides, dashboards) automatically respect the chosen theme.

### Why Two Themes?

- **Dark Theme**: Reduces eye strain in low light, modern appearance
- **Light Theme**: Traditional document look, better for printing, some consultants prefer it

**All outputs are 100% KDS-compliant in both themes.**

---

## Quick Start

### Python

```python
from core_v3.brand.theme import ThemeMode, set_theme

# Set theme globally
set_theme(ThemeMode.DARK)   # or ThemeMode.LIGHT

# Create charts (automatically use theme)
from core_v3.charts import ChartFactory

chart = ChartFactory.bar(data, x_key="region", y_keys=["revenue"])
# Chart colors, backgrounds, text automatically themed
```

### React

```tsx
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { ThemeToggle } from './components/ThemeToggle';

function App() {
  return (
    <ThemeProvider defaultMode="dark">
      <ThemeToggle />
      {/* All components automatically themed */}
    </ThemeProvider>
  );
}
```

---

## Theme Colors

### Dark Theme (Default)

| Element | Color | Hex |
|---------|-------|-----|
| Background Primary | Kearney Black | `#1E1E1E` |
| Background Secondary | Dark Gray | `#2A2A2A` |
| Text Primary | White | `#FFFFFF` |
| Text Secondary | Light Gray | `#E0E0E0` |
| Border Primary | KDS Purple | `#7823DC` |
| Border Secondary | Charcoal | `#4B4B4B` |

### Light Theme

| Element | Color | Hex |
|---------|-------|-----|
| Background Primary | White | `#FFFFFF` |
| Background Secondary | Light Gray | `#F5F5F5` |
| Text Primary | Kearney Black | `#1E1E1E` |
| Text Secondary | Charcoal | `#4B4B4B` |
| Border Primary | KDS Purple | `#7823DC` |
| Border Secondary | Light Gray | `#D2D2D2` |

### Brand Colors (Same for Both Themes)

- **Primary**: `#7823DC` (Kearney Purple)
- **Accent**: `#9B4DCA` (Light Purple)
- **Light**: `#E0D2FA` (Very Light Purple)

### Chart Colors (Same for Both Themes)

The official KDS 10-color palette is used in order:

1. `#D2D2D2` - Light Gray
2. `#A5A6A5` - Medium Gray
3. `#787878` - Dark Gray
4. `#E0D2FA` - Light Purple
5. `#C8A5F0` - Medium Light Purple
6. `#AF7DEB` - Medium Purple
7. `#4B4B4B` - Charcoal
8. `#1E1E1E` - Kearney Black
9. `#9150E1` - Bright Purple
10. `#7823DC` - Kearney Purple

---

## Usage

### Setting Theme (Python)

```python
from core_v3.brand.theme import ThemeMode, set_theme, get_theme

# Set dark theme (default)
set_theme(ThemeMode.DARK)

# Set light theme
set_theme(ThemeMode.LIGHT)

# Get current theme
theme = get_theme()
print(theme.mode)  # ThemeMode.DARK or ThemeMode.LIGHT

# Get theme colors
bg = theme.get_background()  # Primary background
text = theme.get_text()      # Primary text color
accent = theme.get_accent_color()  # Accent color with good contrast
```

### Theme Manager API

```python
from core_v3.brand.theme import get_theme

theme = get_theme()

# Backgrounds (3 levels for elevation)
theme.get_background("primary")     # Main background
theme.get_background("secondary")   # Cards, elevated surfaces
theme.get_background("tertiary")    # Highest elevation

# Text (3 levels for hierarchy)
theme.get_text("primary")     # Main text
theme.get_text("secondary")   # Muted text
theme.get_text("tertiary")    # Disabled text

# Borders
theme.get_border("primary")   # Brand borders (purple)
theme.get_border("secondary") # Subtle borders

# Chart colors
theme.get_chart_colors()      # All 10 colors
theme.get_chart_colors(5)     # First 5 colors (cycles if more needed)

# Semantic colors
theme.get_semantic_color("success")  # Green
theme.get_semantic_color("warning")  # Orange
theme.get_semantic_color("error")    # Red
theme.get_semantic_color("info")     # Blue

# Folium integration
tiles = theme.get_folium_tiles()  # "CartoDB dark_matter" or "CartoDB positron"

# CSS variables (for web components)
css_vars = theme.get_css_variables()
```

### Project Theme Configuration

```python
from core_v3.config.theme_config import ProjectThemeConfig

config = ProjectThemeConfig()

# Save theme preference to project
config.save_theme(ThemeMode.LIGHT)

# Load theme preference from project
mode = config.load_theme()

# Apply theme from project config
config.apply_theme()

# Change theme
config.change_theme(ThemeMode.DARK)
```

Theme preference is stored in `project_state/spec.yaml`:

```yaml
preferences:
  theme: light
```

### React Components

```tsx
import { useTheme } from './contexts/ThemeContext';

function MyComponent() {
  const { mode, colors, toggleTheme, setTheme } = useTheme();

  return (
    <div style={{ backgroundColor: colors.backgroundPrimary }}>
      <h1 style={{ color: colors.textPrimary }}>
        Current theme: {mode}
      </h1>

      <button onClick={toggleTheme}>
        Toggle Theme
      </button>

      <button onClick={() => setTheme('light')}>
        Light Theme
      </button>
    </div>
  );
}
```

### Theme Toggle Button

```tsx
import { ThemeToggle } from './components/ThemeToggle';

function Header() {
  return (
    <header>
      <h1>My Dashboard</h1>
      <ThemeToggle showLabel={true} />
    </header>
  );
}
```

### Tailwind CSS

Use theme-aware Tailwind classes:

```tsx
// Theme-aware colors (CSS variables)
<div className="bg-bg-primary text-text-primary border-border-primary">
  Content
</div>

// Fixed KDS colors
<div className="bg-kds-primary text-white border-kds-purple">
  Brand Element
</div>
```

---

## Charts with Themes

All chart builders automatically use the current theme:

```python
from core_v3.brand.theme import set_theme, ThemeMode
from core_v3.charts import ChartFactory

# Set theme BEFORE creating charts
set_theme(ThemeMode.LIGHT)

# Create chart (automatically uses light theme)
chart = ChartFactory.bar(
    data=data,
    x_key="region",
    y_keys=["revenue"],
    title="Revenue by Region"
)

# Background, text, tooltips all use light theme colors
```

### React + Recharts (KIE v3)

KIE v3 uses React + Recharts; theme applies via CSS tokens.

---

## Maps with Themes

Maps automatically use the current theme:

```python
from core_v3.brand.theme import set_theme, ThemeMode
from core_v3.geo.maps import create_marker_map

# Set theme
set_theme(ThemeMode.LIGHT)

# Create map (automatically uses light tiles and styling)
map_builder = create_marker_map(
    data=locations,
    popup_cols=["name", "value"]
)

# Tiles, popups, legends all themed
map_builder.save("map.html")
```

### Manual Map Configuration

```python
from core_v3.geo.maps import MapBuilder, MapConfig

# MapConfig auto-populates from theme
config = MapConfig()  # Uses current theme

# Or override specific colors
config = MapConfig(
    background_color="#FFFFFF",  # Custom background
    text_color="#000000",        # Custom text
    # tiles auto-selected based on theme
)

builder = MapBuilder(config=config)
```

---

## Project Interview

During the `/start` command, KIE asks for theme preference:

```
🎨 Theme Preference
==================================================
KIE supports both dark and light themes.

1. Dark theme (default)
   • Dark backgrounds (#1E1E1E)
   • White text on dark surfaces
   • Reduces eye strain in low light

2. Light theme
   • Light backgrounds (#FFFFFF)
   • Dark text on light surfaces
   • Traditional document appearance

Choose theme (1 or 2) [1]:
```

This preference is saved to `project_state/spec.yaml` and applied automatically.

### Programmatic Interview

```python
from core_v3.config.theme_config import prompt_theme_preference

# Prompt user for theme
mode = prompt_theme_preference()

# Save to project
config = ProjectThemeConfig()
config.save_theme(mode)
```

---

## Contrast Requirements

**CRITICAL**: All text must meet WCAG 2.1 AA contrast ratios (4.5:1 minimum).

### Text on Dark Backgrounds

✅ **Correct:**
```python
# Use white or light purple
text_color = "#FFFFFF"          # White
text_color = "#E0D2FA"          # Light purple
```

❌ **Wrong:**
```python
# NEVER use primary purple on dark backgrounds
text_color = "#7823DC"  # Insufficient contrast!
```

### Text on Light Backgrounds

✅ **Correct:**
```python
# Use dark colors or primary purple
text_color = "#1E1E1E"          # Kearney Black
text_color = "#7823DC"          # Primary purple (good contrast on white)
```

### Using `get_accent_color()`

```python
theme = get_theme()

# Automatically returns color with good contrast
accent = theme.get_accent_color(for_background=theme.get_background())

# On dark: returns light purple (#E0D2FA)
# On light: returns primary purple (#7823DC)
```

---

## Best Practices

### 1. Set Theme Early

```python
# Set theme at start of script
from core_v3.brand.theme import set_theme, ThemeMode

set_theme(ThemeMode.LIGHT)

# All subsequent operations use light theme
```

### 2. Use Theme Manager

```python
# Don't hardcode colors
bg = "#1E1E1E"  # ❌ Wrong

# Use theme manager
from core_v3.brand.theme import get_theme
bg = get_theme().get_background()  # ✅ Correct
```

### 3. Load Theme from Project

```python
# At project startup
from core_v3.config.theme_config import initialize_project_theme

initialize_project_theme()  # Loads from spec.yaml

# Now all outputs use saved preference
```

### 4. Test Both Themes

Always test outputs in both dark and light themes to ensure readability.

```python
# Generate with dark theme
set_theme(ThemeMode.DARK)
create_chart(data, "chart_dark.json")

# Generate with light theme
set_theme(ThemeMode.LIGHT)
create_chart(data, "chart_light.json")
```

### 5. Respect User Choice

Never override user's theme preference without asking.

---

## Migration from v2

KIE v2 only supported dark theme. To migrate:

1. **No code changes needed** - Theme defaults to dark
2. **Optional**: Add theme preference to project interview
3. **Optional**: Let users toggle theme in web UI

### Updating Existing Code

```python
# Old v2 code (still works)
chart = ChartFactory.bar(data, x="region", y="revenue")

# New v3 code with theme
from core_v3.brand.theme import set_theme, ThemeMode
set_theme(ThemeMode.LIGHT)
chart = ChartFactory.bar(data, x="region", y="revenue")
```

---

## Examples

See `examples/theme_example.py` for comprehensive demonstration:

```bash
python examples/theme_example.py
```

This generates:
- Bar charts in both themes
- Maps in both themes
- Shows color comparison
- Demonstrates project config

---

## Troubleshooting

### Charts Not Using Theme

Make sure to set theme **before** creating charts:

```python
# Wrong order
chart = ChartFactory.bar(data, ...)
set_theme(ThemeMode.LIGHT)  # Too late!

# Correct order
set_theme(ThemeMode.LIGHT)
chart = ChartFactory.bar(data, ...)  # Uses light theme
```

### Theme Not Persisting

Ensure `project_state/spec.yaml` exists:

```python
from core_v3.config.theme_config import ProjectThemeConfig

config = ProjectThemeConfig()
config.save_theme(ThemeMode.LIGHT)  # Creates spec.yaml if needed
```

### Poor Contrast

Use `get_accent_color()` for text on colored backgrounds:

```python
theme = get_theme()
text_color = theme.get_accent_color(for_background=bg)
```

### React Theme Not Applying

Wrap app in `ThemeProvider`:

```tsx
import { ThemeProvider } from './contexts/ThemeContext';

ReactDOM.render(
  <ThemeProvider defaultMode="dark">
    <App />
  </ThemeProvider>,
  document.getElementById('root')
);
```

---

## API Reference

### Python

```python
# Enums
ThemeMode.DARK
ThemeMode.LIGHT

# Functions
set_theme(mode: ThemeMode)
get_theme() -> ThemeManager
get_theme_mode() -> ThemeMode

# ThemeManager methods
.get_background(level: "primary" | "secondary" | "tertiary") -> str
.get_text(level: "primary" | "secondary" | "tertiary") -> str
.get_border(level: "primary" | "secondary") -> str
.get_chart_colors(count: int = None) -> List[str]
.get_semantic_color(type: "success" | "warning" | "error" | "info") -> str
.get_accent_color(for_background: str = None) -> str
.get_folium_tiles() -> str
.get_css_variables() -> Dict
.to_dict() -> Dict

# Project config
ProjectThemeConfig(project_dir: Path = None)
.load_theme() -> ThemeMode
.save_theme(mode: ThemeMode)
.apply_theme()
.change_theme(mode: ThemeMode)

# Interview
prompt_theme_preference() -> ThemeMode
get_theme_display_name(mode: ThemeMode) -> str
get_theme_description(mode: ThemeMode) -> str
```

### React

```tsx
// Context
<ThemeProvider defaultMode="dark" | "light">

// Hook
const { mode, colors, toggleTheme, setTheme } = useTheme()

// Types
type ThemeMode = 'dark' | 'light'
interface ThemeColors { ... }

// Constants
KDS_CHART_COLORS: string[]  // 10 official colors
```

---

## Support

For issues or questions:
- See `examples/theme_example.py` for full example
- Check inline documentation in source files
- File an issue in the KIE repository
