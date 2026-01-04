"""
Interview Engine

Conversational requirements gathering using step-by-step prompting.
Supports express (6 questions) and full (11 questions) modes.
"""

from typing import Optional, List, Dict, Any
import re
from pathlib import Path
import yaml
from datetime import datetime

from kie.interview.schema import (
    InterviewState,
    ProjectSpec,
    ProjectType,
    DeliverableType,
    DataSource,
    ChartSpec,
    ThemePreferences,
)
from kie.interview.question_bank import QuestionBank


class InterviewEngine:
    """
    Conversational interview system with step-by-step prompting.

    EXPRESS mode: 6 required questions
    FULL mode: 11 questions (adds client, audience, deadline, success criteria, constraints)
    """

    # Question sequences
    EXPRESS_SEQUENCE = [
        "project_type",
        "objective",
        "data_source",
        "deliverables",
        "theme",
        "project_name",
    ]

    FULL_SEQUENCE = EXPRESS_SEQUENCE + [
        "client_name",
        "audience",
        "deadline",
        "success_criteria",
        "constraints",
    ]

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

        Returns single focused question based on current state.

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

    def _is_field_missing(self, field: str) -> bool:
        """
        Check if a specific field is missing.

        For type-specific fields, checks spec.context dict.
        """
        # Core completion flags
        field_status = {
            "project_type": self.state.has_project_type,
            "objective": self.state.has_objective,
            "data_source": self.state.has_data_source,
            "deliverables": self.state.has_deliverables,
            "theme": self.state.has_theme_preference,
            "project_name": self.state.has_project_name,
            "client_name": self.state.has_client_name,
            "audience": self.state.has_audience,
            "deadline": self.state.has_deadline,
            "success_criteria": self.state.has_success_criteria,
            "constraints": self.state.has_constraints,
        }

        # Check core fields first
        if field in field_status:
            return not field_status[field]

        # Type-specific fields stored in context
        type_specific_fields = [
            "dashboard_views",
            "dashboard_filters",
            "update_frequency",
            "slide_count",
            "key_message",
            "presentation_style",
        ]

        if field in type_specific_fields:
            # Check if field exists in context
            if not self.state.spec.context:
                return True
            return field not in self.state.spec.context

        # Unknown field - assume missing
        return True

    def _get_next_question(self) -> Optional[str]:
        """
        Return single focused question based on interview mode and project type.

        Uses QuestionBank for type-specific routing.
        """
        # If mode not selected, ask for mode first
        if not self.state.interview_mode:
            return QuestionBank.get_question_text("mode")

        # If project_type not selected or not in sequence, ask for it
        if not self.state.has_project_type:
            return QuestionBank.get_question_text("project_type")

        # Build or use active question sequence
        if not self.state.active_question_sequence:
            # First time: build the sequence based on type and mode
            try:
                self.state.active_question_sequence = QuestionBank.get_question_sequence(
                    self.state.spec.project_type,
                    self.state.interview_mode
                )
                self.state.current_question_index = 0
            except ValueError:
                # Unsupported type - should have been caught earlier
                return QuestionBank.get_question_text("project_type")

        # Get next question from sequence
        while self.state.current_question_index < len(self.state.active_question_sequence):
            question_key = self.state.active_question_sequence[self.state.current_question_index]

            # Check if this field is already filled
            if self._is_field_missing(question_key):
                return QuestionBank.get_question_text(
                    question_key,
                    self.state.spec.project_type
                )

            # Field already filled, advance to next
            self.state.current_question_index += 1

        return None  # All questions answered

    def _extract_information(self, message: str) -> Dict[str, Any]:
        """
        Extract structured information from message.

        Args:
            message: User message

        Returns:
            Dict of extracted information
        """
        message_lower = message.lower().strip()
        extracted = {}

        # Interview mode detection
        if not self.state.interview_mode:
            if "express" in message_lower or "fast" in message_lower or "quick" in message_lower:
                extracted["interview_mode"] = "express"
            elif "full" in message_lower or "detailed" in message_lower or "complete" in message_lower:
                extracted["interview_mode"] = "full"

        # Project type detection
        project_type_patterns = {
            ProjectType.ANALYTICS: ["analyz", "analysis", "insight", "explore", "investigate", "analytics"],
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
            ProjectType.MODELING: ["model", "predict", "forecast", "machine learning", "ml", "modeling"],
            ProjectType.PROPOSAL: ["proposal", "rfp", "pitch", "bid"],
            ProjectType.RESEARCH: ["research", "market", "competitive", "landscape"],
            ProjectType.DATA_ENGINEERING: ["data engineering", "pipeline", "etl", "data_engineering"],
            ProjectType.WEBAPP: ["webapp", "web app", "application"],
        }

        for proj_type, patterns in project_type_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                # Check if type is supported
                if not QuestionBank.is_type_supported(proj_type):
                    # Record attempted unsupported type
                    extracted["attempted_unsupported_type"] = proj_type
                else:
                    extracted["project_type"] = proj_type
                break

        # Client name detection (proper nouns, capitalized words)
        client_patterns = [
            r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
        ]

        for pattern in client_patterns:
            match = re.search(pattern, message)
            if match and len(match.group(1).split()) <= 3:  # Limit to reasonable company names
                potential_client = match.group(1)
                # Filter out common false positives
                if potential_client not in ["I", "The", "A", "An", "Type", "Options"]:
                    extracted["client_name"] = potential_client
                    break

        # Objective extraction - take the full message as objective if it's descriptive
        if len(message) > 20 and not any(kw in message_lower for kw in ["yes", "no", "express", "full", "dark", "light"]):
            # This might be an objective description
            extracted["objective_candidate"] = message

        # Deliverable type detection
        deliverable_patterns = {
            DeliverableType.POWERPOINT: ["powerpoint", "pptx", "slides", "deck", "presentation"],
            DeliverableType.REACT_APP: ["dashboard", "interactive", "react", "html"],
            DeliverableType.HTML: ["html", "webpage", "web"],
            DeliverableType.PDF: ["pdf", "report"],
            DeliverableType.EXCEL: ["excel", "xlsx", "spreadsheet"],
            DeliverableType.JUPYTER: ["jupyter", "notebook", "ipynb"],
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
            "database": ["database", "sql", "postgres", "mysql", "db"],
            "api": ["api", "endpoint", "rest"],
            "mock": ["mock", "sample", "test data", "fake data", "generate"],
        }

        for data_type, patterns in data_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                extracted["data_source_type"] = data_type
                break

        # File path detection
        if "/" in message or "\\" in message or ".csv" in message_lower or ".xlsx" in message_lower:
            extracted["data_location"] = message.strip()

        # Theme preference (explicit only - no defaults)
        if "dark" in message_lower and not "light" in message_lower:
            extracted["theme"] = "dark"
        elif "light" in message_lower and not "dark" in message_lower:
            extracted["theme"] = "light"

        # Audience detection
        audience_keywords = ["executive", "c-suite", "ceo", "cfo", "analyst", "team", "trading", "desk", "client"]
        if any(kw in message_lower for kw in audience_keywords):
            extracted["audience"] = message

        # Deadline detection
        deadline_patterns = [
            r"((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2})",
            r"(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"((?:end of|eow|eom|eoq|eoy)(?:\s+week|\s+month|\s+quarter|\s+year)?)",
            r"(\d+\s+(?:days?|weeks?|months?))",
        ]

        for pattern in deadline_patterns:
            match = re.search(pattern, message_lower)
            if match:
                extracted["deadline"] = match.group(1)
                break

        # Success criteria detection
        success_keywords = ["success", "goal", "achieve", "measure", "metric", "kpi"]
        if any(kw in message_lower for kw in success_keywords):
            extracted["success_criteria"] = message

        # Constraints detection
        if "none" in message_lower and not self.state.has_constraints:
            extracted["constraints"] = "None specified"
        elif any(kw in message_lower for kw in ["budget", "constraint", "limit", "restriction", "compliance", "cannot", "must not"]):
            extracted["constraints"] = message

        # Project name (if it looks like a title)
        if len(message.split()) <= 5 and message[0].isupper() and not self.state.has_project_name:
            extracted["project_name"] = message

        # Type-specific field extraction (flexible - captures any response)
        # Check which question we're currently on
        if self.state.active_question_sequence and self.state.current_question_index < len(self.state.active_question_sequence):
            current_question_key = self.state.active_question_sequence[self.state.current_question_index]

            type_specific_fields = [
                "dashboard_views",
                "dashboard_filters",
                "update_frequency",
                "slide_count",
                "key_message",
                "presentation_style",
            ]

            if current_question_key in type_specific_fields:
                # Capture the response for this type-specific field
                extracted[current_question_key] = message.strip()

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

        # Interview mode
        if "interview_mode" in extracted and not self.state.interview_mode:
            self.state.interview_mode = extracted["interview_mode"]
            slots_filled.append("interview_mode")

        # Project type (only set if supported)
        if "project_type" in extracted and not self.state.has_project_type:
            self.state.spec.project_type = extracted["project_type"]
            self.state.has_project_type = True
            slots_filled.append("project_type")

        # Unsupported project type (audit trail - blocks completion)
        if "attempted_unsupported_type" in extracted:
            if not self.state.spec.context:
                self.state.spec.context = {}
            self.state.spec.context["attempted_project_type"] = extracted["attempted_unsupported_type"].value
            slots_filled.append("attempted_unsupported_type")
            # has_project_type stays False - blocks completion until supported type selected

        # Objective
        if "objective_candidate" in extracted and not self.state.has_objective:
            # Use the full message as objective if we're expecting it
            if not self.state.has_objective:
                self.state.spec.objective = extracted["objective_candidate"]
                self.state.has_objective = True
                slots_filled.append("objective")

        # Client name
        if "client_name" in extracted and not self.state.has_client_name:
            self.state.spec.client_name = extracted["client_name"]
            self.state.has_client_name = True
            slots_filled.append("client_name")

        # Deliverables
        if "deliverables" in extracted and not self.state.has_deliverables:
            self.state.spec.deliverables.extend(extracted["deliverables"])
            self.state.has_deliverables = True
            slots_filled.append("deliverables")

        # Data source
        if "data_source_type" in extracted and not self.state.has_data_source:
            data_source = DataSource(
                type=extracted["data_source_type"],
                location=extracted.get("data_location"),
                description="Data source provided by user"
            )
            self.state.spec.data_sources.append(data_source)
            self.state.has_data_source = True
            slots_filled.append("data_source")

        # Theme (REQUIRED - no silent defaults)
        if "theme" in extracted and not self.state.has_theme_preference:
            self.state.spec.preferences.theme.mode = extracted["theme"]
            self.state.has_theme_preference = True
            slots_filled.append("theme")

        # Project name
        if "project_name" in extracted and not self.state.has_project_name:
            self.state.spec.project_name = extracted["project_name"]
            self.state.has_project_name = True
            slots_filled.append("project_name")

        # Audience
        if "audience" in extracted and not self.state.has_audience:
            self.state.spec.audience = extracted["audience"]
            self.state.has_audience = True
            slots_filled.append("audience")

        # Deadline
        if "deadline" in extracted and not self.state.has_deadline:
            # Store as string for now (can be parsed later if needed)
            if not self.state.spec.context:
                self.state.spec.context = {}
            self.state.spec.context["deadline_str"] = extracted["deadline"]
            self.state.has_deadline = True
            slots_filled.append("deadline")

        # Success criteria
        if "success_criteria" in extracted and not self.state.has_success_criteria:
            if not self.state.spec.success_criteria:
                self.state.spec.success_criteria = []
            self.state.spec.success_criteria.append(extracted["success_criteria"])
            self.state.has_success_criteria = True
            slots_filled.append("success_criteria")

        # Constraints
        if "constraints" in extracted and not self.state.has_constraints:
            if not self.state.spec.constraints:
                self.state.spec.constraints = []
            self.state.spec.constraints.append(extracted["constraints"])
            self.state.has_constraints = True
            slots_filled.append("constraints")

        # Type-specific fields (stored in spec.context)
        type_specific_fields = [
            "dashboard_views", "dashboard_filters", "update_frequency",
            "slide_count", "key_message", "presentation_style",
        ]

        for field in type_specific_fields:
            if field in extracted:
                if not self.state.spec.context:
                    self.state.spec.context = {}
                self.state.spec.context[field] = extracted[field]
                slots_filled.append(field)
                # Advance question index for type-specific questions
                if self.state.active_question_sequence and self.state.current_question_index < len(self.state.active_question_sequence):
                    self.state.current_question_index += 1

        # Auto-generate project name if we have enough info and it's missing
        if not self.state.has_project_name and self.state.has_project_type:
            client = self.state.spec.client_name or "Project"
            proj_type = self.state.spec.project_type.value.title()
            self.state.spec.project_name = f"{client} {proj_type}"
            self.state.has_project_name = True
            slots_filled.append("project_name_auto")

        # Update slots tracking
        self.state.slots_filled.extend(slots_filled)

        # Update remaining slots
        self.state.slots_remaining = self.state.get_missing_required_fields()

        return slots_filled

    def _generate_response(
        self, extracted: Dict[str, Any], slots_filled: List[str]
    ) -> Dict[str, Any]:
        """
        Generate response to user with single next question.

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

        # Generate acknowledgment for what was captured
        acknowledgments = []

        if "interview_mode" in extracted:
            mode_name = "Express (6 questions)" if extracted["interview_mode"] == "express" else "Full (11 questions)"
            acknowledgments.append(f"Interview mode: {mode_name}")

        if "project_type" in extracted:
            acknowledgments.append(f"Type: {extracted['project_type'].value.title()}")

        # Unsupported type redirect
        if "attempted_unsupported_type" in extracted:
            unsupported_type = extracted["attempted_unsupported_type"]
            redirect_msg = QuestionBank.get_redirect_message(unsupported_type)
            if redirect_msg:
                acknowledgments.append(f"⚠️ {redirect_msg}")

        if "objective_candidate" in extracted and "objective" in slots_filled:
            obj_preview = extracted['objective_candidate'][:60] + "..." if len(extracted['objective_candidate']) > 60 else extracted['objective_candidate']
            acknowledgments.append(f"Objective: {obj_preview}")

        if "deliverables" in extracted:
            deliv_names = [d.value for d in extracted["deliverables"]]
            acknowledgments.append(f"Deliverables: {', '.join(deliv_names)}")

        if "data_source_type" in extracted:
            acknowledgments.append(f"Data: {extracted['data_source_type']}")

        if "theme" in extracted:
            acknowledgments.append(f"Theme: {extracted['theme']} mode")

        if "client_name" in extracted:
            acknowledgments.append(f"Client: {extracted['client_name']}")

        if "project_name" in extracted:
            acknowledgments.append(f"Project: {extracted['project_name']}")

        # Type-specific field acknowledgments
        if "dashboard_views" in extracted:
            acknowledgments.append(f"Dashboard views: {extracted['dashboard_views']}")
        if "dashboard_filters" in extracted:
            acknowledgments.append(f"Filters: {extracted['dashboard_filters']}")
        if "update_frequency" in extracted:
            acknowledgments.append(f"Update frequency: {extracted['update_frequency']}")
        if "slide_count" in extracted:
            acknowledgments.append(f"Target slides: {extracted['slide_count']}")
        if "key_message" in extracted:
            msg_preview = extracted['key_message'][:60] + "..." if len(extracted['key_message']) > 60 else extracted['key_message']
            acknowledgments.append(f"Key message: {msg_preview}")
        if "presentation_style" in extracted:
            acknowledgments.append(f"Style: {extracted['presentation_style']}")

        response["acknowledgment"] = acknowledgments

        # Get next question (single focused question)
        if not self.state.is_complete():
            next_q = self._get_next_question()
            response["next_question"] = next_q
        else:
            response["next_question"] = None
            response["message"] = "✅ Interview complete! Spec saved to project_state/spec.yaml"

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

        mode_display = "Not selected"
        if self.state.interview_mode:
            mode_display = f"{self.state.interview_mode.upper()} mode"
        lines.append(f"Interview Mode: {mode_display}")
        lines.append(f"Completion: {completion:.0f}%")
        lines.append("")

        lines.append(f"Project: {spec.project_name or 'Not set'}")
        lines.append(f"Type: {spec.project_type.value.title()}")

        if spec.client_name:
            lines.append(f"Client: {spec.client_name}")

        lines.append(f"Objective: {spec.objective or 'Not set'}")
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

        theme_display = spec.preferences.theme.mode if self.state.has_theme_preference else "NOT SET (required)"
        lines.append(f"\nTheme: {theme_display}")

        if spec.audience:
            lines.append(f"Audience: {spec.audience}")

        if not self.state.is_complete():
            lines.append("")
            lines.append("Missing Required Fields:")
            for field in self.state.get_missing_required_fields():
                lines.append(f"  • {field}")

        lines.append("=" * 60)

        return "\n".join(lines)
