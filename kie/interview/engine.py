"""
Interview Engine

Conversational requirements gathering using slot-filling.
"""

from typing import Optional, List, Dict, Any
import re
from pathlib import Path
import yaml

from kie.interview.schema import (
    InterviewState,
    ProjectSpec,
    ProjectType,
    DeliverableType,
    DataSource,
    ChartSpec,
    ThemePreferences,
)


class InterviewEngine:
    """
    Conversational interview system.

    Extracts structured requirements from natural language.
    """

    def __init__(self, state_path: Optional[Path] = None):
        """
        Initialize interview engine.

        Args:
            state_path: Path to save interview state
        """
        self.state = InterviewState()
        self.state_path = state_path or Path("project_state/interview_state.yaml")

        # Load existing state if available
        if self.state_path.exists():
            self.load_state()

    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process user message and extract requirements.

        Args:
            message: User message

        Returns:
            Response dict with:
              - acknowledgment: What was understood
              - slots_filled: Which slots were filled
              - next_question: Next question to ask (if any)
              - complete: Whether interview is complete
        """
        # Add to conversation history
        self.state.conversation.append({"role": "user", "content": message})

        # Extract information
        extracted = self._extract_information(message)

        # Update state
        slots_filled = self._update_state(extracted)

        # Generate response
        response = self._generate_response(extracted, slots_filled)

        # Save state
        self.save_state()

        return response

    def _extract_information(self, message: str) -> Dict[str, Any]:
        """
        Extract structured information from message.

        Args:
            message: User message

        Returns:
            Dict of extracted information
        """
        message_lower = message.lower()
        extracted = {}

        # Project type detection
        project_type_patterns = {
            ProjectType.ANALYTICS: ["analyz", "analysis", "insight", "explore", "investigate"],
            ProjectType.PRESENTATION: [
                "presentation",
                "slides",
                "deck",
                "powerpoint",
                "pptx",
                "present",
            ],
            ProjectType.DASHBOARD: [
                "dashboard",
                "monitor",
                "real-time",
                "interactive",
                "visualiz",
            ],
            ProjectType.MODELING: ["model", "predict", "forecast", "machine learning", "ml"],
            ProjectType.PROPOSAL: ["proposal", "rfp", "pitch", "bid"],
            ProjectType.RESEARCH: ["research", "market", "competitive", "landscape"],
        }

        for proj_type, patterns in project_type_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                extracted["project_type"] = proj_type
                break

        # Client name detection (proper nouns, capitalized words)
        # Look for patterns like "for [Company]", "client: [Company]", "[Company] Corp"
        client_patterns = [
            r"for ([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
            r"client:\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
            r"([A-Z][a-zA-Z]+)\s+(?:Corp|Inc|LLC|Ltd)",
        ]

        for pattern in client_patterns:
            match = re.search(pattern, message)
            if match:
                extracted["client_name"] = match.group(1)
                break

        # Objective extraction (sentences describing what they want)
        objective_patterns = [
            r"(?:I need|I want|need to|want to|looking to|trying to)\s+(.+?)(?:\.|$)",
            r"(?:showing|show|displaying|display|analyzing|analyze)\s+(.+?)(?:\.|$)",
        ]

        for pattern in objective_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                extracted["objective"] = match.group(1).strip()
                break

        # Deliverable type detection
        deliverable_patterns = {
            DeliverableType.POWERPOINT: ["powerpoint", "pptx", "slides", "deck", "presentation"],
            DeliverableType.STREAMLIT: ["dashboard", "interactive", "streamlit"],
            DeliverableType.HTML: ["html", "webpage", "web page", "web"],
            DeliverableType.PDF: ["pdf", "report"],
            DeliverableType.EXCEL: ["excel", "xlsx", "spreadsheet"],
        }

        deliverables = []
        for deliv_type, patterns in deliverable_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                deliverables.append(deliv_type)

        if deliverables:
            extracted["deliverables"] = deliverables

        # Data source detection
        data_patterns = {
            "csv": ["csv", ".csv"],
            "excel": ["excel", "xlsx", ".xlsx", "xls", ".xls"],
            "database": ["database", "sql", "postgres", "mysql"],
            "api": ["api", "endpoint", "rest"],
            "mock": ["mock", "sample", "test data", "fake data"],
        }

        for data_type, patterns in data_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                extracted["data_source_type"] = data_type
                break

        # Theme preference
        if "dark" in message_lower and "theme" in message_lower:
            extracted["theme"] = "dark"
        elif "light" in message_lower and "theme" in message_lower:
            extracted["theme"] = "light"

        # Timeframe detection (Q1, Q2, monthly, weekly, etc.)
        timeframe_patterns = [
            r"Q[1-4]",
            r"[Qq]uarter\s+\d",
            r"\d{4}",  # Year
            r"(?:monthly|weekly|daily|yearly)",
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)",
        ]

        for pattern in timeframe_patterns:
            match = re.search(pattern, message)
            if match:
                extracted["timeframe"] = match.group(0)
                break

        return extracted

    def _update_state(self, extracted: Dict[str, Any]) -> List[str]:
        """
        Update interview state with extracted information.

        Args:
            extracted: Extracted information

        Returns:
            List of slots that were filled
        """
        slots_filled = []

        # Project type
        if "project_type" in extracted and not self.state.has_project_type:
            self.state.spec.project_type = extracted["project_type"]
            self.state.has_project_type = True
            slots_filled.append("project_type")

            # Auto-generate project name if not set
            if not self.state.has_project_name:
                client = self.state.spec.client_name or "Project"
                proj_type = extracted["project_type"].value
                self.state.spec.project_name = f"{client} {proj_type.title()}"
                self.state.has_project_name = True
                slots_filled.append("project_name")

        # Client name
        if "client_name" in extracted:
            self.state.spec.client_name = extracted["client_name"]

            # Update project name if not explicitly set
            if self.state.has_project_type:
                self.state.spec.project_name = (
                    f"{extracted['client_name']} {self.state.spec.project_type.value.title()}"
                )

        # Objective
        if "objective" in extracted and not self.state.has_objective:
            self.state.spec.objective = extracted["objective"]
            self.state.has_objective = True
            slots_filled.append("objective")

        # Deliverables
        if "deliverables" in extracted and not self.state.has_deliverables:
            self.state.spec.deliverables.extend(extracted["deliverables"])
            self.state.has_deliverables = True
            slots_filled.append("deliverables")

        # Data source
        if "data_source_type" in extracted and not self.state.has_data_source:
            data_source = DataSource(
                type=extracted["data_source_type"], description="Data source mentioned by user"
            )
            self.state.spec.data_sources.append(data_source)
            self.state.has_data_source = True
            slots_filled.append("data_source")

        # Theme
        if "theme" in extracted and not self.state.has_theme_preference:
            self.state.spec.preferences.theme.mode = extracted["theme"]
            self.state.has_theme_preference = True
            slots_filled.append("theme")

        # Timeframe (add to context)
        if "timeframe" in extracted:
            if not self.state.spec.context:
                self.state.spec.context = {}
            self.state.spec.context["timeframe"] = extracted["timeframe"]

        # Update slots tracking
        self.state.slots_filled.extend(slots_filled)

        # Update remaining slots
        self.state.slots_remaining = self.state.get_missing_required_fields()

        return slots_filled

    def _generate_response(
        self, extracted: Dict[str, Any], slots_filled: List[str]
    ) -> Dict[str, Any]:
        """
        Generate response to user.

        Args:
            extracted: Extracted information
            slots_filled: Slots that were filled

        Returns:
            Response dict
        """
        response = {
            "extracted": extracted,
            "slots_filled": slots_filled,
            "complete": self.state.is_complete(),
            "completion_percentage": self.state.get_completion_percentage(),
        }

        # Generate acknowledgment
        acknowledgments = []

        if "client_name" in extracted:
            acknowledgments.append(f"Client: {extracted['client_name']}")

        if "project_type" in extracted:
            acknowledgments.append(f"Type: {extracted['project_type'].value.title()}")

        if "objective" in extracted:
            acknowledgments.append(f"Goal: {extracted['objective']}")

        if "deliverables" in extracted:
            deliv_names = [d.value for d in extracted["deliverables"]]
            acknowledgments.append(f"Deliverables: {', '.join(deliv_names)}")

        if "data_source_type" in extracted:
            acknowledgments.append(f"Data: {extracted['data_source_type']}")

        if "theme" in extracted:
            acknowledgments.append(f"Theme: {extracted['theme']}")

        response["acknowledgment"] = acknowledgments

        # Generate next question
        if not self.state.is_complete():
            missing = self.state.get_missing_required_fields()
            next_field = missing[0]

            questions = {
                "project_name": "What would you like to call this project?",
                "project_type": "What type of deliverable do you need? (presentation, dashboard, analysis, etc.)",
                "objective": "What's the main goal or question you're trying to answer?",
                "data_source": "What data do you have? (CSV file, Excel, database, or should I create mock data?)",
                "deliverables": "What format do you need? (PowerPoint, PDF, Excel, interactive dashboard?)",
            }

            response["next_question"] = questions.get(next_field, "What else can you tell me?")
        else:
            response["next_question"] = None

        # Add conversation to response
        self.state.conversation.append({"role": "assistant", "content": str(response)})

        return response

    def get_spec(self) -> ProjectSpec:
        """
        Get current project specification.

        Returns:
            ProjectSpec object
        """
        return self.state.spec

    def save_state(self):
        """Save interview state to disk."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for YAML serialization
        # Use mode='json' to convert enums to their string values
        state_dict = self.state.model_dump(mode='json')

        with open(self.state_path, "w") as f:
            yaml.dump(state_dict, f, default_flow_style=False, sort_keys=False)

    def load_state(self):
        """Load interview state from disk."""
        with open(self.state_path) as f:
            state_dict = yaml.safe_load(f)

        self.state = InterviewState(**state_dict)

    def reset(self):
        """Reset interview state."""
        self.state = InterviewState()
        if self.state_path.exists():
            self.state_path.unlink()

    def export_spec_yaml(self, output_path: Optional[Path] = None) -> Path:
        """
        Export spec to YAML file.

        Args:
            output_path: Output path (default: project_state/spec.yaml)

        Returns:
            Path to saved file
        """
        output_path = output_path or Path("project_state/spec.yaml")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use mode='json' to convert enums to string values for YAML serialization
        spec_dict = self.state.spec.model_dump(mode='json')

        with open(output_path, "w") as f:
            yaml.dump(spec_dict, f, default_flow_style=False, sort_keys=False)

        return output_path

    def get_interview_summary(self) -> str:
        """
        Get human-readable interview summary.

        Returns:
            Formatted summary
        """
        spec = self.state.spec
        completion = self.state.get_completion_percentage()

        lines = []
        lines.append("=" * 60)
        lines.append("PROJECT SPECIFICATION")
        lines.append("=" * 60)
        lines.append(f"Completion: {completion:.0f}%")
        lines.append("")

        lines.append(f"Project: {spec.project_name}")
        lines.append(f"Type: {spec.project_type.value.title()}")

        if spec.client_name:
            lines.append(f"Client: {spec.client_name}")

        lines.append(f"Objective: {spec.objective}")
        lines.append("")

        if spec.data_sources:
            lines.append("Data Sources:")
            for ds in spec.data_sources:
                lines.append(f"  • {ds.type}")
                if ds.location:
                    lines.append(f"    Location: {ds.location}")

        if spec.deliverables:
            lines.append("\nDeliverables:")
            for deliv in spec.deliverables:
                lines.append(f"  • {deliv.value}")

        lines.append(f"\nTheme: {spec.preferences.theme.mode}")

        if not self.state.is_complete():
            lines.append("")
            lines.append("Missing Required Fields:")
            for field in self.state.get_missing_required_fields():
                lines.append(f"  • {field}")

        lines.append("=" * 60)

        return "\n".join(lines)
