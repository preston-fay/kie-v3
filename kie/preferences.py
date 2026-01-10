"""
Output Preferences - User preference storage for formatted deliverables.

Manages output_theme preference (light vs dark) for PowerPoint and dashboard generation.
Stored in project_state/output_preferences.yaml.

CRITICAL CONSTRAINTS:
- Never mutates rails_state.json
- Only stores output formatting preferences
- One-time prompt per project
- Explicit user choice required
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml


OutputTheme = Literal["light", "dark"]


class OutputPreferences:
    """
    Manages output formatting preferences for deliverables.

    Preferences are stored in project_state/output_preferences.yaml
    and apply to PowerPoint themes and dashboard themes.
    """

    def __init__(self, project_root: Path):
        """
        Initialize preferences manager.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)
        self.prefs_path = self.project_root / "project_state" / "output_preferences.yaml"

    def get_theme(self) -> OutputTheme | None:
        """
        Get current output theme preference.

        Returns:
            Theme value ('light' or 'dark') or None if not set
        """
        if not self.prefs_path.exists():
            return None

        try:
            with open(self.prefs_path) as f:
                prefs = yaml.safe_load(f)

            if not prefs:
                return None

            theme = prefs.get("output_theme")

            # Validate
            if theme not in ["light", "dark"]:
                return None

            return theme

        except Exception:
            return None

    def set_theme(self, theme: OutputTheme, source: str = "user_prompt") -> None:
        """
        Set output theme preference.

        Args:
            theme: Theme value ('light' or 'dark')
            source: Source of preference (default: 'user_prompt')

        Raises:
            ValueError: If theme is invalid
        """
        if theme not in ["light", "dark"]:
            raise ValueError(f"Invalid theme: {theme}. Must be 'light' or 'dark'")

        # Ensure directory exists
        self.prefs_path.parent.mkdir(parents=True, exist_ok=True)

        # Create preference data
        prefs = {
            "output_theme": theme,
            "set_at": datetime.now().isoformat(),
            "source": source,
        }

        # Save
        with open(self.prefs_path, "w") as f:
            yaml.dump(prefs, f, default_flow_style=False)

    def is_theme_set(self) -> bool:
        """
        Check if output theme has been set.

        Returns:
            True if theme preference exists, False otherwise
        """
        return self.get_theme() is not None

    def get_all_preferences(self) -> dict:
        """
        Get all output preferences.

        Returns:
            Dictionary of all preferences
        """
        if not self.prefs_path.exists():
            return {}

        try:
            with open(self.prefs_path) as f:
                prefs = yaml.safe_load(f)
            return prefs or {}
        except Exception:
            return {}


def get_theme(project_root: Path) -> OutputTheme | None:
    """
    Get current output theme preference.

    Convenience function.

    Args:
        project_root: Project root directory

    Returns:
        Theme value or None if not set
    """
    prefs = OutputPreferences(project_root)
    return prefs.get_theme()


def set_theme(project_root: Path, theme: OutputTheme, source: str = "user_prompt") -> None:
    """
    Set output theme preference.

    Convenience function.

    Args:
        project_root: Project root directory
        theme: Theme value ('light' or 'dark')
        source: Source of preference
    """
    prefs = OutputPreferences(project_root)
    prefs.set_theme(theme, source)


def is_theme_set(project_root: Path) -> bool:
    """
    Check if output theme has been set.

    Convenience function.

    Args:
        project_root: Project root directory

    Returns:
        True if theme preference exists
    """
    prefs = OutputPreferences(project_root)
    return prefs.is_theme_set()
