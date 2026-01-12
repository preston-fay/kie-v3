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
from kie.skills.actionability_scoring import ActionabilityScoringSkill
from kie.skills.client_pack import ClientPackSkill
from kie.skills.client_readiness import ClientReadinessSkill
from kie.skills.eda_review import EDAReviewSkill
from kie.skills.eda_synthesis import EDASynthesisSkill
from kie.skills.executive_summary import ExecutiveSummarySkill
from kie.skills.insight_brief import InsightBriefSkill
from kie.skills.insight_triage import InsightTriageSkill
from kie.skills.narrative_synthesis import NarrativeSynthesisSkill
from kie.skills.run_story import RunStorySkill
from kie.skills.story_manifest import StoryManifestSkill
from kie.skills.visual_qc import VisualQCSkill
from kie.skills.visualization_planner import VisualizationPlannerSkill
from kie.skills.visual_storyboard import VisualStoryboardSkill

# Auto-register skills
register_skill(ActionabilityScoringSkill())
register_skill(ClientPackSkill())
register_skill(ClientReadinessSkill())
register_skill(EDAReviewSkill())
register_skill(EDASynthesisSkill())
register_skill(ExecutiveSummarySkill())
register_skill(InsightBriefSkill())
register_skill(InsightTriageSkill())
register_skill(NarrativeSynthesisSkill())
register_skill(RunStorySkill())
register_skill(StoryManifestSkill())
register_skill(VisualQCSkill())
register_skill(VisualizationPlannerSkill())
register_skill(VisualStoryboardSkill())

__all__ = [
    "Skill",
    "SkillContext",
    "SkillResult",
    "SkillRegistry",
    "get_registry",
    "register_skill",
    "ActionabilityScoringSkill",
    "ClientPackSkill",
    "ClientReadinessSkill",
    "EDAReviewSkill",
    "EDASynthesisSkill",
    "ExecutiveSummarySkill",
    "InsightBriefSkill",
    "InsightTriageSkill",
    "NarrativeSynthesisSkill",
    "RunStorySkill",
    "StoryManifestSkill",
    "VisualQCSkill",
    "VisualizationPlannerSkill",
    "VisualStoryboardSkill",
]
