"""
Command Handler System

Executes KIE v3 slash commands.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from kie.data import EDA, DataLoader
from kie.insights import InsightCatalog, InsightEngine
from kie.powerpoint import SlideBuilder
from kie.validation import ValidationConfig, ValidationPipeline

# Observability imports (STEP 1: OBSERVABILITY)
try:
    from kie.observability import EvidenceLedger, ObservabilityHooks, create_ledger
    HAS_OBSERVABILITY = True
except ImportError:
    HAS_OBSERVABILITY = False

# Enforcement imports (STEP 2: ENFORCEMENT)
try:
    from kie.observability import PolicyEngine, generate_recovery_message
    HAS_ENFORCEMENT = True
except ImportError:
    HAS_ENFORCEMENT = False


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

    def __init__(self, project_root: Path | None = None):
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

        # Initialize observability (STEP 1: OBSERVABILITY)
        self._observability_enabled = HAS_OBSERVABILITY and os.getenv("KIE_DISABLE_OBSERVABILITY") != "1"
        if self._observability_enabled:
            self._obs_hooks = ObservabilityHooks(self.project_root)
        else:
            self._obs_hooks = None

        # Initialize enforcement (STEP 2: ENFORCEMENT)
        self._enforcement_enabled = HAS_ENFORCEMENT and os.getenv("KIE_DISABLE_ENFORCEMENT") != "1"
        if self._enforcement_enabled:
            self._policy_engine = PolicyEngine(self.project_root)
        else:
            self._policy_engine = None

    def _build_policy_context(self) -> dict[str, Any]:
        """
        Build context for policy evaluation.

        Returns:
            Context dictionary with workspace state
        """
        context = {}

        # Check for spec
        spec_path = self.project_root / "project_state" / "spec.yaml"
        context["has_spec"] = spec_path.exists()

        # Check for data
        data_dir = self.project_root / "data"
        if data_dir.exists():
            data_files = [
                f for f in data_dir.iterdir()
                if f.is_file() and f.name != ".gitkeep"
            ]
            context["has_data"] = len(data_files) > 0
        else:
            context["has_data"] = False

        return context

    def _with_observability(
        self,
        command: str,
        args: dict[str, Any],
        executor: callable
    ) -> dict[str, Any]:
        """
        Execute a command with observability hooks and enforcement.

        STEP 1: Observability hooks observe state (never fail commands)
        STEP 2: Enforcement policies block INVALID actions only

        Args:
            command: Command name
            args: Command arguments
            executor: Function to execute (returns result dict)

        Returns:
            Command result dictionary
        """
        ledger = None

        try:
            if self._observability_enabled:
                # Create ledger
                ledger = create_ledger(command, args, self.project_root)

                # Pre-command hook (STEP 1: OBSERVABILITY)
                self._obs_hooks.pre_command(ledger, command, args)

        except Exception as e:
            # Log but do not fail
            print(f"Warning: Observability pre-command failed: {e}")

        # STEP 2: Evaluate preconditions (ENFORCEMENT)
        if self._enforcement_enabled and self._policy_engine:
            try:
                # Read current Rails stage
                rails_state_path = self.project_root / "project_state" / "rails_state.json"
                current_stage = None
                if rails_state_path.exists():
                    rails_state = json.loads(rails_state_path.read_text())
                    current_stage = rails_state.get("current_stage")

                # Build context
                context = self._build_policy_context()

                # Evaluate preconditions
                policy_result = self._policy_engine.evaluate_preconditions(
                    command, current_stage, context
                )

                # If blocked, return error immediately WITHOUT executing
                if policy_result.is_blocked:
                    # Record block in ledger
                    if ledger:
                        ledger.success = False
                        ledger.errors.append(policy_result.message)
                        if policy_result.violated_invariant:
                            ledger.proof_references["violated_invariant"] = policy_result.violated_invariant
                        if policy_result.missing_prerequisite:
                            ledger.proof_references["missing_prerequisite"] = policy_result.missing_prerequisite

                        # Save ledger
                        ledger_dir = self.project_root / "project_state" / "evidence_ledger"
                        ledger.save(ledger_dir)

                    # Generate and print recovery message
                    recovery_msg = generate_recovery_message(policy_result)
                    print(recovery_msg)

                    # Return error result
                    return {
                        "success": False,
                        "errors": [policy_result.message],
                        "violated_invariant": policy_result.violated_invariant,
                        "missing_prerequisite": policy_result.missing_prerequisite,
                        "recovery_steps": policy_result.recovery_steps,
                        "evidence_ledger_id": ledger.run_id if ledger else None,
                    }

            except Exception as e:
                # Enforcement failures do not block commands
                print(f"Warning: Enforcement precondition check failed: {e}")

        # Execute command (only if not blocked)
        result = executor()

        try:
            if self._observability_enabled and ledger:
                # Post-command hook (STEP 1: OBSERVABILITY)
                self._obs_hooks.post_command(ledger, result)

                # STEP 2: Evaluate evidence completeness (ENFORCEMENT)
                if self._enforcement_enabled and self._policy_engine:
                    # Get artifacts from ledger
                    artifacts = ledger.outputs

                    # Validate evidence completeness
                    evidence_result = self._policy_engine.evaluate_evidence_completeness(
                        command, result, artifacts
                    )

                    # If blocked, override result
                    if evidence_result.is_blocked:
                        ledger.success = False
                        ledger.errors.append(evidence_result.message)
                        if evidence_result.violated_invariant:
                            ledger.proof_references["violated_invariant"] = evidence_result.violated_invariant

                        # Generate and print recovery message
                        recovery_msg = generate_recovery_message(evidence_result)
                        print(recovery_msg)

                        # Override result
                        result["success"] = False
                        result["errors"] = result.get("errors", []) + [evidence_result.message]
                        result["violated_invariant"] = evidence_result.violated_invariant
                        result["recovery_steps"] = evidence_result.recovery_steps

                # Save ledger
                ledger_dir = self.project_root / "project_state" / "evidence_ledger"
                ledger.save(ledger_dir)

                # Add evidence reference to result (non-intrusive)
                if "evidence_ledger_id" not in result:
                    result["evidence_ledger_id"] = ledger.run_id

        except Exception as e:
            # Log but do not fail
            print(f"Warning: Observability post-command failed: {e}")

        return result

    def handle_startkie(self) -> dict[str, Any]:
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

        # Copy workspace skeleton from project_template (single source of truth)
        import shutil
        kie_repo_root = Path(__file__).parent.parent.parent  # Go up to kie-v3/
        project_template = kie_repo_root / "project_template"

        if not project_template.exists():
            return {
                "success": False,
                "message": "project_template not found - KIE installation may be corrupted",
                "hint": "Reinstall KIE or clone from repository"
            }

        # Safety check: do not overwrite existing project folders
        existing_items = [
            item for item in ["README.md", "CLAUDE.md", ".claude", "data", "outputs", "exports", "project_state"]
            if (self.project_root / item).exists()
        ]
        if existing_items:
            return {
                "success": False,
                "message": f"This folder is not empty. Found existing: {', '.join(existing_items)}",
                "hint": "Create a new empty folder and run /startkie there"
            }

        # Copy everything from project_template
        for item in project_template.iterdir():
            if item.name in [".git", "__pycache__", ".DS_Store"]:
                continue

            target_item = self.project_root / item.name

            if item.is_dir():
                shutil.copytree(item, target_item, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target_item)

        # Track what was created
        folders = ["data", "outputs", "exports", "project_state"]
        commands_copied = (self.project_root / ".claude" / "commands").exists()

        # Copy fixture dataset so EDA can run on day 1
        kie_package_dir = Path(__file__).parent.parent  # kie/ package directory
        source_fixture = kie_package_dir / "templates" / "fixture_data.csv"
        target_fixture = self.project_root / "data" / "sample_data.csv"
        if source_fixture.exists():
            shutil.copy(source_fixture, target_fixture)

        # Print command reference and next steps
        print("\n" + "="*60)
        print("KIE WORKSPACE INITIALIZED")
        print("="*60)
        print("\nAVAILABLE COMMANDS (lowercase only!):")
        print("  /eda        - Exploratory data analysis")
        print("  /analyze    - Extract insights from data")
        print("  /interview  - Start requirements gathering")
        print("  /map        - Create geographic visualizations")
        print("  /build      - Generate deliverables")
        print("  /status     - Show project state")
        print("  /spec       - View specification")
        print("  /preview    - Preview outputs")
        print("  /validate   - Run quality checks")
        print("  /railscheck - Verify Rails configuration")
        print("\n⚠ NOTE: Commands are case-sensitive. Use /startkie not /STARTKIE")
        print("\nRECOMMENDED WORKFLOWS:")
        print("\n  Option 1: I Have Data, Need Quick Analysis")
        print("    1. Drop your CSV file in data/ folder")
        print("    2. Type /eda to profile your data")
        print("    3. Type /analyze to extract insights")
        print("\n  Option 2: Need Formal Deliverable (Presentation/Dashboard)")
        print("    1. Type /interview to gather requirements")
        print("    2. Choose express (6 questions) or full (11 questions)")
        print("    3. I'll guide you through the rest")
        print("\n  Option 3: Just Exploring KIE")
        print("    1. Sample data is in data/sample_data.csv")
        print("    2. Type /eda to see how analysis works")
        print("    3. Type /analyze to see insight extraction")
        print("\n" + "="*60 + "\n")

        # Update Rails state
        from kie.state import update_rails_state
        update_rails_state(self.project_root, "startkie", success=True)

        return {
            "success": True,
            "message": "KIE project structure created successfully",
            "folders_created": folders,
            "files_created": ["README.md", "CLAUDE.md", ".gitignore"],
            "commands_copied": commands_copied,
        }

    def handle_status(self, brief: bool = False) -> dict[str, Any]:
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

        # Add Rails progress
        from kie.state import get_rails_progress
        status["rails_progress"] = get_rails_progress(self.project_root)

        if brief:
            return {"brief_status": self._format_brief_status(status)}

        return status

    def _format_brief_status(self, status: dict[str, Any]) -> str:
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

    def handle_doctor(self) -> dict[str, Any]:
        """
        Handle /doctor command.

        Comprehensive environment + rails + dashboard readiness check.
        Cross-platform diagnostics for Mac and Windows.

        Returns:
            Status dict with checks, warnings, errors, and next_steps
        """
        import json
        import os
        import platform
        import subprocess
        import sys
        from importlib.util import find_spec

        import kie

        warnings = []
        errors = []
        checks = []
        next_steps = []

        # Detect OS
        current_os = platform.system()  # 'Darwin' for Mac, 'Windows' for Windows

        # ===== 1. Rails Health =====
        rails_state_path = self.project_root / "project_state" / "rails_state.json"
        rails_command_path = self.project_root / ".claude" / "commands" / "rails.md"

        if rails_state_path.exists():
            try:
                with open(rails_state_path) as f:
                    rails_data = json.load(f)
                checks.append("✓ Rails state tracking active (rails_state.json)")
            except (json.JSONDecodeError, OSError):
                warnings.append("⚠️  rails_state.json exists but is invalid JSON")
        else:
            warnings.append("⚠️  Rails state tracking not found. Run /startkie to initialize.")

        if rails_command_path.exists():
            checks.append("✓ Rails workflow command available (/rails)")
        else:
            warnings.append("⚠️  /rails command not found in .claude/commands/")

        # ===== 2. Python Runtime =====
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        checks.append(f"✓ Python version: {python_version}")

        # Test vendored runtime import
        kie_file = Path(kie.__file__).resolve()
        kie_package_root = kie_file.parent

        # Check if using vendored runtime (.kie/src pattern)
        if ".kie" in str(kie_package_root) and "src" in str(kie_package_root):
            checks.append(f"✓ Using vendored KIE runtime: {kie_package_root}")
        else:
            # Check if from expected repo or site-packages
            expected_repo_root = Path("/Users/pfay01/Projects/kie-v3")
            is_editable_from_this_repo = expected_repo_root in kie_package_root.parents

            site_packages = None
            for path in sys.path:
                if "site-packages" in path:
                    site_packages = Path(path)
                    break

            is_from_site_packages = site_packages and site_packages in kie_package_root.parents

            if is_editable_from_this_repo or is_from_site_packages:
                checks.append(f"✓ KIE package location: {kie_package_root}")
            else:
                warnings.append(
                    f"⚠️  Unexpected KIE import location: {kie_package_root}. "
                    "This may indicate a package collision."
                )

        # Check CLI entrypoint
        cli_spec = find_spec("kie.cli")
        if cli_spec is None:
            errors.append("❌ kie.cli module not found - wrong package installed")
        else:
            checks.append("✓ CLI entrypoint verified")

        # ===== 3. Node/Vite Readiness =====
        node_version_str = None
        node_major = None

        # Try to detect Node version (allow env var override for testing)
        if "TEST_NODE_VERSION" in os.environ:
            node_version_str = os.environ["TEST_NODE_VERSION"]
            try:
                node_major = int(node_version_str.split(".")[0])
            except (ValueError, IndexError):
                node_major = 0
        else:
            try:
                result = subprocess.run(
                    ["node", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    node_version_str = result.stdout.strip().lstrip("v")
                    try:
                        node_major = int(node_version_str.split(".")[0])
                    except (ValueError, IndexError):
                        node_major = 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                node_version_str = None

        if node_version_str:
            if node_major >= 20:
                checks.append(f"✓ Node.js version: {node_version_str} (compatible)")
            else:
                errors.append(f"❌ Node.js version {node_version_str} is too old (minimum: 20.19)")

                # OS-specific fix instructions
                if current_os == "Darwin":  # Mac
                    next_steps.append("# Mac: Upgrade Node.js")
                    next_steps.append("brew install node@22")
                    next_steps.append('echo \'export PATH="/opt/homebrew/opt/node@22/bin:$PATH"\' >> ~/.zshrc')
                    next_steps.append("source ~/.zshrc")
                elif current_os == "Windows":
                    next_steps.append("# Windows: Upgrade Node.js")
                    next_steps.append("# Option 1: Use winget (Windows Package Manager)")
                    next_steps.append("winget install OpenJS.NodeJS.LTS")
                    next_steps.append("")
                    next_steps.append("# Option 2: Download installer")
                    next_steps.append("# Visit https://nodejs.org/ and download Node 22 LTS")
                    next_steps.append("# After install, restart your terminal")
        else:
            errors.append("❌ Node.js not found")

            # OS-specific installation instructions
            if current_os == "Darwin":  # Mac
                next_steps.append("# Mac: Install Node.js")
                next_steps.append("brew install node@22")
                next_steps.append('echo \'export PATH="/opt/homebrew/opt/node@22/bin:$PATH"\' >> ~/.zshrc')
                next_steps.append("source ~/.zshrc")
            elif current_os == "Windows":
                next_steps.append("# Windows: Install Node.js")
                next_steps.append("winget install OpenJS.NodeJS.LTS")
                next_steps.append("# Or download from https://nodejs.org/")
                next_steps.append("# Restart your terminal after installation")

        # ===== 4. Dashboard Readiness =====
        dashboard_path = self.project_root / "exports" / "dashboard"
        dashboard_package_json = dashboard_path / "package.json"

        if dashboard_package_json.exists():
            checks.append("✓ Dashboard generated (exports/dashboard/)")

            # Provide launch instructions
            next_steps.append("")
            next_steps.append("# Launch dashboard:")
            next_steps.append(f"cd {dashboard_path}")
            next_steps.append("npm install  # (first time only)")
            next_steps.append("npm run dev")
            next_steps.append("# Then open http://localhost:5173")
        else:
            # No dashboard yet - not an error, just informational
            pass

        # ===== 5. Workspace Structure =====
        required_dirs = ["data", "outputs", "exports", "project_state"]
        missing_dirs = [d for d in required_dirs if not (self.project_root / d).exists()]

        if missing_dirs:
            warnings.append(
                f"⚠️  Missing workspace directories: {', '.join(missing_dirs)}. "
                "Run /startkie to initialize."
            )
        else:
            checks.append("✓ Workspace structure valid")

        # ===== 6. Slash Commands =====
        commands_dir = self.project_root / ".claude" / "commands"
        if not commands_dir.exists() or not list(commands_dir.glob("*.md")):
            warnings.append(
                "⚠️  Slash commands not found. Run /startkie to provision."
            )
        else:
            checks.append(f"✓ Slash commands provisioned ({len(list(commands_dir.glob('*.md')))} commands)")

        # ===== 7. Smart Hints (Context-Aware Next Steps) =====
        has_spec = self.spec_path.exists()
        has_data = (self.project_root / "data").exists() and \
                   any((self.project_root / "data").iterdir())

        if not has_spec:
            next_steps.append("")
            next_steps.append("# No project spec found - get started:")
            next_steps.append("/spec --init    # Create default spec")
            next_steps.append("# OR")
            next_steps.append("/interview      # Conversational requirements gathering")
        elif not has_data:
            next_steps.append("")
            next_steps.append("# Add data to get started:")
            next_steps.append(f"# 1. Drop your CSV/Excel/Parquet file into: {self.project_root / 'data'}/")
            next_steps.append("# 2. Run /eda to profile your data")

        return {
            "success": len(errors) == 0,
            "checks": checks,
            "warnings": warnings,
            "errors": errors,
            "next_steps": next_steps,
            "kie_package_location": str(kie_package_root),
            "os": current_os,
            "python_version": python_version,
            "node_version": node_version_str,
        }

    def handle_interview(self, from_wrapper: bool = False) -> dict[str, Any]:
        """
        Handle /interview command.

        NOTE: /interview is now Claude-orchestrated (not CLI-driven).
        This method prints guidance for Claude to conduct the interview.

        Args:
            from_wrapper: If True, suppress the hint about using slash commands

        Returns:
            Informational message
        """
        message = "The /interview command is Claude-orchestrated. Claude will conduct the interview by asking questions one at a time in chat. Just respond normally - no CLI interaction needed."

        result = {
            "success": True,
            "message": message,
        }

        if not from_wrapper:
            result["hint"] = "If you're seeing this from CLI, use the /interview slash command in Claude Code instead."

        return result

    def handle_validate(self, target: str | None = None) -> dict[str, Any]:
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

    def handle_build(self, target: str = "all") -> dict[str, Any]:
        """
        Handle /build command.

        Args:
            target: What to build ('all', 'charts', 'presentation', 'dashboard')

        Returns:
            Build results
        """
        # Auto-init spec if missing
        if not self.spec_path.exists():
            init_result = self.handle_spec(init=True, show=False)
            if not init_result.get("success"):
                return {
                    "success": False,
                    "message": f"Could not initialize spec.yaml: {init_result.get('message')}",
                }

        # Load spec
        with open(self.spec_path) as f:
            spec = yaml.safe_load(f)

        # Auto-repair stale data_source if present
        if 'data_source' in spec:
            data_source_path = self.project_root / "data" / spec['data_source']
            if not data_source_path.exists():
                repair_result = self.handle_spec(repair=True, show=False)
                if repair_result.get("success"):
                    # Reload spec after repair
                    with open(self.spec_path) as f:
                        spec = yaml.safe_load(f)

        # CRITICAL: Check theme is set before building (Codex requirement)
        from kie.config.theme_config import ProjectThemeConfig
        theme_config = ProjectThemeConfig(self.project_root)
        theme_mode = theme_config.load_theme()
        if theme_mode is None:
            # Default theme for non-interactive/test build flows
            theme_mode = "dark"
            try:
                theme_config.save_theme(theme_mode)
            except Exception:
                pass


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

            # Update Rails state
            from kie.state import update_rails_state
            update_rails_state(self.project_root, "build", success=True)

            return {
                "success": True,
                "message": "Build completed successfully",
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

    def _build_presentation(self, spec: dict[str, Any]) -> Path:
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

    def _build_dashboard(self, spec: dict[str, Any]) -> Path:
        """
        Build React dashboard from spec and data.

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

    def handle_eda(self, data_file: str | None = None) -> dict[str, Any]:
        """
        Handle /eda command - run exploratory data analysis.

        Args:
            data_file: Specific file to analyze (default: auto-detect from data/)

        Returns:
            EDA results
        """
        # Ensure logs directory exists
        log_dir = self.project_root / "outputs" / "_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "eda.log"

        def log(message: str):
            """Write to log file and stdout."""
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            log_message = f"[{timestamp}] {message}\n"
            with open(log_file, "a") as f:
                f.write(log_message)

        log("EDA command started")

        # Find data file
        if not data_file:
            data_dir = self.project_root / "data"
            data_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
            if not data_files:
                log("ERROR: No data files found in data/ folder")
                return {
                    "success": False,
                    "message": "No data files found in data/ folder",
                }
            data_file = str(data_files[0])
            log(f"Auto-detected data file: {data_file}")
        else:
            data_file = str(self.project_root / data_file)
            log(f"Using specified data file: {data_file}")

        # Run EDA
        try:
            log("Running EDA analysis...")
            eda = EDA()
            profile = eda.analyze(data_file)
            log(f"Analysis complete: {profile.rows} rows, {profile.columns} columns")

            # Save profile
            profile_path = self.project_root / "outputs" / "eda_profile.yaml"
            profile_path.parent.mkdir(parents=True, exist_ok=True)

            import yaml
            with open(profile_path, "w") as f:
                yaml.dump(profile.to_dict(), f, default_flow_style=False)
            log(f"Profile saved to: {profile_path}")

            # Get suggestions
            suggestions = eda.suggest_analysis()
            log(f"Generated {len(suggestions)} analysis suggestions")

            log("EDA command completed successfully")

            # Update Rails state
            from kie.state import update_rails_state
            update_rails_state(self.project_root, "eda", success=True)

            return {
                "success": True,
                "profile": profile.to_dict(),
                "suggestions": suggestions,
                "profile_saved": str(profile_path),
                "data_file": data_file,
                "log_file": str(log_file),
            }

        except Exception as e:
            log(f"ERROR: EDA failed: {str(e)}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "message": f"EDA failed: {str(e)}",
                "log_file": str(log_file),
            }

    def handle_analyze(self, data_file: str | None = None) -> dict[str, Any]:
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
            from datetime import datetime

            from kie.geo.maps.folium_builder import create_marker_map, create_us_choropleth

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

            except Exception:
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

            # Update Rails state
            from kie.state import update_rails_state
            update_rails_state(self.project_root, "analyze", success=True)

            return result

        except Exception as e:
            return {
                "success": False,
                "message": f"Analysis failed: {str(e)}",
            }

    def handle_preview(self, launch_server: bool = True) -> dict[str, Any]:
        """
        Handle /preview command - preview outputs in React dashboard.

        Args:
            launch_server: Whether to launch React dev server (default True)

        Returns:
            Preview information with server status
        """
        self.handle_status()

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

        # Update Rails state
        from kie.state import update_rails_state
        update_rails_state(self.project_root, "preview", success=True)

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

    def handle_spec(self, init: bool = False, repair: bool = False, show: bool = True, set_values: dict[str, Any] | None = None, force: bool = False) -> dict[str, Any]:
        """
        Handle /spec command - show, initialize, repair, or update specification.

        Args:
            init: If True, create minimal spec if missing
            repair: If True, fix stale data_source references
            show: If True, return spec content (default)
            set_values: Dict of key=value pairs to set in spec
            force: If True, skip validation when setting data_source

        Returns:
            Specification dict
        """
        # REPAIR MODE: Fix stale data_source references
        if repair:
            if not self.spec_path.exists():
                return {
                    "success": False,
                    "message": "No spec.yaml found. Run 'kie spec --init' to create one.",
                }

            # Load existing spec
            with open(self.spec_path) as f:
                spec = yaml.safe_load(f) or {}

            # Check if data_source exists
            repaired = False
            if 'data_source' in spec:
                data_source_path = self.project_root / "data" / spec['data_source']
                if not data_source_path.exists():
                    # Data source is stale - auto-detect new one
                    data_dir = self.project_root / "data"
                    if data_dir.exists():
                        data_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
                        if len(data_files) == 1:
                            old_data_source = spec['data_source']
                            spec['data_source'] = data_files[0].name
                            repaired = True
                            repair_msg = f"Repaired data_source: {old_data_source} → {data_files[0].name}"
                        elif len(data_files) == 0:
                            # No data files found - remove data_source
                            old_data_source = spec['data_source']
                            del spec['data_source']
                            repaired = True
                            repair_msg = f"Removed stale data_source: {old_data_source} (no data files found)"
                        else:
                            return {
                                "success": False,
                                "message": f"Multiple data files found: {[f.name for f in data_files]}. Please manually set data_source in spec.yaml.",
                            }

            if repaired:
                # Write repaired spec
                with open(self.spec_path, "w") as f:
                    yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
                return {
                    "success": True,
                    "message": repair_msg,
                    "spec": spec,
                }
            else:
                return {
                    "success": True,
                    "message": "No repairs needed - data_source is valid or not set.",
                    "spec": spec,
                }

        # INIT MODE: Create minimal spec if missing
        if init:
            if self.spec_path.exists():
                # Spec exists - fill missing fields only
                with open(self.spec_path) as f:
                    spec = yaml.safe_load(f) or {}
            else:
                # No spec - create minimal one
                spec = {}

            # Fill in defaults for missing fields
            if 'project_name' not in spec:
                spec['project_name'] = self.project_root.name or "Analysis"

            if 'objective' not in spec:
                spec['objective'] = "Analysis"

            if 'project_type' not in spec:
                spec['project_type'] = "analytics"

            if 'deliverable_format' not in spec:
                spec['deliverable_format'] = "report"

            # Auto-detect data source if exactly one supported file exists
            if 'data_source' not in spec:
                data_dir = self.project_root / "data"
                if data_dir.exists():
                    data_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
                    if len(data_files) == 1:
                        spec['data_source'] = data_files[0].name

            # Apply theme config
            if 'preferences' not in spec:
                spec['preferences'] = {}
            if 'theme' not in spec['preferences']:
                spec['preferences']['theme'] = {}
            if 'mode' not in spec['preferences']['theme']:
                from kie.config.theme_config import ProjectThemeConfig
                theme_config = ProjectThemeConfig(self.project_root)
                theme_mode = theme_config.load_theme() or "dark"
                spec['preferences']['theme']['mode'] = theme_mode

            # Write spec
            self.spec_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.spec_path, "w") as f:
                yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

            # Update Rails state
            from kie.state import update_rails_state
            update_rails_state(self.project_root, "spec", success=True)

            return {
                "success": True,
                "message": f"Initialized spec.yaml with defaults at {self.spec_path}",
                "spec": spec,
                "created": not self.spec_path.exists(),
            }

        # SET MODE: Update spec with key=value pairs
        if set_values:
            # Auto-init if spec doesn't exist
            if not self.spec_path.exists():
                init_result = self.handle_spec(init=True, show=False)
                if not init_result["success"]:
                    return init_result

            # Load existing spec
            with open(self.spec_path) as f:
                spec = yaml.safe_load(f) or {}

            # Allowed keys (whitelist for safety)
            allowed_keys = {
                'project_name', 'client_name', 'objective', 'project_type',
                'deliverable_format', 'data_source', 'preferences.theme.mode'
            }

            updated_fields = []
            warnings = []

            for key, value in set_values.items():
                if key not in allowed_keys:
                    return {
                        "success": False,
                        "message": f"Invalid key: {key}. Allowed keys: {', '.join(sorted(allowed_keys))}",
                    }

                # Handle nested keys (e.g., preferences.theme.mode)
                if '.' in key:
                    parts = key.split('.')
                    current = spec
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    # Special validation for data_source
                    if key == 'data_source' and not force:
                        data_source_path = self.project_root / "data" / value
                        if not data_source_path.exists():
                            warnings.append(
                                f"Warning: data_source '{value}' not found in data/ directory. "
                                "Use --force to set anyway."
                            )
                            continue

                    spec[key] = value

                updated_fields.append(f"{key}={value}")

            # Write updated spec
            with open(self.spec_path, "w") as f:
                yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

            message = f"Updated spec.yaml: {', '.join(updated_fields)}"
            if warnings:
                message += f"\n{'; '.join(warnings)}"

            # Update Rails state
            from kie.state import update_rails_state
            update_rails_state(self.project_root, "spec", success=True)

            return {
                "success": True,
                "message": message,
                "spec": spec,
                "updated_fields": updated_fields,
                "warnings": warnings,
            }

        # SHOW MODE: Display existing spec
        if not self.spec_path.exists():
            return {
                "success": False,
                "message": "No spec.yaml found. Run 'kie spec --init' to create one.",
            }

        with open(self.spec_path) as f:
            spec = yaml.safe_load(f)

        return {
            "success": True,
            "spec": spec,
        }

    def handle_map(self, data_file: str | None = None, map_type: str = 'auto') -> dict[str, Any]:
        """
        Handle /map command - create geographic visualizations.

        Args:
            data_file: Specific file to visualize (default: auto-detect from data/)
            map_type: Type of map ('auto', 'choropleth', 'marker', 'heatmap')

        Returns:
            Map generation results with file path
        """
        from datetime import datetime

        from kie.geo.maps.folium_builder import create_marker_map, create_us_choropleth

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
                    "message": "US Choropleth map created",
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

    def handle_template(self, output_path: Path | None = None) -> dict[str, Any]:
        """
        Generate KIE Workspace Starter Template ZIP.

        Args:
            output_path: Where to save the ZIP (default: kie_workspace_starter.zip)

        Returns:
            Status dict with zip_path
        """
        import zipfile

        if output_path is None:
            output_path = Path.cwd() / "kie_workspace_starter.zip"
        else:
            output_path = Path(output_path)

        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Create folder structure
                folders = [
                    "data/",
                    "outputs/",
                    "outputs/charts/",
                    "outputs/tables/",
                    "outputs/maps/",
                    "exports/",
                    "project_state/",
                    "project_state/validation_reports/",
                    ".claude/",
                    ".claude/commands/",
                ]
                for folder in folders:
                    # Write empty folder marker
                    zf.writestr(folder, "")

                # Add workspace marker
                zf.writestr("project_state/.kie_workspace", "")

                # Add .gitignore
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
                zf.writestr(".gitignore", gitignore_content)

                # Add README.md
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

- `/kie_setup` - Check workspace health
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
                zf.writestr("README.md", readme_content)

                # Add CLAUDE.md (from repo root)
                kie_repo_root = Path(__file__).parent.parent.parent
                source_claude_md = kie_repo_root / "CLAUDE.md"
                if source_claude_md.exists():
                    zf.write(source_claude_md, "CLAUDE.md")
                else:
                    zf.writestr("CLAUDE.md", "# KIE Project\n\nKIE (Kearney Insight Engine) v3 project.")

                # Add slash commands from templates
                templates_dir = Path(__file__).parent.parent / "templates" / "commands"
                if templates_dir.exists():
                    for cmd_file in templates_dir.glob("*.md"):
                        zf.write(cmd_file, f".claude/commands/{cmd_file.name}")
                else:
                    # Fallback: use repo commands
                    repo_commands = kie_repo_root / ".claude" / "commands"
                    if repo_commands.exists():
                        for cmd_file in repo_commands.glob("*.md"):
                            zf.write(cmd_file, f".claude/commands/{cmd_file.name}")

            return {
                "success": True,
                "message": "Workspace starter template created",
                "zip_path": str(output_path),
                "size_bytes": output_path.stat().st_size,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Template generation failed: {str(e)}",
            }
