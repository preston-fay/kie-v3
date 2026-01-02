"""
KIE v3 Workflow Orchestration

Coordinates end-to-end workflows from requirements to delivery.

Workflow Stages:
1. Requirements - Conversational gathering via interview system
2. Data Loading - Load and validate data sources
3. Analysis - Find insights and patterns
4. Visualization - Create charts, tables, maps
5. Validation - Comprehensive QC checks
6. Build - Assemble deliverables
7. Delivery - Package and export
8. Complete - Workflow finished

Usage:
    from kie.workflow import WorkflowOrchestrator

    # Initialize
    orchestrator = WorkflowOrchestrator()

    # Run stages
    orchestrator.run_requirements_stage()
    orchestrator.run_data_loading_stage()
    orchestrator.run_visualization_stage()
    orchestrator.run_validation_stage()
    orchestrator.run_build_stage()
    orchestrator.run_delivery_stage()

    # Get recommendations
    next_action = orchestrator.get_next_action()

    # Check progress
    summary = orchestrator.get_workflow_summary()
"""

from kie.workflow.orchestrator import (
    WorkflowOrchestrator,
    WorkflowStage,
    WorkflowStatus,
)

__all__ = [
    "WorkflowOrchestrator",
    "WorkflowStage",
    "WorkflowStatus",
]
