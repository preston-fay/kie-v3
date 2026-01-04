"""
React Dashboard Builder for KIE v3 - KDS COMPLIANT

Generates KDS-compliant React/Recharts dashboards using:
- shadcn/ui components
- Tailwind CSS
- Radix UI primitives
- Official Kearney Design System
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from kie.data.loader import DataSchema


class ReactDashboardBuilder:
    """Build KDS-compliant React dashboards with shadcn/ui + Tailwind."""

    def __init__(
        self,
        project_name: str,
        client_name: str,
        objective: str,
        data_schema: Optional[DataSchema] = None,
        column_mapping: Optional[Dict[str, str]] = None
    ):
        self.project_name = project_name
        self.client_name = client_name
        self.objective = objective
        self.data_schema = data_schema
        self.column_mapping = column_mapping or {}  # Phase 5: Intelligent column selection

    def build_dashboard(
        self,
        data_path: Path,
        charts_dir: Path,
        output_dir: Path,
        theme_mode: str = "dark"
    ) -> Path:
        """
        Build KDS-compliant React dashboard with proper infrastructure.

        Returns:
            Path to dashboard directory
        """
        # AUTO-INFER SCHEMA if not provided (Runtime Intelligence!)
        if self.data_schema is None:
            from kie.data.loader import DataLoader
            loader = DataLoader()
            loader.load(data_path)
            self.data_schema = loader.schema

        # Create directory structure
        src_dir = output_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        components_dir = src_dir / "components" / "ui"
        components_dir.mkdir(parents=True, exist_ok=True)
        public_dir = output_dir / "public"
        public_dir.mkdir(parents=True, exist_ok=True)

        # Copy/convert data file to public directory as CSV
        import shutil
        import pandas as pd

        # If not CSV, convert to CSV first
        if data_path.suffix.lower() not in ['.csv']:
            # Load with DataLoader (handles Excel, JSON, Parquet, TSV, etc.)
            from kie.data.loader import DataLoader
            loader = DataLoader()
            df = loader.load(data_path)
            df.to_csv(public_dir / "data.csv", index=False)
        else:
            shutil.copy(data_path, public_dir / "data.csv")

        # Generate all files
        self._generate_package_json(output_dir)
        self._generate_vite_config(output_dir)
        self._generate_tsconfig(output_dir)
        self._generate_tailwind_config(output_dir)
        self._generate_postcss_config(output_dir)
        self._generate_index_html(output_dir)
        self._generate_index_css(src_dir)
        self._generate_main_tsx(src_dir)
        self._generate_app_tsx(src_dir)
        self._generate_utils(components_dir)
        self._generate_card_component(components_dir)
        self._generate_tabs_component(components_dir)
        self._generate_dashboard_component(src_dir, data_path)
        self._generate_readme(output_dir)

        return output_dir

    def _get_column_mapping(self) -> Dict[str, str]:
        """Get mapping from generic names to actual column names."""
        if self.data_schema is None:
            # Fall back to hardcoded names if no schema provided
            return {
                'entity': 'company',
                'category': 'revised_territory',
                'score': 'revised_score',
                'opportunity': 'opportunity_millions',
                'state': 'state'
            }

        # Use schema suggestions
        mapping = {}
        mapping['entity'] = self.data_schema.suggested_entity_column or 'company'
        mapping['category'] = self.data_schema.suggested_category_column or 'category'

        # Map metrics
        metrics = self.data_schema.suggested_metric_columns
        if len(metrics) >= 1:
            mapping['score'] = metrics[0]
        if len(metrics) >= 2:
            mapping['opportunity'] = metrics[1]

        # Try to find state/region column
        for col in self.data_schema.categorical_columns:
            if 'state' in col.lower() or 'region' in col.lower():
                mapping['state'] = col
                break

        return mapping

    def _generate_ts_interface(self) -> str:
        """Generate TypeScript interface from schema."""
        if self.data_schema is None:
            # Fall back to hardcoded interface
            return """interface DataRow {
  lo_id: string;
  company: string;
  city: string;
  state: string;
  revised_score: number;
  revised_territory: string;
  opportunity_millions: number;
  competitor_count: number;
  weighted_pressure: number;
}"""

        # Generate interface from actual columns
        lines = ["interface DataRow {"]
        for col in self.data_schema.columns:
            if col in self.data_schema.numeric_columns:
                lines.append(f"  {col}: number;")
            else:
                lines.append(f"  {col}: string;")
        lines.append("}")
        return "\n".join(lines)

    def _generate_package_json(self, output_dir: Path):
        """Generate package.json with all required dependencies."""
        content = '''{
  "name": "kie-dashboard",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "recharts": "^2.15.2",
    "@radix-ui/react-tabs": "^1.1.1",
    "lucide-react": "^0.468.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",
    "papaparse": "^5.4.1"
  },
  "devDependencies": {
    "@types/react": "^19.2.5",
    "@types/react-dom": "^19.2.3",
    "@types/papaparse": "^5.3.14",
    "@vitejs/plugin-react": "^5.1.1",
    "typescript": "~5.9.3",
    "vite": "^7.2.4",
    "tailwindcss": "^3.4.19",
    "postcss": "^8.5.6",
    "autoprefixer": "^10.4.23"
  }
}
'''
        (output_dir / "package.json").write_text(content)

    def _generate_vite_config(self, output_dir: Path):
        """Generate vite.config.ts."""
        content = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  }
})
'''
        (output_dir / "vite.config.ts").write_text(content)

    def _generate_tsconfig(self, output_dir: Path):
        """Generate tsconfig.json."""
        content = '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
'''
        (output_dir / "tsconfig.json").write_text(content)

    def _generate_tailwind_config(self, output_dir: Path):
        """Generate Tailwind config with KDS theme."""
        content = '''/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        chart: {
          1: "var(--chart-1)",
          2: "var(--chart-2)",
          3: "var(--chart-3)",
          4: "var(--chart-4)",
          5: "var(--chart-5)",
          6: "var(--chart-6)",
          7: "var(--chart-7)",
          8: "var(--chart-8)",
          9: "var(--chart-9)",
          10: "var(--chart-10)",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Inter", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
}
'''
        (output_dir / "tailwind.config.js").write_text(content)

    def _generate_postcss_config(self, output_dir: Path):
        """Generate PostCSS config."""
        content = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'''
        (output_dir / "postcss.config.js").write_text(content)

    def _generate_index_html(self, output_dir: Path):
        """Generate index.html."""
        content = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <title>{self.project_name} | KIE v3</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''
        (output_dir / "index.html").write_text(content)

    def _generate_index_css(self, src_dir: Path):
        """Generate index.css with KDS theme variables (hex colors)."""
        content = '''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Kearney Main Colors */
    --kearney-black: #1E1E1E;
    --kearney-white: #FFFFFF;
    --kearney-gray: #A5A5A5;
    --kearney-purple: #7823DC;

    /* Dark Theme */
    --background: #1E1E1E;
    --foreground: #FFFFFF;
    --card: #323232;
    --card-foreground: #FFFFFF;
    --popover: #323232;
    --popover-foreground: #FFFFFF;
    --primary: #9150E1;
    --primary-foreground: #FFFFFF;
    --secondary: #323232;
    --secondary-foreground: #FFFFFF;
    --muted: #4B4B4B;
    --muted-foreground: #A5A5A5;
    --accent: #4B4B4B;
    --accent-foreground: #FFFFFF;
    --border: #4B4B4B;
    --input: #4B4B4B;
    --ring: #9150E1;
    --radius: 0.5rem;

    /* Chart colors - Official KDS 10-color palette (exact sequence) */
    --chart-1: #D2D2D2;  /* Light Gray */
    --chart-2: #A5A6A5;  /* Medium Gray */
    --chart-3: #787878;  /* Dark Gray */
    --chart-4: #E0D2FA;  /* Light Purple */
    --chart-5: #C8A5F0;  /* Medium Light Purple */
    --chart-6: #AF7DEB;  /* Medium Purple */
    --chart-7: #4B4B4B;  /* Charcoal */
    --chart-8: #1E1E1E;  /* Kearney Black */
    --chart-9: #9150E1;  /* Bright Purple */
    --chart-10: #7823DC; /* Kearney Purple (primary brand) */
  }
}

@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
    font-family: 'Inter', Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  h1 {
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.02em;
  }

  h2 {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.3;
    letter-spacing: -0.01em;
  }

  h3 {
    font-size: 1.5rem;
    font-weight: 600;
    line-height: 1.4;
  }

  h4 {
    font-size: 1.25rem;
    font-weight: 600;
    line-height: 1.4;
  }

  h5 {
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.5;
  }
}
'''
        (src_dir / "index.css").write_text(content)

    def _generate_main_tsx(self, src_dir: Path):
        """Generate main.tsx entry point."""
        content = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
'''
        (src_dir / "main.tsx").write_text(content)

    def _generate_app_tsx(self, src_dir: Path):
        """Generate App.tsx component."""
        content = '''import { Dashboard } from './Dashboard';

function App() {
  return (
    <div className="min-h-screen bg-background">
      <Dashboard />
    </div>
  );
}

export default App;
'''
        (src_dir / "App.tsx").write_text(content)

    def _generate_utils(self, components_dir: Path):
        """Generate utils.ts for cn() function."""
        content = '''import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
'''
        (components_dir / "utils.ts").write_text(content)

    def _generate_card_component(self, components_dir: Path):
        """Generate shadcn/ui Card component."""
        content = '''import * as React from "react";
import { cn } from "./utils";

function Card({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border",
        className,
      )}
      {...props}
    />
  );
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("space-y-1.5 px-6 pt-6", className)}
      {...props}
    />
  );
}

function CardTitle({ className, ...props }: React.ComponentProps<"h3">) {
  return (
    <h3
      className={cn("text-2xl font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  );
}

function CardDescription({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("px-6 [&:last-child]:pb-6", className)}
      {...props}
    />
  );
}

function CardFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("flex items-center px-6 pb-6", className)}
      {...props}
    />
  );
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
};
'''
        (components_dir / "card.tsx").write_text(content)

    def _generate_tabs_component(self, components_dir: Path):
        """Generate shadcn/ui Tabs component."""
        content = '''import * as React from "react";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "./utils";

const Tabs = TabsPrimitive.Root;

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground",
      className
    )}
    {...props}
  />
));
TabsList.displayName = TabsPrimitive.List.displayName;

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm",
      className
    )}
    {...props}
  />
));
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      className
    )}
    {...props}
  />
));
TabsContent.displayName = TabsPrimitive.Content.displayName;

export { Tabs, TabsList, TabsTrigger, TabsContent };
'''
        (components_dir / "tabs.tsx").write_text(content)

    def _generate_dashboard_component(self, src_dir: Path, data_path: Path):
        """Generate KDS-compliant Dashboard component using Tailwind."""
        # Schema should always exist by this point (auto-inferred in build_dashboard if needed)
        assert self.data_schema is not None, "Schema should have been inferred in build_dashboard"

        # PHASE 5: Use intelligent column mapping if provided, otherwise fallback to naive selection
        # Define categorical_cols early to avoid NameError on line 628
        categorical_cols = self.data_schema.categorical_columns[:2] if self.data_schema.categorical_columns else []

        if self.column_mapping:
            # Intelligently selected columns from DataLoader
            metric1_col = self.column_mapping.get('revenue') or self.column_mapping.get('cost') or self.column_mapping.get('profit')
            category_col = self.column_mapping.get('category')
            # Fallback to first available if intelligent selection didn't find anything
            if not metric1_col and self.data_schema.numeric_columns:
                metric1_col = self.data_schema.numeric_columns[0]
            if not category_col and self.data_schema.categorical_columns:
                category_col = self.data_schema.categorical_columns[0]
            # Use metric1 for other metrics as fallback
            metric2_col = metric1_col
            metric3_col = metric1_col
            entity_col = category_col
        else:
            # FALLBACK: Naive selection (original behavior)
            numeric_cols = self.data_schema.numeric_columns[:3] if self.data_schema.numeric_columns else []

            entity_col = categorical_cols[0] if len(categorical_cols) > 0 else 'entity'
            category_col = categorical_cols[1] if len(categorical_cols) > 1 else categorical_cols[0] if len(categorical_cols) > 0 else 'category'
            metric1_col = numeric_cols[0] if len(numeric_cols) > 0 else 'value1'
            metric2_col = numeric_cols[1] if len(numeric_cols) > 1 else metric1_col
            metric3_col = numeric_cols[2] if len(numeric_cols) > 2 else metric1_col

        # For state detection, use any categorical column with "state", "region", or "location" in the name
        state_col = None
        for col in self.data_schema.categorical_columns:
            if any(keyword in col.lower() for keyword in ['state', 'region', 'location', 'territory', 'area']):
                state_col = col
                break
        if state_col is None:
            state_col = categorical_cols[1] if len(categorical_cols) > 1 else category_col

        ts_interface = self._generate_ts_interface()

        # Format column names for display (replace underscores with spaces, title case)
        metric1_display = metric1_col.replace('_', ' ').title()
        metric2_display = metric2_col.replace('_', ' ').title()
        category_display = category_col.replace('_', ' ').title()

        # Use .format() with double braces to escape JSX braces properly
        # In the template: {{ becomes {, }} becomes }, and {var} gets replaced
        content = """/**
 * {project_name}
 * Generated by KIE v3 - KDS Compliant
 *
 * Uses Recharts + shadcn/ui + Tailwind following Kearney Design System
 */

import {{ useState, useEffect }} from 'react';
import Papa from 'papaparse';
import {{
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList
}} from 'recharts';
import {{ Card, CardHeader, CardTitle, CardDescription, CardContent }} from './components/ui/card';
import {{ Tabs, TabsContent, TabsList, TabsTrigger }} from './components/ui/tabs';
import {{ TrendingUp }} from 'lucide-react';

{ts_interface}

export function Dashboard() {{
  const [data, setData] = useState<DataRow[]>([]);

  useEffect(() => {{
    fetch('/data.csv')
      .then(res => res.text())
      .then(csvText => {{
        Papa.parse(csvText, {{
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true,
          complete: (results) => {{
            const parsed = results.data as any[];
            setData(parsed);
          }},
          error: (error: any) => {{
            console.error('CSV parsing error:', error);
          }}
        }});
      }})
      .catch((err: any) => console.error('Fetch error:', err));
  }}, []);

  // GENERIC STATISTICS - works with ANY data
  const totalMetric1 = data.reduce((sum, d: any) => sum + (parseFloat(String(d['{metric1_col}'])) || 0), 0);
  const avgMetric1 = totalMetric1 / (data.length || 1);
  const totalMetric2 = data.reduce((sum, d: any) => sum + (parseFloat(String(d['{metric2_col}'])) || 0), 0);
  const totalRows = data.length;

  // Top categories by count
  const categoryCounts = data.reduce((acc: Record<string, number>, d: any) => {{
    const cat = d['{category_col}'];
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }}, {{}});
  const topCategory = Object.entries(categoryCounts)
    .sort(([,a], [,b]) => (b as number) - (a as number))[0];

  // Category distribution (top 10)
  const categoryData = Object.entries(categoryCounts)
    .map(([category, count]) => ({{ category, count }}))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  // Metric by category (top 10 categories)
  const metricByCategory = Object.entries(
    data.reduce((acc: Record<string, number>, d: any) => {{
      const cat = d['{category_col}'];
      acc[cat] = (acc[cat] || 0) + (parseFloat(String(d['{metric1_col}'])) || 0);
      return acc;
    }}, {{}})
  )
    .map(([category, value]) => ({{ category, value }}))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="mb-2">{project_name}</h1>
          <p className="text-muted-foreground">{objective}</p>
        </div>
      </div>

      {{/* GENERIC KPI CARDS */}}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Total Rows</p>
            <h2 className="mb-1">{{totalRows.toLocaleString()}}</h2>
            <div className="flex items-center gap-1">
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Dataset size
              </span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Avg {metric1_display}</p>
            <h2 className="mb-1">{{avgMetric1.toFixed(1)}}</h2>
            <div className="flex items-center gap-1">
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Mean value
              </span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Total {metric2_display}</p>
            <h2 className="mb-1">{{totalMetric2.toFixed(0)}}</h2>
            <div className="flex items-center gap-1">
              <span className="text-sm text-muted-foreground">
                Sum of all values
              </span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Top {category_display}</p>
            <h2 className="mb-1">{{topCategory ? topCategory[1] : 0}}</h2>
            <div className="flex items-center gap-1">
              <span className="text-sm text-muted-foreground">
                {{topCategory ? topCategory[0] : 'N/A'}}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {{/* Tabs */}}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="breakdown">Detailed Breakdown</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3>{metric1_display} by {category_display}</h3>
                  <p className="text-sm text-muted-foreground">Top 10 categories by total</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={{280}}>
                <BarChart data={{metricByCategory}}>
                  <XAxis
                    dataKey="category"
                    axisLine={{false}}
                    tickLine={{false}}
                    tick={{{{ fill: 'currentColor', fontSize: 12 }}}}
                  />
                  <YAxis
                    axisLine={{false}}
                    tickLine={{false}}
                    tick={{false}}
                  />
                  <Tooltip
                    contentStyle={{{{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}}}
                  />
                  <Bar dataKey="value" fill="var(--chart-10)" radius={{[4, 4, 0, 0]}}>
                    <LabelList
                      dataKey="value"
                      position="top"
                      style={{{{ fill: 'currentColor', fontSize: 14, fontWeight: 600 }}}}
                      formatter={{(value: number) => value.toFixed(0)}}
                    />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3>{category_display} Distribution</h3>
                  <p className="text-sm text-muted-foreground">Record count by category</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={{280}}>
                <BarChart data={{categoryData}}>
                  <XAxis
                    dataKey="category"
                    axisLine={{false}}
                    tickLine={{false}}
                    tick={{{{ fill: 'currentColor', fontSize: 12 }}}}
                  />
                  <YAxis
                    axisLine={{false}}
                    tickLine={{false}}
                    tick={{false}}
                  />
                  <Tooltip
                    contentStyle={{{{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}}}
                  />
                  <Bar dataKey="count" fill="#9150E1" radius={{[4, 4, 0, 0]}}>
                    <LabelList
                      dataKey="count"
                      position="top"
                      style={{{{ fill: 'currentColor', fontSize: 12 }}}}
                    />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="breakdown">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3>Top {category_display} by {metric1_display}</h3>
                <p className="text-sm text-muted-foreground">Detailed breakdown</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={{400}}>
              <BarChart data={{metricByCategory}} layout="horizontal">
                <XAxis type="number" axisLine={{false}} tickLine={{false}} tick={{false}} />
                <YAxis
                  type="category"
                  dataKey="category"
                  axisLine={{false}}
                  tickLine={{false}}
                  tick={{{{ fill: 'currentColor', fontSize: 12 }}}}
                  width={{120}}
                />
                <Tooltip
                  contentStyle={{{{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px'
                  }}}}
                  formatter={{(value: number) => value.toFixed(0)}}
                />
                <Bar dataKey="value" fill="var(--chart-10)" radius={{[0, 4, 4, 0]}}>
                  <LabelList
                    dataKey="value"
                    position="right"
                    style={{{{ fill: 'currentColor', fontSize: 12 }}}}
                    formatter={{(value: number) => value.toFixed(0)}}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        <TabsContent value="insights">
          <Card className="p-6">
            <CardHeader>
              <CardTitle>Data Insights</CardTitle>
              <CardDescription>Key findings and patterns in your data</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Summary Statistics</h4>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li>Total records: {{totalRows.toLocaleString()}}</li>
                    <li>Unique {category_display}: {{Object.keys(categoryCounts).length}}</li>
                    <li>Average {metric1_display}: {{avgMetric1.toFixed(2)}}</li>
                    <li>Total {metric2_display}: {{totalMetric2.toFixed(0)}}</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <footer className="text-center text-sm text-muted-foreground py-8">
        <p>{project_name} | Generated with KIE v3 | KDS Compliant</p>
      </footer>
    </div>
  );
}}
""".format(
            project_name=self.project_name,
            objective=self.objective,
            client_name=self.client_name,
            ts_interface=ts_interface,
            entity_col=entity_col,
            state_col=state_col,
            category_col=category_col,
            metric1_col=metric1_col,
            metric2_col=metric2_col,
            metric1_display=metric1_display,
            metric2_display=metric2_display,
            category_display=category_display
        )
        (src_dir / "Dashboard.tsx").write_text(content)

    def _generate_readme(self, output_dir: Path):
        """Generate README."""
        content = f'''# {self.project_name}

KDS-compliant React dashboard generated by KIE v3.

## Features

- ✅ **shadcn/ui components** (Card, Tabs)
- ✅ **Tailwind CSS** for styling
- ✅ **Radix UI** primitives
- ✅ **Recharts** visualizations (KDS requirement)
- ✅ **No gridlines** (KDS requirement)
- ✅ **Value labels** on all charts (KDS requirement)
- ✅ **Inter font** family (KDS requirement)
- ✅ **Official Kearney colors** (#7823DC, #C8A5F0, etc.)
- ✅ **Lucide React icons** (KDS requirement)

## Setup

```bash
npm install
npm run dev
```

## KDS Compliance

This dashboard follows the official Kearney Design System guidelines:

- Uses **shadcn/ui** with Tailwind CSS (official KDS pattern)
- Uses **Recharts** (required by KDS)
- **NO gridlines** on any charts (`axisLine={{false}}`, `tickLine={{false}}`)
- **Value labels** positioned outside data points with `LabelList`
- **Y-axis hidden** when labels are present
- **Inter font** family throughout
- **Official KDS colors**: #7823DC (purple), #C8A5F0 (accent), etc.
- **Lucide React icons** for visual indicators
'''
        (output_dir / "README.md").write_text(content)
