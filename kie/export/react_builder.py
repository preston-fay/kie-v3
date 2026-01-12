"""
React Dashboard Builder for KIE v3 - KDS COMPLIANT

Generates KDS-compliant React/Recharts dashboards using:
- shadcn/ui components
- Tailwind CSS
- Radix UI primitives
- Official Kearney Design System
"""

from pathlib import Path

from kie.data.loader import DataSchema


class ReactDashboardBuilder:
    """Build KDS-compliant React dashboards with shadcn/ui + Tailwind."""

    def __init__(
        self,
        project_name: str,
        client_name: str,
        objective: str,
        data_schema: DataSchema | None = None,
        column_mapping: dict[str, str] | None = None
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
        import json


        # If not CSV, convert to CSV first
        if data_path.suffix.lower() not in ['.csv']:
            # Load with DataLoader (handles Excel, JSON, Parquet, TSV, etc.)
            from kie.data.loader import DataLoader
            loader = DataLoader()
            df = loader.load(data_path)
            df.to_csv(public_dir / "data.csv", index=False)
        else:
            shutil.copy(data_path, public_dir / "data.csv")

        # COPY STORY MANIFEST AND CHARTS (MANDATORY FOR DASHBOARD RENDERING)
        outputs_dir = data_path.parent.parent / "outputs"
        manifest_path = outputs_dir / "story_manifest.json"

        if manifest_path.exists():
            # Copy story manifest to public/
            shutil.copy(manifest_path, public_dir / "story_manifest.json")

            # Load manifest to get chart references
            with open(manifest_path) as f:
                manifest = json.load(f)

            # Copy only charts referenced in manifest
            charts_public_dir = public_dir / "charts"
            charts_public_dir.mkdir(exist_ok=True)

            for section in manifest.get("sections", []):
                for visual in section.get("visuals", []):
                    chart_ref = visual.get("chart_ref", "")
                    if chart_ref:
                        source_chart = charts_dir / chart_ref
                        if source_chart.exists():
                            shutil.copy(source_chart, charts_public_dir / chart_ref)

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

    def _get_column_mapping(self) -> dict[str, str]:
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
        """Generate Dashboard component that renders from story_manifest.json."""
        # Read template from dashboard_template.tsx
        template_path = Path(__file__).parent / "dashboard_template.tsx"
        if template_path.exists():
            template_content = template_path.read_text()
            # Inject project name (simple replacement)
            dashboard_code = template_content.replace(
                "Generated by KIE v3 - Story Manifest Dashboard",
                f"{self.project_name} - Generated by KIE v3"
            )
        else:
            # Fallback: inline the improved template
            dashboard_code = """/**
 * Dashboard Template - Consultant-Grade UI
 * Generated by KIE v3 - Story Manifest Dashboard
 *
 * Renders structured story with Main Story and Appendix tabs
 * Features: Clean hierarchy, actionability badges, visual quality badges
 */

import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { AlertCircle, CheckCircle, Info } from 'lucide-react';

interface Visual {
  chart_ref: string;
  visualization_type: string;
  visual_quality: string;
  role: string;
  transition_text: string;
  emphasis: string;
}

interface Narrative {
  headline: string;
  bullets?: string[];
  purpose?: string;
}

interface Section {
  title: string;
  actionability_level: string;
  narrative: Narrative;
  visuals: Visual[];
}

interface StoryManifest {
  project_name: string;
  objective: string;
  generated_at?: string;
  sections: Section[];
}

interface ChartData {
  type: string;
  data: any[];
  config: any;
}

export function Dashboard() {
  const [manifest, setManifest] = useState<StoryManifest | null>(null);
  const [charts, setCharts] = useState<Record<string, ChartData>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch story manifest
    fetch('/story_manifest.json')
      .then(res => {
        if (!res.ok) throw new Error('Story manifest not found');
        return res.json();
      })
      .then((data: StoryManifest) => {
        setManifest(data);

        // Fetch all chart specs
        const chartPromises = data.sections.flatMap(section =>
          section.visuals.map(visual =>
            fetch(`/charts/${visual.chart_ref}`)
              .then(res => res.json())
              .then(chartData => [visual.chart_ref, chartData] as const)
          )
        );

        return Promise.all(chartPromises);
      })
      .then(chartEntries => {
        const chartsMap: Record<string, ChartData> = {};
        chartEntries.forEach(([ref, data]) => {
          chartsMap[ref] = data;
        });
        setCharts(chartsMap);
      })
      .catch(err => {
        console.error('Error loading manifest or charts:', err);
        setError(err.message);
      });
  }, []);

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <Card className="p-6 max-w-lg">
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold mb-2">Dashboard Error</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Unable to load story manifest: {error}
              </p>
              <p className="text-sm text-muted-foreground">
                Ensure the /build command has been run and story_manifest.json exists.
              </p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (!manifest) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted-foreground">Loading story...</p>
      </div>
    );
  }

  // Classify sections into Main Story vs Appendix
  const mainStorySections: Section[] = [];
  const appendixSections: Section[] = [];

  manifest.sections.forEach(section => {
    const isDecisionEnabling = section.actionability_level === 'decision_enabling';
    const hasInternalOnlyVisual = section.visuals.some(
      v => v.visual_quality === 'internal_only'
    );

    if (isDecisionEnabling && !hasInternalOnlyVisual) {
      mainStorySections.push(section);
    } else {
      appendixSections.push(section);
    }
  });

  const renderChart = (visual: Visual) => {
    const chartSpec = charts[visual.chart_ref];
    if (!chartSpec) {
      return (
        <div className="text-sm text-muted-foreground">
          Loading chart: {visual.chart_ref}
        </div>
      );
    }

    // Render bar chart (minimum viable implementation)
    if (chartSpec.type === 'bar' && chartSpec.config?.xAxis && chartSpec.config?.bars?.[0]) {
      const xKey = chartSpec.config.xAxis.dataKey;
      const yKey = chartSpec.config.bars[0].dataKey;
      const barColor = chartSpec.config.bars[0].fill || 'var(--chart-10)';

      return (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartSpec.data}>
            <XAxis
              dataKey={xKey}
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'currentColor', fontSize: 12 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px'
              }}
            />
            <Bar dataKey={yKey} fill={barColor} radius={[4, 4, 0, 0]}>
              <LabelList
                dataKey={yKey}
                position="top"
                style={{ fill: 'currentColor', fontSize: 14, fontWeight: 600 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      );
    }

    return (
      <div className="text-sm text-muted-foreground">
        Unsupported chart type: {chartSpec.type}
      </div>
    );
  };

  const renderActionabilityBadge = (level: string) => {
    const badges = {
      decision_enabling: {
        label: 'DECISION',
        icon: CheckCircle,
        className: 'bg-primary/10 text-primary border border-primary/20'
      },
      directional: {
        label: 'DIRECTION',
        icon: Info,
        className: 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
      },
      informational: {
        label: 'INFO',
        icon: Info,
        className: 'bg-muted/30 text-muted-foreground border border-muted'
      }
    };

    const badge = badges[level as keyof typeof badges] || badges.informational;
    const Icon = badge.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium ${badge.className}`}>
        <Icon className="w-3.5 h-3.5" />
        {badge.label}
      </span>
    );
  };

  const renderVisualQualityBadge = (quality: string) => {
    if (quality === 'client_ready_with_caveats') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-yellow-500/10 text-yellow-500 border border-yellow-500/20">
          <AlertCircle className="w-3.5 h-3.5" />
          ⚠️ Caveat
        </span>
      );
    }
    if (quality === 'internal_only') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
          Internal Only
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
        <CheckCircle className="w-3.5 h-3.5" />
        OK
      </span>
    );
  };

  const renderSection = (section: Section) => {
    return (
      <section key={section.title} className="space-y-6">
        {/* Section Header */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-3xl font-bold tracking-tight">{section.title}</h2>
            {renderActionabilityBadge(section.actionability_level)}
          </div>

          {section.narrative.purpose && (
            <p className="text-sm text-muted-foreground">
              {section.narrative.purpose}
            </p>
          )}

          <div className="border-l-4 border-primary/30 pl-4 py-2">
            <h3 className="text-xl font-semibold mb-3">
              {section.narrative.headline}
            </h3>
            {section.narrative.bullets && section.narrative.bullets.length > 0 && (
              <ul className="space-y-2">
                {section.narrative.bullets.map((bullet, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <span className="text-primary mt-1">•</span>
                    <span className="text-sm text-muted-foreground flex-1">{bullet}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Visuals */}
        {section.visuals.length > 0 ? (
          <div className="space-y-6">
            {section.visuals.map((visual, idx) => (
              <Card key={idx} className="overflow-hidden">
                <CardHeader className="space-y-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold">
                      {visual.role}
                    </CardTitle>
                    {renderVisualQualityBadge(visual.visual_quality)}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {visual.transition_text}
                  </p>
                </CardHeader>
                <CardContent className="pb-6">
                  {renderChart(visual)}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="p-6">
            <p className="text-sm text-muted-foreground text-center">
              No visuals required for this section.
            </p>
          </Card>
        )}
      </section>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Page Header */}
      <header className="border-b border-border bg-card/50">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold tracking-tight mb-3">
            {manifest.project_name}
          </h1>
          <p className="text-lg text-muted-foreground mb-2">
            {manifest.objective}
          </p>
          {manifest.generated_at && (
            <p className="text-xs text-muted-foreground">
              Generated: {new Date(manifest.generated_at).toLocaleString()}
            </p>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-6 py-8">
        <Tabs defaultValue="main-story" className="space-y-8">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="main-story" className="text-sm font-medium">
              Main Story
            </TabsTrigger>
            <TabsTrigger value="appendix" className="text-sm font-medium">
              Appendix
            </TabsTrigger>
          </TabsList>

          <TabsContent value="main-story" className="space-y-12">
            {mainStorySections.length > 0 ? (
              mainStorySections.map(renderSection)
            ) : (
              <Card className="p-8">
                <p className="text-muted-foreground text-center">
                  No main story sections available.
                </p>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="appendix" className="space-y-12">
            {appendixSections.length > 0 ? (
              appendixSections.map(renderSection)
            ) : (
              <Card className="p-8">
                <p className="text-muted-foreground text-center">
                  No appendix sections available.
                </p>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-16">
        <div className="max-w-5xl mx-auto px-6 py-6">
          <p className="text-center text-sm text-muted-foreground">
            {manifest.project_name} | Generated with KIE v3 | Story Manifest Dashboard
          </p>
        </div>
      </footer>
    </div>
  );
}
"""
        
        (src_dir / "Dashboard.tsx").write_text(dashboard_code)

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
