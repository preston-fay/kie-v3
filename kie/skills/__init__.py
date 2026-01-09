"""
KIE Skills Runtime System

Skills are declarative, stage-scoped units that:
- Produce artifacts from existing analysis
- Emit evidence for traceability
- NEVER mutate Rails state
- NEVER block execution on failure

This module implements Skills as a first-class runtime primitive
aligned with docs/SKILLS_AND_HOOKS_CONTRACT.md.
"""

from kie.skills.base import Skill, SkillContext, SkillResult
from kie.skills.registry import SkillRegistry, get_registry, register_skill

# Import and register skills
from kie.skills.insight_brief import InsightBriefSkill
from kie.skills.run_story import RunStorySkill

# Auto-register skills
register_skill(InsightBriefSkill())
register_skill(RunStorySkill())

__all__ = [
    "Skill",
    "SkillContext",
    "SkillResult",
    "SkillRegistry",
    "get_registry",
    "register_skill",
    "InsightBriefSkill",
    "RunStorySkill",
]
