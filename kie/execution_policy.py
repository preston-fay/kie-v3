"""
Execution Policy Management

Manages project execution mode (rails vs freeform) to prevent off-rails
execution without explicit user permission.

CRITICAL: Default mode is "rails" - forbids ad-hoc scripts and custom analysis.
Freeform mode requires explicit user opt-in via /freeform enable.
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml

ExecutionMode = Literal["rails", "freeform"]


class ExecutionPolicy:
    """
    Manages execution mode preference for KIE projects.

    Modes:
    - rails (default): Forbids off-rails execution (ad-hoc scripts, matplotlib, custom analysis)
    - freeform: Allows custom analysis after explicit user opt-in

    Storage: project_state/execution_policy.yaml
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
            Current execution mode ("rails" or "freeform")
            Defaults to "rails" if not set
        """
        if not self.policy_path.exists():
            return "rails"

        try:
            with open(self.policy_path) as f:
                data = yaml.safe_load(f)

            if not data or "mode" not in data:
                return "rails"

            mode = data["mode"]
            if mode not in ["rails", "freeform"]:
                return "rails"

            return mode
        except Exception:
            return "rails"

    def set_mode(self, mode: ExecutionMode, set_by: str = "user") -> None:
        """
        Set execution mode.

        Args:
            mode: Execution mode to set ("rails" or "freeform")
            set_by: Who set the mode (default: "user")

        Raises:
            ValueError: If mode is invalid
        """
        if mode not in ["rails", "freeform"]:
            raise ValueError(f"Invalid execution mode: {mode}. Must be 'rails' or 'freeform'")

        # Ensure project_state directory exists
        policy_dir = self.policy_path.parent
        policy_dir.mkdir(parents=True, exist_ok=True)

        # Build policy data
        policy_data = {
            "mode": mode,
            "set_at": datetime.now().isoformat(),
            "set_by": set_by,
        }

        # Write to file
        with open(self.policy_path, "w") as f:
            yaml.dump(policy_data, f, default_flow_style=False)

    def is_freeform_enabled(self) -> bool:
        """
        Check if freeform mode is enabled.

        Returns:
            True if freeform mode is enabled, False otherwise
        """
        return self.get_mode() == "freeform"

    def is_rails_mode(self) -> bool:
        """
        Check if rails mode is active.

        Returns:
            True if rails mode is active, False otherwise
        """
        return self.get_mode() == "rails"

    def get_policy_info(self) -> dict:
        """
        Get full policy information.

        Returns:
            Dict with mode, set_at, set_by (or defaults)
        """
        if not self.policy_path.exists():
            return {
                "mode": "rails",
                "set_at": None,
                "set_by": "default",
            }

        try:
            with open(self.policy_path) as f:
                data = yaml.safe_load(f)

            if not data:
                return {
                    "mode": "rails",
                    "set_at": None,
                    "set_by": "default",
                }

            return {
                "mode": data.get("mode", "rails"),
                "set_at": data.get("set_at"),
                "set_by": data.get("set_by", "default"),
            }
        except Exception:
            return {
                "mode": "rails",
                "set_at": None,
                "set_by": "default",
            }
