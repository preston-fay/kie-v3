"""
Canonical paths for all KIE artifacts with backward compatibility.

Provides centralized path management to keep consultant-facing folders clean:
- outputs/internal/ → ALL JSON/YAML technical artifacts
- outputs/charts/ → ONLY SVG files (consultant-visible)
- outputs/deliverables/ → Markdown reports
- exports/ → Final deliverables (PPTX, HTML)
"""

from pathlib import Path


class ArtifactPaths:
    """
    Canonical paths for all KIE artifacts with backward compatibility.

    Provides fallback logic: checks new path first, falls back to old path
    for reading. For writing, always uses new path and creates directories.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.outputs = self.project_root / "outputs"
        self.internal = self.outputs / "internal"

    def _get_path(
        self,
        new_relative: str,
        old_relative: str,
        create_dirs: bool = False
    ) -> Path:
        """
        Get path with fallback logic.

        Args:
            new_relative: Path relative to outputs/ for new location
            old_relative: Path relative to outputs/ for old location
            create_dirs: If True, create parent directories for new path

        Returns:
            Path to use (new if exists or creating, old if exists, else new)
        """
        new_path = self.outputs / new_relative
        old_path = self.outputs / old_relative

        # Writing: always use new location
        if create_dirs:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            return new_path

        # Reading: prefer new location, fall back to old
        if new_path.exists():
            return new_path
        if old_path.exists():
            return old_path

        # Default: return new path
        return new_path

    # Insights artifacts
    def insights_catalog(self, create_dirs: bool = False) -> Path:
        """Path to insights_catalog.json (NEW: internal/, OLD: outputs/)."""
        return self._get_path(
            "internal/insights_catalog.json",
            "insights_catalog.json",
            create_dirs
        )

    def insights_yaml(self, create_dirs: bool = False) -> Path:
        """Path to insights.yaml (NEW: internal/, OLD: outputs/)."""
        return self._get_path(
            "internal/insights.yaml",
            "insights.yaml",
            create_dirs
        )

    # EDA artifacts
    def eda_profile_json(self, create_dirs: bool = False) -> Path:
        """Path to eda_profile.json (NEW: internal/, OLD: outputs/)."""
        return self._get_path(
            "internal/eda_profile.json",
            "eda_profile.json",
            create_dirs
        )

    def eda_profile_yaml(self, create_dirs: bool = False) -> Path:
        """Path to eda_profile.yaml (NEW: internal/, OLD: outputs/)."""
        return self._get_path(
            "internal/eda_profile.yaml",
            "eda_profile.yaml",
            create_dirs
        )

    # Client readiness artifacts
    def client_readiness_json(self, create_dirs: bool = False) -> Path:
        """Path to client_readiness.json (NEW: internal/, OLD: outputs/)."""
        return self._get_path(
            "internal/client_readiness.json",
            "client_readiness.json",
            create_dirs
        )

    # Chart artifacts
    def chart_config(self, filename: str, create_dirs: bool = False) -> Path:
        """
        Path to chart JSON config (NEW: internal/chart_configs/, OLD: charts/).

        Args:
            filename: Chart filename (e.g., "insight_0__bar__top_n.json")
            create_dirs: If True, create internal/chart_configs/ directory

        Returns:
            Path to chart config JSON file
        """
        return self._get_path(
            f"internal/chart_configs/{filename}",
            f"charts/{filename}",
            create_dirs
        )

    def chart_svg(self, filename: str) -> Path:
        """
        Path to chart SVG (always in outputs/charts/ - consultant-visible).

        Args:
            filename: SVG filename (e.g., "insight_0__bar__top_n.svg")

        Returns:
            Path to SVG file in outputs/charts/
        """
        svg_path = self.outputs / "charts" / filename
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        return svg_path
