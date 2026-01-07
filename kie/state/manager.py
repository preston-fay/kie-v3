"""
State Management System

Centralized state tracking for KIE v3 projects.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class StateType(str, Enum):
    """State types."""

    PROJECT = "project"
    INTERVIEW = "interview"
    WORKFLOW = "workflow"
    BUILD = "build"
    VALIDATION = "validation"


@dataclass
class StateSnapshot:
    """Snapshot of system state at a point in time."""

    timestamp: datetime
    state_type: StateType
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


class StateManager:
    """
    Centralized state management for KIE v3.

    Manages:
    - Project state (spec, configuration)
    - Interview state (requirements gathering)
    - Workflow state (stage tracking)
    - Build state (task execution)
    - Validation state (QC results)

    All state persisted to project_state/ directory.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize state manager.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.state_dir = self.project_root / "project_state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # State file paths
        self.paths = {
            StateType.PROJECT: self.state_dir / "spec.yaml",
            StateType.INTERVIEW: self.state_dir / "interview_state.yaml",
            StateType.WORKFLOW: self.state_dir / "workflow_state.yaml",
            StateType.BUILD: self.state_dir / "build_state.json",
            StateType.VALIDATION: self.state_dir / "validation_state.json",
        }

        # History directory
        self.history_dir = self.state_dir / "history"
        self.history_dir.mkdir(exist_ok=True)

    def load_state(self, state_type: StateType) -> dict[str, Any] | None:
        """
        Load state by type.

        Args:
            state_type: Type of state to load

        Returns:
            State dict or None if not found
        """
        path = self.paths[state_type]

        if not path.exists():
            return None

        if path.suffix == ".yaml":
            with open(path) as f:
                return yaml.safe_load(f)
        else:
            with open(path) as f:
                return json.load(f)

    def save_state(
        self,
        state_type: StateType,
        data: dict[str, Any],
        create_snapshot: bool = True,
    ) -> None:
        """
        Save state by type.

        Args:
            state_type: Type of state
            data: State data
            create_snapshot: Whether to create history snapshot
        """
        path = self.paths[state_type]

        # Add timestamp
        if "updated_at" not in data:
            data["updated_at"] = datetime.now().isoformat()

        # Save
        if path.suffix == ".yaml":
            with open(path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)

        # Create snapshot
        if create_snapshot:
            self.create_snapshot(state_type, data)

    def create_snapshot(self, state_type: StateType, data: dict[str, Any]) -> None:
        """
        Create historical snapshot.

        Args:
            state_type: State type
            data: State data
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"{state_type.value}_{timestamp}.yaml"
        snapshot_path = self.history_dir / snapshot_name

        with open(snapshot_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_project_state(self) -> dict[str, Any] | None:
        """Get project spec state."""
        return self.load_state(StateType.PROJECT)

    def get_interview_state(self) -> dict[str, Any] | None:
        """Get interview state."""
        return self.load_state(StateType.INTERVIEW)

    def get_workflow_state(self) -> dict[str, Any] | None:
        """Get workflow state."""
        return self.load_state(StateType.WORKFLOW)

    def get_build_state(self) -> dict[str, Any] | None:
        """Get build state."""
        return self.load_state(StateType.BUILD)

    def get_validation_state(self) -> dict[str, Any] | None:
        """Get validation state."""
        return self.load_state(StateType.VALIDATION)

    def get_all_states(self) -> dict[StateType, dict[str, Any] | None]:
        """
        Get all states.

        Returns:
            Dict mapping state types to their data
        """
        return {state_type: self.load_state(state_type) for state_type in StateType}

    def get_state_summary(self) -> dict[str, Any]:
        """
        Get summary of all states.

        Returns:
            Summary dict
        """
        states = self.get_all_states()

        summary = {
            "project_initialized": states[StateType.PROJECT] is not None,
            "interview_complete": False,
            "workflow_stage": "not_started",
            "build_status": "not_started",
            "validation_passed": False,
        }

        # Interview status
        if states[StateType.INTERVIEW]:
            interview = states[StateType.INTERVIEW]
            summary["interview_complete"] = interview.get("has_project_name", False) and interview.get(
                "has_objective", False
            )

            summary["interview_completion"] = sum(
                [
                    interview.get("has_project_name", False),
                    interview.get("has_project_type", False),
                    interview.get("has_objective", False),
                    interview.get("has_data_source", False),
                    interview.get("has_deliverables", False),
                ]
            ) / 5.0 * 100

        # Workflow status
        if states[StateType.WORKFLOW]:
            workflow = states[StateType.WORKFLOW]
            summary["workflow_stage"] = workflow.get("current_stage", "not_started")
            summary["workflow_status"] = workflow.get("status", "pending")

        # Build status
        if states[StateType.BUILD]:
            build = states[StateType.BUILD]
            summary["build_status"] = build.get("status", "not_started")

        # Validation status
        if states[StateType.VALIDATION]:
            validation = states[StateType.VALIDATION]
            summary["validation_passed"] = validation.get("all_passed", False)
            summary["validation_reports"] = validation.get("total_reports", 0)

        return summary

    def reset_state(self, state_type: StateType | None = None) -> None:
        """
        Reset state(s).

        Args:
            state_type: Specific state to reset, or None for all
        """
        if state_type:
            # Reset specific state
            path = self.paths[state_type]
            if path.exists():
                # Create backup before deleting
                backup_name = f"{state_type.value}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
                backup_path = self.history_dir / backup_name

                if path.suffix == ".yaml":
                    backup_path.write_text(path.read_text())
                else:
                    backup_path.write_text(path.read_text())

                path.unlink()

        else:
            # Reset all states
            for state_type in StateType:
                self.reset_state(state_type)

    def get_history(
        self, state_type: StateType | None = None
    ) -> list[dict[str, Any]]:
        """
        Get state history.

        Args:
            state_type: Specific state type, or None for all

        Returns:
            List of historical snapshots
        """
        snapshots = []

        # Filter files
        if state_type:
            pattern = f"{state_type.value}_*.yaml"
        else:
            pattern = "*.yaml"

        # Load snapshots
        for snapshot_path in sorted(self.history_dir.glob(pattern)):
            with open(snapshot_path) as f:
                data = yaml.safe_load(f)

            # Extract timestamp from filename
            filename = snapshot_path.stem
            parts = filename.split("_")
            timestamp_str = "_".join(parts[-2:])

            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except Exception:
                timestamp = datetime.fromtimestamp(snapshot_path.stat().st_mtime)

            snapshots.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "file": snapshot_path.name,
                    "data": data,
                }
            )

        return snapshots

    def export_complete_state(self, output_path: Path | None = None) -> Path:
        """
        Export complete project state.

        Args:
            output_path: Output path (default: project_state/complete_state.yaml)

        Returns:
            Path to exported file
        """
        output_path = output_path or (self.state_dir / "complete_state.yaml")

        # Convert StateType enum keys to strings for YAML serialization
        all_states = self.get_all_states()
        states_for_yaml = {st.value: data for st, data in all_states.items()}

        complete_state = {
            "exported_at": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "states": states_for_yaml,
            "summary": self.get_state_summary(),
        }

        with open(output_path, "w") as f:
            yaml.dump(complete_state, f, default_flow_style=False, sort_keys=False)

        return output_path

    def import_state(self, import_path: Path) -> None:
        """
        Import complete project state.

        Args:
            import_path: Path to state file
        """
        with open(import_path) as f:
            imported = yaml.safe_load(f)

        # Restore states
        for state_type, data in imported["states"].items():
            if data:
                self.save_state(StateType(state_type), data, create_snapshot=False)

    def watch_state_changes(self) -> dict[str, datetime]:
        """
        Get last modified times for all states.

        Returns:
            Dict mapping state types to last modified times
        """
        changes = {}

        for state_type, path in self.paths.items():
            if path.exists():
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                changes[state_type.value] = mtime

        return changes

    def get_state_health(self) -> dict[str, Any]:
        """
        Get state health check.

        Returns:
            Health status
        """
        health = {
            "healthy": True,
            "issues": [],
            "warnings": [],
        }

        # Check for missing required states
        project_state = self.get_project_state()
        if not project_state:
            health["issues"].append("No project spec (spec.yaml) found")
            health["healthy"] = False

        # Check for stale states (not updated in 7 days)
        changes = self.watch_state_changes()
        now = datetime.now()

        for state_type, mtime in changes.items():
            age_days = (now - mtime).days

            if age_days > 7:
                health["warnings"].append(f"{state_type} not updated in {age_days} days")

        # Check for orphaned files
        for file in self.state_dir.glob("*"):
            if file.is_file() and file.suffix not in [".yaml", ".json", ".md"]:
                health["warnings"].append(f"Unexpected file: {file.name}")

        return health
