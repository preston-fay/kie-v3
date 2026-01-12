"""
Freeform Bridge Skill

Converts freeform analysis artifacts into KIE-governed story inputs.

MISSION:
- Scan outputs/freeform/ for tables, metrics, and summaries
- Convert into structured insights_catalog.json
- Enable governed story generation from freeform analysis

CRITICAL CONSTRAINTS:
- NO new analysis or clustering
- Only bridges existing freeform outputs
- Must validate execution_mode == freeform
- Outputs must be ready for existing triage/narrative pipeline
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.insights import Insight, InsightCatalog, InsightType, InsightSeverity, InsightCategory, Evidence
from kie.skills.base import Skill, SkillContext, SkillResult
from kie.state import ExecutionPolicy, ExecutionMode


class FreeformBridgeSkill(Skill):
    """
    Bridges freeform analysis artifacts into KIE-governed story inputs.

    Converts freeform tables/metrics into insights_catalog.json
    that the existing triage/narrative pipeline can consume.

    Stage Scope: analyze, build
    Required Artifacts: outputs/freeform/ directory with artifacts
    Produces: insights_catalog.json, freeform_insights_catalog.json
    """

    skill_id = "freeform_bridge"
    description = "Bridge freeform artifacts into KIE-governed story inputs"
    stage_scope = ["analyze", "build"]
    required_artifacts = []  # Dynamically checks freeform/
    produces_artifacts = ["insights_catalog.json", "freeform_insights_catalog.json"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Convert freeform artifacts into insights_catalog.json.

        Args:
            context: Skill execution context

        Returns:
            SkillResult with insights catalog and metadata
        """
        # Validate execution mode
        policy = ExecutionPolicy(context.project_root)
        if policy.get_mode() != ExecutionMode.FREEFORM:
            return SkillResult(
                success=False,
                message="Freeform bridge requires execution_mode == freeform. Run /freeform enable first.",
                errors=["Execution mode is not freeform"],
                artifacts_produced=[]
            )

        freeform_dir = context.project_root / "outputs" / "freeform"
        outputs_dir = context.project_root / "outputs"

        # Ensure freeform directory exists
        if not freeform_dir.exists():
            freeform_dir.mkdir(parents=True, exist_ok=True)

        # Create NOTICE.md for freeform visual policy
        self._create_visual_notice(freeform_dir)

        # Scan for freeform artifacts
        tables_dir = freeform_dir / "tables"
        summaries_dir = freeform_dir / "summaries"
        metrics_dir = freeform_dir / "metrics"

        insights = []
        artifact_refs = []

        # Process tables
        if tables_dir.exists():
            for table_file in tables_dir.glob("*.csv"):
                table_insights = self._process_table(table_file, freeform_dir)
                insights.extend(table_insights)
                artifact_refs.append(str(table_file.relative_to(context.project_root)))

        # Process summaries
        if summaries_dir.exists():
            for summary_file in summaries_dir.glob("*.json"):
                summary_insights = self._process_summary(summary_file, freeform_dir)
                insights.extend(summary_insights)
                artifact_refs.append(str(summary_file.relative_to(context.project_root)))

        # Process metrics
        if metrics_dir.exists():
            for metrics_file in metrics_dir.glob("*.json"):
                metrics_insights = self._process_metrics(metrics_file, freeform_dir)
                insights.extend(metrics_insights)
                artifact_refs.append(str(metrics_file.relative_to(context.project_root)))

        # If no artifacts found, create minimal catalog
        if not insights:
            insights = [
                Insight(
                    id="freeform-placeholder-1",
                    headline="Freeform Analysis Completed",
                    supporting_text="Detailed freeform analysis was conducted. Review outputs/freeform/ for full analysis.",
                    insight_type=InsightType.COMPARISON,
                    severity=InsightSeverity.CONTEXT,
                    category=InsightCategory.FINDING,
                    confidence=0.5,
                    evidence=[],
                    tags=["freeform", "exploratory"]
                )
            ]

        # Get business question from spec
        spec_path = context.project_root / "project_state" / "spec.yaml"
        business_question = "Freeform Analysis"
        if spec_path.exists():
            import yaml
            with open(spec_path) as f:
                spec = yaml.safe_load(f)
                if spec:
                    business_question = spec.get("objective", business_question)

        # Create insights catalog
        catalog = InsightCatalog(
            generated_at=datetime.now().isoformat(),
            business_question=business_question,
            insights=insights,
            narrative_arc={
                "source": "freeform_bridge",
                "artifact_count": len(artifact_refs),
                "artifact_refs": artifact_refs
            },
            data_summary={
                "freeform_artifacts_processed": len(artifact_refs),
                "insights_generated": len(insights)
            }
        )

        # Save freeform insights catalog
        freeform_catalog_path = outputs_dir / "freeform_insights_catalog.json"
        with open(freeform_catalog_path, "w") as f:
            json.dump(catalog.to_dict(), f, indent=2)

        # Save as standard insights_catalog.json for pipeline
        insights_catalog_path = outputs_dir / "insights_catalog.json"
        with open(insights_catalog_path, "w") as f:
            json.dump(catalog.to_dict(), f, indent=2)

        return SkillResult(
            success=True,
            artifacts={
                "freeform_catalog": str(freeform_catalog_path.relative_to(context.project_root)),
                "insights_catalog": str(insights_catalog_path.relative_to(context.project_root))
            },
            metadata={
                "artifact_count": len(artifact_refs),
                "insight_count": len(insights),
                "artifact_refs": artifact_refs,
                "summary": f"Bridged {len(artifact_refs)} freeform artifacts into {len(insights)} insights"
            }
        )

    def _process_table(self, table_path: Path, freeform_dir: Path) -> list[Insight]:
        """
        Process a CSV table into insights.

        Args:
            table_path: Path to CSV table
            freeform_dir: Freeform directory

        Returns:
            List of insights extracted from table
        """
        insights = []

        try:
            with open(table_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                return insights

            # Get headers
            headers = rows[0].keys() if rows else []

            # Create insight from table
            table_name = table_path.stem
            row_count = len(rows)

            # Try to extract metrics from first row
            metric_values = []
            for col in headers:
                try:
                    val = float(rows[0][col])
                    metric_values.append((col, val))
                except (ValueError, KeyError):
                    continue

            if metric_values:
                # Create insight from metrics
                top_metric = max(metric_values, key=lambda x: abs(x[1]))
                insight = Insight(
                    id=f"freeform-table-{table_name}",
                    headline=f"{table_name.replace('_', ' ').title()}: {top_metric[0]} Shows {top_metric[1]:.1f}",
                    supporting_text=f"Analysis of {table_name} shows {row_count} data points. Key metric {top_metric[0]} has value {top_metric[1]:.2f}.",
                    insight_type=InsightType.COMPARISON,
                    severity=InsightSeverity.SUPPORTING,
                    category=InsightCategory.FINDING,
                    confidence=0.7,
                    evidence=[
                        Evidence(
                            evidence_type="data_point",
                            reference=str(table_path.relative_to(freeform_dir.parent)),
                            value=top_metric[1],
                            label=top_metric[0]
                        )
                    ],
                    tags=["freeform", "table", table_name]
                )
                insights.append(insight)

        except Exception as e:
            # Graceful failure - create placeholder insight
            insight = Insight(
                id=f"freeform-table-{table_path.stem}",
                headline=f"Table Analysis: {table_path.stem}",
                supporting_text=f"Processed table from {table_path.name}. See file for details.",
                insight_type=InsightType.COMPARISON,
                severity=InsightSeverity.CONTEXT,
                category=InsightCategory.FINDING,
                confidence=0.5,
                evidence=[
                    Evidence(
                        evidence_type="data_point",
                        reference=str(table_path.relative_to(freeform_dir.parent)),
                        value=f"Error: {str(e)}",
                        label="processing_error"
                    )
                ],
                tags=["freeform", "table", "error"]
            )
            insights.append(insight)

        return insights

    def _process_summary(self, summary_path: Path, freeform_dir: Path) -> list[Insight]:
        """
        Process a JSON summary into insights.

        Args:
            summary_path: Path to summary JSON
            freeform_dir: Freeform directory

        Returns:
            List of insights extracted from summary
        """
        insights = []

        try:
            with open(summary_path) as f:
                summary_data = json.load(f)

            summary_name = summary_path.stem

            # Extract insights from summary structure
            if isinstance(summary_data, dict):
                # Try to extract headline and supporting text
                headline = summary_data.get("headline", summary_data.get("title", f"Summary: {summary_name}"))
                supporting = summary_data.get("text", summary_data.get("description", "See summary file for details."))

                insight = Insight(
                    id=f"freeform-summary-{summary_name}",
                    headline=headline[:100],  # Truncate if needed
                    supporting_text=supporting[:500],  # Truncate if needed
                    insight_type=InsightType.COMPARISON,
                    severity=InsightSeverity.SUPPORTING,
                    category=InsightCategory.FINDING,
                    confidence=0.7,
                    evidence=[
                        Evidence(
                            evidence_type="metric",
                            reference=str(summary_path.relative_to(freeform_dir.parent)),
                            value=summary_data,
                            label="summary"
                        )
                    ],
                    tags=["freeform", "summary", summary_name]
                )
                insights.append(insight)

        except Exception as e:
            # Graceful failure
            insight = Insight(
                id=f"freeform-summary-{summary_path.stem}",
                headline=f"Summary: {summary_path.stem}",
                supporting_text=f"Processed summary from {summary_path.name}.",
                insight_type=InsightType.COMPARISON,
                severity=InsightSeverity.CONTEXT,
                category=InsightCategory.FINDING,
                confidence=0.5,
                evidence=[],
                tags=["freeform", "summary", "error"]
            )
            insights.append(insight)

        return insights

    def _process_metrics(self, metrics_path: Path, freeform_dir: Path) -> list[Insight]:
        """
        Process metrics JSON into insights.

        Args:
            metrics_path: Path to metrics JSON
            freeform_dir: Freeform directory

        Returns:
            List of insights extracted from metrics
        """
        insights = []

        try:
            with open(metrics_path) as f:
                metrics_data = json.load(f)

            metrics_name = metrics_path.stem

            # Extract metrics
            if isinstance(metrics_data, dict):
                for key, value in metrics_data.items():
                    if isinstance(value, (int, float)):
                        insight = Insight(
                            id=f"freeform-metric-{metrics_name}-{key}",
                            headline=f"{key.replace('_', ' ').title()}: {value}",
                            supporting_text=f"Metric {key} from {metrics_name} shows value of {value}.",
                            insight_type=InsightType.COMPARISON,
                            severity=InsightSeverity.SUPPORTING,
                            category=InsightCategory.FINDING,
                            confidence=0.8,
                            evidence=[
                                Evidence(
                                    evidence_type="metric",
                                    reference=str(metrics_path.relative_to(freeform_dir.parent)),
                                    value=value,
                                    label=key
                                )
                            ],
                            tags=["freeform", "metric", metrics_name]
                        )
                        insights.append(insight)

        except Exception as e:
            # Graceful failure
            insight = Insight(
                id=f"freeform-metrics-{metrics_path.stem}",
                headline=f"Metrics: {metrics_path.stem}",
                supporting_text=f"Processed metrics from {metrics_path.name}.",
                insight_type=InsightType.COMPARISON,
                severity=InsightSeverity.CONTEXT,
                category=InsightCategory.FINDING,
                confidence=0.5,
                evidence=[],
                tags=["freeform", "metrics", "error"]
            )
            insights.append(insight)

        return insights

    def _create_visual_notice(self, freeform_dir: Path):
        """
        Create NOTICE.md for freeform visual policy.

        Args:
            freeform_dir: Freeform directory
        """
        notice_path = freeform_dir / "NOTICE.md"

        # Scan for PNG files
        png_files = list(freeform_dir.glob("**/*.png"))

        notice_content = """# Freeform Visual Policy

## NON-KIE Visuals

This directory may contain visuals (PNGs, charts) created outside the KIE chart engine.

**CRITICAL:**
- These visuals are NOT KDS-compliant
- They are EXCLUDED from client deliverables (PPT, Dashboard)
- They are marked as exploratory/internal only

## KDS Compliance

For KDS-compliant visuals that CAN be included in client deliverables:
1. Use the KIE chart engine via /freeform export
2. Charts will be rendered through visualization_planner → chart_renderer
3. All charts will enforce KDS design rules (purple palette, no gridlines, etc.)

## Guidance

Deep freeform analysis is allowed. However:
- **Visuals MUST be rendered via KIE chart engine for KDS compliance**
- Ad-hoc matplotlib/seaborn PNGs are exploratory only
- Not promoted to client artifacts automatically

"""

        if png_files:
            notice_content += f"\n## Detected Non-KIE Visuals\n\n"
            notice_content += f"Found {len(png_files)} PNG files in freeform/:\n\n"
            for png_file in png_files:
                rel_path = png_file.relative_to(freeform_dir)
                notice_content += f"- {rel_path} (NON-KIE, exploratory only)\n"
            notice_content += "\nThese files are excluded from story_manifest and client deliverables.\n"

        with open(notice_path, "w") as f:
            f.write(notice_content)
