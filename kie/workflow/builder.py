"""
Workflow Builder

Builds dynamic interviews and execution plans based on detected workflow.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml

from kie.workflow.detector import DetectedWorkflow, WorkflowPhase
from kie.interview.schema import SlotDefinition, SlotType, ProjectType, RequirementSchema


@dataclass
class DynamicQuestion:
    """A question in the dynamic interview."""
    slot_name: str
    question: str
    slot_type: SlotType
    options: Optional[List[str]] = None
    required: bool = True
    default: Any = None
    help_text: Optional[str] = None
    phase: Optional[WorkflowPhase] = None


@dataclass
class DynamicInterview:
    """A dynamically generated interview based on workflow."""
    workflow: DetectedWorkflow
    questions: List[DynamicQuestion]
    filled_values: Dict[str, Any] = field(default_factory=dict)

    @property
    def remaining_questions(self) -> List[DynamicQuestion]:
        """Get questions not yet answered."""
        return [q for q in self.questions if q.slot_name not in self.filled_values]

    @property
    def is_complete(self) -> bool:
        """Check if all required questions are answered."""
        required = [q for q in self.questions if q.required]
        return all(q.slot_name in self.filled_values for q in required)

    def fill(self, slot_name: str, value: Any):
        """Fill a slot value."""
        self.filled_values[slot_name] = value

    def get_next_question(self) -> Optional[DynamicQuestion]:
        """Get the next unanswered question."""
        for q in self.questions:
            if q.slot_name not in self.filled_values:
                return q
        return None

    def to_spec(self) -> Dict[str, Any]:
        """Convert to spec.yaml format."""
        spec = {
            "project": {
                "name": self.filled_values.get("project_name", "Untitled"),
                "workflow": [p.value for p in self.workflow.phases],
                "primary_goal": self.workflow.primary_goal,
                "deliverables": self.workflow.deliverables,
            },
            "requirements": {},
        }

        # Group values by phase
        for q in self.questions:
            if q.slot_name in self.filled_values:
                if q.phase:
                    phase_key = q.phase.value
                    if phase_key not in spec["requirements"]:
                        spec["requirements"][phase_key] = {}
                    spec["requirements"][phase_key][q.slot_name] = self.filled_values[q.slot_name]
                else:
                    spec["requirements"][q.slot_name] = self.filled_values[q.slot_name]

        return spec


class WorkflowBuilder:
    """
    Build dynamic interviews and execution plans from workflows.
    """

    # Question templates for each phase
    PHASE_QUESTIONS: Dict[WorkflowPhase, List[Dict[str, Any]]] = {
        WorkflowPhase.EDA: [
            {
                "slot_name": "data_questions",
                "question": "What specific aspects of the data do you want to explore?",
                "slot_type": SlotType.TEXT,
                "help_text": "e.g., distributions, correlations, missing values, outliers",
            },
        ],
        WorkflowPhase.MODELING: [
            {
                "slot_name": "target_variable",
                "question": "What are you trying to predict or classify?",
                "slot_type": SlotType.TEXT,
                "required": True,
            },
            {
                "slot_name": "model_type",
                "question": "What type of model do you need?\n1. Classification (predict categories)\n2. Regression (predict numbers)\n3. Clustering (find groups)\n4. Time series (forecast future values)\n5. Not sure (let me recommend)",
                "slot_type": SlotType.CHOICE,
                "options": ["classification", "regression", "clustering", "time_series", "recommend"],
                "default": "recommend",
            },
            {
                "slot_name": "evaluation_priority",
                "question": "What's more important for your use case?\n1. Accuracy (correct predictions)\n2. Interpretability (understand why)\n3. Speed (fast predictions)\n4. Balanced approach",
                "slot_type": SlotType.CHOICE,
                "options": ["accuracy", "interpretability", "speed", "balanced"],
                "default": "balanced",
            },
        ],
        WorkflowPhase.ANALYSIS: [
            {
                "slot_name": "business_questions",
                "question": "What business questions do you want to answer?",
                "slot_type": SlotType.LIST,
                "help_text": "List the key questions, e.g., 'What drives customer churn?'",
            },
            {
                "slot_name": "comparison_dimensions",
                "question": "What dimensions do you want to compare?\n(e.g., by region, by channel, by time period)",
                "slot_type": SlotType.TEXT,
            },
        ],
        WorkflowPhase.VISUALIZATION: [
            {
                "slot_name": "chart_types",
                "question": "What types of charts would be most useful?\n1. Bar charts (comparisons)\n2. Line charts (trends)\n3. Scatter plots (relationships)\n4. Pie/donut (composition)\n5. Heatmaps (patterns)\n6. Let me recommend",
                "slot_type": SlotType.MULTI_SELECT,
                "options": ["bar", "line", "scatter", "pie", "heatmap", "recommend"],
                "default": ["recommend"],
            },
        ],
        WorkflowPhase.DASHBOARD: [
            {
                "slot_name": "interactivity_level",
                "question": "How interactive should the dashboard be?\n1. Static (view only)\n2. Filters (slice by dimensions)\n3. Drill-down (click for details)\n4. Full (filters + drill-down + export)",
                "slot_type": SlotType.CHOICE,
                "options": ["static", "filters", "drilldown", "full"],
                "default": "filters",
            },
            {
                "slot_name": "refresh_frequency",
                "question": "How often should data refresh?\n1. One-time snapshot\n2. Daily\n3. Real-time\n4. On-demand",
                "slot_type": SlotType.CHOICE,
                "options": ["snapshot", "daily", "realtime", "on_demand"],
                "default": "snapshot",
            },
        ],
        WorkflowPhase.REPORT: [
            {
                "slot_name": "report_format",
                "question": "What format for the report?\n1. Executive summary (1-2 pages)\n2. Full analysis (5-10 pages)\n3. Technical deep-dive (10+ pages)",
                "slot_type": SlotType.CHOICE,
                "options": ["executive", "full", "technical"],
                "default": "executive",
            },
        ],
        WorkflowPhase.PRESENTATION: [
            {
                "slot_name": "presentation_length",
                "question": "How long is the presentation?\n1. 5 minutes (5-7 slides)\n2. 15 minutes (10-12 slides)\n3. 30 minutes (15-20 slides)\n4. 60 minutes (25-30 slides)",
                "slot_type": SlotType.CHOICE,
                "options": ["5min", "15min", "30min", "60min"],
                "default": "15min",
            },
            {
                "slot_name": "presentation_style",
                "question": "What's the presentation style?\n1. Data-heavy (lots of charts)\n2. Narrative (story-driven)\n3. Balanced (mix of both)",
                "slot_type": SlotType.CHOICE,
                "options": ["data_heavy", "narrative", "balanced"],
                "default": "balanced",
            },
        ],
    }

    # Common questions for all workflows
    COMMON_QUESTIONS = [
        {
            "slot_name": "project_name",
            "question": "What would you like to call this project?",
            "slot_type": SlotType.TEXT,
            "required": True,
            "default": "Untitled Analysis",
        },
        {
            "slot_name": "audience",
            "question": "Who is the audience for this work?",
            "slot_type": SlotType.TEXT,
            "required": True,
            "help_text": "e.g., executive team, marketing department, technical stakeholders",
        },
        {
            "slot_name": "design_system",
            "question": "What branding should we use?\n1. Kearney (default purple/dark theme)\n2. Client's existing brand\n3. Create new client brand",
            "slot_type": SlotType.CHOICE,
            "options": ["kearney", "client_existing", "client_new"],
            "default": "kearney",
        },
        {
            "slot_name": "timeline",
            "question": "What's the timeline?\n1. Exploratory (no deadline)\n2. This week\n3. Urgent (today/tomorrow)",
            "slot_type": SlotType.CHOICE,
            "options": ["exploratory", "this_week", "urgent"],
            "default": "exploratory",
        },
    ]

    def build_interview(self, workflow: DetectedWorkflow) -> DynamicInterview:
        """
        Build a dynamic interview for the given workflow.

        Args:
            workflow: Detected workflow with phases

        Returns:
            DynamicInterview ready to execute
        """
        questions = []

        # Add common questions first
        for q_def in self.COMMON_QUESTIONS:
            questions.append(DynamicQuestion(
                slot_name=q_def["slot_name"],
                question=q_def["question"],
                slot_type=q_def["slot_type"],
                options=q_def.get("options"),
                required=q_def.get("required", True),
                default=q_def.get("default"),
                help_text=q_def.get("help_text"),
                phase=None,
            ))

        # Add phase-specific questions
        for phase in workflow.phases:
            phase_questions = self.PHASE_QUESTIONS.get(phase, [])
            for q_def in phase_questions:
                questions.append(DynamicQuestion(
                    slot_name=q_def["slot_name"],
                    question=q_def["question"],
                    slot_type=q_def["slot_type"],
                    options=q_def.get("options"),
                    required=q_def.get("required", True),
                    default=q_def.get("default"),
                    help_text=q_def.get("help_text"),
                    phase=phase,
                ))

        return DynamicInterview(
            workflow=workflow,
            questions=questions,
        )

    def get_execution_plan(self, workflow: DetectedWorkflow) -> List[Dict[str, Any]]:
        """
        Generate an execution plan for the workflow.

        Args:
            workflow: Detected workflow

        Returns:
            List of execution steps
        """
        steps = []

        for i, phase in enumerate(workflow.phases, 1):
            step = {
                "step": i,
                "phase": phase.value,
                "command": self._phase_to_command(phase),
                "description": self._get_phase_description(phase),
                "outputs": self._get_phase_outputs(phase),
            }
            steps.append(step)

        return steps

    def _phase_to_command(self, phase: WorkflowPhase) -> str:
        """Map phase to KIE command."""
        mapping = {
            WorkflowPhase.EDA: "eda",
            WorkflowPhase.FEATURE_ENGINEERING: "feature",
            WorkflowPhase.MODELING: "model",
            WorkflowPhase.ANALYSIS: "analyze",
            WorkflowPhase.VISUALIZATION: "chart",
            WorkflowPhase.DASHBOARD: "dashboard",
            WorkflowPhase.REPORT: "report",
            WorkflowPhase.PRESENTATION: "present",
            WorkflowPhase.DATA_PIPELINE: "pipeline",
        }
        return mapping.get(phase, phase.value)

    def _get_phase_description(self, phase: WorkflowPhase) -> str:
        """Get human-readable description for phase."""
        descriptions = {
            WorkflowPhase.EDA: "Explore data structure, distributions, and quality",
            WorkflowPhase.FEATURE_ENGINEERING: "Create and select features for modeling",
            WorkflowPhase.MODELING: "Train and evaluate predictive model",
            WorkflowPhase.ANALYSIS: "Generate business insights and findings",
            WorkflowPhase.VISUALIZATION: "Create charts and visualizations",
            WorkflowPhase.DASHBOARD: "Build interactive dashboard",
            WorkflowPhase.REPORT: "Write analysis report",
            WorkflowPhase.PRESENTATION: "Create slide presentation",
            WorkflowPhase.DATA_PIPELINE: "Build data pipeline",
        }
        return descriptions.get(phase, phase.value)

    def _get_phase_outputs(self, phase: WorkflowPhase) -> List[str]:
        """Get expected outputs for phase."""
        outputs = {
            WorkflowPhase.EDA: ["outputs/eda_report.html", "outputs/data_profile.json"],
            WorkflowPhase.FEATURE_ENGINEERING: ["outputs/features.csv", "outputs/feature_importance.png"],
            WorkflowPhase.MODELING: ["outputs/model.pkl", "outputs/model_evaluation.html"],
            WorkflowPhase.ANALYSIS: ["outputs/insights.yaml", "outputs/findings.md"],
            WorkflowPhase.VISUALIZATION: ["outputs/charts/*.png"],
            WorkflowPhase.DASHBOARD: ["outputs/dashboard.html"],
            WorkflowPhase.REPORT: ["exports/report.docx"],
            WorkflowPhase.PRESENTATION: ["exports/presentation.pptx"],
            WorkflowPhase.DATA_PIPELINE: ["outputs/pipeline_config.yaml"],
        }
        return outputs.get(phase, [])


def build_dynamic_interview(workflow: DetectedWorkflow) -> DynamicInterview:
    """
    Convenience function to build a dynamic interview.

    Args:
        workflow: Detected workflow

    Returns:
        DynamicInterview
    """
    builder = WorkflowBuilder()
    return builder.build_interview(workflow)
