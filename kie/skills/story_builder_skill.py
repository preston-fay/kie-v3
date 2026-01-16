"""
Story Builder Skill

LLM-POWERED STORY-FIRST ARCHITECTURE: Generates domain-agnostic story manifests.

This skill runs DURING the analyze stage (not build) and creates story manifests
using LLM-powered components that work for ANY data type (healthcare, IoT,
manufacturing, finance, business, etc.).

INPUTS (read-only, required):
- outputs/insights.yaml (raw insights from InsightEngine)
- project_state/spec.yaml (project metadata)

OUTPUTS (canonical artifacts):
- outputs/internal/story_manifest.json (executive mode)
- outputs/internal/story_manifest_analyst.json (analyst mode)
- outputs/internal/story_manifest_technical.json (technical mode)

STAGE SCOPE: analyze

KEY FEATURES:
- Dynamic topic learning (no hardcoded business keywords)
- Pattern-based chart selection (27 chart types)
- Domain-agnostic narratives (adapts language to context)
- Works for literally ANY tabular data

This transforms insights→story BEFORE visualization planning.
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from kie.story.models import StoryInsight
from kie.skills.base import Skill, SkillContext, SkillResult
from kie.story import LLMStoryBuilder, NarrativeMode

logger = logging.getLogger(__name__)


class StoryBuilderSkill(Skill):
    """
    Build story manifest from insights using story-first architecture.

    NEW ARCHITECTURE: Generates story manifest directly from insights
    during analyze stage (before visualization planning).
    """

    @property
    def skill_id(self) -> str:
        return "story_builder"

    @property
    def description(self) -> str:
        return "Transform insights into consultant-grade story with thesis, KPIs, and sections"

    @property
    def stage_scope(self) -> list[str]:
        return ["analyze"]

    @property
    def required_artifacts(self) -> list[str]:
        return ["insights_catalog"]  # outputs/insights.yaml

    @property
    def produces_artifacts(self) -> list[str]:
        return [
            "story_manifest_executive",
            "story_manifest_analyst",
            "story_manifest_technical"
        ]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute story builder.

        Args:
            context: Skill execution context

        Returns:
            SkillResult with story manifests in 3 modes
        """
        outputs_dir = context.project_root / "outputs"
        internal_dir = outputs_dir / "internal"
        internal_dir.mkdir(parents=True, exist_ok=True)

        warnings = []
        errors = []

        try:
            # Load insights catalog
            insights_yaml = context.artifacts.get("insights_catalog")
            if not insights_yaml:
                insights_yaml = outputs_dir / "insights.yaml"
            else:
                insights_yaml = Path(insights_yaml)

            if not insights_yaml.exists():
                errors.append("insights_catalog not found at outputs/insights.yaml")
                return SkillResult(
                    success=False,
                    artifacts={},
                    evidence=[],
                    warnings=warnings,
                    errors=errors,
                )

            # Load insights
            with open(insights_yaml, encoding="utf-8") as f:
                insights_data = yaml.safe_load(f)

            if not insights_data or "insights" not in insights_data:
                errors.append("No insights found in insights_catalog")
                return SkillResult(
                    success=False,
                    artifacts={},
                    evidence=[],
                    warnings=warnings,
                    errors=errors,
                )

            # Convert to Insight objects
            insights = []
            for item in insights_data["insights"]:
                # Combine headline + supporting_text into text field
                text = item.get("headline", "")
                if item.get("supporting_text"):
                    text += " " + item["supporting_text"]

                # Calculate business_value from severity
                severity_map = {
                    "critical": 1.0,
                    "key": 0.9,
                    "supporting": 0.7,
                    "context": 0.5,
                }
                business_value = severity_map.get(item.get("severity", "supporting"), 0.7)

                # Estimate actionability from insight_type
                actionability_map = {
                    "comparison": 0.9,
                    "anomaly": 0.95,
                    "trend": 0.85,
                    "distribution": 0.6,
                    "concentration": 0.7,
                    "outlier": 0.8,
                }
                actionability = actionability_map.get(item.get("insight_type", ""), 0.7)

                insight = StoryInsight(
                    insight_id=item.get("id", ""),
                    text=text,
                    category=item.get("category", "finding"),
                    confidence=item.get("confidence", 0.0),
                    business_value=business_value,
                    actionability=actionability,
                    supporting_data=item.get("evidence", []),
                )
                insights.append(insight)

            if not insights:
                errors.append("No insights to process")
                return SkillResult(
                    success=False,
                    artifacts={},
                    evidence=[],
                    warnings=warnings,
                    errors=errors,
                )

            # Load project metadata
            spec_path = context.project_root / "project_state" / "spec.yaml"
            project_name = "Analysis"
            objective = None

            if spec_path.exists():
                with open(spec_path, encoding="utf-8") as f:
                    spec = yaml.safe_load(f)
                    if spec:
                        project_name = spec.get("project_name", "Analysis")
                        objective = spec.get("objective")

            # Build chart refs (will be populated later by visualization skills)
            chart_refs = {}  # insight_id -> chart_path mapping (empty for now)

            # Build story manifests in all three modes using LLM-powered builder
            # This provides domain-agnostic story generation (works for ANY data type)
            artifacts = {}
            evidence = []

            for mode in [NarrativeMode.EXECUTIVE, NarrativeMode.ANALYST, NarrativeMode.TECHNICAL]:
                builder = LLMStoryBuilder(
                    narrative_mode=mode,
                    use_llm_grouping=True,   # Dynamic topic learning
                    use_llm_narrative=True,  # Domain-agnostic narratives
                    use_llm_charts=True      # Pattern-based chart selection
                )

                manifest = builder.build_story(
                    insights=insights,
                    project_name=project_name,
                    objective=objective,
                    chart_refs=chart_refs,
                    context_str=""  # Could add sample size info here later
                )

                # Save manifest
                mode_suffix = "" if mode == NarrativeMode.EXECUTIVE else f"_{mode.value}"
                output_path = internal_dir / f"story_manifest{mode_suffix}.json"
                manifest.save(output_path)

                artifacts[f"story_manifest{mode_suffix}"] = output_path

                evidence.append(
                    f"{mode.value.title()}: {len(manifest.sections)} sections, "
                    f"{len(manifest.top_kpis)} top KPIs, thesis='{manifest.thesis.title}'"
                )

                logger.info(f"Created {mode.value} story manifest at {output_path}")

            return SkillResult(
                success=True,
                artifacts=artifacts,
                evidence=evidence,
                warnings=warnings,
                errors=errors,
            )

        except Exception as e:
            logger.error(f"Story builder failed: {e}", exc_info=True)
            errors.append(f"Story builder failed: {e}")
            return SkillResult(
                success=False,
                artifacts={},
                evidence=[],
                warnings=warnings,
                errors=[str(e)],
            )
