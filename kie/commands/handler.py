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

    def _select_data_file(self) -> Path | None:
        """
        Select the current data file deterministically.

        Priority:
        1. User-provided files (non-sample, prefer non-CSV over CSV if both exist)
        2. sample_data.csv
        3. None if no files

        Supports: CSV, XLSX, Parquet, JSON

        Returns:
            Path to selected data file, or None if no data exists
        """
        data_dir = self.project_root / "data"
        if not data_dir.exists():
            return None

        # Supported extensions (in priority order for user files)
        supported_exts = [".xlsx", ".parquet", ".json", ".csv"]

        # Collect all data files
        all_files = []
        for ext in supported_exts:
            all_files.extend(data_dir.glob(f"*{ext}"))

        # Filter out .gitkeep
        all_files = [f for f in all_files if f.name != ".gitkeep"]

        if not all_files:
            return None

        # Separate sample from user files
        sample_file = None
        user_files = []

        for f in all_files:
            if f.name == "sample_data.csv":
                sample_file = f
            else:
                user_files.append(f)

        # Priority 1: User files (prefer non-CSV)
        if user_files:
            # Sort by extension priority (xlsx, parquet, json, csv)
            ext_priority = {".xlsx": 0, ".parquet": 1, ".json": 2, ".csv": 3}
            user_files.sort(key=lambda f: ext_priority.get(f.suffix, 99))
            return user_files[0]

        # Priority 2: sample_data.csv
        if sample_file:
            return sample_file

        return None

    def _save_data_file_selection(self, data_file: Path) -> None:
        """
        Save the selected data file to project state for consistency.

        Args:
            data_file: Path to selected data file
        """
        state_dir = self.project_root / "project_state"
        state_dir.mkdir(parents=True, exist_ok=True)

        selection_file = state_dir / "current_data_file.txt"
        selection_file.write_text(str(data_file.relative_to(self.project_root)))

    def _load_data_file_selection(self) -> Path | None:
        """
        Load the previously selected data file from project state.

        Returns:
            Path to previously selected file, or None
        """
        selection_file = self.project_root / "project_state" / "current_data_file.txt"
        if not selection_file.exists():
            return None

        try:
            rel_path = selection_file.read_text().strip()
            abs_path = self.project_root / rel_path
            if abs_path.exists():
                return abs_path
        except Exception:
            pass

        return None

    def _check_node_version(self) -> tuple[bool, str | None, str]:
        """
        Check if Node.js is installed and meets minimum version requirement.

        Returns:
            Tuple of (is_compatible, version_string, message)
        """
        import subprocess

        # Allow test override
        if "TEST_NODE_VERSION" in os.environ:
            node_version_str = os.environ["TEST_NODE_VERSION"]
            try:
                node_major = int(node_version_str.split(".")[0])
                if node_major >= 20:
                    return (True, node_version_str, f"Node.js {node_version_str} detected (compatible)")
                else:
                    return (False, node_version_str, f"Node.js {node_version_str} is too old (minimum: 20.19)")
            except Exception:
                return (False, node_version_str, f"Could not parse Node.js version: {node_version_str}")

        # Try to detect Node
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                node_version_str = result.stdout.strip().lstrip("v")
                try:
                    node_major = int(node_version_str.split(".")[0])
                    if node_major >= 20:
                        return (True, node_version_str, f"Node.js {node_version_str} detected (compatible)")
                    else:
                        return (False, node_version_str, f"Node.js {node_version_str} is too old (minimum: 20.19). Install Node 20+ from https://nodejs.org/")
                except Exception:
                    return (False, node_version_str, f"Could not parse Node.js version: {node_version_str}")
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        return (False, None, "Node.js not found. Install Node 20+ from https://nodejs.org/ to enable dashboard generation.")

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
        print("  /sampledata - Install/manage demo data")
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
        print("    1. Type /sampledata install to get demo data")
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

    def handle_sampledata(self, subcommand: str = "status") -> dict[str, Any]:
        """
        Handle /sampledata command - manage demo data.

        Args:
            subcommand: One of 'status', 'install', 'remove'

        Returns:
            Result dict
        """
        import shutil
        import yaml
        from datetime import datetime

        sample_file = self.project_root / "data" / "sample_data.csv"
        tracking_file = self.project_root / "project_state" / "sampledata.yaml"

        if subcommand == "status":
            # Check if sample data is installed
            if sample_file.exists():
                print()
                print("Sample Data: INSTALLED")
                print(f"  Location: data/sample_data.csv")
                print()

                # Check tracking file
                if tracking_file.exists():
                    with open(tracking_file) as f:
                        tracking = yaml.safe_load(f)
                        if tracking and tracking.get("installed_at"):
                            print(f"  Installed: {tracking['installed_at']}")
                            print()

                return {
                    "success": True,
                    "installed": True,
                    "location": "data/sample_data.csv",
                }
            else:
                print()
                print("Sample Data: NOT INSTALLED")
                print()
                print("Install with: /sampledata install")
                print()
                return {
                    "success": True,
                    "installed": False,
                }

        elif subcommand == "install":
            # Install sample data
            if sample_file.exists():
                print()
                print("Sample data already installed at data/sample_data.csv")
                print()
                return {
                    "success": True,
                    "message": "Sample data already installed",
                }

            # Copy from package templates
            kie_package_dir = Path(__file__).parent.parent
            source_fixture = kie_package_dir / "templates" / "fixture_data.csv"

            if not source_fixture.exists():
                print()
                print("Error: Sample data template not found")
                print()
                return {
                    "success": False,
                    "message": "Sample data template not found in package",
                }

            # Copy sample data
            shutil.copy(source_fixture, sample_file)

            # Record installation
            tracking_file.parent.mkdir(parents=True, exist_ok=True)
            tracking_data = {
                "installed": True,
                "installed_at": datetime.now().isoformat(),
            }
            with open(tracking_file, "w") as f:
                yaml.dump(tracking_data, f, default_flow_style=False)

            print()
            print("✓ Sample data installed at data/sample_data.csv")
            print()
            print("Try it:")
            print("  /eda      - Profile the demo data")
            print("  /analyze  - Extract insights")
            print()

            return {
                "success": True,
                "message": "Sample data installed",
                "location": "data/sample_data.csv",
            }

        elif subcommand == "remove":
            # Remove sample data
            if not sample_file.exists():
                print()
                print("Sample data is not installed")
                print()
                return {
                    "success": True,
                    "message": "Sample data not installed",
                }

            # Remove sample file
            sample_file.unlink()

            # Update tracking
            if tracking_file.exists():
                tracking_data = {
                    "installed": False,
                    "removed_at": datetime.now().isoformat(),
                }
                with open(tracking_file, "w") as f:
                    yaml.dump(tracking_data, f, default_flow_style=False)

            print()
            print("✓ Sample data removed")
            print()

            return {
                "success": True,
                "message": "Sample data removed",
            }

        else:
            print()
            print(f"Error: Unknown subcommand '{subcommand}'")
            print()
            print("Usage:")
            print("  /sampledata status   Show sample data status")
            print("  /sampledata install  Install demo data")
            print("  /sampledata remove   Remove demo data")
            print()
            return {
                "success": False,
                "message": f"Unknown subcommand: {subcommand}",
            }

    def handle_intent(self, subcommand: str = "status", objective: str | None = None) -> dict[str, Any]:
        """
        Handle /intent command - manage user intent.

        Args:
            subcommand: One of 'status', 'set', 'clear'
            objective: Objective text (required for 'set')

        Returns:
            Result dict
        """
        from kie.state import IntentStorage

        storage = IntentStorage(self.project_root)

        if subcommand == "status":
            # Show current intent
            intent = storage.get_intent()
            if intent:
                print()
                print("Intent:")
                print(f"  {intent['objective']}")
                print()
                print(f"Captured via: {intent.get('captured_via', 'unknown')}")
                print()
                return {
                    "success": True,
                    "intent": intent['objective'],
                    "captured_via": intent.get('captured_via', 'unknown'),
                }
            else:
                print()
                print("Intent: NOT SET")
                print()
                print("Set intent with: /intent set \"<objective>\"")
                print("Or run /interview for guided setup")
                print()
                return {
                    "success": True,
                    "intent": "NOT SET",
                }

        elif subcommand == "set":
            # Set intent
            if not objective:
                print()
                print("Error: Objective required for /intent set")
                print()
                print("Usage: /intent set \"<one sentence objective>\"")
                print("Example: /intent set \"Analyze quarterly revenue trends\"")
                print()
                return {
                    "success": False,
                    "message": "Objective required for /intent set",
                }

            # Validate non-empty
            objective = objective.strip()
            if not objective:
                return {
                    "success": False,
                    "message": "Objective cannot be empty",
                }

            # Capture intent
            result = storage.capture_intent(objective, captured_via="cli")
            print()
            print(f"✓ Intent set: {objective}")
            print()
            return {
                "success": True,
                "objective": objective,
            }

        elif subcommand == "clear":
            # Clear intent
            intent_path = self.project_root / "project_state" / "intent.yaml"
            if intent_path.exists():
                intent_path.unlink()
                print()
                print("✓ Intent cleared")
                print()
                return {
                    "success": True,
                    "message": "Intent cleared",
                }
            else:
                print()
                print("Intent is already NOT SET")
                print()
                return {
                    "success": True,
                    "message": "Intent already not set",
                }

        else:
            print()
            print(f"Error: Unknown subcommand '{subcommand}'")
            print()
            print("Usage:")
            print("  /intent status              Show current intent")
            print("  /intent set \"<objective>\"   Set intent")
            print("  /intent clear               Clear intent")
            print()
            return {
                "success": False,
                "message": f"Unknown subcommand: {subcommand}",
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

        # Add output theme preference
        from kie.preferences import OutputPreferences
        prefs = OutputPreferences(self.project_root)
        output_theme = prefs.get_theme()
        status["output_theme"] = output_theme

        # Add execution mode
        from kie.execution_policy import ExecutionPolicy
        policy = ExecutionPolicy(self.project_root)
        execution_mode = policy.get_mode()
        status["execution_mode"] = execution_mode

        # Add intent status
        from kie.state import get_intent
        intent_data = get_intent(self.project_root)
        if intent_data:
            status["intent"] = intent_data.get("objective", "NOT SET")
        else:
            status["intent"] = "NOT SET"

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
        # Use node_provider for detection (without auto-install)
        from kie.tooling import NodeProvider

        provider = NodeProvider(self.project_root)

        # Check system Node
        system_ok, system_version, system_msg = provider.detect_system_node()

        # Check bundled Node
        bundled_exists, bundled_version, bundled_bin = provider.detect_bundled_node()

        # Determine node_source and dashboard_ready
        node_source = "none"
        node_version_str = None
        dashboard_ready = False

        if system_ok and system_version:
            node_source = "system"
            node_version_str = system_version
            dashboard_ready = True
            checks.append(f"✓ Node.js source: system")
            checks.append(f"✓ Node.js version: {system_version} (compatible)")
        elif bundled_exists and bundled_version:
            node_source = "bundled"
            node_version_str = bundled_version
            dashboard_ready = True
            checks.append(f"✓ Node.js source: bundled (workspace-local)")
            checks.append(f"✓ Node.js version: {bundled_version} (compatible)")
        else:
            node_source = "none"
            dashboard_ready = False
            checks.append(f"ℹ️  Node.js source: none (will auto-install on first /build)")
            checks.append(f"ℹ️  Dashboard generation: ready (auto-provisioning available)")

            # Note: We don't add errors or next_steps because auto-install handles it

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
            "node_source": node_source,
            "dashboard_ready": dashboard_ready,
        }

    def handle_theme(self, set_theme: str | None = None) -> dict[str, Any]:
        """
        Handle /theme command - view or change output theme preference.

        Args:
            set_theme: Optional theme to set ('light' or 'dark')

        Returns:
            Theme preference information
        """
        from kie.preferences import OutputPreferences

        prefs = OutputPreferences(self.project_root)

        # If setting theme
        if set_theme:
            if set_theme not in ["light", "dark"]:
                return {
                    "success": False,
                    "message": f"Invalid theme: {set_theme}. Must be 'light' or 'dark'",
                }

            # Save preference
            prefs.set_theme(set_theme, source="theme_command")

            print()
            print("=" * 70)
            print(f"✓ Output theme updated to: {set_theme}")
            print("=" * 70)
            print()
            print("Theme updated. Re-run /build to apply the new theme.")
            print()

            return {
                "success": True,
                "theme": set_theme,
                "message": f"Theme set to {set_theme}. Re-run /build to apply.",
            }

        # Otherwise, show current theme
        current_theme = prefs.get_theme()

        if current_theme is None:
            print()
            print("=" * 70)
            print("NO THEME SET")
            print("=" * 70)
            print()
            print("Output theme has not been set yet.")
            print("It will be requested when you run /build.")
            print()
            print("To set manually:")
            print("  python3 -m kie.cli theme light")
            print("  python3 -m kie.cli theme dark")
            print()

            return {
                "success": True,
                "theme": None,
                "message": "No theme set - will be prompted during /build",
            }

        # Show current theme
        print()
        print("=" * 70)
        print(f"CURRENT OUTPUT THEME: {current_theme.upper()}")
        print("=" * 70)
        print()

        theme_descriptions = {
            "light": "Light backgrounds (#FFFFFF) with dark text\nTraditional document appearance",
            "dark": "Dark backgrounds (#1E1E1E) with white text\nReduces eye strain in low light",
        }

        print(theme_descriptions.get(current_theme, ""))
        print()
        print("To change theme:")
        print("  python3 -m kie.cli theme light")
        print("  python3 -m kie.cli theme dark")
        print()

        return {
            "success": True,
            "theme": current_theme,
            "message": f"Current theme: {current_theme}",
        }

    def handle_freeform(self, action: str | None = None) -> dict[str, Any]:
        """
        Handle /freeform command - manage execution mode (rails vs freeform).

        Args:
            action: Action to perform ("status", "enable", "disable", or None for status)

        Returns:
            Result dict with success, mode, and message
        """
        from kie.execution_policy import ExecutionPolicy

        policy = ExecutionPolicy(self.project_root)

        # Default to status if no action provided
        if action is None or action == "status":
            policy_info = policy.get_policy_info()
            current_mode = policy_info["mode"]
            set_at = policy_info.get("set_at")
            set_by = policy_info.get("set_by", "default")

            print()
            print("=" * 70)
            print(f"EXECUTION MODE: {current_mode.upper()}")
            print("=" * 70)
            print()

            if current_mode == "rails":
                print("Rails Mode (default) - Off-rails execution disabled")
                print()
                print("What's Forbidden:")
                print("  • Ad-hoc Python scripts outside KIE")
                print("  • Matplotlib/Seaborn charts")
                print("  • Arbitrary bash/python execution")
                print("  • Non-KIE artifacts")
                print()
                print("What's Allowed:")
                print("  • All KIE CLI commands (/eda, /analyze, /build, etc.)")
                print("  • Recharts dashboards")
                print("  • PowerPoint presentations")
                print("  • KIE-managed analysis")
                print()
                print("To enable custom analysis:")
                print("  python3 -m kie.cli freeform enable")
            else:
                print("Freeform Mode - Custom analysis enabled")
                print()
                print("User has opted in to custom analysis, including:")
                print("  • Ad-hoc Python scripts")
                print("  • Custom visualization libraries")
                print("  • Exploratory analysis outside KIE")
                print()
                print("To return to Rails Mode:")
                print("  python3 -m kie.cli freeform disable")

            if set_at:
                print()
                print(f"Mode set: {set_at}")
                print(f"Set by: {set_by}")

            print()

            return {
                "success": True,
                "mode": current_mode,
                "message": f"Current execution mode: {current_mode}",
            }

        elif action == "enable":
            policy.set_mode("freeform", set_by="user")
            print()
            print("=" * 70)
            print("✓ FREEFORM MODE ENABLED")
            print("=" * 70)
            print()
            print("Custom analysis is now allowed, including:")
            print("  • Ad-hoc Python scripts")
            print("  • Matplotlib/Seaborn visualizations")
            print("  • Exploratory analysis outside KIE")
            print()
            print("To return to Rails Mode:")
            print("  python3 -m kie.cli freeform disable")
            print()

            return {
                "success": True,
                "mode": "freeform",
                "message": "Freeform mode enabled",
            }

        elif action == "disable":
            policy.set_mode("rails", set_by="user")
            print()
            print("=" * 70)
            print("✓ RAILS MODE RESTORED")
            print("=" * 70)
            print()
            print("Off-rails execution is now disabled.")
            print("Only KIE CLI commands are permitted.")
            print()
            print("To re-enable custom analysis:")
            print("  python3 -m kie.cli freeform enable")
            print()

            return {
                "success": True,
                "mode": "rails",
                "message": "Rails mode enabled (freeform disabled)",
            }

        else:
            return {
                "success": False,
                "message": f"Invalid action: {action}. Use 'status', 'enable', or 'disable'",
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
        # INTENT GATE: Check if intent is clarified
        from kie.state import is_intent_clarified, print_intent_required_message

        if not is_intent_clarified(self.project_root):
            # Intent not clarified - print guidance and block
            print_intent_required_message()
            return {
                "success": False,
                "blocked": True,
                "message": "Intent clarification required. Use: /intent set \"<objective>\" or run /interview",
            }

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

        # CRITICAL: Check output theme preference is set before building
        # User must explicitly choose theme - no silent defaults
        from kie.preferences import OutputPreferences

        prefs = OutputPreferences(self.project_root)
        output_theme = prefs.get_theme()

        if output_theme is None:
            # Theme not set - prompt user
            print()
            print("=" * 70)
            print("OUTPUT THEME REQUIRED")
            print("=" * 70)
            print()
            print("Which output theme do you want for formatted deliverables?")
            print()
            print("1) Light")
            print("   • Light backgrounds (#FFFFFF)")
            print("   • Dark text on light surfaces")
            print("   • Traditional document appearance")
            print()
            print("2) Dark")
            print("   • Dark backgrounds (#1E1E1E)")
            print("   • White text on dark surfaces")
            print("   • Reduces eye strain in low light")
            print()

            while True:
                choice = input("Choose theme (1 or 2): ").strip()

                if choice == "1":
                    output_theme = "light"
                    break
                elif choice == "2":
                    output_theme = "dark"
                    break
                elif choice.lower() in ["q", "quit", "cancel", "exit"]:
                    print()
                    print("Build cancelled - no theme selected")
                    return {
                        "success": False,
                        "message": "Build cancelled by user - theme selection required",
                    }
                else:
                    print("Invalid choice. Please enter 1 or 2 (or 'q' to cancel).")

            # Save preference
            prefs.set_theme(output_theme, source="user_prompt")
            print()
            print(f"✓ Output theme set to: {output_theme}")
            print("  (To change: run /theme command)")
            print()
            print("Continuing build...")
            print()

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
                # Get Node runtime with automatic provisioning
                from kie.tooling import get_node_bin

                node_source, node_bin, node_msg = get_node_bin(self.project_root)

                if node_source != "none" and node_bin:
                    dashboard_path = self._build_dashboard(spec, node_bin=node_bin, theme=output_theme)
                    results["dashboard"] = str(dashboard_path)
                    results["message"] = f"Dashboard built at {dashboard_path}. Open index.html in browser or run 'npm install && npm run dev'"
                    results["node_source"] = node_source
                else:
                    # Auto-install failed - provide manual guidance
                    results["dashboard_skipped"] = node_msg
                    if target == "dashboard":
                        # Dashboard was explicitly requested but can't be built
                        return {
                            "success": False,
                            "message": f"Cannot build dashboard: {node_msg}\n\nManual installation:\n- Visit https://nodejs.org/ and install Node.js 20+\n- Or run: brew install node@22 (macOS) / winget install OpenJS.NodeJS.LTS (Windows)",
                        }
                    # Otherwise continue with presentation
                    print(f"⚠️  Dashboard skipped: {node_msg}")
                    print(f"   Install Node.js 20+ from https://nodejs.org/ to enable dashboards.")

            # Build presentation if requested
            if target in ["all", "presentation"]:
                pres_path = self._build_presentation(spec, theme=output_theme)
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

    def _build_presentation(self, spec: dict[str, Any], theme: str = "dark") -> Path:
        """
        Build PowerPoint presentation from spec and insights.

        Args:
            spec: Project specification
            theme: Output theme ('light' or 'dark')

        Returns:
            Path to generated presentation
        """
        # Load insights if available
        insights_path = self.project_root / "outputs" / "insights.yaml"
        insights = []
        if insights_path.exists():
            catalog = InsightCatalog.load(str(insights_path))
            insights = catalog.insights

        # Create presentation with theme
        builder = SlideBuilder(title=spec.get("project_name", "Analysis"), theme=theme)

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

    def _build_dashboard(self, spec: dict[str, Any], node_bin: Path | None = None, theme: str = "dark") -> Path:
        """
        Build React dashboard from spec and data.

        Args:
            spec: Project specification
            node_bin: Path to Node.js binary (optional, for bundled Node)
            theme: Output theme ('light' or 'dark')

        Returns:
            Path to generated dashboard
        """
        from kie.export.react_builder import ReactDashboardBuilder

        # Use deterministic data file selection (same as EDA/analyze)
        selected_file = self._load_data_file_selection() or self._select_data_file()

        if not selected_file:
            raise ValueError(
                "No data files found in data/ directory. "
                "Supported formats: CSV, XLSX, Parquet, JSON. "
                "Run /eda first to analyze your data."
            )

        data_path = selected_file

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
            column_mapping=column_mapping,  # Phase 5: Pass intelligent selections + overrides
            theme=theme  # Apply user-selected output theme
        )

        # Output directory
        exports_dir = self.project_root / "exports" / "dashboard"

        # Charts directory
        charts_dir = self.project_root / "outputs" / "charts"

        # Build React dashboard (KDS COMPLIANT)
        # If using bundled Node, temporarily add to PATH for npm commands
        env_override = None
        if node_bin and node_bin != Path("node"):
            # Bundled Node - add bin dir to PATH
            node_bin_dir = node_bin.parent
            current_path = os.environ.get("PATH", "")
            env_override = os.environ.copy()
            env_override["PATH"] = f"{node_bin_dir}{os.pathsep}{current_path}"

        # Store original env and apply override if needed
        original_env = None
        if env_override:
            original_env = os.environ.copy()
            os.environ.update(env_override)

        try:
            dashboard_path = builder.build_dashboard(
                data_path=data_path,
                charts_dir=charts_dir,
                output_dir=exports_dir,
                theme_mode=spec.get("preferences", {}).get("theme", {}).get("mode", "dark")
            )
            return dashboard_path
        finally:
            # Restore original environment
            if original_env:
                os.environ.clear()
                os.environ.update(original_env)

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

        # Find data file using deterministic selection
        if not data_file:
            selected_file = self._select_data_file()
            if not selected_file:
                log("ERROR: No data files found in data/ folder")
                print()
                print("No data files found.")
                print()
                print("Options:")
                print("  1. Add your data file to data/ folder")
                print("  2. Run /sampledata install for demo data")
                print()
                return {
                    "success": False,
                    "message": "No data files found. Add a file to data/ or run /sampledata install.",
                }
            data_file = str(selected_file)
            self._save_data_file_selection(selected_file)
            log(f"Auto-selected data file: {data_file}")

            # Check if using sample data
            is_sample_data = selected_file.name == "sample_data.csv"
            if is_sample_data:
                log("WARNING: Using sample data (DEMO mode)")
        else:
            data_file = str(self.project_root / data_file)
            is_sample_data = Path(data_file).name == "sample_data.csv"
            log(f"Using specified data file: {data_file}")

        # Run EDA
        try:
            log("Running EDA analysis...")
            eda = EDA()
            profile = eda.analyze(data_file)
            log(f"Analysis complete: {profile.rows} rows, {profile.columns} columns")

            # Save profile (both YAML and JSON for compatibility)
            profile_path = self.project_root / "outputs" / "eda_profile.yaml"
            profile_path.parent.mkdir(parents=True, exist_ok=True)

            import yaml
            profile_dict = profile.to_dict()

            # Save YAML
            with open(profile_path, "w") as f:
                yaml.dump(profile_dict, f, default_flow_style=False)
            log(f"Profile saved to: {profile_path}")

            # Also save JSON (for better compatibility with skills)
            import json
            json_path = self.project_root / "outputs" / "eda_profile.json"
            with open(json_path, "w") as f:
                json.dump(profile_dict, f, indent=2, default=str)
            log(f"Profile also saved as JSON: {json_path}")

            # Get suggestions
            suggestions = eda.suggest_analysis()
            log(f"Generated {len(suggestions)} analysis suggestions")

            log("EDA command completed successfully")

            # Update Rails state
            from kie.state import update_rails_state
            update_rails_state(self.project_root, "eda", success=True)

            # Execute EDA stage skills
            skill_results = {}
            try:
                from kie.skills import get_registry, SkillContext

                registry = get_registry()

                # Build skill context
                skill_context = SkillContext(
                    project_root=self.project_root,
                    current_stage="eda",
                    artifacts={
                        "selected_data_file": data_file,
                        "eda_profile": str(profile_path),
                        "is_sample_data": is_sample_data,
                    },
                    evidence_ledger_id=None,  # No ledger for direct calls
                )

                # Execute skills for eda stage
                results = registry.execute_skills_for_stage("eda", skill_context)
                skill_results = results

                log(f"Executed {len(results)} skills for eda stage")
                for skill_id, result in results.items():
                    if result.success:
                        log(f"  ✓ {skill_id}: {list(result.artifacts.keys())}")
                    else:
                        log(f"  ✗ {skill_id}: {result.errors}")

            except Exception as e:
                log(f"Warning: Skill execution failed: {e}")
                # Don't fail the command if skills fail
                import traceback
                log(f"Traceback: {traceback.format_exc()}")

            return {
                "success": True,
                "profile": profile.to_dict(),
                "suggestions": suggestions,
                "profile_saved": str(profile_path),
                "data_file": data_file,
                "is_sample_data": is_sample_data,
                "log_file": str(log_file),
                "skill_results": skill_results,
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
        # INTENT GATE: Check if intent is clarified
        from kie.state import is_intent_clarified, print_intent_required_message

        if not is_intent_clarified(self.project_root):
            # Intent not clarified - print guidance and block
            print_intent_required_message()
            return {
                "success": False,
                "blocked": True,
                "message": "Intent clarification required. Use: /intent set \"<objective>\" or run /interview",
            }

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

            # NOTE: Skills (Insight Brief, Run Story) now invoked via ObservabilityHooks
            # This removes hardcoded skill logic from handler.py
            # Skills execute based on stage_scope declared in registry

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
        # INTENT GATE: Check if intent is clarified
        from kie.state import is_intent_clarified, print_intent_required_message

        if not is_intent_clarified(self.project_root):
            # Intent not clarified - print guidance and block
            print_intent_required_message()
            return {
                "success": False,
                "blocked": True,
                "message": "Intent clarification required. Use: /intent set \"<objective>\" or run /interview",
            }

        self.handle_status()

        # List available outputs
        previews = {
            "charts": [],
            "tables": [],
            "maps": [],
            "deliverables": [],
            "exports": [],
        }

        outputs_dir = self.project_root / "outputs"

        # Check for chart JSON configs
        if (outputs_dir / "charts").exists():
            previews["charts"] = [f.name for f in (outputs_dir / "charts").glob("*.json")]

        # Check for table JSON
        if (outputs_dir / "tables").exists():
            previews["tables"] = [f.name for f in (outputs_dir / "tables").glob("*.json")]

        # Check for map HTML
        if (outputs_dir / "maps").exists():
            previews["maps"] = [f.name for f in (outputs_dir / "maps").glob("*.html")]

        # Check for deliverables (PPT, dashboard)
        if outputs_dir.exists():
            # PowerPoint presentations
            ppt_files = list(outputs_dir.glob("*.pptx"))
            if ppt_files:
                previews["deliverables"].extend([str(f.relative_to(self.project_root)) for f in ppt_files])

            # Dashboard build
            dashboard_index = outputs_dir / "dashboard" / "index.html"
            if dashboard_index.exists():
                previews["deliverables"].append(str(dashboard_index.relative_to(self.project_root)))

        exports_dir = self.project_root / "exports"
        if exports_dir.exists():
            previews["exports"] = [f.name for f in exports_dir.glob("*") if f.is_file()]

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
                len(previews["deliverables"]),
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

    def handle_go(self, full: bool = False) -> dict[str, Any]:
        """
        Handle /go command - Golden Path consultant entrypoint.

        Routes consultant through workflow based on rails_state.json.

        Args:
            full: If True, execute sequential stages until preview or blocked.
                  If False (default), execute EXACTLY ONE next action.

        Returns:
            Result dict with executed_command, evidence_ledger_id, and next_step
        """
        # Check for Showcase Mode FIRST (before any other logic)
        from kie.showcase import should_activate_showcase, run_showcase, mark_showcase_completed

        if should_activate_showcase(self.project_root):
            # Run showcase mode
            result = run_showcase(self.project_root)

            # Mark as completed
            mark_showcase_completed(self.project_root)

            return result

        def executor() -> dict[str, Any]:
            """Execute /go logic (wrapped by observability + enforcement)."""
            from kie.state import load_rails_state

            # Load rails_state to determine next action
            rails_state = load_rails_state(self.project_root)
            completed = rails_state.get("completed_stages", [])
            workflow_started = rails_state.get("workflow_started", False)

            # FULL MODE: Chain stages until preview or blocked
            if full:
                return self._execute_full_mode(completed, workflow_started)

            # DEFAULT MODE: Execute EXACTLY ONE next action
            return self._execute_single_step(completed, workflow_started)

        # Wrap with observability + enforcement like other commands
        return self._with_observability("go", {"full": full}, executor)

    def _execute_single_step(self, completed: list[str], workflow_started: bool) -> dict[str, Any]:
        """
        Execute EXACTLY ONE next action based on rails_state.

        Args:
            completed: List of completed stages from rails_state
            workflow_started: Whether workflow has started

        Returns:
            Result dict with executed_command and next_step
        """
        # INTENT GATE: Check before running analyze/build/preview stages
        from kie.state import is_intent_clarified, print_intent_required_message

        # Determine if next stage requires intent
        next_stage_requires_intent = False
        if "eda" in completed and "analyze" not in completed:
            next_stage_requires_intent = True
        elif "analyze" in completed and "build" not in completed:
            next_stage_requires_intent = True
        elif "build" in completed and "preview" not in completed:
            next_stage_requires_intent = True

        if next_stage_requires_intent and not is_intent_clarified(self.project_root):
            # Intent not clarified - print guidance and block
            print_intent_required_message()
            return {
                "success": False,
                "blocked": True,
                "message": "Intent clarification required. Use: /intent set \"<objective>\" or run /interview",
            }

        # CASE 1: Project not bootstrapped
        if not workflow_started:
            result = self.handle_startkie()
            result["executed_command"] = "startkie"
            return result

        # CASE 2: Startkie complete, spec not initialized
        if "startkie" in completed and "spec" not in completed:
            result = self.handle_spec(init=True)
            result["executed_command"] = "spec"
            return result

        # CASE 3: Spec complete, check if data present
        if "spec" in completed and "eda" not in completed:
            # Check for data files (read-only signal, NOT workflow authority)
            data_dir = self.project_root / "data"
            has_data = False
            if data_dir.exists():
                data_files = [
                    f for f in data_dir.iterdir()
                    if f.is_file() and f.name != ".gitkeep"
                ]
                has_data = len(data_files) > 0

            if not has_data:
                # EMIT GUIDANCE (do NOT run EDA without data)
                return {
                    "success": True,
                    "executed_command": "guidance",
                    "message": "Spec complete. Add data files to data/ directory to continue.",
                    "next_step": "Add CSV/Excel files to data/ folder, then run /go again (or /eda directly)",
                }

            # Data present - execute EDA
            result = self.handle_eda()
            result["executed_command"] = "eda"
            return result

        # CASE 4: EDA complete, ready for analyze
        if "eda" in completed and "analyze" not in completed:
            result = self.handle_analyze()
            result["executed_command"] = "analyze"
            return result

        # CASE 5: Analyze complete, ready for build
        if "analyze" in completed and "build" not in completed:
            result = self.handle_build(target="all")
            result["executed_command"] = "build"
            return result

        # CASE 6: Build complete, ready for preview
        if "build" in completed and "preview" not in completed:
            result = self.handle_preview()
            result["executed_command"] = "preview"
            return result

        # CASE 7: All stages complete
        return {
            "success": True,
            "executed_command": "complete",
            "message": "Workflow complete! All stages finished.",
            "next_step": "Run /preview to review outputs, or /validate for quality checks",
        }

    def _execute_full_mode(self, completed: list[str], workflow_started: bool) -> dict[str, Any]:
        """
        Execute sequential stages until preview or blocked.

        Args:
            completed: List of completed stages from rails_state
            workflow_started: Whether workflow has started

        Returns:
            Result dict with stages_executed list
        """
        from kie.state import load_rails_state

        stages_executed = []
        current_completed = completed.copy()

        # Define stage execution order
        stage_order = ["startkie", "spec", "eda", "analyze", "build", "preview"]

        for stage in stage_order:
            # Skip already completed stages
            if stage in current_completed:
                continue

            # Execute next stage
            try:
                if stage == "startkie":
                    result = self.handle_startkie()
                elif stage == "spec":
                    result = self.handle_spec(init=True)
                elif stage == "eda":
                    # Check for data before running EDA
                    data_dir = self.project_root / "data"
                    has_data = False
                    if data_dir.exists():
                        data_files = [
                            f for f in data_dir.iterdir()
                            if f.is_file() and f.name != ".gitkeep"
                        ]
                        has_data = len(data_files) > 0

                    if not has_data:
                        # BLOCKED: No data
                        return {
                            "success": True,
                            "executed_command": "full",
                            "stages_executed": stages_executed,
                            "blocked_at": "eda",
                            "message": "Stopped: No data files in data/ directory",
                            "next_step": "Add CSV/Excel files to data/ folder, then run /go --full again",
                        }

                    result = self.handle_eda()
                elif stage == "analyze":
                    result = self.handle_analyze()
                elif stage == "build":
                    result = self.handle_build(target="all")
                elif stage == "preview":
                    result = self.handle_preview()

                # Check if stage succeeded
                if not result.get("success", False):
                    # BLOCKED: Stage failed
                    return {
                        "success": True,
                        "executed_command": "full",
                        "stages_executed": stages_executed,
                        "blocked_at": stage,
                        "message": f"Stopped at {stage}: {result.get('message', 'Stage failed')}",
                        "next_step": f"Fix issues with /{stage}, then run /go --full again",
                    }

                # Stage succeeded
                stages_executed.append({
                    "stage": stage,
                    "success": True,
                })

                # Reload rails_state to get updated completed list
                rails_state = load_rails_state(self.project_root)
                current_completed = rails_state.get("completed_stages", [])

            except Exception as e:
                # BLOCKED: Exception during stage
                return {
                    "success": True,
                    "executed_command": "full",
                    "stages_executed": stages_executed,
                    "blocked_at": stage,
                    "message": f"Stopped at {stage}: {str(e)}",
                    "next_step": f"Fix issues with /{stage}, then run /go --full again",
                }

        # All stages completed
        return {
            "success": True,
            "executed_command": "full",
            "stages_executed": stages_executed,
            "message": f"Full workflow complete! Executed {len(stages_executed)} stages.",
            "next_step": "Run /validate for quality checks, or /preview to review outputs",
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
