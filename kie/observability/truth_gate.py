"""
Truth Gate - Constitution Section 5 Enforcement

Validates that all claimed outputs and artifacts actually exist on disk.
Never allows commands to claim non-existent outputs.

CRITICAL INVARIANT:
If a command claims an output exists, that output MUST exist on disk.
If validation fails, the command is marked as FAILED with explicit truth violation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TruthValidation:
    """Result of truth validation check."""

    passed: bool
    missing_artifacts: list[str] = field(default_factory=list)
    validated_artifacts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "missing_artifacts": self.missing_artifacts,
            "validated_artifacts": self.validated_artifacts,
            "warnings": self.warnings,
        }


class TruthGate:
    """
    Validates that command outputs exist on disk.

    Prevents Constitution Section 5 violations where commands claim
    artifacts that don't actually exist.
    """

    def __init__(self, project_root: Path):
        """
        Initialize Truth Gate.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)
        self.outputs_dir = self.project_root / "outputs"
        self.exports_dir = self.project_root / "exports"

    def validate_command_outputs(
        self, command: str, result: dict[str, Any]
    ) -> TruthValidation:
        """
        Validate that all claimed outputs exist.

        Args:
            command: Command that was executed
            result: Command result dict with claimed outputs

        Returns:
            TruthValidation with pass/fail and missing artifacts
        """
        missing = []
        validated = []
        warnings = []

        # Skip validation if command failed already
        if not result.get("success", True):
            return TruthValidation(passed=True)  # Don't double-fail

        # Validate based on command type
        if command == "eda":
            missing.extend(self._validate_eda_outputs(result, validated))
        elif command == "analyze":
            missing.extend(self._validate_analyze_outputs(result, validated))
        elif command == "build":
            missing.extend(self._validate_build_outputs(result, validated))
        elif command == "preview":
            missing.extend(self._validate_preview_outputs(result, validated))
        elif command == "map":
            missing.extend(self._validate_map_outputs(result, validated))

        passed = len(missing) == 0

        return TruthValidation(
            passed=passed,
            missing_artifacts=missing,
            validated_artifacts=validated,
            warnings=warnings,
        )

    def _validate_eda_outputs(
        self, result: dict[str, Any], validated: list[str]
    ) -> list[str]:
        """Validate EDA outputs."""
        missing = []

        # Check profile file
        if "profile_saved" in result:
            profile_path = Path(result["profile_saved"])
            if not profile_path.exists():
                missing.append(str(profile_path))
            else:
                validated.append(str(profile_path))

        # Check EDA review artifacts from skills
        if "skill_results" in result:
            skill_results = result["skill_results"]
            if "artifacts_produced" in skill_results:
                for artifact_name, artifact_path in skill_results[
                    "artifacts_produced"
                ].items():
                    path = Path(artifact_path)
                    if not path.exists():
                        missing.append(str(path))
                    else:
                        validated.append(str(path))

        return missing

    def _validate_analyze_outputs(
        self, result: dict[str, Any], validated: list[str]
    ) -> list[str]:
        """Validate analyze outputs."""
        missing = []

        # Check insights catalog
        if "catalog_saved" in result:
            catalog_path = Path(result["catalog_saved"])
            if not catalog_path.exists():
                missing.append(str(catalog_path))
            else:
                validated.append(str(catalog_path))

        # Check charts if claimed
        if "charts_created" in result and result["charts_created"] > 0:
            charts_dir = self.outputs_dir / "charts"
            if not charts_dir.exists():
                missing.append(f"{charts_dir}/ (directory)")
            else:
                chart_files = list(charts_dir.glob("*.*"))
                if len(chart_files) == 0:
                    missing.append(f"{charts_dir}/ (empty, claimed {result['charts_created']} charts)")
                else:
                    for chart in chart_files:
                        validated.append(str(chart))

        # Check maps if claimed
        if "map_created" in result and result["map_created"]:
            maps_dir = self.outputs_dir / "maps"
            if not maps_dir.exists():
                missing.append(f"{maps_dir}/ (directory)")
            else:
                map_files = list(maps_dir.glob("*.html"))
                if len(map_files) == 0:
                    missing.append(f"{maps_dir}/ (empty, claimed map created)")
                else:
                    validated.append(str(map_files[0]))

        return missing

    def _validate_build_outputs(
        self, result: dict[str, Any], validated: list[str]
    ) -> list[str]:
        """Validate build outputs."""
        missing = []

        # Check presentation if claimed
        if "presentation_path" in result:
            pptx_path = Path(result["presentation_path"])
            if not pptx_path.exists():
                missing.append(str(pptx_path))
            else:
                validated.append(str(pptx_path))

        # Check dashboard if claimed
        if "dashboard_path" in result:
            dashboard_path = Path(result["dashboard_path"])
            if not dashboard_path.exists():
                missing.append(str(dashboard_path))
            else:
                validated.append(str(dashboard_path))

        return missing

    def _validate_preview_outputs(
        self, result: dict[str, Any], validated: list[str]
    ) -> list[str]:
        """Validate preview outputs (should only show what exists)."""
        missing = []

        # Preview should not claim outputs, just list them
        # But we can validate that any mentioned paths exist
        if "outputs" in result:
            for category, paths in result["outputs"].items():
                if isinstance(paths, list):
                    for path_str in paths:
                        path = Path(path_str)
                        if not path.exists():
                            missing.append(f"{path_str} (claimed in preview)")
                        else:
                            validated.append(str(path))

        return missing

    def _validate_map_outputs(
        self, result: dict[str, Any], validated: list[str]
    ) -> list[str]:
        """Validate map outputs."""
        missing = []

        # Check map file if claimed
        if "map_path" in result:
            map_path = Path(result["map_path"])
            if not map_path.exists():
                missing.append(str(map_path))
            else:
                validated.append(str(map_path))

        return missing


def validate_truth(project_root: Path, command: str, result: dict[str, Any]) -> TruthValidation:
    """
    Validate that command outputs exist (convenience function).

    Args:
        project_root: Project root directory
        command: Command that was executed
        result: Command result dict

    Returns:
        TruthValidation result
    """
    gate = TruthGate(project_root)
    return gate.validate_command_outputs(command, result)


def print_truth_violation_message(validation: TruthValidation):
    """Print truth violation message."""
    print()
    print("=" * 70)
    print("TRUTH GATE VIOLATION - Constitution Section 5")
    print("=" * 70)
    print()
    print("Command claimed outputs that DO NOT EXIST on disk.")
    print()
    print("Missing artifacts:")
    for artifact in validation.missing_artifacts:
        print(f"  ✗ {artifact}")
    print()
    print("This is a Constitution violation. The command has been marked as FAILED.")
    print("=" * 70)
    print()
