"""
Execution Policy Management (Constitution Section 4: Mode Gate)

Controls whether KIE operates in Rails Mode (default) or Freeform Mode.

CRITICAL CONSTRAINTS:
- Rails Mode is the default for all new projects
- Freeform Mode must be explicitly enabled by user
- Mode changes are persisted and tracked in audit trail
- Mode must be visible in /status, Trust Bundle, Evidence Ledger
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ExecutionMode(Enum):
    """Execution mode for KIE."""
    RAILS = "rails"
    FREEFORM = "freeform"


class ExecutionPolicy:
    """
    Manages execution mode policy for KIE workspace.

    Controls whether off-rails execution is allowed.
    """

    def __init__(self, project_root: Path):
        """
        Initialize execution policy manager.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)
        self.policy_path = self.project_root / "project_state" / "execution_policy.yaml"

    def get_mode(self) -> ExecutionMode:
        """
        Get current execution mode.

        Returns:
            Current execution mode (defaults to RAILS if not set)
        """
        if not self.policy_path.exists():
            return ExecutionMode.RAILS

        with open(self.policy_path) as f:
            policy = yaml.safe_load(f)
            if not policy or "mode" not in policy:
                return ExecutionMode.RAILS

            mode_str = policy["mode"]
            return ExecutionMode(mode_str) if mode_str else ExecutionMode.RAILS

    def set_mode(self, mode: ExecutionMode, set_by: str = "user") -> dict[str, Any]:
        """
        Set execution mode.

        Args:
            mode: Execution mode to set
            set_by: Who set the mode (default: "user")

        Returns:
            Dict with success status and policy info
        """
        policy_data = {
            "mode": mode.value,
            "set_at": datetime.now().isoformat(),
            "set_by": set_by,
        }

        # Ensure directory exists
        self.policy_path.parent.mkdir(parents=True, exist_ok=True)

        # Write policy
        with open(self.policy_path, "w") as f:
            yaml.dump(policy_data, f, default_flow_style=False, sort_keys=False)

        return {
            "success": True,
            "mode": mode.value,
            "set_at": policy_data["set_at"],
        }

    def is_freeform_enabled(self) -> bool:
        """
        Check if freeform mode is enabled.

        Returns:
            True if freeform mode is enabled, False otherwise
        """
        return self.get_mode() == ExecutionMode.FREEFORM

    def get_policy_info(self) -> dict[str, Any]:
        """
        Get full policy information.

        Returns:
            Dict with mode, set_at, set_by if available
        """
        mode = self.get_mode()
        result = {"mode": mode.value}

        if self.policy_path.exists():
            with open(self.policy_path) as f:
                policy = yaml.safe_load(f)
                if policy:
                    result.update({
                        "set_at": policy.get("set_at"),
                        "set_by": policy.get("set_by"),
                    })

        return result


def get_execution_mode(project_root: Path) -> ExecutionMode:
    """
    Get current execution mode for project.

    Args:
        project_root: Project root directory

    Returns:
        Current execution mode
    """
    policy = ExecutionPolicy(project_root)
    return policy.get_mode()


def is_freeform_enabled(project_root: Path) -> bool:
    """
    Check if freeform mode is enabled for project.

    Args:
        project_root: Project root directory

    Returns:
        True if freeform enabled, False otherwise
    """
    policy = ExecutionPolicy(project_root)
    return policy.is_freeform_enabled()


def print_mode_restriction_message():
    """Print message when Rails Mode blocks off-rails execution."""
    print()
    print("=" * 70)
    print("OFF-RAILS EXECUTION DISABLED (RAILS MODE)")
    print("=" * 70)
    print()
    print("Custom analysis and ad-hoc scripts are not allowed in Rails Mode.")
    print()
    print("To enable off-rails execution:")
    print("  /freeform enable")
    print()
    print("Or use KIE commands instead:")
    print("  /eda        # Exploratory data analysis")
    print("  /analyze    # Extract insights")
    print("  /build      # Create deliverables")
    print("  /preview    # View outputs")
    print()
    print("=" * 70)
    print()
