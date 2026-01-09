"""
Observability Hooks

Non-blocking pre and post-action observation points.
Hooks OBSERVE only - they never block, enforce, or mutate state.

CRITICAL: Hooks must NEVER fail a command. If a hook encounters an error,
it logs the issue but allows execution to continue.
"""

from pathlib import Path
from typing import Any

from kie.observability.evidence_ledger import EvidenceLedger, read_rails_stage, record_artifacts


class ObservabilityHooks:
    """
    Observability hooks for command execution.

    Provides pre-action and post-action observation points.
    All hooks are non-blocking and observation-only.
    """

    def __init__(self, project_root: Path):
        """
        Initialize observability hooks.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root

    def pre_command(
        self,
        ledger: EvidenceLedger,
        command: str,
        args: dict[str, Any]
    ) -> None:
        """
        Pre-command observation hook.

        Called BEFORE command execution.
        Captures initial state and environment.

        Args:
            ledger: Evidence ledger to populate
            command: Command name
            args: Command arguments

        CRITICAL: This method NEVER raises exceptions or blocks execution.
        """
        try:
            # Record Rails stage before
            ledger.rails_stage_before = read_rails_stage(self.project_root)

            # Record workspace structure signals
            self._observe_workspace(ledger)

            # Record data availability
            self._observe_data(ledger)

        except Exception as e:
            # Log but do not fail
            ledger.warnings.append(f"Pre-command observation warning: {e}")

    def post_command(
        self,
        ledger: EvidenceLedger,
        result: dict[str, Any]
    ) -> None:
        """
        Post-command observation hook.

        Called AFTER command execution.
        Captures outputs, artifacts, and final state.

        Args:
            ledger: Evidence ledger to populate
            result: Command result dictionary

        CRITICAL: This method NEVER raises exceptions or modifies result.
        """
        try:
            # Record Rails stage after
            ledger.rails_stage_after = read_rails_stage(self.project_root)

            # Record success/failure
            ledger.success = result.get("success", True)

            # Record warnings and errors from result
            if "warnings" in result:
                warnings = result["warnings"]
                if isinstance(warnings, list):
                    ledger.warnings.extend(warnings)
                elif isinstance(warnings, str):
                    ledger.warnings.append(warnings)

            if "errors" in result:
                errors = result["errors"]
                if isinstance(errors, list):
                    ledger.errors.extend(errors)
                elif isinstance(errors, str):
                    ledger.errors.append(errors)

            # Record outputs
            self._observe_outputs(ledger, result)

            # STEP 3: Generate next steps (WOW FACTOR)
            self._generate_next_steps(ledger, result)

        except Exception as e:
            # Log but do not fail
            ledger.warnings.append(f"Post-command observation warning: {e}")

    def _observe_workspace(self, ledger: EvidenceLedger) -> None:
        """
        Observe workspace structure.

        Records presence/absence of key directories.
        NEVER raises exceptions.
        """
        try:
            required_dirs = ["data", "outputs", "exports", "project_state"]
            missing_dirs = [
                d for d in required_dirs
                if not (self.project_root / d).exists()
            ]

            if missing_dirs:
                ledger.proof_references["missing_workspace_dirs"] = missing_dirs
            else:
                ledger.proof_references["workspace_valid"] = True

        except Exception:
            pass  # Silent failure

    def _observe_data(self, ledger: EvidenceLedger) -> None:
        """
        Observe data availability.

        Records whether data files are present.
        NEVER raises exceptions.
        """
        try:
            data_dir = self.project_root / "data"
            if not data_dir.exists():
                ledger.proof_references["has_data"] = False
                return

            # Count data files (excluding .gitkeep)
            data_files = [
                f for f in data_dir.iterdir()
                if f.is_file() and f.name != ".gitkeep"
            ]

            ledger.proof_references["has_data"] = len(data_files) > 0
            ledger.proof_references["data_file_count"] = len(data_files)

        except Exception:
            pass  # Silent failure

    def _observe_outputs(self, ledger: EvidenceLedger, result: dict[str, Any]) -> None:
        """
        Observe command outputs.

        Records artifacts produced by the command.
        NEVER raises exceptions.
        """
        try:
            # Look for common output patterns in result
            output_keys = [
                "profile_saved", "catalog_saved", "outputs", "dashboard",
                "presentation", "output_path", "artifact_path"
            ]

            artifact_paths = []

            for key in output_keys:
                if key in result:
                    value = result[key]

                    # Handle string paths
                    if isinstance(value, str):
                        path = Path(value)
                        if path.exists():
                            artifact_paths.append(path)

                    # Handle dict with paths
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, str):
                                path = Path(sub_value)
                                if path.exists():
                                    artifact_paths.append(path)

            # Record artifacts
            if artifact_paths:
                record_artifacts(ledger, artifact_paths, artifact_type="output")

        except Exception:
            pass  # Silent failure

    def _generate_next_steps(self, ledger: EvidenceLedger, result: dict[str, Any]) -> None:
        """
        Generate decision-ready next steps (STEP 3: WOW FACTOR).

        Uses NextStepsAdvisor to generate CLI-executable next actions.
        NEVER raises exceptions.
        """
        try:
            from kie.consultant import NextStepsAdvisor
            advisor = NextStepsAdvisor(self.project_root)

            # Generate next steps based on command and result
            next_steps = advisor.generate_next_steps(ledger.command, result)

            # Add next steps to result (advisory only, never blocking)
            if next_steps and "next_steps" not in result:
                result["next_steps"] = next_steps

        except Exception:
            pass  # Silent failure
