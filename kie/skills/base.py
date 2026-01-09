"""
Base Skill Contract

Defines the declarative interface all Skills must implement.

CRITICAL CONSTRAINTS (from governance contract):
- Skills guide AI reasoning (do NOT mutate state)
- Skills are stage-scoped
- Skills are read-only over artifacts
- Skills produce evidence
- Skills NEVER block execution
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SkillContext:
    """
    Context provided to a Skill during execution.

    Contains read-only access to project state and artifacts.
    """
    project_root: Path
    current_stage: str | None
    artifacts: dict[str, Any] = field(default_factory=dict)
    evidence_ledger_id: str | None = None

    def get_artifact_path(self, artifact_name: str) -> Path | None:
        """Get path to an artifact if it exists."""
        if artifact_name in self.artifacts:
            return self.artifacts[artifact_name]
        return None


@dataclass
class SkillResult:
    """
    Result of a Skill execution.

    Contains artifacts produced and evidence for traceability.
    """
    success: bool
    artifacts: dict[str, str] = field(default_factory=dict)  # name -> path
    evidence: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Skill(ABC):
    """
    Base class for all KIE Skills.

    Skills are declarative units that:
    - Are stage-scoped (run only in appropriate workflow stages)
    - Read existing artifacts (NEVER mutate state)
    - Produce new artifacts with evidence
    - Fail gracefully (warnings, not exceptions)

    From governance contract:
    "Skills are bounded capabilities that GUIDE AI REASONING.
     Skills do NOT mutate Rails state. Skills do NOT perform work.
     Skills provide structured context for decision-making."
    """

    # Declarative metadata (must be set by subclasses)
    skill_id: str = ""  # Stable identifier
    description: str = ""  # Human-readable purpose
    stage_scope: list[str] = []  # Rails stages where skill is applicable
    required_artifacts: list[str] = []  # Artifacts this skill needs
    produces_artifacts: list[str] = []  # Artifacts this skill generates

    def __init__(self):
        """Initialize skill and validate metadata."""
        if not self.skill_id:
            raise ValueError(f"{self.__class__.__name__} must define skill_id")
        if not self.stage_scope:
            raise ValueError(f"{self.__class__.__name__} must define stage_scope")

    @abstractmethod
    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute the skill with given context.

        Args:
            context: Read-only context with project state and artifacts

        Returns:
            SkillResult with artifacts, evidence, and status

        CRITICAL: This method MUST NOT:
        - Mutate Rails state
        - Modify existing artifacts
        - Block execution on failure
        - Perform new analysis

        This method SHOULD:
        - Read existing artifacts
        - Synthesize new artifacts
        - Emit evidence for all claims
        - Fail gracefully with warnings
        """
        pass

    def is_applicable(self, stage: str | None) -> bool:
        """Check if skill is applicable in the given stage."""
        if stage is None:
            return False
        return stage in self.stage_scope

    def check_prerequisites(self, context: SkillContext) -> tuple[bool, list[str]]:
        """
        Check if required artifacts are available.

        Returns:
            Tuple of (prerequisites_met, missing_artifacts)
        """
        missing = []
        for artifact_name in self.required_artifacts:
            if artifact_name not in context.artifacts:
                missing.append(artifact_name)

        return len(missing) == 0, missing

    def __repr__(self) -> str:
        """String representation of skill."""
        return f"<Skill:{self.skill_id} stages={self.stage_scope}>"
