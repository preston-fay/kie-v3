"""
Showcase Mode Detector

Determines when Showcase Mode should activate and tracks completion.

ACTIVATION RULES:
- KIE_SHOWCASE=1 environment variable
- OR first-ever run (no data/, no spec.yaml, no showcase_completed flag)

AUTO-DISABLE RULES:
- Real data exists in data/
- Real spec.yaml exists in project_state/
- Showcase completion flag exists
"""

import os
from pathlib import Path


def should_activate_showcase(project_root: Path) -> bool:
    """
    Determine if Showcase Mode should activate.

    Args:
        project_root: Project root directory

    Returns:
        True if showcase should activate
    """
    # Check environment variable override
    if os.environ.get("KIE_SHOWCASE") == "1":
        return True

    # Check for showcase completion flag
    showcase_flag = project_root / "project_state" / "showcase_completed"
    if showcase_flag.exists():
        return False

    # Check for real data
    data_dir = project_root / "data"
    if data_dir.exists() and any(data_dir.iterdir()):
        return False

    # Check for real spec
    spec_file = project_root / "project_state" / "spec.yaml"
    if spec_file.exists():
        # Check if it's the demo spec
        try:
            content = spec_file.read_text()
            if "showcase_mode: true" in content or "SHOWCASE DEMO" in content:
                # This is the demo spec, not real - allow showcase
                pass
            else:
                # Real spec exists
                return False
        except Exception:
            return False

    # First-ever run conditions met
    return True


def mark_showcase_completed(project_root: Path) -> None:
    """
    Mark showcase as completed to prevent auto-activation.

    Args:
        project_root: Project root directory
    """
    project_state = project_root / "project_state"
    project_state.mkdir(parents=True, exist_ok=True)

    showcase_flag = project_state / "showcase_completed"
    showcase_flag.write_text(f"Showcase completed\n")


def is_showcase_active(project_root: Path) -> bool:
    """
    Check if showcase is currently active (for labeling outputs).

    Args:
        project_root: Project root directory

    Returns:
        True if KIE_SHOWCASE=1 or showcase outputs exist
    """
    if os.environ.get("KIE_SHOWCASE") == "1":
        return True

    # Check for showcase outputs
    showcase_dir = project_root / "project_state" / "showcase"
    return showcase_dir.exists()
