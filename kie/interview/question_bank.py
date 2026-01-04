"""
Question Bank for Type-Specific Interview Questions

Centralizes all question definitions and routing logic for different project types.
Supports express (short) and full (detailed) interview modes.
"""

from typing import Dict, List, Optional
from kie.interview.schema import ProjectType


class QuestionBank:
    """Registry of type-specific question sets and routing logic."""

    # Supported project types (code-backed with builders)
    SUPPORTED_TYPES = [
        ProjectType.DASHBOARD,
        ProjectType.PRESENTATION,
    ]

    # Unsupported types with redirect messages
    UNSUPPORTED_TYPES = {
        ProjectType.ANALYTICS: "Analytics is not a standalone deliverable. Choose 'dashboard' for interactive data visualizations or 'presentation' for insight slides. Run /analyze first to generate insights for either.",
        ProjectType.MODELING: "Modeling projects not yet supported. Choose 'presentation' to present model results or 'dashboard' for model metrics visualization.",
        ProjectType.PROPOSAL: "Proposal generation not yet supported. Choose 'presentation' for pitch decks.",
        ProjectType.RESEARCH: "Research reports not yet supported. Choose 'presentation' for findings decks or 'dashboard' for research data visualization.",
        ProjectType.DATA_ENGINEERING: "Pipeline generation not yet supported. Choose 'dashboard' for data monitoring or 'presentation' for pipeline documentation.",
        ProjectType.WEBAPP: "General webapp generation not supported. Choose 'dashboard' for data visualization apps only.",
    }

    # Common questions (all types use these)
    COMMON_QUESTIONS = {
        "mode": "Do you want the express interview (fast, shorter) or the full interview (more detail)?\n\nType 'express' or 'full':",
        "project_type": "What type of deliverable do you need?\n\nSupported options: dashboard, presentation",
        "objective": "What's the main goal or decision this needs to support?\n\n(Be specific about what question you're trying to answer or what action you want to enable)",
        "data_source": "What data do you have?\n\nOptions:\n- CSV file (provide path)\n- Excel file (provide path)\n- Database (I'll ask for connection details)\n- Mock data (I'll generate sample data)",
        "theme": "Do you prefer dark mode or light mode for visuals?\n\nType 'dark' or 'light' (no default - I need your explicit choice):",
        "project_name": "What would you like to call this project?",
        # Full mode only
        "client_name": "What is the client name?",
        "audience": "Who will see these deliverables?\n\n(e.g., C-suite executives, analysts, trading desk, internal team)",
        "deadline": "When do you need this delivered?\n\n(e.g., 'December 15', 'end of week', '2 days')",
        "success_criteria": "What does success look like for this project?\n\n(How will you know if this deliverable achieved its goal?)",
        "constraints": "Are there any constraints or limitations I should know about?\n\n(e.g., budget limits, technology restrictions, data quality issues, compliance requirements)\n\n(Type 'none' if no constraints)",
    }

    # Type-specific questions
    TYPE_SPECIFIC_QUESTIONS = {
        ProjectType.DASHBOARD: {
            "dashboard_views": "How many dashboard views or tabs do you need?\n\n(e.g., '3 tabs: overview, detail, comparison' or 'single view')",
            "dashboard_filters": "What filters or controls should users have?\n\n(e.g., 'date range, region, product line' or 'none')",
            "update_frequency": "How often should data update?\n\n(e.g., 'static', 'daily refresh', 'real-time')",
        },
        ProjectType.PRESENTATION: {
            "slide_count": "Target slide count?\n\n(e.g., '10-12 slides' or 'around 8')",
            "key_message": "What's the key message or recommendation?\n\n(The main takeaway you want the audience to remember)",
            "presentation_style": "Presentation style preference?\n\n(e.g., 'data-heavy with charts', 'narrative-driven', 'visual/minimal text')",
        },
    }

    @classmethod
    def get_question_sequence(
        cls, project_type: ProjectType, mode: str
    ) -> List[str]:
        """
        Build the question sequence for a given project type and mode.

        Args:
            project_type: The project type (dashboard, presentation)
            mode: Interview mode ("express" or "full")

        Returns:
            List of question keys in order
        """
        if project_type not in cls.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported project type: {project_type}")

        # Base sequence (common to all)
        sequence = [
            "project_type",
            "objective",
            "data_source",
        ]

        # Add type-specific questions
        if project_type == ProjectType.DASHBOARD:
            sequence.extend(["dashboard_views", "dashboard_filters"])
        elif project_type == ProjectType.PRESENTATION:
            sequence.extend(["slide_count", "key_message"])

        # Add common ending questions
        sequence.extend(["theme", "project_name"])

        # Add full mode questions
        if mode == "full":
            if project_type == ProjectType.DASHBOARD:
                # Insert update_frequency before theme
                theme_idx = sequence.index("theme")
                sequence.insert(theme_idx, "update_frequency")
            elif project_type == ProjectType.PRESENTATION:
                # Insert presentation_style before theme
                theme_idx = sequence.index("theme")
                sequence.insert(theme_idx, "presentation_style")

            # Add full mode common questions at the end
            sequence.extend([
                "client_name",
                "audience",
                "deadline",
                "success_criteria",
                "constraints",
            ])

        return sequence

    @classmethod
    def get_question_text(cls, question_key: str, project_type: Optional[ProjectType] = None) -> str:
        """
        Get the question text for a given question key.

        Args:
            question_key: The question identifier
            project_type: Optional project type for type-specific questions

        Returns:
            Question text
        """
        # Check common questions first
        if question_key in cls.COMMON_QUESTIONS:
            return cls.COMMON_QUESTIONS[question_key]

        # Check type-specific questions
        if project_type and project_type in cls.TYPE_SPECIFIC_QUESTIONS:
            if question_key in cls.TYPE_SPECIFIC_QUESTIONS[project_type]:
                return cls.TYPE_SPECIFIC_QUESTIONS[project_type][question_key]

        return f"[Question not found: {question_key}]"

    @classmethod
    def is_type_supported(cls, project_type: ProjectType) -> bool:
        """Check if a project type is supported."""
        return project_type in cls.SUPPORTED_TYPES

    @classmethod
    def get_redirect_message(cls, project_type: ProjectType) -> Optional[str]:
        """Get redirect message for unsupported project types."""
        return cls.UNSUPPORTED_TYPES.get(project_type)
