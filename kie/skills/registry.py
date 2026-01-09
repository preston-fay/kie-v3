"""
Skill Registry

Central registry for skill discovery, lifecycle, and metadata.

Provides:
- Auto-registration of skills
- Stage-based lookup
- Enable/disable via config
- Metadata exposure for policy and hooks
"""

from pathlib import Path
from typing import Any

from kie.skills.base import Skill, SkillContext


class SkillRegistry:
    """
    Central registry for all Skills.

    Manages skill lifecycle, discovery, and execution.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._skills: dict[str, Skill] = {}
        self._disabled_skills: set[str] = set()

    def register(self, skill: Skill) -> None:
        """
        Register a skill.

        Args:
            skill: Skill instance to register
        """
        if skill.skill_id in self._skills:
            raise ValueError(f"Skill {skill.skill_id} already registered")

        self._skills[skill.skill_id] = skill

    def get_skill(self, skill_id: str) -> Skill | None:
        """Get a skill by ID."""
        return self._skills.get(skill_id)

    def get_skills_for_stage(self, stage: str) -> list[Skill]:
        """
        Get all enabled skills applicable to a stage.

        Args:
            stage: Rails stage name

        Returns:
            List of applicable, enabled skills
        """
        return [
            skill for skill in self._skills.values()
            if skill.is_applicable(stage) and skill.skill_id not in self._disabled_skills
        ]

    def list_skills(self) -> list[dict[str, Any]]:
        """
        List all registered skills with metadata.

        Returns:
            List of skill metadata dictionaries
        """
        return [
            {
                "skill_id": skill.skill_id,
                "description": skill.description,
                "stage_scope": skill.stage_scope,
                "required_artifacts": skill.required_artifacts,
                "produces_artifacts": skill.produces_artifacts,
                "enabled": skill.skill_id not in self._disabled_skills,
            }
            for skill in self._skills.values()
        ]

    def disable_skill(self, skill_id: str) -> None:
        """Disable a skill by ID."""
        self._disabled_skills.add(skill_id)

    def enable_skill(self, skill_id: str) -> None:
        """Enable a skill by ID."""
        self._disabled_skills.discard(skill_id)

    def is_enabled(self, skill_id: str) -> bool:
        """Check if a skill is enabled."""
        return skill_id not in self._disabled_skills

    def execute_skills_for_stage(
        self,
        stage: str,
        context: SkillContext
    ) -> dict[str, Any]:
        """
        Execute all applicable skills for a stage.

        Args:
            stage: Rails stage name
            context: Skill execution context

        Returns:
            Dictionary with results from all skills
        """
        results = {
            "skills_executed": [],
            "artifacts_produced": {},
            "warnings": [],
            "errors": [],
        }

        skills = self.get_skills_for_stage(stage)

        for skill in skills:
            # Check prerequisites
            prereqs_met, missing = skill.check_prerequisites(context)

            if not prereqs_met:
                results["warnings"].append(
                    f"Skill {skill.skill_id} skipped: missing artifacts {missing}"
                )
                continue

            # Execute skill
            try:
                result = skill.execute(context)

                results["skills_executed"].append({
                    "skill_id": skill.skill_id,
                    "success": result.success,
                    "artifacts": result.artifacts,
                    "evidence": result.evidence,
                })

                # Collect artifacts
                results["artifacts_produced"].update(result.artifacts)

                # Collect warnings and errors
                results["warnings"].extend(result.warnings)
                results["errors"].extend(result.errors)

            except Exception as e:
                # Skills NEVER block - log error and continue
                results["errors"].append(
                    f"Skill {skill.skill_id} failed: {str(e)}"
                )

        return results


# Global registry instance
_global_registry: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    """Get the global skill registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = SkillRegistry()
    return _global_registry


def register_skill(skill: Skill) -> None:
    """Register a skill in the global registry."""
    registry = get_registry()
    registry.register(skill)
