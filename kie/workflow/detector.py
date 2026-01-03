"""
Workflow Detector

Parses user intent and maps to a dynamic workflow sequence.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Set
import re


class WorkflowPhase(Enum):
    """Available workflow phases."""
    EDA = "eda"                      # Exploratory data analysis
    FEATURE_ENGINEERING = "feature"  # Feature creation/selection
    MODELING = "modeling"            # ML/statistical modeling
    ANALYSIS = "analysis"            # Business analysis/insights
    VISUALIZATION = "visualization"  # Charts and graphs
    DASHBOARD = "dashboard"          # Interactive dashboard
    REPORT = "report"                # Written report/document
    PRESENTATION = "presentation"    # Slide deck
    DATA_PIPELINE = "pipeline"       # ETL/data engineering


@dataclass
class DetectedWorkflow:
    """Result of workflow detection."""
    phases: List[WorkflowPhase]          # Ordered phases to execute
    primary_goal: str                     # Main objective
    deliverables: List[str]               # Expected outputs
    confidence: float                     # Detection confidence (0-1)
    suggested_questions: List[str]        # Follow-up questions needed
    raw_intent: str                       # Original user input

    @property
    def has_modeling(self) -> bool:
        return WorkflowPhase.MODELING in self.phases

    @property
    def has_dashboard(self) -> bool:
        return WorkflowPhase.DASHBOARD in self.phases

    @property
    def has_presentation(self) -> bool:
        return WorkflowPhase.PRESENTATION in self.phases

    def get_interview_slots(self) -> List[str]:
        """Get the interview slots needed for this workflow."""
        slots = ["project_name", "audience", "design_system"]

        if WorkflowPhase.EDA in self.phases:
            slots.extend(["data_questions", "analysis_depth"])

        if WorkflowPhase.MODELING in self.phases:
            slots.extend(["target_variable", "model_type", "evaluation_metrics"])

        if WorkflowPhase.ANALYSIS in self.phases:
            slots.extend(["business_questions", "kpis", "time_period"])

        if WorkflowPhase.DASHBOARD in self.phases:
            slots.extend(["interactivity_level", "refresh_frequency"])

        if WorkflowPhase.PRESENTATION in self.phases:
            slots.extend(["slide_count", "presentation_length"])

        if WorkflowPhase.REPORT in self.phases:
            slots.extend(["report_sections", "format"])

        return slots


class WorkflowDetector:
    """
    Detect workflow from natural language intent.

    Uses keyword matching and pattern recognition to understand
    what the user wants to accomplish and maps to phases.
    """

    # Keywords that indicate each phase
    PHASE_KEYWORDS: Dict[WorkflowPhase, Set[str]] = {
        WorkflowPhase.EDA: {
            "explore", "eda", "understand", "profile", "examine",
            "look at", "what's in", "overview", "summary", "describe",
            "distribution", "missing values", "outliers", "data quality"
        },
        WorkflowPhase.FEATURE_ENGINEERING: {
            "feature", "transform", "create variables", "encode",
            "normalize", "scale", "engineer", "derive", "calculate"
        },
        WorkflowPhase.MODELING: {
            "model", "modeling", "predict", "forecast", "classify", "cluster",
            "regression", "machine learning", "ml", "train", "algorithm",
            "random forest", "xgboost", "neural", "deep learning",
            "predictive", "classification", "supervised", "unsupervised"
        },
        WorkflowPhase.ANALYSIS: {
            "analyze", "analysis", "insight", "trend", "pattern",
            "compare", "segment", "breakdown", "performance", "roi",
            "kpi", "metrics", "drivers", "impact", "correlation"
        },
        WorkflowPhase.VISUALIZATION: {
            "chart", "graph", "plot", "visualize", "visualization",
            "bar chart", "line chart", "pie chart", "scatter"
        },
        WorkflowPhase.DASHBOARD: {
            "dashboard", "interactive", "drill down", "filter",
            "real-time", "monitor", "kpi board", "scorecard"
        },
        WorkflowPhase.REPORT: {
            "report", "document", "write up", "findings", "summary",
            "executive summary", "brief", "memo", "analysis document"
        },
        WorkflowPhase.PRESENTATION: {
            "presentation", "slides", "deck", "powerpoint", "pptx",
            "present", "board", "leadership", "stakeholder"
        },
        WorkflowPhase.DATA_PIPELINE: {
            "pipeline", "etl", "extract", "transform", "load",
            "ingest", "data flow", "automate", "schedule"
        },
    }

    # Common workflow patterns
    WORKFLOW_PATTERNS = [
        # Analysis -> Presentation
        (r"analyz.*\s+(and|then|to)\s+present",
         [WorkflowPhase.EDA, WorkflowPhase.ANALYSIS, WorkflowPhase.PRESENTATION]),

        # EDA -> Modeling -> Report
        (r"(explore|understand).*model.*report",
         [WorkflowPhase.EDA, WorkflowPhase.FEATURE_ENGINEERING,
          WorkflowPhase.MODELING, WorkflowPhase.REPORT]),

        # Full ML pipeline
        (r"(predict|forecast|classify).*present",
         [WorkflowPhase.EDA, WorkflowPhase.FEATURE_ENGINEERING,
          WorkflowPhase.MODELING, WorkflowPhase.VISUALIZATION,
          WorkflowPhase.PRESENTATION]),

        # Dashboard build
        (r"(build|create).*dashboard",
         [WorkflowPhase.EDA, WorkflowPhase.ANALYSIS, WorkflowPhase.DASHBOARD]),

        # Quick analysis
        (r"what.*driv(es|ing)",
         [WorkflowPhase.EDA, WorkflowPhase.ANALYSIS]),
    ]

    def detect(self, user_intent: str) -> DetectedWorkflow:
        """
        Detect workflow from user intent.

        Args:
            user_intent: Natural language description of what user wants

        Returns:
            DetectedWorkflow with phases and metadata
        """
        intent_lower = user_intent.lower()

        # Always do keyword detection first to capture all mentioned phases
        detected_phases = []
        for phase, keywords in self.PHASE_KEYWORDS.items():
            for kw in keywords:
                # Use word boundary matching for better accuracy
                pattern = r'\b' + re.escape(kw.strip()) + r'\b'
                if re.search(pattern, intent_lower):
                    detected_phases.append(phase)
                    break

        # If keyword detection found phases, use those with calculated confidence
        if detected_phases:
            confidence = min(0.85, 0.5 + 0.1 * len(detected_phases))
        else:
            # Try pattern matching as fallback for common workflows
            for pattern, phases in self.WORKFLOW_PATTERNS:
                if re.search(pattern, intent_lower):
                    return self._build_workflow(
                        phases=phases,
                        intent=user_intent,
                        confidence=0.9,
                        match_type="pattern"
                    )

            # Last resort: infer defaults
            detected_phases = self._infer_defaults(intent_lower)
            confidence = 0.5

        # Order phases logically
        detected_phases = self._order_phases(detected_phases)

        return self._build_workflow(
            phases=detected_phases,
            intent=user_intent,
            confidence=confidence,
            match_type="keyword"
        )

    def _build_workflow(
        self,
        phases: List[WorkflowPhase],
        intent: str,
        confidence: float,
        match_type: str
    ) -> DetectedWorkflow:
        """Build a DetectedWorkflow from phases."""
        # Determine primary goal
        if WorkflowPhase.MODELING in phases:
            primary_goal = "Build predictive model"
        elif WorkflowPhase.DASHBOARD in phases:
            primary_goal = "Create interactive dashboard"
        elif WorkflowPhase.PRESENTATION in phases:
            primary_goal = "Prepare presentation"
        elif WorkflowPhase.ANALYSIS in phases:
            primary_goal = "Generate business insights"
        else:
            primary_goal = "Explore and understand data"

        # Determine deliverables
        deliverables = []
        if WorkflowPhase.EDA in phases:
            deliverables.append("Data profile report")
        if WorkflowPhase.MODELING in phases:
            deliverables.append("Trained model with evaluation")
        if WorkflowPhase.ANALYSIS in phases:
            deliverables.append("Insight summary")
        if WorkflowPhase.VISUALIZATION in phases:
            deliverables.append("Charts and visualizations")
        if WorkflowPhase.DASHBOARD in phases:
            deliverables.append("Interactive dashboard")
        if WorkflowPhase.REPORT in phases:
            deliverables.append("Written report")
        if WorkflowPhase.PRESENTATION in phases:
            deliverables.append("Slide deck")

        # Determine follow-up questions
        questions = self._get_clarifying_questions(phases, confidence)

        return DetectedWorkflow(
            phases=phases,
            primary_goal=primary_goal,
            deliverables=deliverables,
            confidence=confidence,
            suggested_questions=questions,
            raw_intent=intent,
        )

    def _infer_defaults(self, intent: str) -> List[WorkflowPhase]:
        """Infer default phases when no keywords match."""
        # If they mention data at all, start with EDA
        if any(word in intent for word in ["data", "file", "csv", "dataset"]):
            return [WorkflowPhase.EDA, WorkflowPhase.ANALYSIS]

        # Default minimal workflow
        return [WorkflowPhase.EDA]

    def _order_phases(self, phases: List[WorkflowPhase]) -> List[WorkflowPhase]:
        """Order phases in logical execution sequence."""
        # Define phase order
        phase_order = [
            WorkflowPhase.EDA,
            WorkflowPhase.FEATURE_ENGINEERING,
            WorkflowPhase.MODELING,
            WorkflowPhase.ANALYSIS,
            WorkflowPhase.VISUALIZATION,
            WorkflowPhase.DASHBOARD,
            WorkflowPhase.REPORT,
            WorkflowPhase.PRESENTATION,
            WorkflowPhase.DATA_PIPELINE,
        ]

        # Always start with EDA if doing analysis
        if any(p in phases for p in [WorkflowPhase.ANALYSIS, WorkflowPhase.MODELING]):
            if WorkflowPhase.EDA not in phases:
                phases.insert(0, WorkflowPhase.EDA)

        # Sort by defined order
        return sorted(phases, key=lambda p: phase_order.index(p))

    def _get_clarifying_questions(
        self,
        phases: List[WorkflowPhase],
        confidence: float
    ) -> List[str]:
        """Get clarifying questions based on detected phases."""
        questions = []

        if confidence < 0.7:
            questions.append("Can you tell me more about your end goal?")

        if WorkflowPhase.MODELING in phases:
            questions.append("What are you trying to predict or classify?")

        if WorkflowPhase.ANALYSIS in phases:
            questions.append("What business questions do you want to answer?")

        if WorkflowPhase.PRESENTATION in phases:
            questions.append("Who is the audience for this presentation?")

        if WorkflowPhase.DASHBOARD in phases:
            questions.append("How interactive should the dashboard be?")

        return questions[:3]  # Limit to 3 questions


def detect_workflow(user_intent: str) -> DetectedWorkflow:
    """
    Convenience function to detect workflow.

    Args:
        user_intent: Natural language description

    Returns:
        DetectedWorkflow
    """
    detector = WorkflowDetector()
    return detector.detect(user_intent)
