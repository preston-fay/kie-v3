"""
KIE v3 State Management

Centralized state tracking and persistence for all project components.

State Types:
- PROJECT: Project specification and configuration
- INTERVIEW: Requirements gathering progress
- WORKFLOW: Stage-based workflow tracking
- BUILD: Build execution status
- VALIDATION: Quality control results

All state persisted to project_state/ directory with:
- Automatic snapshots in history/
- Last modified tracking
- Health monitoring
- Complete state export/import

Usage:
    from kie.state import StateManager, StateType

    # Initialize
    manager = StateManager()

    # Load state
    project = manager.get_project_state()
    workflow = manager.get_workflow_state()

    # Save state
    manager.save_state(StateType.WORKFLOW, workflow_data)

    # Get summary
    summary = manager.get_state_summary()

    # Export everything
    manager.export_complete_state()
"""

from kie.state.manager import (
    StateManager,
    StateType,
    StateSnapshot,
)

__all__ = [
    "StateManager",
    "StateType",
    "StateSnapshot",
]
