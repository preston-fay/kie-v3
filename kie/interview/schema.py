"""
Interview System Schema

Defines project specification models for conversational requirements gathering.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProjectType(str, Enum):
    """Project types supported by KIE."""

    ANALYTICS = "analytics"
    PRESENTATION = "presentation"
    DASHBOARD = "dashboard"
    MODELING = "modeling"
    PROPOSAL = "proposal"
    RESEARCH = "research"
    DATA_ENGINEERING = "data_engineering"
    WEBAPP = "webapp"


class DeliverableType(str, Enum):
    """Output deliverable types."""

    POWERPOINT = "powerpoint"
    PDF = "pdf"
    WORD = "word"
    HTML = "html"
    EXCEL = "excel"
    CSV = "csv"
    REACT_APP = "react_app"
    JUPYTER = "jupyter"


class DataSource(BaseModel):
    """Data source specification."""

    type: str = Field(..., description="Type: csv, excel, database, api, mock")
    location: str | None = Field(None, description="File path or URL")
    description: str | None = Field(None, description="Human description")
    columns: list[str] | None = Field(None, description="Column names")
    sample_rows: int | None = Field(None, description="Number of rows")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class ChartSpec(BaseModel):
    """Chart specification."""

    chart_type: str = Field(..., description="bar, line, pie, map, etc.")
    title: str = Field(..., description="Chart title")
    data_source: str = Field(..., description="Reference to data source")
    x_axis: str | None = Field(None, description="X-axis column")
    y_axis: list[str] | None = Field(None, description="Y-axis columns")
    filters: dict[str, Any] | None = Field(None, description="Data filters")
    notes: str | None = Field(None, description="Notes for consultant")


class SlideSpec(BaseModel):
    """Slide specification."""

    slide_type: str = Field(..., description="title, content, chart, section")
    title: str = Field(..., description="Slide title")
    charts: list[ChartSpec] | None = Field(None, description="Charts on slide")
    bullet_points: list[str] | None = Field(None, description="Bullet points")
    speaker_notes: str | None = Field(None, description="Speaker notes")


class ThemePreferences(BaseModel):
    """Theme preferences."""

    mode: str = Field("dark", description="dark or light")
    custom_colors: list[str] | None = Field(None, description="Custom colors")


class ProjectPreferences(BaseModel):
    """Project-wide preferences."""

    theme: ThemePreferences = Field(default_factory=ThemePreferences)
    number_format: str = Field("abbreviated", description="abbreviated, full, scientific")
    date_format: str = Field("%Y-%m-%d", description="Date format string")
    currency: str = Field("USD", description="Currency code")
    language: str = Field("en", description="Language code")


class ProjectSpec(BaseModel):
    """
    Complete project specification.

    Generated through conversational interview process.
    """

    # Metadata
    project_name: str = Field(..., description="Project name")
    project_type: ProjectType = Field(..., description="Project type")
    client_name: str | None = Field(None, description="Client name")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Requirements
    objective: str = Field(..., description="Project objective")
    audience: str | None = Field(None, description="Target audience")
    deadline: datetime | None = Field(None, description="Delivery deadline")

    # Data
    data_sources: list[DataSource] = Field(default_factory=list, description="Data sources")

    # Outputs
    deliverables: list[DeliverableType] = Field(
        default_factory=list, description="Output deliverables"
    )
    charts: list[ChartSpec] = Field(default_factory=list, description="Chart specifications")
    slides: list[SlideSpec] = Field(default_factory=list, description="Slide specifications")

    # Preferences
    preferences: ProjectPreferences = Field(
        default_factory=ProjectPreferences, description="Project preferences"
    )

    # Context
    context: dict[str, Any] | None = Field(None, description="Additional context")
    constraints: list[str] | None = Field(None, description="Constraints/limitations")
    success_criteria: list[str] | None = Field(None, description="Success criteria")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class InterviewState(BaseModel):
    """
    Current state of interview process.

    Tracks what has been gathered and what's still needed.
    """

    # Interview mode selection
    interview_mode: str | None = None  # "express" or "full"

    # Completion status
    has_project_name: bool = False
    has_project_type: bool = False
    has_objective: bool = False
    has_data_source: bool = False
    has_deliverables: bool = False
    has_theme_preference: bool = False
    has_client_name: bool = False
    has_audience: bool = False
    has_deadline: bool = False
    has_success_criteria: bool = False
    has_constraints: bool = False

    # Current spec (partially filled)
    spec: ProjectSpec = Field(
        default_factory=lambda: ProjectSpec(
            project_name="",
            project_type=ProjectType.ANALYTICS,
            objective="",
        )
    )

    # Interview progress
    questions_asked: list[str] = Field(default_factory=list)
    answers_received: list[str] = Field(default_factory=list)
    slots_filled: list[str] = Field(default_factory=list)
    slots_remaining: list[str] = Field(default_factory=list)

    # NEW: Type-specific question routing (Phase 1)
    active_question_sequence: list[str] = Field(default_factory=list)
    current_question_index: int = 0

    # Conversation history
    conversation: list[dict[str, str]] = Field(default_factory=list)

    def is_complete(self) -> bool:
        """
        Check if interview is complete.

        Uses BOTH sequence completion AND required field checks to ensure theme is enforced.
        """
        # Sequence completion (if sequence is active)
        sequence_complete = (
            len(self.active_question_sequence) > 0
            and self.current_question_index >= len(self.active_question_sequence)
        )

        # Required fields (explicit check including theme)
        required = (
            self.has_project_name
            and self.has_project_type
            and self.has_objective
            and self.has_data_source
            and self.has_deliverables
            and self.has_theme_preference  # Theme is REQUIRED - cannot be bypassed
        )

        if self.interview_mode == "full":
            # Full mode requires additional fields
            required = required and (
                self.has_client_name
                and self.has_audience
                and self.has_deadline
                and self.has_success_criteria
                and self.has_constraints
            )

        # Must satisfy BOTH conditions (or fall back to required-only if no sequence)
        if len(self.active_question_sequence) > 0:
            return sequence_complete and required
        else:
            # Legacy/backward compat: if no sequence, use required fields only
            return required

    def get_completion_percentage(self) -> float:
        """Get completion percentage."""
        if self.interview_mode == "express":
            required_fields = [
                self.has_project_name,
                self.has_project_type,
                self.has_objective,
                self.has_data_source,
                self.has_deliverables,
                self.has_theme_preference,
            ]
            return (sum(required_fields) / len(required_fields)) * 100
        elif self.interview_mode == "full":
            required_fields = [
                self.has_project_name,
                self.has_project_type,
                self.has_objective,
                self.has_data_source,
                self.has_deliverables,
                self.has_theme_preference,
                self.has_client_name,
                self.has_audience,
                self.has_deadline,
                self.has_success_criteria,
                self.has_constraints,
            ]
            return (sum(required_fields) / len(required_fields)) * 100
        else:
            # No mode selected yet
            return 0.0

    def get_missing_required_fields(self) -> list[str]:
        """Get list of missing required fields."""
        missing = []

        # If theme mode is already populated in the spec, treat theme as satisfied.
        try:
            mode = getattr(self.spec.preferences.theme, 'mode', None)
            if mode and not self.has_theme_preference:
                self.has_theme_preference = True
        except Exception:
            pass

        if not self.has_project_name:
            missing.append("project_name")
        if not self.has_project_type:
            missing.append("project_type")
        if not self.has_objective:
            missing.append("objective")
        if not self.has_data_source:
            missing.append("data_source")
        if not self.has_deliverables:
            missing.append("deliverables")
        if not self.has_theme_preference:
            missing.append("theme")

        if self.interview_mode == "full":
            if not self.has_client_name:
                missing.append("client_name")
            if not self.has_audience:
                missing.append("audience")
            if not self.has_deadline:
                missing.append("deadline")
            if not self.has_success_criteria:
                missing.append("success_criteria")
            if not self.has_constraints:
                missing.append("constraints")

        return missing
