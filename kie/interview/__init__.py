"""
KIE v3 Interview System

Conversational requirements gathering using slot-filling.

Instead of rigid questionnaires, KIE uses natural language understanding
to extract structured requirements from conversation.

Example:
    User: "I need a sales dashboard for Acme Corp showing Q3 performance"

    Extracted:
    - Client: Acme Corp
    - Type: Dashboard
    - Objective: Show Q3 performance
    - Missing: Data source, specific deliverable format

    Next Question: "What data do you have? (CSV, Excel, database?)"

Usage:
    from kie.interview import InterviewEngine

    # Initialize
    interview = InterviewEngine()

    # Process messages
    response = interview.process_message("I need a presentation for Q4 results")

    # Check completion
    if response["complete"]:
        spec = interview.get_spec()
        interview.export_spec_yaml()
"""

from kie.interview.engine import InterviewEngine
from kie.interview.schema import (
    ChartSpec,
    DataSource,
    DeliverableType,
    InterviewState,
    ProjectPreferences,
    ProjectSpec,
    ProjectType,
    SlideSpec,
    ThemePreferences,
)

__all__ = [
    # Engine
    "InterviewEngine",
    # Schema
    "ProjectSpec",
    "ProjectType",
    "DeliverableType",
    "DataSource",
    "ChartSpec",
    "SlideSpec",
    "ThemePreferences",
    "ProjectPreferences",
    "InterviewState",
]
