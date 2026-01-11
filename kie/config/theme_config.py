"""
Project Theme Configuration

Manages theme preferences at the project level.
Integrates with project spec and persists theme choice.
"""

from pathlib import Path

import yaml

from kie.brand.theme import ThemeMode, set_theme


class ProjectThemeConfig:
    """
    Manage theme configuration for a KIE project.

    Theme preference is stored in project_state/spec.yaml
    """

    def __init__(self, project_dir: Path = None):
        """
        Initialize project theme config.

        Args:
            project_dir: Project root directory (default: current directory)
        """
        self.project_dir = project_dir or Path.cwd()
        self.spec_path = self.project_dir / "project_state" / "spec.yaml"

    def load_theme(self) -> ThemeMode | None:
        """
        Load theme preference from project spec.

        Returns:
            ThemeMode if set, None if unset (no silent defaults)
        """
        if not self.spec_path.exists():
            return None  # No spec = no theme set

        try:
            with open(self.spec_path) as f:
                spec = yaml.safe_load(f) or {}

            # Handle both old format (string) and new format (dict with mode key)
            raw_theme = spec.get("preferences", {}).get("theme", None)

            if isinstance(raw_theme, dict):
                theme_value = raw_theme.get("mode", None)
            else:
                theme_value = raw_theme

            # Explicit check: only "dark" or "light" are valid
            if theme_value not in {"dark", "light"}:
                return None  # Explicit: no theme means no theme

            return ThemeMode(theme_value)

        except Exception as e:
            print(f"Warning: Could not load theme from spec: {e}")
            return None  # On error, return None instead of defaulting

    def save_theme(self, mode: ThemeMode) -> None:
        """
        Save theme preference to project spec.

        Args:
            mode: Theme mode to save
        """
        # Ensure directory exists
        self.spec_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing spec
        spec = {}
        if self.spec_path.exists():
            try:
                with open(self.spec_path) as f:
                    spec = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Could not load existing spec: {e}")

        # Update theme preference
        if "preferences" not in spec:
            spec["preferences"] = {}

        spec["preferences"]["theme"] = mode.value

        # Save spec
        try:
            with open(self.spec_path, "w") as f:
                yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

            print(f"✓ Theme set to: {mode.value}")

        except Exception as e:
            print(f"Error: Could not save theme to spec: {e}")

    def apply_theme(self) -> None:
        """
        Load and apply theme preference from project spec.

        Sets global theme based on project configuration.
        If no theme is set, does nothing (caller should handle this).
        """
        mode = self.load_theme()
        if mode is not None:
            set_theme(mode)

    def change_theme(self, mode: ThemeMode) -> None:
        """
        Change project theme preference.

        Args:
            mode: New theme mode
        """
        # Save to spec
        self.save_theme(mode)

        # Apply globally
        set_theme(mode)


def initialize_project_theme() -> None:
    """
    Initialize theme for current project.

    Loads theme from project_state/spec.yaml and applies globally.
    Should be called at project startup.
    """
    config = ProjectThemeConfig()
    config.apply_theme()


def prompt_theme_preference() -> ThemeMode:
    """
    DEPRECATED: Do not use - causes stdin issues in non-interactive contexts.

    Use /theme command instead to set theme preference.
    Theme must be set via /theme light or /theme dark.

    Returns:
        ThemeMode.DARK (fallback only, should not be called)
    """
    print()
    print("ERROR: prompt_theme_preference() is deprecated")
    print("Use /theme command to set theme preference:")
    print("  /theme light  - Light backgrounds, dark text")
    print("  /theme dark   - Dark backgrounds, white text")
    print()
    # Return default to avoid crashes, but this should never be called
    return ThemeMode.DARK


def get_theme_display_name(mode: ThemeMode) -> str:
    """
    Get display name for theme mode.

    Args:
        mode: Theme mode

    Returns:
        Human-readable name
    """
    if mode == ThemeMode.DARK:
        return "Dark Theme"
    else:
        return "Light Theme"


def get_theme_description(mode: ThemeMode) -> str:
    """
    Get description for theme mode.

    Args:
        mode: Theme mode

    Returns:
        Theme description
    """
    if mode == ThemeMode.DARK:
        return "Dark backgrounds with white text. Reduces eye strain."
    else:
        return "Light backgrounds with dark text. Traditional appearance."
