"""
Interview System Schema

Defines project specification models for conversational requirements gathering.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


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
    STREAMLIT = "streamlit"
    REACT_APP = "react_app"
    JUPYTER = "jupyter"


class DataSource(BaseModel):
    """Data source specification."""

    type: str = Field(..., description="Type: csv, excel, database, api, mock")
    location: Optional[str] = Field(None, description="File path or URL")
    description: Optional[str] = Field(None, description="Human description")
    columns: Optional[List[str]] = Field(None, description="Column names")
    sample_rows: Optional[int] = Field(None, description="Number of rows")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChartSpec(BaseModel):
    """Chart specification."""

    chart_type: str = Field(..., description="bar, line, pie, map, etc.")
    title: str = Field(..., description="Chart title")
    data_source: str = Field(..., description="Reference to data source")
    x_axis: Optional[str] = Field(None, description="X-axis column")
    y_axis: Optional[List[str]] = Field(None, description="Y-axis columns")
    filters: Optional[Dict[str, Any]] = Field(None, description="Data filters")
    notes: Optional[str] = Field(None, description="Notes for consultant")


class SlideSpec(BaseModel):
    """Slide specification."""

    slide_type: str = Field(..., description="title, content, chart, section")
    title: str = Field(..., description="Slide title")
    charts: Optional[List[ChartSpec]] = Field(None, description="Charts on slide")
    bullet_points: Optional[List[str]] = Field(None, description="Bullet points")
    speaker_notes: Optional[str] = Field(None, description="Speaker notes")


class ThemePreferences(BaseModel):
    """Theme preferences."""

    mode: str = Field("dark", description="dark or light")
    custom_colors: Optional[List[str]] = Field(None, description="Custom colors")


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
    client_name: Optional[str] = Field(None, description="Client name")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Requirements
    objective: str = Field(..., description="Project objective")
    audience: Optional[str] = Field(None, description="Target audience")
    deadline: Optional[datetime] = Field(None, description="Delivery deadline")

    # Data
    data_sources: List[DataSource] = Field(default_factory=list, description="Data sources")

    # Outputs
    deliverables: List[DeliverableType] = Field(
        default_factory=list, description="Output deliverables"
    )
    charts: List[ChartSpec] = Field(default_factory=list, description="Chart specifications")
    slides: List[SlideSpec] = Field(default_factory=list, description="Slide specifications")

    # Preferences
    preferences: ProjectPreferences = Field(
        default_factory=ProjectPreferences, description="Project preferences"
    )

    # Context
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    constraints: Optional[List[str]] = Field(None, description="Constraints/limitations")
    success_criteria: Optional[List[str]] = Field(None, description="Success criteria")

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
    interview_mode: Optional[str] = None  # "express" or "full"

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
    questions_asked: List[str] = Field(default_factory=list)
    answers_received: List[str] = Field(default_factory=list)
    slots_filled: List[str] = Field(default_factory=list)
    slots_remaining: List[str] = Field(default_factory=list)

    # Conversation history
    conversation: List[Dict[str, str]] = Field(default_factory=list)

    def is_complete(self) -> bool:
        """Check if interview is complete (minimum required fields including theme)."""
        required = (
            self.has_project_name
            and self.has_project_type
            and self.has_objective
            and self.has_data_source
            and self.has_deliverables
            and self.has_theme_preference  # Theme is now REQUIRED
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

    def get_missing_required_fields(self) -> List[str]:
        """Get list of missing required fields."""
        missing = []

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
