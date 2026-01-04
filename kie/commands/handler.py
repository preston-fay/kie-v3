"""
Command Handler System

Executes KIE v3 slash commands.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import yaml
import json
from datetime import datetime

from kie.interview import InterviewEngine
from kie.validation import ValidationPipeline, ValidationConfig
from kie.data import EDA, DataLoader, load_data
from kie.insights import InsightEngine, InsightCatalog
from kie.charts import ChartFactory
from kie.powerpoint import SlideBuilder


class CommandHandler:
    """
    Handles KIE v3 slash commands.

    Commands:
    - /startkie: Bootstrap new project
    - /status: Show project status
    - /interview: Start/continue requirements gathering
    - /validate: Run validation on outputs
    - /build: Build deliverables
    - /preview: Preview current outputs
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize command handler.

        Args:
            project_root: Project root directory (default: current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.spec_path = self.project_root / "project_state" / "spec.yaml"
        self.state_path = self.project_root / "project_state" / "status.json"

        # Apply saved theme if available (Codex requirement)
        from kie.config.theme_config import ProjectThemeConfig
        theme_config = ProjectThemeConfig(self.project_root)
        theme_config.apply_theme()  # Applies theme if set, does nothing if not

    def handle_startkie(self) -> Dict[str, Any]:
        """
        Handle /startkie command.

        Returns:
            Status dict
        """
        # Check if already a KIE project
        claude_md = self.project_root / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            if "KIE Project" in content:
                return {
                    "success": False,
                    "message": "This is already a KIE project (CLAUDE.md exists)",
                }

        # Check if in KIE repo
        if (self.project_root / "project_template").exists():
            return {
                "success": False,
                "message": "You're in the KIE repository itself - no need to bootstrap",
            }

        # Create folder structure
        folders = ["data", "outputs", "exports", "project_state"]
        for folder in folders:
            (self.project_root / folder).mkdir(exist_ok=True)

        # Create subdirectories
        (self.project_root / "outputs" / "charts").mkdir(exist_ok=True)
        (self.project_root / "outputs" / "tables").mkdir(exist_ok=True)
        (self.project_root / "outputs" / "maps").mkdir(exist_ok=True)
        (self.project_root / "project_state" / "validation_reports").mkdir(exist_ok=True)

        # Create .gitignore
        gitignore_content = """# Data files
data/*
!data/.gitkeep

# Outputs
outputs/*
!outputs/.gitkeep

# Exports
exports/*
!exports/.gitkeep

# Project state (keep structure, not content)
project_state/*.yaml
project_state/*.json
project_state/validation_reports/*

# Python
__pycache__/
*.pyc
.venv/
venv/

# Node
node_modules/
.next/
build/
dist/
"""

        (self.project_root / ".gitignore").write_text(gitignore_content)

        # Create README.md
        readme_content = """# KIE Project

## Quick Start

1. **Drop your data file** into the chat or `data/` folder
2. **Describe what you want** in plain English
3. **Let Claude (KIE)** create brand-compliant deliverables

That's it! Claude will guide you through the rest.

## Folder Structure

```
data/           - Put your data files here
outputs/        - Generated charts, tables, maps
  charts/       - Chart outputs
  tables/       - Table configurations
  maps/         - Map outputs
exports/        - Final deliverables (PPTX, etc.)
project_state/  - Project tracking
  spec.yaml     - Requirements (source of truth)
  status.json   - Build status
  validation_reports/ - QC reports
```

## Commands

- `/status` - Show project status
- `/interview` - Start requirements gathering
- `/validate` - Run quality checks
- `/build` - Build deliverables
- `/preview` - Preview outputs

## Tips

- Just describe what you need naturally
- Say "preview" to see what's been generated
- Say "export" when ready for final deliverables
- KIE enforces Kearney brand standards automatically
- All outputs are validated before delivery
"""

        (self.project_root / "README.md").write_text(readme_content)

        # Copy CLAUDE.md from KIE repo (don't hardcode - keep it in sync!)
        import shutil
        kie_repo_root = Path(__file__).parent.parent.parent  # Go up to kie-v3/
        source_claude_md = kie_repo_root / "CLAUDE.md"
        target_claude_md = self.project_root / "CLAUDE.md"

        if source_claude_md.exists():
            shutil.copy(source_claude_md, target_claude_md)
        else:
            # Fallback: create minimal CLAUDE.md if source doesn't exist
            target_claude_md.write_text("# KIE Project\n\nKIE (Kearney Insight Engine) v3 project.")

        # Copy slash commands from package (cross-platform compatible)
        import shutil
        kie_package_dir = Path(__file__).parent.parent  # kie/ package directory
        source_commands = kie_package_dir / "commands" / "slash_commands"
        target_commands = self.project_root / ".claude" / "commands"

        commands_copied = False
        if source_commands.exists():
            target_commands.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_commands, target_commands, dirs_exist_ok=True)
            commands_copied = True
        else:
            # Fallback: try repo location (for development)
            kie_repo_root = Path(__file__).parent.parent.parent  # Go up to kie-v3/
            source_commands_fallback = kie_repo_root / ".claude" / "commands"
            if source_commands_fallback.exists():
                target_commands.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source_commands_fallback, target_commands, dirs_exist_ok=True)
                commands_copied = True

        return {
            "success": True,
            "message": "KIE project structure created successfully",
            "folders_created": folders,
            "files_created": ["README.md", "CLAUDE.md", ".gitignore"],
            "commands_copied": commands_copied,
        }

    def handle_status(self, brief: bool = False) -> Dict[str, Any]:
        """
        Handle /status command.

        Args:
            brief: If True, return one-line summary

        Returns:
            Status dict
        """
        status = {
            "has_spec": self.spec_path.exists(),
            "has_data": any((self.project_root / "data").glob("*")),
            "outputs": {},
            "validation_reports": [],
        }

        # Load spec if exists
        if status["has_spec"]:
            with open(self.spec_path) as f:
                spec = yaml.safe_load(f)
                status["spec"] = spec

        # Check outputs
        outputs_dir = self.project_root / "outputs"
        if outputs_dir.exists():
            status["outputs"]["charts"] = len(list((outputs_dir / "charts").glob("*")))
            status["outputs"]["tables"] = len(list((outputs_dir / "tables").glob("*.json")))
            status["outputs"]["maps"] = len(list((outputs_dir / "maps").glob("*.html")))

        # Check exports
        exports_dir = self.project_root / "exports"
        if exports_dir.exists():
            status["exports"] = {
                "pptx": len(list(exports_dir.glob("*.pptx"))),
                "pdf": len(list(exports_dir.glob("*.pdf"))),
                "excel": len(list(exports_dir.glob("*.xlsx"))),
            }

        # Check validation reports
        reports_dir = self.project_root / "project_state" / "validation_reports"
        if reports_dir.exists():
            status["validation_reports"] = [f.name for f in reports_dir.glob("*.txt")]

        if brief:
            return {"brief_status": self._format_brief_status(status)}

        return status

    def _format_brief_status(self, status: Dict[str, Any]) -> str:
        """Format brief status line."""
        parts = []

        if status["has_spec"]:
            spec = status["spec"]
            parts.append(f"{spec['project_name']}")
            parts.append(f"({spec['project_type']})")

        if status.get("outputs"):
            outputs = status["outputs"]
            parts.append(
                f"Outputs: {outputs.get('charts', 0)} charts, {outputs.get('tables', 0)} tables"
            )

        if not parts:
            parts.append("No project initialized")

        return " | ".join(parts)

    def handle_interview(self) -> Dict[str, Any]:
        """
        Handle /interview command.

        Returns:
            Interview state
        """
        interview = InterviewEngine(
            state_path=self.project_root / "project_state" / "interview_state.yaml"
        )

        state = interview.state

        return {
            "complete": state.is_complete(),
            "completion_percentage": state.get_completion_percentage(),
            "missing_fields": state.get_missing_required_fields(),
            "spec": state.spec.model_dump() if state.spec else None,
        }

    def handle_validate(self, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle /validate command.

        Args:
            target: Specific target to validate (chart/table/slide path)

        Returns:
            Validation results
        """
        pipeline = ValidationPipeline(
            ValidationConfig(
                strict=True,
                save_reports=True,
                report_dir=self.project_root / "project_state" / "validation_reports",
            )
        )

        # Get summary of all reports
        summary = pipeline.get_pipeline_summary()

        return {
            "total_reports": summary["total_reports"],
            "passed": summary["passed"],
            "failed": summary["failed"],
            "pass_rate": summary["pass_rate"],
            "total_issues": summary["total_issues"],
        }

    def handle_build(self, target: str = "all") -> Dict[str, Any]:
        """
        Handle /build command.

        Args:
            target: What to build ('all', 'charts', 'presentation', 'dashboard')

        Returns:
            Build results
        """
        if not self.spec_path.exists():
            return {
                "success": False,
                "message": "No spec.yaml found. Run /interview first.",
            }

        # Load spec
        with open(self.spec_path) as f:
            spec = yaml.safe_load(f)

        # CRITICAL: Check theme is set before building (Codex requirement)
        from kie.config.theme_config import ProjectThemeConfig
        theme_config = ProjectThemeConfig(self.project_root)
        theme_mode = theme_config.load_theme()

        if theme_mode is None:
            return {
                "success": False,
                "message": "❌ Theme preference required. Run /interview and select dark or light mode.",
            }

        # Update status
        status = {
            "started_at": datetime.now().isoformat(),
            "target": target,
            "status": "building",
        }

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(status, f, indent=2)

        try:
            results = {}

            # Build dashboard FIRST (generates Recharts HTML)
            # This is what users actually want to see!
            if target in ["all", "dashboard", "charts"]:
                dashboard_path = self._build_dashboard(spec)
                results["dashboard"] = str(dashboard_path)
                results["message"] = f"Dashboard built at {dashboard_path}. Open index.html in browser or run 'npm install && npm run dev'"

            # Build presentation if requested
            if target in ["all", "presentation"]:
                pres_path = self._build_presentation(spec)
                results["presentation"] = str(pres_path)

            # Update status
            status["status"] = "completed"
            status["completed_at"] = datetime.now().isoformat()
            with open(self.state_path, "w") as f:
                json.dump(status, f, indent=2)

            return {
                "success": True,
                "message": f"Build completed successfully",
                "outputs": results,
            }

        except Exception as e:
            status["status"] = "failed"
            status["error"] = str(e)
            with open(self.state_path, "w") as f:
                json.dump(status, f, indent=2)

            return {
                "success": False,
                "message": f"Build failed: {str(e)}",
            }

    def _build_presentation(self, spec: Dict[str, Any]) -> Path:
        """
        Build PowerPoint presentation from spec and insights.

        Args:
            spec: Project specification

        Returns:
            Path to generated presentation
        """
        # Load insights if available
        insights_path = self.project_root / "outputs" / "insights.yaml"
        insights = []
        if insights_path.exists():
            catalog = InsightCatalog.load(str(insights_path))
            insights = catalog.insights

        # Create presentation
        builder = SlideBuilder(title=spec.get("project_name", "Analysis"))

        # Title slide
        builder.add_title_slide(
            title=spec.get("project_name", "Analysis"),
            subtitle=spec.get("description", ""),
            author=spec.get("client_name", ""),
            date=datetime.now().strftime("%B %Y"),
        )

        # Add insights as content slides
        if insights:
            for insight in insights[:10]:  # Limit to top 10 insights
                # Build bullet points from insight attributes
                bullet_points = [insight.supporting_text or ""]

                # Add confidence and severity info
                if insight.confidence:
                    bullet_points.append(f"Confidence: {insight.confidence:.0%}")
                if insight.statistical_significance:
                    bullet_points.append(f"Statistical Significance: p={insight.statistical_significance:.3f}")

                builder.add_content_slide(
                    title=insight.headline,
                    bullet_points=bullet_points,
                    notes=f"Insight Type: {insight.insight_type.value}, Severity: {insight.severity.value}",
                )
        else:
            # Add placeholder content
            builder.add_content_slide(
                title="Key Findings",
                bullet_points=["Run /analyze to extract insights from your data"],
            )

        # Save presentation
        exports_dir = self.project_root / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)

        output_path = exports_dir / f"{spec.get('project_name', 'presentation').replace(' ', '_')}.pptx"
        builder.save(str(output_path))

        return output_path

    def _build_dashboard(self, spec: Dict[str, Any]) -> Path:
        """
        Build Streamlit dashboard from spec and data.

        Args:
            spec: Project specification

        Returns:
            Path to generated dashboard
        """
        from kie.export.react_builder import ReactDashboardBuilder

        # Find data file
        data_dir = self.project_root / "data"
        data_files = list(data_dir.glob("*.csv"))

        if not data_files:
            raise ValueError("No CSV data files found in data/ directory")

        data_path = data_files[0]

        # PHASE 3+4+5: Apply FULL INTELLIGENCE (same as handle_analyze)
        loader = DataLoader()
        loader.load(data_path)  # Auto-infers schema
        schema = loader.schema

        # Read spec for overrides and objective
        objective = ''
        column_overrides = {}
        if self.spec_path.exists():
            import yaml
            with open(self.spec_path) as f:
                spec_yaml = yaml.safe_load(f)
                if spec_yaml:
                    objective = spec_yaml.get('objective', '')
                    column_overrides = spec_yaml.get('column_mapping', {})

        # Apply objective-driven intelligence
        objective_lower = objective.lower()
        if any(term in objective_lower for term in ['revenue growth', 'sales growth', 'profit growth', 'growth', 'revenue', 'sales', 'income']):
            metric_request = 'revenue'
        elif any(term in objective_lower for term in ['spend', 'cost', 'expense', 'budget', 'overhead']):
            metric_request = 'spend'
        elif any(term in objective_lower for term in ['efficiency', 'margin', 'rate', 'ratio', 'profitability']):
            metric_request = 'efficiency'
        else:
            metric_request = 'revenue'

        # Get intelligent column mapping (with overrides!)
        required_cols = [metric_request, 'category', 'date']
        column_mapping = loader.suggest_column_mapping(required_cols, overrides=column_overrides)

        # Build dashboard with INTELLIGENT column selection (Phase 5!)
        builder = ReactDashboardBuilder(
            project_name=spec.get("project_name", "Dashboard"),
            client_name=spec.get("client_name", "Client"),
            objective=spec.get("objective", "Analysis"),
            data_schema=schema,
            column_mapping=column_mapping  # Phase 5: Pass intelligent selections + overrides
        )

        # Output directory
        exports_dir = self.project_root / "exports" / "dashboard"

        # Charts directory
        charts_dir = self.project_root / "outputs" / "charts"

        # Build React dashboard (KDS COMPLIANT)
        dashboard_path = builder.build_dashboard(
            data_path=data_path,
            charts_dir=charts_dir,
            output_dir=exports_dir,
            theme_mode=spec.get("preferences", {}).get("theme", {}).get("mode", "dark")
        )

        return dashboard_path

    def handle_eda(self, data_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle /eda command - run exploratory data analysis.

        Args:
            data_file: Specific file to analyze (default: auto-detect from data/)

        Returns:
            EDA results
        """
        # Find data file
        if not data_file:
            data_dir = self.project_root / "data"
            data_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
            if not data_files:
                return {
                    "success": False,
                    "message": "No data files found in data/ folder",
                }
            data_file = str(data_files[0])
        else:
            data_file = str(self.project_root / data_file)

        # Run EDA
        try:
            eda = EDA()
            profile = eda.analyze(data_file)

            # Save profile
            profile_path = self.project_root / "outputs" / "eda_profile.yaml"
            profile_path.parent.mkdir(parents=True, exist_ok=True)

            import yaml
            with open(profile_path, "w") as f:
                yaml.dump(profile.to_dict(), f, default_flow_style=False)

            # Get suggestions
            suggestions = eda.suggest_analysis()

            return {
                "success": True,
                "profile": profile.to_dict(),
                "suggestions": suggestions,
                "profile_saved": str(profile_path),
                "data_file": data_file,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"EDA failed: {str(e)}",
            }

    def handle_analyze(self, data_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle /analyze command - extract insights from data.

        Args:
            data_file: Specific file to analyze (default: auto-detect from data/)

        Returns:
            Insights results
        """
        # Find data file
        if not data_file:
            data_dir = self.project_root / "data"
            data_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
            if not data_files:
                return {
                    "success": False,
                    "message": "No data files found in data/ folder",
                }
            data_file = str(data_files[0])
        else:
            data_file = str(self.project_root / data_file)

        try:
            # CENTRALIZED INTELLIGENCE: Use DataLoader as the single source of truth
            from pathlib import Path
            loader = DataLoader()
            df = loader.load(Path(data_file))  # This auto-infers schema

            # Get schema from loader (already inferred during load)
            schema = loader.schema
            if not schema:
                return {
                    "success": False,
                    "message": "Could not infer schema from data",
                }

            # Use intelligent column mapping to find key metrics
            # Phase 3+4: DYNAMIC semantic hints based on project objective
            # Phase 5: HUMAN OVERRIDE - read explicit column_mapping from spec
            objective = ''
            column_overrides = {}
            if self.spec_path.exists():
                import yaml
                with open(self.spec_path) as f:
                    spec = yaml.safe_load(f)
                    if spec:
                        objective = spec.get('objective', '')
                        # Phase 5: Read explicit column mappings (God Mode)
                        column_overrides = spec.get('column_mapping', {})

            # OBJECTIVE-DRIVEN INTELLIGENCE:
            # Pass a semantic request that matches the objective
            objective_lower = objective.lower()

            # Determine what type of metric to request based on objective
            # Check growth/revenue terms first (most specific)
            if any(term in objective_lower for term in ['revenue growth', 'sales growth', 'profit growth', 'growth', 'revenue', 'sales', 'income']):
                # Request growth/revenue metrics
                metric_request = 'revenue'
            # Then check spend/cost terms
            elif any(term in objective_lower for term in ['spend', 'cost', 'expense', 'budget', 'overhead']):
                # Request spend metrics - triggers prefer_spend in loader
                metric_request = 'spend'
            # Then check efficiency/margin terms
            elif any(term in objective_lower for term in ['efficiency', 'margin', 'rate', 'ratio', 'profitability']):
                # Request efficiency metrics - triggers prefer_percentage in loader
                metric_request = 'efficiency'
            else:
                # Default to growth/revenue metrics
                metric_request = 'revenue'

            # Request the appropriate metric type + supporting columns
            required_cols = [metric_request, 'category', 'date']
            # Phase 5: Pass overrides to loader - they take absolute precedence
            mapping = loader.suggest_column_mapping(required_cols, overrides=column_overrides)

            # Extract mapped columns
            value_column = mapping.get(metric_request)
            group_column = mapping.get('category')
            time_column = mapping.get('date')

            # Fallback: if no mapping found, use first available columns
            if not value_column and schema.numeric_columns:
                value_column = schema.numeric_columns[0]
            if not group_column and schema.categorical_columns:
                group_column = schema.categorical_columns[0]

            if not value_column:
                return {
                    "success": False,
                    "message": "No numeric columns found for analysis",
                }

            # Extract insights using the intelligently mapped columns
            engine = InsightEngine()
            insights = engine.auto_extract(
                df,
                value_column=value_column,
                group_column=group_column,
                time_column=time_column
            )

            # Build catalog
            catalog = engine.build_catalog(
                insights,
                business_question="What are the key findings from this data?"
            )

            # Save catalog
            catalog_path = self.project_root / "outputs" / "insights.yaml"
            catalog_path.parent.mkdir(parents=True, exist_ok=True)
            catalog.save(str(catalog_path))

            # PHASE 6: AUTO-MAP GENERATION
            # Detect geospatial columns and automatically generate maps
            from kie.geo.maps.folium_builder import create_us_choropleth, create_marker_map
            from datetime import datetime

            map_path = None
            map_type = None

            try:
                # Detect geo columns explicitly (name-based matching)
                geo_mapping = {}

                # State detection
                state_keywords = ['state', 'st', 'state_abbr', 'state_code']
                for col in loader.schema.columns:
                    col_lower = col.lower()
                    if any(kw == col_lower or kw in col_lower for kw in state_keywords):
                        geo_mapping['state'] = col
                        break

                # Lat/Lon detection (must be numeric with coordinate-like names)
                lat_keywords = ['latitude', 'lat', 'lat_deg', 'y']
                lon_keywords = ['longitude', 'lon', 'lng', 'long', 'lon_deg', 'x']

                for col in loader.schema.numeric_columns:
                    col_lower = col.lower()
                    if not geo_mapping.get('latitude') and any(kw in col_lower for kw in lat_keywords):
                        geo_mapping['latitude'] = col
                    if not geo_mapping.get('longitude') and any(kw in col_lower for kw in lon_keywords):
                        geo_mapping['longitude'] = col

                # Generate map ONLY if geo data found (don't generate garbage!)
                has_latlon = geo_mapping.get('latitude') and geo_mapping.get('longitude')
                has_state = geo_mapping.get('state')

                if has_latlon or has_state:
                    # Validate that coordinates look reasonable if lat/lon
                    if has_latlon:
                        lat_values = df[geo_mapping['latitude']].dropna()
                        lon_values = df[geo_mapping['longitude']].dropna()
                        # Skip if coordinates are clearly invalid (all zeros, out of range, etc.)
                        if len(lat_values) == 0 or len(lon_values) == 0:
                            raise ValueError("Latitude/longitude columns are empty")
                        if lat_values.abs().max() > 90 or lon_values.abs().max() > 180:
                            raise ValueError("Latitude/longitude values out of valid range")
                        if lat_values.std() < 0.01 and lon_values.std() < 0.01:
                            raise ValueError("Coordinates have no variance (all same location)")

                    # Only proceed if validation passed
                    maps_dir = self.project_root / "outputs" / "maps"
                    maps_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                    if has_latlon:
                        # Create marker map
                        popup_cols = [col for col in loader.schema.columns
                                     if col not in [geo_mapping['latitude'], geo_mapping['longitude']]][:3]

                        map_builder = create_marker_map(
                            data=df,
                            latitude_col=geo_mapping['latitude'],
                            longitude_col=geo_mapping['longitude'],
                            popup_cols=popup_cols,
                            cluster=True
                        )

                        map_path = maps_dir / f"auto_map_{timestamp}.html"
                        map_builder.save(str(map_path))
                        map_type = "marker"

                    elif has_state:
                        # Create US choropleth
                        # Use intelligent value selection (prefer the metric we already found)
                        value_col = value_column  # Already intelligently selected above

                        map_builder = create_us_choropleth(
                            data=df,
                            value_column=value_col,
                            key_column=geo_mapping['state'],
                            title=f"{value_col} by State"
                        )

                        map_path = maps_dir / f"auto_map_{timestamp}.html"
                        map_builder.save(str(map_path))
                        map_type = "choropleth"

            except Exception as map_error:
                # Map generation is optional - don't fail the whole analysis
                pass

            result = {
                "success": True,
                "insights_count": len(insights),
                "catalog_saved": str(catalog_path),
                "data_file": data_file,
                "insights": [
                    {
                        "type": i.insight_type.value,
                        "headline": i.headline,
                        "confidence": i.confidence,
                        "severity": i.severity.value,
                    }
                    for i in insights[:5]  # Return top 5
                ],
            }

            # Add map info if generated
            if map_path:
                result["map_generated"] = str(map_path)
                result["map_type"] = map_type

            return result

        except Exception as e:
            return {
                "success": False,
                "message": f"Analysis failed: {str(e)}",
            }

    def handle_preview(self, launch_server: bool = True) -> Dict[str, Any]:
        """
        Handle /preview command - preview outputs in React dashboard.

        Args:
            launch_server: Whether to launch React dev server (default True)

        Returns:
            Preview information with server status
        """
        status = self.handle_status()

        # List available outputs
        previews = {
            "charts": [],
            "tables": [],
            "maps": [],
            "exports": [],
        }

        outputs_dir = self.project_root / "outputs"

        if (outputs_dir / "charts").exists():
            previews["charts"] = [f.name for f in (outputs_dir / "charts").glob("*")]

        if (outputs_dir / "tables").exists():
            previews["tables"] = [f.name for f in (outputs_dir / "tables").glob("*.json")]

        if (outputs_dir / "maps").exists():
            previews["maps"] = [f.name for f in (outputs_dir / "maps").glob("*.html")]

        exports_dir = self.project_root / "exports"
        if exports_dir.exists():
            previews["exports"] = [f.name for f in exports_dir.glob("*")]

        # Launch React dashboard if requested
        dashboard_url = None
        if launch_server:
            # Check if web exists (should be in kie-v3 repo)
            web_dir = Path(__file__).parent.parent.parent / "web"
            if web_dir.exists():
                dashboard_url = "http://localhost:5173"
                previews["dashboard_instruction"] = f"Run 'cd {web_dir} && npm run dev' to launch React dashboard"
            else:
                previews["dashboard_instruction"] = "React dashboard not found (web/ directory missing)"

        return {
            **previews,
            "dashboard_url": dashboard_url,
            "total_outputs": sum([
                len(previews["charts"]),
                len(previews["tables"]),
                len(previews["maps"]),
                len(previews["exports"]),
            ]),
        }

    def handle_spec(self) -> Dict[str, Any]:
        """
        Handle /spec command - show current specification.

        Returns:
            Specification dict
        """
        if not self.spec_path.exists():
            return {
                "success": False,
                "message": "No spec.yaml found. Run /interview to create one.",
            }

        with open(self.spec_path) as f:
            spec = yaml.safe_load(f)

        return {
            "success": True,
            "spec": spec,
        }

    def handle_map(self, data_file: Optional[str] = None, map_type: str = 'auto') -> Dict[str, Any]:
        """
        Handle /map command - create geographic visualizations.

        Args:
            data_file: Specific file to visualize (default: auto-detect from data/)
            map_type: Type of map ('auto', 'choropleth', 'marker', 'heatmap')

        Returns:
            Map generation results with file path
        """
        from kie.geo.maps.folium_builder import create_us_choropleth, create_marker_map
        from datetime import datetime

        # Find data file
        if not data_file:
            data_dir = self.project_root / "data"
            data_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
            if not data_files:
                return {
                    "success": False,
                    "message": "No data files found in data/ folder",
                }
            data_file = str(data_files[0])
        else:
            data_file = str(self.project_root / data_file)

        try:
            # Load data with intelligence
            loader = DataLoader()
            df = loader.load(Path(data_file))

            # Detect geo columns explicitly (don't use suggest_column_mapping for geo!)
            # For geo columns, we need exact/fuzzy name matches, not semantic intelligence
            mapping = {}

            # State detection (case-insensitive, exact/fuzzy match)
            state_keywords = ['state', 'st', 'state_abbr', 'state_code']
            for col in loader.schema.columns:
                col_lower = col.lower()
                if any(kw == col_lower or kw in col_lower for kw in state_keywords):
                    mapping['state'] = col
                    break

            # Lat/Lon detection (must be numeric AND have coordinate-like names)
            lat_keywords = ['latitude', 'lat', 'lat_deg', 'y']
            lon_keywords = ['longitude', 'lon', 'lng', 'long', 'lon_deg', 'x']

            for col in loader.schema.numeric_columns:
                col_lower = col.lower()
                if not mapping.get('latitude') and any(kw in col_lower for kw in lat_keywords):
                    mapping['latitude'] = col
                if not mapping.get('longitude') and any(kw in col_lower for kw in lon_keywords):
                    mapping['longitude'] = col

            # Determine map type based on available columns
            has_latlon = mapping.get('latitude') and mapping.get('longitude')
            has_state = mapping.get('state')

            if map_type == 'auto':
                if has_latlon:
                    map_type = 'marker'
                elif has_state:
                    map_type = 'choropleth'
                else:
                    return {
                        "success": False,
                        "message": "⚠️  No geospatial data found. Cannot generate map.",
                        "hint": "Your data needs either:\n  • 'state' column (for US choropleth)\n  • 'latitude' and 'longitude' columns (for marker map)\n\nColumn names detected: " + ", ".join(loader.schema.columns[:20]) + ("..." if len(loader.schema.columns) > 20 else ""),
                        "skip_map": True
                    }

            # Create output directory
            maps_dir = self.project_root / "outputs" / "maps"
            maps_dir.mkdir(parents=True, exist_ok=True)

            # Generate map based on type
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if map_type == 'choropleth' and has_state:
                # Find a value column (prefer revenue/value metrics)
                value_candidates = ['revenue', 'value', 'amount', 'total', 'count']
                value_mapping = loader.suggest_column_mapping(value_candidates)
                value_col = value_mapping.get('revenue') or value_mapping.get('value')

                if not value_col and loader.schema.numeric_columns:
                    value_col = loader.schema.numeric_columns[0]

                if not value_col:
                    return {
                        "success": False,
                        "message": "No value column found for choropleth",
                    }

                # Create choropleth
                map_builder = create_us_choropleth(
                    data=df,
                    value_column=value_col,
                    key_column=mapping['state'],
                    title=f"{value_col} by State"
                )

                output_path = maps_dir / f"choropleth_{timestamp}.html"
                map_builder.save(str(output_path))

                return {
                    "success": True,
                    "message": f"US Choropleth map created",
                    "map_path": str(output_path),
                    "map_type": "choropleth",
                    "columns_used": {
                        "state": mapping['state'],
                        "value": value_col
                    }
                }

            elif map_type == 'marker' and has_latlon:
                # Create marker map
                popup_cols = [col for col in loader.schema.columns if col not in [mapping['latitude'], mapping['longitude']]][:3]

                map_builder = create_marker_map(
                    data=df,
                    latitude_col=mapping['latitude'],
                    longitude_col=mapping['longitude'],
                    popup_cols=popup_cols,
                    cluster=True
                )

                output_path = maps_dir / f"markers_{timestamp}.html"
                map_builder.save(str(output_path))

                return {
                    "success": True,
                    "message": f"Marker map created with {len(df)} points",
                    "map_path": str(output_path),
                    "map_type": "marker",
                    "columns_used": {
                        "latitude": mapping['latitude'],
                        "longitude": mapping['longitude']
                    }
                }

            else:
                return {
                    "success": False,
                    "message": f"Cannot create {map_type} map with available data",
                    "available_columns": loader.schema.columns
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Map creation failed: {str(e)}",
            }
