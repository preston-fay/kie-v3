"""
Simplified React Dashboard Builder for KIE v3 - FULLY DATA-AGNOSTIC
Generates dashboards that work with ANY data structure
"""

import json
from pathlib import Path

from kie.data.loader import DataSchema


class ReactDashboardBuilderV2:
    """Build data-agnostic React dashboards."""

    def __init__(
        self,
        project_name: str,
        objective: str,
        data_schema: DataSchema
    ):
        self.project_name = project_name
        self.objective = objective
        self.schema = data_schema

    def build_dashboard(
        self,
        data_path: Path,
        output_dir: Path,
    ) -> Path:
        """Build dashboard with actual data inspection."""
        # Create structure
        src_dir = output_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        public_dir = output_dir / "public"
        public_dir.mkdir(parents=True, exist_ok=True)

        # Copy data
        import shutil
        if data_path.suffix.lower() == '.csv':
            shutil.copy(data_path, public_dir / "data.csv")
        else:
            # Convert to CSV
            from kie.data.loader import DataLoader
            loader = DataLoader()
            df = loader.load(data_path)
            df.to_csv(public_dir / "data.csv", index=False)

        # Generate files
        self._write_package_json(output_dir)
        self._write_vite_config(output_dir)
        self._write_tsconfig(output_dir)
        self._write_tailwind_config(output_dir)
        self._write_postcss_config(output_dir)
        self._write_index_html(output_dir)
        self._write_index_css(src_dir)
        self._write_main_tsx(src_dir)
        self._write_dashboard_tsx(src_dir)

        return output_dir

    def _write_package_json(self, output_dir: Path):
        pkg = {
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
                "papaparse": "^5.4.1",
                "tailwindcss": "^3.4.19"
            },
            "devDependencies": {
                "@types/react": "^19.2.5",
                "@types/react-dom": "^19.2.3",
                "@types/papaparse": "^5.3.14",
                "@vitejs/plugin-react": "^5.1.1",
                "typescript": "~5.9.3",
                "vite": "^7.2.4",
                "postcss": "^8.5.6",
                "autoprefixer": "^10.4.23"
            }
        }
        (output_dir / "package.json").write_text(json.dumps(pkg, indent=2))

    def _write_vite_config(self, output_dir: Path):
        content = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
"""
        (output_dir / "vite.config.ts").write_text(content)

    def _write_tsconfig(self, output_dir: Path):
        config = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True
            },
            "include": ["src"],
            "references": [{"path": "./tsconfig.node.json"}]
        }
        (output_dir / "tsconfig.json").write_text(json.dumps(config, indent=2))

    def _write_tailwind_config(self, output_dir: Path):
        content = """/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#7823DC',
        'primary-light': '#9B4DCA',
      },
    },
  },
  plugins: [],
}
"""
        (output_dir / "tailwind.config.js").write_text(content)

    def _write_postcss_config(self, output_dir: Path):
        content = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
        (output_dir / "postcss.config.js").write_text(content)

    def _write_index_html(self, output_dir: Path):
        content = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{self.project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
        (output_dir / "index.html").write_text(content)

    def _write_index_css(self, src_dir: Path):
        content = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: 'Inter', system-ui, sans-serif;
  background-color: #1E1E1E;
  color: #FFFFFF;
}
"""
        (src_dir / "index.css").write_text(content)

    def _write_main_tsx(self, src_dir: Path):
        content = """import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import Dashboard from './Dashboard'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Dashboard />
  </StrictMode>,
)
"""
        (src_dir / "main.tsx").write_text(content)

    def _write_dashboard_tsx(self, src_dir: Path):
        # Generate TypeScript interface
        interface_lines = ["interface DataRow {"]
        for col in self.schema.columns:
            col_type = "number" if col in self.schema.numeric_columns else "string"
            interface_lines.append(f"  '{col}': {col_type};")
        interface_lines.append("}")
        ts_interface = "\n".join(interface_lines)

        # Get column info
        numeric_cols = self.schema.numeric_columns
        categorical_cols = self.schema.categorical_columns

        content = f"""/**
 * {self.project_name}
 * Generated by KIE v3
 */

import {{ useState, useEffect }} from 'react';
import Papa from 'papaparse';

{ts_interface}

export default function Dashboard() {{
  const [data, setData] = useState<DataRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {{
    fetch('/data.csv')
      .then(res => res.text())
      .then(csvText => {{
        Papa.parse(csvText, {{
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true,
          complete: (results) => {{
            setData(results.data as DataRow[]);
            setLoading(false);
          }},
          error: (error) => {{
            console.error('CSV parsing error:', error);
            setLoading(false);
          }}
        }});
      }})
      .catch(err => {{
        console.error('Fetch error:', err);
        setLoading(false);
      }});
  }}, []);

  if (loading) {{
    return <div className="p-6 text-white">Loading...</div>;
  }}

  // Calculate stats
  const rowCount = data.length;
  const numericSummary = {{}};

  return (
    <div className="min-h-screen bg-[#1E1E1E] p-6 text-white">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2" style={{{{color: '#7823DC'}}}}>
          {self.project_name}
        </h1>
        <p className="text-gray-400">{self.objective}</p>
      </div>

      <div className="mb-6 p-6 bg-[#2A2A2A] rounded-lg">
        <h2 className="text-xl font-bold mb-4">Data Overview</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-gray-400 text-sm">Total Rows</p>
            <p className="text-2xl font-bold">{{{"row_count"}}}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Columns</p>
            <p className="text-2xl font-bold">{len(self.schema.columns)}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Numeric</p>
            <p className="text-2xl font-bold">{len(numeric_cols)}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Categorical</p>
            <p className="text-2xl font-bold">{len(categorical_cols)}</p>
          </div>
        </div>
      </div>

      <div className="p-6 bg-[#2A2A2A] rounded-lg overflow-auto">
        <h2 className="text-xl font-bold mb-4">Data Table</h2>
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-700">
              {{{self._generate_column_headers()}}}
            </tr>
          </thead>
          <tbody>
            {{data.slice(0, 100).map((row, i) => (
              <tr key={{i}} className="border-b border-gray-800 hover:bg-[#333333]">
                {{{self._generate_row_cells()}}}
              </tr>
            ))}}
          </tbody>
        </table>
        {{data.length > 100 && (
          <p className="mt-4 text-gray-400 text-sm">
            Showing first 100 of {{data.length}} rows
          </p>
        )}}
      </div>
    </div>
  );
}}
"""
        (src_dir / "Dashboard.tsx").write_text(content)

    def _generate_column_headers(self) -> str:
        """Generate table header JSX."""
        headers = []
        for col in self.schema.columns:
            headers.append(f"<th className='px-4 py-2 text-left'>{col}</th>")
        return "\n              ".join(headers)

    def _generate_row_cells(self) -> str:
        """Generate table row JSX."""
        cells = []
        for col in self.schema.columns:
            safe_col = col.replace("'", "\\'")
            cells.append(f"<td className='px-4 py-2'>{{row['{safe_col}']}}</td>")
        return "\n                ".join(cells)
