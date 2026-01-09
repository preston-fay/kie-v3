"""
Rails State Management

Tracks progress through the KIE Rails workflow:
startkie → spec → eda → analyze → build → preview

This module provides deterministic, CLI-only state tracking.
Claude NEVER writes this file - only CLI handlers mutate state.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class RailsState:
    """Manages Rails workflow state tracking."""

    STAGES = [
        "startkie",   # Workspace initialized
        "spec",       # Requirements gathered
        "eda",        # Data explored
        "analyze",    # Insights extracted
        "build",      # Deliverables created
        "preview"     # Outputs reviewed
    ]

    def __init__(self, project_root: Path):
        """Initialize Rails state manager."""
        self.project_root = project_root
        self.state_path = project_root / "project_state" / "rails_state.json"

    def load(self) -> dict[str, Any]:
        """
        Load current Rails state.

        Returns:
            State dict with completed_stages, current_stage, last_updated
        """
        if not self.state_path.exists():
            return {
                "completed_stages": [],
                "current_stage": None,
                "last_updated": None,
                "workflow_started": False
            }

        with open(self.state_path) as f:
            return json.load(f)

    def update(self, stage: str, success: bool = True) -> dict[str, Any]:
        """
        Update Rails state after command execution.

        Args:
            stage: Stage name (must be in STAGES)
            success: Whether command succeeded

        Returns:
            Updated state dict
        """
        if stage not in self.STAGES:
            raise ValueError(f"Invalid stage: {stage}. Must be one of {self.STAGES}")

        state = self.load()

        if success:
            # Mark stage as completed
            if stage not in state["completed_stages"]:
                state["completed_stages"].append(stage)

            # Update current stage
            state["current_stage"] = stage
            state["workflow_started"] = True

        # Update timestamp
        state["last_updated"] = datetime.now().isoformat()

        # Write state
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2)

        return state

    def suggest_next(self) -> str | None:
        """
        Suggest next Rails command based on current state.

        Returns:
            Next command name or None if workflow complete
        """
        state = self.load()

        if not state["workflow_started"]:
            return "startkie"

        completed = state["completed_stages"]

        # Find first incomplete stage
        for stage in self.STAGES:
            if stage not in completed:
                return stage

        # All stages complete
        return None

    def get_progress_summary(self) -> dict[str, Any]:
        """
        Get human-readable progress summary.

        Returns:
            Dict with progress info for display
        """
        state = self.load()
        completed = state["completed_stages"]

        if not state["workflow_started"]:
            return {
                "status": "Not started",
                "progress": "0/6",
                "next_step": "Run /startkie to initialize workspace",
                "completed": [],
                "remaining": self.STAGES
            }

        remaining = [s for s in self.STAGES if s not in completed]
        progress_pct = (len(completed) / len(self.STAGES)) * 100

        next_cmd = self.suggest_next()
        next_step = f"Run /{next_cmd}" if next_cmd else "Workflow complete! Run /preview to review outputs"

        return {
            "status": "In progress" if remaining else "Complete",
            "progress": f"{len(completed)}/{len(self.STAGES)}",
            "progress_percent": round(progress_pct),
            "next_step": next_step,
            "completed": completed,
            "remaining": remaining,
            "current_stage": state.get("current_stage"),
            "last_updated": state.get("last_updated")
        }


# Module-level convenience functions
def load_rails_state(project_root: Path) -> dict[str, Any]:
    """Load Rails state for a project."""
    return RailsState(project_root).load()


def update_rails_state(project_root: Path, stage: str, success: bool = True) -> dict[str, Any]:
    """Update Rails state after command execution."""
    return RailsState(project_root).update(stage, success)


def suggest_next_command(project_root: Path) -> str | None:
    """Suggest next Rails command."""
    return RailsState(project_root).suggest_next()


def get_rails_progress(project_root: Path) -> dict[str, Any]:
    """Get Rails progress summary."""
    return RailsState(project_root).get_progress_summary()
