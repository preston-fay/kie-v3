"""
Policy Engine

Determines WARN vs BLOCK decisions based on invariants and evidence.
Enforces Rails stage preconditions and evidence completeness.

CRITICAL: Policy engine NEVER mutates state. It only evaluates and decides.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class PolicyDecision(Enum):
    """Policy decision outcomes."""
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


@dataclass
class PolicyResult:
    """
    Result of a policy evaluation.

    Contains the decision (ALLOW/WARN/BLOCK) and context.
    """
    decision: PolicyDecision
    message: str = ""
    violated_invariant: str | None = None
    missing_prerequisite: str | None = None
    recovery_steps: list[str] | None = None

    @property
    def is_blocked(self) -> bool:
        """Check if action is blocked."""
        return self.decision == PolicyDecision.BLOCK

    @property
    def is_warning(self) -> bool:
        """Check if action has warnings."""
        return self.decision == PolicyDecision.WARN


class PolicyEngine:
    """
    Evaluates policies and determines enforcement actions.

    Enforces:
    - Stage preconditions (Rails workflow invariants)
    - Evidence completeness (no false success)
    - Recovery guarantees (CLI-only recovery paths)
    """

    def __init__(self, project_root: Path):
        """
        Initialize policy engine.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root

    def evaluate_preconditions(
        self,
        command: str,
        current_stage: str | None,
        context: dict[str, Any]
    ) -> PolicyResult:
        """
        Evaluate stage preconditions before command execution.

        Args:
            command: Command to execute
            current_stage: Current Rails stage
            context: Execution context (workspace state, artifacts, etc.)

        Returns:
            PolicyResult with decision and recovery path
        """
        # Map commands to required stages/preconditions
        precondition_checks = {
            "spec": self._check_spec_preconditions,
            "eda": self._check_eda_preconditions,
            "analyze": self._check_analyze_preconditions,
            "build": self._check_build_preconditions,
            "preview": self._check_preview_preconditions,
        }

        if command in precondition_checks:
            return precondition_checks[command](current_stage, context)

        # Commands without preconditions always allowed
        return PolicyResult(decision=PolicyDecision.ALLOW)

    def evaluate_evidence_completeness(
        self,
        command: str,
        result: dict[str, Any],
        artifacts: list[dict[str, str]]
    ) -> PolicyResult:
        """
        Evaluate evidence completeness after command execution.

        Blocks claims of success without artifacts.

        Args:
            command: Command that was executed
            result: Command result dictionary
            artifacts: List of artifacts produced (from Evidence Ledger)

        Returns:
            PolicyResult indicating if evidence is complete
        """
        success = result.get("success", True)

        # If command failed, no evidence required
        if not success:
            return PolicyResult(decision=PolicyDecision.ALLOW)

        # Commands that must produce artifacts
        artifact_required_commands = ["eda", "analyze", "build"]

        if command in artifact_required_commands and not artifacts:
            return PolicyResult(
                decision=PolicyDecision.BLOCK,
                message=f"Command /{command} claimed success but produced no artifacts",
                violated_invariant="Artifact Existence (Invariant 5)",
                missing_prerequisite="Output artifacts",
                recovery_steps=[
                    f"# Command claimed success without outputs - this is a bug",
                    f"# Report this issue with evidence ledger ID",
                    f"# DO NOT assume command succeeded",
                ]
            )

        return PolicyResult(decision=PolicyDecision.ALLOW)

    # ===== Precondition Checks =====

    def _check_spec_preconditions(
        self,
        current_stage: str | None,
        context: dict[str, Any]
    ) -> PolicyResult:
        """Check preconditions for /spec command."""
        # /spec requires startkie to be complete
        # Current stage should be 'startkie' or later
        valid_stages = ["startkie", "spec", "eda", "analyze", "build", "preview"]

        if current_stage not in valid_stages:
            return PolicyResult(
                decision=PolicyDecision.BLOCK,
                message="Cannot initialize spec without workspace",
                violated_invariant="Stage Preconditions (Invariant 2)",
                missing_prerequisite="Workspace initialization (/startkie)",
                recovery_steps=[
                    "/startkie    # Initialize KIE workspace first",
                    "/spec --init # Then create spec",
                ]
            )

        return PolicyResult(decision=PolicyDecision.ALLOW)

    def _check_eda_preconditions(
        self,
        current_stage: str | None,
        context: dict[str, Any]
    ) -> PolicyResult:
        """Check preconditions for /eda command."""
        # /eda requires:
        # 1. spec initialized
        # 2. data present

        has_spec = context.get("has_spec", False)
        has_data = context.get("has_data", False)

        if not has_spec:
            return PolicyResult(
                decision=PolicyDecision.BLOCK,
                message="Cannot run EDA without project spec",
                violated_invariant="Stage Preconditions (Invariant 2)",
                missing_prerequisite="spec.yaml",
                recovery_steps=[
                    "/spec --init    # Create project spec first",
                    "# Then run /eda",
                ]
            )

        if not has_data:
            return PolicyResult(
                decision=PolicyDecision.BLOCK,
                message="Cannot run EDA without data",
                violated_invariant="Stage Preconditions (Invariant 2)",
                missing_prerequisite="Data files in data/",
                recovery_steps=[
                    "# Add your CSV/Excel/Parquet file to data/ folder",
                    "# Then run /eda",
                ]
            )

        return PolicyResult(decision=PolicyDecision.ALLOW)

    def _check_analyze_preconditions(
        self,
        current_stage: str | None,
        context: dict[str, Any]
    ) -> PolicyResult:
        """Check preconditions for /analyze command."""
        # /analyze requires EDA artifacts
        eda_profile = self.project_root / "outputs" / "eda_profile.json"

        if not eda_profile.exists():
            return PolicyResult(
                decision=PolicyDecision.BLOCK,
                message="Cannot analyze without EDA profile",
                violated_invariant="Stage Preconditions (Invariant 2)",
                missing_prerequisite="outputs/eda_profile.json",
                recovery_steps=[
                    "/eda        # Run EDA first to profile data",
                    "/analyze    # Then extract insights",
                    "# ISSUE #4 FIX: If EDA was run but file missing, check outputs/ folder permissions",
                ]
            )

        return PolicyResult(decision=PolicyDecision.ALLOW)

    def _check_build_preconditions(
        self,
        current_stage: str | None,
        context: dict[str, Any]
    ) -> PolicyResult:
        """Check preconditions for /build command."""
        # /build requires analyze artifacts
        insights_catalog = self.project_root / "outputs" / "insights_catalog.json"

        if not insights_catalog.exists():
            return PolicyResult(
                decision=PolicyDecision.BLOCK,
                message="Cannot build without insights",
                violated_invariant="Stage Preconditions (Invariant 2)",
                missing_prerequisite="outputs/insights_catalog.json",
                recovery_steps=[
                    "/analyze    # Extract insights first",
                    "/build      # Then generate deliverables",
                    "# ISSUE #4 FIX: If analyze was run but file missing, check outputs/ folder",
                ]
            )

        return PolicyResult(decision=PolicyDecision.ALLOW)

    def _check_preview_preconditions(
        self,
        current_stage: str | None,
        context: dict[str, Any]
    ) -> PolicyResult:
        """Check preconditions for /preview command."""
        # /preview requires build artifacts
        dashboard_dir = self.project_root / "exports" / "dashboard"

        if not dashboard_dir.exists():
            return PolicyResult(
                decision=PolicyDecision.BLOCK,
                message="Cannot preview without build artifacts",
                violated_invariant="Stage Preconditions (Invariant 2)",
                missing_prerequisite="exports/dashboard/",
                recovery_steps=[
                    "/build      # Generate deliverables first",
                    "/preview    # Then preview outputs",
                ]
            )

        return PolicyResult(decision=PolicyDecision.ALLOW)


def generate_recovery_message(result: PolicyResult) -> str:
    """
    Generate formatted recovery message from policy result.

    Args:
        result: Policy result with block details

    Returns:
        Formatted recovery message
    """
    if not result.is_blocked:
        return ""

    lines = []
    lines.append("=" * 60)
    lines.append("❌ ACTION BLOCKED")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Reason: {result.message}")
    lines.append("")

    if result.violated_invariant:
        lines.append(f"Violated: {result.violated_invariant}")

    if result.missing_prerequisite:
        lines.append(f"Missing: {result.missing_prerequisite}")

    if result.recovery_steps:
        lines.append("")
        lines.append("Recovery:")
        for step in result.recovery_steps:
            lines.append(f"  {step}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
