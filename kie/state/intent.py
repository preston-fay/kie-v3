"""
Intent Storage and Checking

Manages user intent clarification state for KIE Constitution Section 3 compliance.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class IntentStorage:
    """Manages intent clarification state."""

    def __init__(self, project_root: Path):
        """
        Initialize intent storage.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.intent_path = project_root / "project_state" / "intent.yaml"

    def is_clarified(self) -> bool:
        """
        Check if intent has been clarified.

        Intent is clarified if ANY of the following exist:
        1. Completed /interview record
        2. Explicit analytical objective in intent.yaml
        3. Explicit plan confirmation artifact
        4. Explicit intent declaration via CLI prompt

        Returns:
            True if intent is clarified, False otherwise
        """
        # Check for explicit intent declaration
        if self.intent_path.exists():
            import yaml
            with open(self.intent_path) as f:
                intent_data = yaml.safe_load(f)
                if intent_data and intent_data.get("objective"):
                    return True

        # Check for completed interview
        interview_state_path = self.project_root / "project_state" / "interview_state.yaml"
        if interview_state_path.exists():
            import yaml
            with open(interview_state_path) as f:
                interview_data = yaml.safe_load(f)
                # Interview is complete if it has captured objective
                if interview_data and interview_data.get("objective"):
                    return True

        # Check spec.yaml for explicit objective
        spec_path = self.project_root / "project_state" / "spec.yaml"
        if spec_path.exists():
            import yaml
            with open(spec_path) as f:
                spec_data = yaml.safe_load(f)
                # Spec has meaningful objective (not just default)
                if spec_data and spec_data.get("objective"):
                    objective = spec_data["objective"]
                    # Reject generic/default objectives
                    if objective and objective.lower() not in ["analysis", "analyze", ""]:
                        return True

        return False

    def capture_intent(self, objective: str, captured_via: str = "prompt") -> dict[str, Any]:
        """
        Capture user intent.

        Args:
            objective: The primary objective (what user wants to achieve)
            captured_via: How intent was captured (interview|prompt)

        Returns:
            Dict with success status
        """
        import yaml

        intent_data = {
            "objective": objective,
            "captured_at": datetime.now().isoformat(),
            "captured_via": captured_via,
        }

        # Ensure directory exists
        self.intent_path.parent.mkdir(parents=True, exist_ok=True)

        # Write intent
        with open(self.intent_path, "w") as f:
            yaml.dump(intent_data, f, default_flow_style=False, sort_keys=False)

        # Record intent capture event in Evidence Ledger if available
        try:
            ledger_dir = self.project_root / "project_state" / "evidence_ledger"
            ledger_dir.mkdir(parents=True, exist_ok=True)

            # Create a simple event record
            event_file = ledger_dir / "intent_capture_events.yaml"
            events = []
            if event_file.exists():
                with open(event_file) as f:
                    events = yaml.safe_load(f) or []

            events.append({
                "timestamp": intent_data["captured_at"],
                "objective": objective,
                "captured_via": captured_via,
            })

            with open(event_file, "w") as f:
                yaml.dump(events, f, default_flow_style=False)
        except Exception:
            # Intent capture must never fail - silently skip event recording
            pass

        return {
            "success": True,
            "objective": objective,
            "captured_at": intent_data["captured_at"],
            "captured_via": captured_via,
        }

    def get_intent(self) -> dict[str, Any] | None:
        """
        Get current intent if clarified.

        Returns:
            Intent dict or None if not clarified
        """
        if not self.is_clarified():
            return None

        # Try to load from intent.yaml first
        if self.intent_path.exists():
            import yaml
            with open(self.intent_path) as f:
                return yaml.safe_load(f)

        # Try to load from interview_state
        interview_state_path = self.project_root / "project_state" / "interview_state.yaml"
        if interview_state_path.exists():
            import yaml
            with open(interview_state_path) as f:
                interview_data = yaml.safe_load(f)
                if interview_data and interview_data.get("objective"):
                    return {
                        "objective": interview_data["objective"],
                        "captured_via": "interview",
                    }

        # Try to load from spec.yaml
        spec_path = self.project_root / "project_state" / "spec.yaml"
        if spec_path.exists():
            import yaml
            with open(spec_path) as f:
                spec_data = yaml.safe_load(f)
                if spec_data and spec_data.get("objective"):
                    return {
                        "objective": spec_data["objective"],
                        "captured_via": "spec",
                    }

        return None


# Module-level convenience functions
def is_intent_clarified(project_root: Path) -> bool:
    """Check if intent has been clarified."""
    return IntentStorage(project_root).is_clarified()


def capture_intent(project_root: Path, objective: str, captured_via: str = "prompt") -> dict[str, Any]:
    """Capture user intent."""
    return IntentStorage(project_root).capture_intent(objective, captured_via)


def get_intent(project_root: Path) -> dict[str, Any] | None:
    """Get current intent if clarified."""
    return IntentStorage(project_root).get_intent()


def prompt_for_intent() -> str:
    """
    Prompt user for intent clarification.

    Returns:
        User's objective as string
    """
    print()
    print("=" * 70)
    print("INTENT CLARIFICATION REQUIRED")
    print("=" * 70)
    print()
    print("Before I proceed, I need clarity on what you want to achieve.")
    print()
    print("What is the primary objective of this work?")
    print("(Examples: explore data patterns, answer a specific question,")
    print(" create a client-ready deliverable)")
    print()
    print("Please answer in one sentence, or run /interview for a guided setup.")
    print()

    objective = input("Objective: ").strip()
    return objective
