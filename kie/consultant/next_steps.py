"""
Next Steps Advisor (STEP 3: CONSULTANT WOW FACTOR)

Generates decision-ready next actions based on Rails state and artifacts.

CRITICAL CONSTRAINTS:
- Deterministic only - no generic advice
- Derives actions ONLY from rails_state + artifacts
- Every action must be CLI-executable
- Output is advisory only (never blocks)
"""

import json
from pathlib import Path
from typing import Any

from kie.paths import ArtifactPaths


class NextStepsAdvisor:
    """
    Generates deterministic next steps based on workflow state.

    Uses Rails state and completed artifacts to suggest next actions.
    All suggestions are CLI-executable commands.
    """

    def __init__(self, project_root: Path):
        """
        Initialize Next Steps Advisor.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.outputs_dir = project_root / "outputs"
        self.exports_dir = project_root / "exports"
        self.project_state_dir = project_root / "project_state"

    def generate_next_steps(
        self, command: str, result: dict[str, Any]
    ) -> list[str]:
        """
        Generate next steps based on command outcome and Rails state.

        Args:
            command: Command that was just executed
            result: Command result dictionary

        Returns:
            List of CLI-executable next steps
        """
        # Read current Rails state
        rails_state = self._read_rails_state()
        current_stage = rails_state.get("current_stage") if rails_state else None

        # Check completed artifacts
        artifacts = self._check_artifacts()

        # Generate steps based on current state
        steps = []

        # If command failed, provide recovery steps
        if not result.get("success", True):
            steps.extend(self._recovery_steps(command, result))
            return steps

        # Command succeeded - determine next logical action
        if command == "startkie":
            steps.append("/spec --init    # Define project requirements")
            steps.append("/interview      # Or use conversational requirements gathering")

        elif command == "spec":
            if artifacts["has_data"]:
                steps.append("/eda    # Analyze your data")
            else:
                steps.append("# Add data file to data/ folder (CSV/Excel/Parquet/JSON)")
                steps.append("/eda    # Then run exploratory data analysis")

        elif command == "eda":
            if artifacts["has_eda_profile"]:
                # Check if intent is clarified before recommending /analyze
                from kie.state import is_intent_clarified
                if is_intent_clarified(self.project_root):
                    steps.append("/analyze    # Extract insights from your data")
                else:
                    # Intent not set - guide user to set it first
                    steps.append("/intent set \"<one sentence>\"    # Set your objective first")
                    steps.append("/interview                        # Or use conversational requirements gathering")

        elif command == "analyze":
            if artifacts["has_insights_catalog"]:
                steps.append("/build presentation    # Generate PowerPoint deck")
                steps.append("/build dashboard       # Or create interactive dashboard")
                steps.append("/validate              # Run quality checks before delivery")

        elif command == "build":
            build_target = result.get("target", "unknown")
            if build_target == "dashboard" and artifacts["has_dashboard"]:
                steps.append("cd exports/dashboard && npm install && npm run dev")
                steps.append("# Dashboard will launch at http://localhost:5173")
            elif build_target == "presentation" and artifacts["has_presentation"]:
                steps.append("# Open exports/presentation.pptx")
                steps.append("/preview    # Preview all deliverables")
            else:
                steps.append("/preview    # Preview generated outputs")

        elif command == "validate":
            validation_passed = result.get("validation_passed", False)
            if validation_passed:
                steps.append("# ✓ All quality checks passed - ready for delivery")
            else:
                steps.append("# Review validation errors above")
                steps.append("# Fix issues and re-run /validate")

        # Add context-aware suggestions based on what's missing
        missing_steps = self._suggest_missing_steps(artifacts, current_stage)
        steps.extend(missing_steps)

        return steps

    def _read_rails_state(self) -> dict[str, Any] | None:
        """Read current Rails state."""
        rails_state_path = self.project_state_dir / "rails_state.json"
        if not rails_state_path.exists():
            return None

        with open(rails_state_path) as f:
            return json.load(f)

    def _check_artifacts(self) -> dict[str, bool]:
        """Check which artifacts exist."""
        paths = ArtifactPaths(self.project_root)
        return {
            "has_data": self._has_data_files(),
            "has_spec": (self.project_state_dir / "spec.yaml").exists(),
            "has_eda_profile": paths.eda_profile_json().exists(),
            "has_insights_catalog": paths.insights_catalog().exists(),
            "has_insight_brief": (self.outputs_dir / "insight_brief.md").exists(),
            "has_dashboard": (self.exports_dir / "dashboard" / "package.json").exists(),
            "has_presentation": (self.exports_dir / "presentation.pptx").exists(),
        }

    def _has_data_files(self) -> bool:
        """Check if data files exist."""
        data_dir = self.project_root / "data"
        if not data_dir.exists():
            return False

        data_files = [
            f for f in data_dir.iterdir()
            if f.is_file() and f.name != ".gitkeep"
        ]
        return len(data_files) > 0

    def _recovery_steps(self, command: str, result: dict[str, Any]) -> list[str]:
        """Generate recovery steps for failed command."""
        steps = []

        # Check if enforcement blocked the command
        if "violated_invariant" in result:
            # Recovery steps are already provided by enforcement
            recovery = result.get("recovery_steps", [])
            if recovery:
                return recovery

        # Generic recovery based on command
        if command == "eda":
            steps.append("# Check that data file exists in data/ folder")
            steps.append("# Verify data file format (CSV, Excel, Parquet, or JSON)")
            steps.append("/eda    # Retry after fixing data issues")

        elif command == "analyze":
            steps.append("# Ensure /eda completed successfully first")
            steps.append("# Check outputs/eda_profile.json exists")
            steps.append("/analyze    # Retry after running /eda")

        elif command == "build":
            steps.append("# Ensure /analyze completed successfully first")
            steps.append("# Check outputs/insights_catalog.json exists")
            steps.append("/build [target]    # Retry after running /analyze")

        return steps

    def _suggest_missing_steps(
        self, artifacts: dict[str, bool], current_stage: str | None
    ) -> list[str]:
        """Suggest steps for missing artifacts."""
        steps = []

        # Only suggest if we're at an appropriate stage
        if current_stage in ["analyze", "build", "preview"]:
            # Check if Insight Brief could be generated
            if artifacts["has_insights_catalog"] and not artifacts["has_insight_brief"]:
                steps.append("# Generate consultant-ready Insight Brief:")
                steps.append("# (This will be auto-generated after /analyze in future)")

        return steps
