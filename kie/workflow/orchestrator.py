"""
Workflow Orchestrator

Coordinates end-to-end KIE v3 workflows from requirements to delivery.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from kie.commands import CommandHandler
from kie.interview import InterviewEngine
from kie.validation import ValidationConfig, ValidationPipeline


class WorkflowStage(str, Enum):
    """Workflow stages."""

    NOT_STARTED = "not_started"
    REQUIREMENTS = "requirements"
    DATA_LOADING = "data_loading"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    VALIDATION = "validation"
    BUILD = "build"
    DELIVERY = "delivery"
    COMPLETE = "complete"


class WorkflowStatus(str, Enum):
    """Status of workflow."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowOrchestrator:
    """
    Orchestrates complete KIE v3 workflows.

    Manages:
    - Requirements gathering (interview)
    - Data loading and validation
    - Analysis and insight generation
    - Visualization creation
    - Output validation
    - Deliverable assembly
    - Quality control
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize orchestrator.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.state_path = self.project_root / "project_state" / "workflow_state.yaml"

        # Initialize subsystems
        self.interview = InterviewEngine(
            state_path=self.project_root / "project_state" / "interview_state.yaml"
        )

        self.validation = ValidationPipeline(
            ValidationConfig(
                strict=True,
                save_reports=True,
                report_dir=self.project_root / "project_state" / "validation_reports",
            )
        )

        self.commands = CommandHandler(project_root=self.project_root)

        # Load or initialize state
        self.state = self._load_or_init_state()

    def _load_or_init_state(self) -> dict[str, Any]:
        """Load or initialize workflow state."""
        if self.state_path.exists():
            with open(self.state_path) as f:
                return yaml.safe_load(f)

        return {
            "current_stage": WorkflowStage.NOT_STARTED.value,
            "status": WorkflowStatus.PENDING.value,
            "stages": {
                stage.value: {
                    "status": WorkflowStatus.PENDING.value,
                    "started_at": None,
                    "completed_at": None,
                    "error": None,
                }
                for stage in WorkflowStage
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def save_state(self):
        """Save workflow state."""
        self.state["updated_at"] = datetime.now().isoformat()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.state_path, "w") as f:
            yaml.dump(self.state, f, default_flow_style=False, sort_keys=False)

    def get_current_stage(self) -> WorkflowStage:
        """Get current workflow stage."""
        return WorkflowStage(self.state["current_stage"])

    def get_next_stage(self) -> WorkflowStage | None:
        """Get next workflow stage."""
        current = self.get_current_stage()

        stages_order = [
            WorkflowStage.NOT_STARTED,
            WorkflowStage.REQUIREMENTS,
            WorkflowStage.DATA_LOADING,
            WorkflowStage.ANALYSIS,
            WorkflowStage.VISUALIZATION,
            WorkflowStage.VALIDATION,
            WorkflowStage.BUILD,
            WorkflowStage.DELIVERY,
            WorkflowStage.COMPLETE,
        ]

        current_idx = stages_order.index(current)

        if current_idx < len(stages_order) - 1:
            return stages_order[current_idx + 1]

        return None

    def advance_to_stage(self, stage: WorkflowStage):
        """
        Advance to specific stage.

        Args:
            stage: Target stage
        """
        # Mark current stage as completed
        current = self.get_current_stage()
        if current != WorkflowStage.NOT_STARTED:
            self.state["stages"][current.value]["status"] = WorkflowStatus.COMPLETED.value
            self.state["stages"][current.value]["completed_at"] = datetime.now().isoformat()

        # Advance to new stage
        self.state["current_stage"] = stage.value
        self.state["stages"][stage.value]["status"] = WorkflowStatus.IN_PROGRESS.value
        self.state["stages"][stage.value]["started_at"] = datetime.now().isoformat()

        self.save_state()

    def run_requirements_stage(self) -> dict[str, Any]:
        """
        Run requirements gathering stage.

        Returns:
            Stage results
        """
        self.advance_to_stage(WorkflowStage.REQUIREMENTS)

        # Non-interactive/test flows: ensure a default theme so requirements can complete.
        try:
            from kie.config.theme_config import ProjectThemeConfig
            theme_cfg = ProjectThemeConfig(self.project_root)
            if theme_cfg.load_theme() is None:
                theme_cfg.save_theme("dark")
        except Exception:
            # Non-fatal: requirements can still proceed; missing theme will be reported if truly required.
            pass

        # Check if interview complete
        if self.interview.state.is_complete():
            # Export spec
            spec_path = self.interview.export_spec_yaml()

            return {
                "success": True,
                "stage": WorkflowStage.REQUIREMENTS.value,
                "message": "Requirements gathered successfully",
                "spec_path": str(spec_path),
                "completion": 100.0,
            }
        else:
            # Interview not complete
            completion = self.interview.state.get_completion_percentage()
            missing = self.interview.state.get_missing_required_fields()

            return {
                "success": False,
                "stage": WorkflowStage.REQUIREMENTS.value,
                "message": "Requirements incomplete",
                "completion": completion,
                "missing_fields": missing,
                "next_action": "Continue interview with /interview",
            }

    def run_data_loading_stage(self, data_path: Path | None = None) -> dict[str, Any]:
        """
        Run data loading stage.

        Args:
            data_path: Path to data file

        Returns:
            Stage results
        """
        self.advance_to_stage(WorkflowStage.DATA_LOADING)

        # Check for data in data/ folder
        data_dir = self.project_root / "data"
        data_files = list(data_dir.glob("*"))

        # Filter out hidden files
        data_files = [f for f in data_files if not f.name.startswith(".")]

        if not data_files and not data_path:
            return {
                "success": False,
                "stage": WorkflowStage.DATA_LOADING.value,
                "message": "No data files found",
                "next_action": "Add data file to data/ folder or provide path",
            }

        # Use provided path or first file found
        target_file = data_path or data_files[0]

        return {
            "success": True,
            "stage": WorkflowStage.DATA_LOADING.value,
            "message": f"Data file found: {target_file.name}",
            "data_path": str(target_file),
            "file_count": len(data_files),
        }

    def run_analysis_stage(self) -> dict[str, Any]:
        """
        Run analysis stage.

        Returns:
            Stage results
        """
        self.advance_to_stage(WorkflowStage.ANALYSIS)

        # This would integrate with the analysis engine
        # For now, just mark as ready for visualization

        return {
            "success": True,
            "stage": WorkflowStage.ANALYSIS.value,
            "message": "Analysis stage ready",
            "next_action": "Proceed to visualization",
        }

    def run_visualization_stage(self) -> dict[str, Any]:
        """
        Run visualization stage.

        Returns:
            Stage results
        """
        self.advance_to_stage(WorkflowStage.VISUALIZATION)

        # Check for generated outputs
        outputs = {
            "charts": len(list((self.project_root / "outputs" / "charts").glob("*"))),
            "tables": len(list((self.project_root / "outputs" / "tables").glob("*.json"))),
            "maps": len(list((self.project_root / "outputs" / "maps").glob("*.html"))),
        }

        total_outputs = sum(outputs.values())

        return {
            "success": True,
            "stage": WorkflowStage.VISUALIZATION.value,
            "message": f"{total_outputs} visualizations created",
            "outputs": outputs,
        }

    def run_validation_stage(self) -> dict[str, Any]:
        """
        Run validation stage.

        Returns:
            Stage results
        """
        self.advance_to_stage(WorkflowStage.VALIDATION)

        # Get validation summary
        summary = self.validation.get_pipeline_summary()

        if summary["total_reports"] == 0:
            return {
                "success": False,
                "stage": WorkflowStage.VALIDATION.value,
                "message": "No outputs validated yet",
                "next_action": "Generate outputs with validation enabled",
            }

        # Check if all passed
        all_passed = summary["failed"] == 0

        if not all_passed:
            return {
                "success": False,
                "stage": WorkflowStage.VALIDATION.value,
                "message": f"Validation failed: {summary['failed']} outputs have issues",
                "summary": summary,
                "next_action": "Fix validation issues and re-run",
            }

        return {
            "success": True,
            "stage": WorkflowStage.VALIDATION.value,
            "message": f"All {summary['passed']} outputs validated successfully",
            "summary": summary,
        }

    def run_build_stage(self) -> dict[str, Any]:
        """
        Run build stage.

        Returns:
            Stage results
        """
        self.advance_to_stage(WorkflowStage.BUILD)

        # Use command handler to build
        result = self.commands.handle_build(target="all")

        return {
            "success": result["success"],
            "stage": WorkflowStage.BUILD.value,
            "message": result["message"],
            "build_result": result,
        }

    def run_delivery_stage(self) -> dict[str, Any]:
        """
        Run delivery stage.

        Returns:
            Stage results
        """
        self.advance_to_stage(WorkflowStage.DELIVERY)

        # Check exports
        exports_dir = self.project_root / "exports"
        exports = {
            "pptx": list(exports_dir.glob("*.pptx")),
            "pdf": list(exports_dir.glob("*.pdf")),
            "excel": list(exports_dir.glob("*.xlsx")),
            "html": list(exports_dir.glob("*.html")),
        }

        total_exports = sum(len(files) for files in exports.values())

        if total_exports == 0:
            return {
                "success": False,
                "stage": WorkflowStage.DELIVERY.value,
                "message": "No deliverables found in exports/",
                "next_action": "Run /build to generate deliverables",
            }

        return {
            "success": True,
            "stage": WorkflowStage.DELIVERY.value,
            "message": f"{total_exports} deliverables ready",
            "exports": {k: [str(f) for f in v] for k, v in exports.items()},
        }

    def complete_workflow(self):
        """Mark workflow as complete."""
        self.advance_to_stage(WorkflowStage.COMPLETE)
        self.state["status"] = WorkflowStatus.COMPLETED.value
        self.save_state()

    def get_workflow_summary(self) -> dict[str, Any]:
        """
        Get complete workflow summary.

        Returns:
            Summary dict
        """
        return {
            "current_stage": self.state["current_stage"],
            "status": self.state["status"],
            "stages": self.state["stages"],
            "created_at": self.state["created_at"],
            "updated_at": self.state["updated_at"],
        }

    def get_next_action(self) -> str:
        """
        Get recommended next action.

        Returns:
            Next action recommendation
        """
        current_stage = self.get_current_stage()

        actions = {
            WorkflowStage.NOT_STARTED: "Run /interview to gather requirements",
            WorkflowStage.REQUIREMENTS: "Complete interview, then load data",
            WorkflowStage.DATA_LOADING: "Add data to data/ folder",
            WorkflowStage.ANALYSIS: "Run analysis on loaded data",
            WorkflowStage.VISUALIZATION: "Generate charts, tables, maps",
            WorkflowStage.VALIDATION: "Run /validate on outputs",
            WorkflowStage.BUILD: "Run /build to assemble deliverables",
            WorkflowStage.DELIVERY: "Review exports/ and deliver",
            WorkflowStage.COMPLETE: "Workflow complete",
        }

        return actions.get(current_stage, "Unknown stage")

    def reset_workflow(self):
        """Reset workflow to initial state."""
        self.state = self._load_or_init_state()
        self.save_state()

        # Reset subsystems
        self.interview.reset()
