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

        # Create CLAUDE.md (project-specific instructions)
        claude_md_content = """# KIE Project

You are working in a **KIE (Kearney Insight Engine) v3 project**.

## Startup Behavior

When this project opens:
1. Check for data files in `data/`
2. Check for existing `project_state/spec.yaml`
3. Greet appropriately:
   - **New project (no data)**: "Welcome! Drop a data file or describe what you're working on."
   - **Has data, no spec**: "I see [filename]. What would you like to analyze?"
   - **Has spec**: "Welcome back! Here's where we left off: [summary]"

## KIE v3 Capabilities

- **Charts**: 25+ chart types including maps, waterfalls, bullets
- **Tables**: Smart tables with auto-formatting and sparklines
- **PowerPoint**: Native, editable charts in slides
- **Dashboards**: React components with Recharts
- **Validation**: Comprehensive QC system prevents bad outputs
- **Themes**: Dark and light modes

## Commands Available

- `/status` - Show project status
- `/interview` - Requirements gathering
- `/validate` - Run QC checks
- `/build` - Build deliverables

## Workflow

1. **Understand**: Gather requirements through `/interview`
2. **Analyze**: Load data, find insights
3. **Visualize**: Create brand-compliant charts/tables/maps
4. **Validate**: Run QC to ensure safety
5. **Deliver**: Package into final deliverable format

## Critical Rules

- ALWAYS use `kie` modules (not old `core`)
- ALWAYS validate outputs before delivery
- NEVER use forbidden green colors
- ALWAYS enforce KDS brand compliance
- NEVER deliver synthetic/test data to consultants
"""

        (self.project_root / "CLAUDE.md").write_text(claude_md_content)

        return {
            "success": True,
            "message": "KIE project structure created successfully",
            "folders_created": folders,
            "files_created": ["README.md", "CLAUDE.md", ".gitignore"],
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
            target: What to build ('all', 'charts', 'presentation', etc.)

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

            # Build presentation (default)
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
                builder.add_content_slide(
                    title=insight.headline,
                    bullet_points=[
                        insight.supporting_text or "",
                        f"Significance: {insight.significance}",
                    ],
                    notes=insight.recommendation or "",
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

        # Load data
        try:
            import pandas as pd
            df = pd.read_csv(data_file) if data_file.endswith('.csv') else pd.read_excel(data_file)

            # Extract insights
            engine = InsightEngine()
            insights = engine.auto_extract(df)

            # Build catalog
            catalog = engine.build_catalog(
                insights,
                question="What are the key findings from this data?"
            )

            # Save catalog
            catalog_path = self.project_root / "outputs" / "insights.yaml"
            catalog_path.parent.mkdir(parents=True, exist_ok=True)
            catalog.save(str(catalog_path))

            return {
                "success": True,
                "insights_count": len(insights),
                "catalog_saved": str(catalog_path),
                "data_file": data_file,
                "insights": [
                    {
                        "type": i.type,
                        "headline": i.headline,
                        "significance": i.significance,
                    }
                    for i in insights[:5]  # Return top 5
                ],
            }

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
            # Check if web_v3 exists (should be in kie-v3 repo)
            web_dir = Path(__file__).parent.parent.parent / "web_v3"
            if web_dir.exists():
                dashboard_url = "http://localhost:5173"
                previews["dashboard_instruction"] = f"Run 'cd {web_dir} && npm run dev' to launch React dashboard"
            else:
                previews["dashboard_instruction"] = "React dashboard not found (web_v3/ directory missing)"

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
