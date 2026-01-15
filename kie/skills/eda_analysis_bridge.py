"""
EDA → Analysis Bridge Skill

Converts EDA synthesis into explicit, opinionated guidance for downstream analysis.

MISSION:
This skill eliminates ambiguity by answering:
1. What to focus on in analysis
2. What to ignore or de-prioritize
3. What is risky to analyze without care
4. What analysis types are most appropriate
5. What decisions this analysis will enable

INPUTS (READ-ONLY):
- outputs/eda_synthesis.json (required)
- outputs/eda_tables/column_reduction.csv (required)
- project_state/intent.yaml (optional)

OUTPUTS:
- outputs/eda_analysis_bridge.md (markdown guidance)
- outputs/eda_analysis_bridge.json (structured guidance)

STAGE SCOPE: eda, analyze (read-only)

RULES:
- Deterministic output
- No speculation
- No "could", "might", "potential"
- Decisive language ("Focus on...", "Do not analyze...")
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.skills.base import Skill, SkillContext, SkillResult


class EDAAnalysisBridgeSkill(Skill):
    """Generate explicit guidance for downstream analysis from EDA synthesis."""

    @property
    def skill_id(self) -> str:
        return "eda_analysis_bridge"

    @property
    def description(self) -> str:
        return "Generate explicit analysis guidance from EDA synthesis"

    @property
    def stage_scope(self) -> list[str]:
        return ["eda"]

    @property
    def required_artifacts(self) -> list[str]:
        return ["eda_synthesis_json"]

    @property
    def produces_artifacts(self) -> list[str]:
        return ["eda_analysis_bridge_markdown", "eda_analysis_bridge_json"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute EDA analysis bridge generation.

        Args:
            context: Read-only context with project state and artifacts

        Returns:
            SkillResult with bridge artifacts and evidence
        """
        outputs_dir = context.project_root / "outputs"

        # Load EDA synthesis (required)
        (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
        synthesis_path = outputs_dir / "internal" / "eda_synthesis.json"
        if not synthesis_path.exists():
            return SkillResult(
                success=False,
                errors=["eda_synthesis.json not found - run /eda first"],
                artifacts={},
            )

        with open(synthesis_path) as f:
            synthesis = json.load(f)

        # Load intent (optional)
        intent_path = context.project_root / "project_state" / "intent.yaml"
        intent_text = None
        if intent_path.exists():
            import yaml
            with open(intent_path) as f:
                intent_data = yaml.safe_load(f)
                intent_text = intent_data.get("text", "")

        # Generate bridge guidance
        bridge_md = self._generate_bridge_markdown(synthesis, intent_text)
        bridge_json = self._generate_bridge_json(context, synthesis, intent_text)

        # Save markdown
        md_path = outputs_dir / "internal" / "eda_analysis_bridge.md"
        md_path.write_text(bridge_md)

        # Save JSON
        json_path = outputs_dir / "internal" / "eda_analysis_bridge.json"
        with open(json_path, "w") as f:
            json.dump(bridge_json, f, indent=2)

        return SkillResult(
            success=True,
            artifacts={
                "eda_analysis_bridge_markdown": md_path,
                "eda_analysis_bridge_json": json_path,
            },
            evidence=[
                f"Generated analysis bridge with {len(bridge_json['primary_focus'])} primary focus areas",
                f"Identified {len(bridge_json['deprioritized'])} columns to deprioritize",
                f"Recommended {len(bridge_json['recommended_analysis_types'])} analysis types",
            ],
        )

    def _generate_bridge_markdown(self, synthesis: dict[str, Any], intent_text: str | None) -> str:
        """Generate markdown bridge guidance."""
        lines = []

        lines.append("# EDA → Analysis Bridge (Internal)")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if intent_text:
            lines.append(f"**Project Intent:** {intent_text}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. Primary Focus Areas
        lines.append("## 1) Primary Focus Areas")
        lines.append("")
        reduction = synthesis.get("column_reduction", {})
        keep_cols = reduction.get("keep", [])
        reasons = reduction.get("reasons", {})

        if keep_cols:
            for col in keep_cols[:6]:  # Limit to 6
                reason = reasons.get(col, "")
                lines.append(f"- **Focus analysis on `{col}`**: {reason}")
        else:
            lines.append("- No strong focus areas identified")
        lines.append("")

        # 2. Secondary / Exploratory Areas
        lines.append("## 2) Secondary / Exploratory Areas")
        lines.append("")
        investigate_cols = reduction.get("investigate", [])

        if investigate_cols:
            for col in investigate_cols[:6]:  # Limit to 6
                reason = reasons.get(col, "")
                lines.append(f"- **`{col}`** (Optional): {reason}")
        else:
            lines.append("- No secondary areas identified")
        lines.append("")

        # 3. Deprioritized / Ignore
        lines.append("## 3) Deprioritized / Ignore")
        lines.append("")
        ignore_cols = reduction.get("ignore", [])

        if ignore_cols:
            for col in ignore_cols:
                reason = reasons.get(col, "")
                lines.append(f"- **Do not analyze `{col}`**: {reason}")
        else:
            lines.append("- No columns to deprioritize")
        lines.append("")

        # 4. Risks & Analytical Traps
        lines.append("## 4) Risks & Analytical Traps")
        lines.append("")

        risks = self._extract_risks(synthesis)
        if risks:
            for risk in risks:
                lines.append(f"- {risk}")
        else:
            lines.append("- No critical risks identified")
        lines.append("")

        # 5. Recommended Analysis Types
        lines.append("## 5) Recommended Analysis Types")
        lines.append("")

        analysis_types = self._recommend_analysis_types(synthesis, keep_cols)
        if analysis_types:
            for analysis_type in analysis_types:
                lines.append(f"- **{analysis_type['type']}**: {analysis_type['reason']}")
        else:
            lines.append("- Diagnostic deep dive")
        lines.append("")

        # 6. What This Analysis Will Enable
        lines.append("## 6) What This Analysis Will Enable")
        lines.append("")

        outcomes = self._determine_outcomes(synthesis, intent_text, keep_cols)
        if outcomes:
            for outcome in outcomes:
                lines.append(f"- {outcome}")
        else:
            lines.append("- Understanding of data patterns and relationships")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("**INTERNAL ONLY** - Analysis guidance artifact")

        return "\n".join(lines)

    def _generate_bridge_json(self, context: SkillContext, synthesis: dict[str, Any], intent_text: str | None) -> dict[str, Any]:
        """Generate JSON bridge guidance."""
        reduction = synthesis.get("column_reduction", {})
        keep_cols = reduction.get("keep", [])
        investigate_cols = reduction.get("investigate", [])
        ignore_cols = reduction.get("ignore", [])
        reasons = reduction.get("reasons", {})

        # Build primary focus
        primary_focus = []
        for col in keep_cols[:6]:
            primary_focus.append({
                "column": col,
                "reason": reasons.get(col, ""),
            })

        # Build secondary
        secondary = []
        for col in investigate_cols[:6]:
            secondary.append({
                "column": col,
                "reason": reasons.get(col, ""),
            })

        # Build deprioritized
        deprioritized = []
        for col in ignore_cols:
            deprioritized.append({
                "column": col,
                "reason": reasons.get(col, ""),
            })

        # Get project name from spec or use default
        spec_path = context.project_root / "project_state" / "spec.yaml"
        project_name = "EDA Analysis"
        if spec_path.exists():
            import yaml
            with open(spec_path) as f:
                spec_data = yaml.safe_load(f)
                if spec_data:
                    project_name = spec_data.get("project_name", project_name)

        return {
            "project_name": project_name,
            "generated_at": datetime.now().isoformat(),
            "project_intent": intent_text,
            "primary_focus": primary_focus,
            "secondary": secondary,
            "deprioritized": deprioritized,
            "risks": self._extract_risks(synthesis),
            "recommended_analysis_types": self._recommend_analysis_types(synthesis, keep_cols),
            "expected_outcomes": self._determine_outcomes(synthesis, intent_text, keep_cols),
            "metadata": {
                "artifact_classification": "INTERNAL",
                "skill_id": self.skill_id,
            },
        }

    def _extract_risks(self, synthesis: dict[str, Any]) -> list[str]:
        """Extract analytical risks from synthesis."""
        risks = []

        # Outlier risks
        outlier_analysis = synthesis.get("outlier_analysis", {})
        outlier_cols = outlier_analysis.get("outlier_columns", [])
        if outlier_cols:
            risks.append(f"Outliers detected in {len(outlier_cols)} columns - may skew aggregations")

        # Quality risks
        quality_analysis = synthesis.get("quality_analysis", {})
        high_null = quality_analysis.get("columns_with_nulls", [])
        if len(high_null) > 0:
            risks.append(f"Missingness in {len(high_null)} columns - verify before aggregating")

        # Small sample risk
        dataset_overview = synthesis.get("dataset_overview", {})
        row_count = dataset_overview.get("row_count", 0)
        if row_count < 100:
            risks.append("Small sample size - statistical significance may be limited")

        # Distribution risks
        distribution_analysis = synthesis.get("distribution_analysis", {})
        skewed_cols = distribution_analysis.get("skewed_columns", [])
        if skewed_cols:
            risks.append(f"Skewed distributions in {len(skewed_cols)} columns - consider transformations")

        # Warnings from synthesis
        warnings = synthesis.get("warnings", [])
        for warning in warnings[:3]:  # Limit to 3 most important
            if warning not in risks:
                risks.append(warning)

        return risks

    def _recommend_analysis_types(self, synthesis: dict[str, Any], keep_cols: list[str]) -> list[dict[str, str]]:
        """Recommend analysis types based on data characteristics."""
        recommendations = []

        dataset_overview = synthesis.get("dataset_overview", {})
        col_types = dataset_overview.get("column_types", {})
        numeric_cols = col_types.get("numeric", [])
        categorical_cols = col_types.get("categorical", [])

        # Keep only columns that passed reduction
        numeric_keep = [c for c in numeric_cols if c in keep_cols]
        categorical_keep = [c for c in categorical_cols if c in keep_cols]

        # Correlation / driver analysis
        if len(numeric_keep) >= 2:
            recommendations.append({
                "type": "Correlation / driver analysis",
                "reason": f"{len(numeric_keep)} numeric columns available for relationship analysis",
            })

        # Segmentation / clustering
        if len(categorical_keep) >= 1 and len(numeric_keep) >= 1:
            recommendations.append({
                "type": "Segmentation / clustering",
                "reason": f"Categorical dimensions ({len(categorical_keep)}) with numeric metrics",
            })

        # Contribution / decomposition
        dominance_analysis = synthesis.get("dominance_analysis", {})
        top_contributors = dominance_analysis.get("top_contributors", {})
        if top_contributors:
            recommendations.append({
                "type": "Contribution / decomposition",
                "reason": "Dominance patterns detected - understand what drives totals",
            })

        # Trend / change analysis (if time-related columns detected)
        for col in keep_cols:
            col_lower = col.lower()
            if any(kw in col_lower for kw in ["date", "time", "year", "quarter", "month", "week"]):
                recommendations.append({
                    "type": "Trend / change analysis",
                    "reason": f"Time-based column detected ({col})",
                })
                break

        # Diagnostic deep dive (default)
        if not recommendations:
            recommendations.append({
                "type": "Diagnostic deep dive",
                "reason": "Explore patterns in focused columns",
            })

        return recommendations

    def _determine_outcomes(
        self, synthesis: dict[str, Any], intent_text: str | None, keep_cols: list[str]
    ) -> list[str]:
        """Determine what decisions this analysis will enable."""
        outcomes = []

        # If intent provided, align outcomes
        if intent_text:
            intent_lower = intent_text.lower()
            if any(kw in intent_lower for kw in ["efficiency", "optimize", "improve"]):
                outcomes.append("Identify efficiency improvement opportunities")
            if any(kw in intent_lower for kw in ["revenue", "sales", "growth"]):
                outcomes.append("Understand revenue drivers and growth levers")
            if any(kw in intent_lower for kw in ["cost", "expense", "spending"]):
                outcomes.append("Pinpoint cost reduction opportunities")
            if any(kw in intent_lower for kw in ["risk", "quality", "defect"]):
                outcomes.append("Quantify risk exposure and quality gaps")
            if any(kw in intent_lower for kw in ["segment", "customer", "market"]):
                outcomes.append("Define actionable customer or market segments")

        # Generic outcomes based on data characteristics
        if not outcomes:
            if len(keep_cols) >= 3:
                outcomes.append("Understand key relationships and drivers")
                outcomes.append("Identify high-impact focus areas")
            else:
                outcomes.append("Validate data quality and patterns")

        # Always add diagnostic outcome
        if len(outcomes) < 2:
            outcomes.append("Build confidence in data for decision-making")

        return outcomes[:5]  # Limit to 5
