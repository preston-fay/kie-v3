"""
EDA Consultant Report Skill

Generates ONE consultant-friendly EDA report from internal analysis files.
This synthesizes eda_synthesis, eda_analysis_bridge, and eda_review into
a single scannable 100-200 line markdown report with business narrative.
"""

from pathlib import Path
import json
from typing import Any
from kie.skills.base import Skill, SkillContext, SkillResult
from kie.formatting.field_registry import FieldRegistry
from kie.charts.formatting import format_currency, format_number, format_percentage


class EDAConsultantReport(Skill):
    """
    Generate consultant-facing EDA report.

    Reads:
    - eda_synthesis.json (statistical analysis)
    - eda_analysis_bridge.json (column guidance)
    - eda_review.json (quality assessment)

    Produces:
    - outputs/EDA_Report.md (consultant-facing narrative)
    """

    @property
    def skill_id(self) -> str:
        return "eda_consultant_report"

    @property
    def stage_scope(self) -> list[str]:
        return ["eda"]

    @property
    def required_artifacts(self) -> list[str]:
        return ["eda_synthesis_json"]  # Requires eda_synthesis to run first

    def execute(self, context: SkillContext) -> SkillResult:
        try:
            # Load internal analysis files
            synthesis_path = context.project_root / "outputs" / "internal" / "eda_synthesis.json"
            bridge_path = context.project_root / "outputs" / "internal" / "eda_analysis_bridge.json"
            review_path = context.project_root / "outputs" / "eda_review.json"

            if not synthesis_path.exists():
                return SkillResult(
                    success=False,
                    errors=["eda_synthesis.json not found - run EDA first"]
                )

            synthesis = json.loads(synthesis_path.read_text())
            bridge = json.loads(bridge_path.read_text()) if bridge_path.exists() else {}
            review = json.loads(review_path.read_text()) if review_path.exists() else {}

            # Generate consultant report
            report_lines = self._generate_report(synthesis, bridge, review, context)

            # Save
            # Write to deliverables/ (consultant-facing finished product)
            output_path = context.project_root / "outputs" / "deliverables" / "EDA_Report.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(report_lines))

            return SkillResult(
                success=True,
                artifacts={"consultant_report": str(output_path)},
                metadata={"line_count": len(report_lines)}
            )

        except Exception as e:
            return SkillResult(
                success=False,
                errors=[f"Failed to generate consultant report: {e}"]
            )

    def _generate_report(self, synthesis: dict, bridge: dict, review: dict, context: SkillContext) -> list[str]:
        """Generate complete consultant report"""
        lines = []

        # Header - get project name from spec if available
        try:
            import yaml
            spec_path = context.project_root / "project_state" / "spec.yaml"
            if spec_path.exists():
                spec = yaml.safe_load(spec_path.read_text())
                project_name = spec.get("project_name", "Your Project")
            else:
                project_name = "Your Project"
        except Exception:
            project_name = "Your Project"
        overview = synthesis.get("dataset_overview", {})
        lines.append(f"# Exploratory Data Analysis: {project_name}")
        lines.append("")
        lines.append(f"**Data Source**: {overview.get('filename', 'Unknown')}")
        lines.append(f"**Records**: {overview.get('rows', 0):,} rows")
        lines.append(f"**Features**: {overview.get('columns', 0)} columns")
        lines.append("")
        lines.append("---")
        lines.append("")

        # KPI Summary Section
        lines.extend(self._generate_kpi_summary(synthesis, bridge))
        lines.append("")
        lines.append("---")
        lines.append("")

        # Executive Summary
        insights = self._extract_insights(synthesis, bridge, review)
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"We analyzed your dataset containing {overview.get('rows', 0):,} records and {overview.get('columns', 0)} features. Here are the {min(3, len(insights))} most important findings:")
        lines.append("")
        for i, insight in enumerate(insights[:3], 1):
            lines.append(f"{i}. **{insight['headline']}** - {insight['summary']}")
            lines.append("")
        lines.append("---")
        lines.append("")

        # Detailed Findings
        for i, insight in enumerate(insights[:5], 1):
            lines.append(f"## Key Finding #{i}: {insight['title']}")
            lines.append("")
            lines.append(insight['narrative'])
            lines.append("")

            if insight.get('chart_path'):
                lines.append(f"**Chart**: ![{insight['title']}]({insight['chart_path']})")
                lines.append("")

            lines.append(f"**What This Means**: {insight['interpretation']}")
            lines.append("")
            lines.append(f"**Recommended Action**: {insight['action']}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Data Quality Summary
        lines.extend(self._generate_quality_section(synthesis, review))

        # Next Steps
        lines.extend(self._generate_next_steps(synthesis, bridge))

        # Technical References
        lines.append("---")
        lines.append("")
        lines.append("**Technical Details**:")
        lines.append("- Full statistical breakdown: `eda_synthesis.md`")
        lines.append("- Column recommendations: `eda_analysis_bridge.md`")
        lines.append("- Data quality report: `eda_review.md`")

        return lines

    def _generate_kpi_summary(self, synthesis: dict, bridge: dict) -> list[str]:
        """Generate executive KPI summary with key metrics"""
        lines = []
        lines.append("## Key Performance Indicators")
        lines.append("")

        # Get dominance analysis for primary metric
        dom = synthesis.get("dominance_analysis", {})
        dominant_metric = dom.get("dominant_metric")
        dominant_value = dom.get("dominant_value", 0)

        # Get distribution analysis for variability insights
        dist_analysis = synthesis.get("distribution_analysis", {})

        # Get column types for context
        overview = synthesis.get("dataset_overview", {})
        rows = overview.get("rows", 0)

        if dominant_metric and dominant_value > 0:
            metric_display = FieldRegistry.beautify(dominant_metric)
            per_record = dominant_value / rows if rows > 0 else 0

            lines.append(f"### Primary Metric: {metric_display}")
            lines.append("")
            lines.append(f"- **Total Value**: {format_currency(dominant_value) if 'revenue' in dominant_metric.lower() or 'cost' in dominant_metric.lower() or 'value' in dominant_metric.lower() or 'income' in dominant_metric.lower() or 'target' in dominant_metric.lower() else format_number(dominant_value)}")
            lines.append(f"- **Per Record Average**: {format_currency(per_record) if 'revenue' in dominant_metric.lower() or 'cost' in dominant_metric.lower() or 'value' in dominant_metric.lower() or 'income' in dominant_metric.lower() or 'target' in dominant_metric.lower() else format_number(per_record)}")

            # Add variability metric if available
            if dominant_metric in dist_analysis:
                stats = dist_analysis[dominant_metric]
                std_val = stats.get("std", 0)
                mean_val = stats.get("mean", 0)
                cv = (std_val / mean_val * 100) if mean_val != 0 else 0
                lines.append(f"- **Variability (CV)**: {cv:.0f}% {'(High - significant heterogeneity)' if cv > 50 else '(Moderate - some variation)' if cv > 20 else '(Low - relatively consistent)'}")

            lines.append("")

        # Data completeness KPI
        quality = synthesis.get("data_quality", {})
        null_pct = quality.get("null_percent", 0)
        duplicate_pct = quality.get("duplicate_percent", 0)

        lines.append("### Data Quality Metrics")
        lines.append("")
        lines.append(f"- **Completeness**: {100 - null_pct:.1f}% {'✓ Excellent' if null_pct < 1 else '⚠ Needs attention' if null_pct < 10 else '❌ Critical gaps'}")
        lines.append(f"- **Uniqueness**: {100 - duplicate_pct:.1f}% {'✓ No duplicates' if duplicate_pct == 0 else f'⚠ {duplicate_pct:.1f}% duplicates detected'}")
        lines.append(f"- **Sample Size**: {rows:,} records {'✓ Adequate' if rows >= 1000 else '⚠ Limited' if rows >= 100 else '❌ Insufficient'}")
        lines.append("")

        # Segment concentration (from top contributors)
        top_contrib = dom.get("top_contributors", {})
        if top_contrib:
            category = FieldRegistry.beautify(top_contrib.get("category", ""))
            values = top_contrib.get("values", {})
            if values and dominant_value > 0:
                # Calculate concentration (top segment %)
                top_value = max(values.values()) if values else 0
                concentration = (top_value / dominant_value * 100) if dominant_value > 0 else 0

                lines.append("### Segment Analysis")
                lines.append("")
                lines.append(f"- **Segmentation Basis**: {category}")
                lines.append(f"- **Number of Segments**: {len(values)}")
                lines.append(f"- **Top Segment Contribution**: {concentration:.0f}% {'⚠ High concentration risk' if concentration > 60 else '✓ Balanced distribution' if concentration < 40 else 'Moderate concentration'}")
                lines.append("")

        return lines

    def _extract_insights(self, synthesis: dict, bridge: dict, review: dict) -> list[dict]:
        """Extract top 5 insights from analysis"""
        insights = []

        # Insight 1: Dominance concentration
        dom = synthesis.get("dominance_analysis", {})
        top_contrib_data = dom.get("top_contributors", {})
        if dom.get("dominant_metric") and top_contrib_data:
            # top_contributors is a dict with 'values' key containing the actual contributors
            top_values = top_contrib_data.get("values", {})
            if top_values:
                total_value = dom.get("dominant_value", 0)
                top_sum = sum(list(top_values.values())[:5])
                top_pct = (top_sum / total_value * 100) if total_value > 0 else 0

                insights.append({
                    "headline": "Revenue is heavily concentrated",
                    "summary": f"The top 5 contributors account for {format_percentage(top_pct, precision=0)} of {dom['dominant_metric']}",
                    "title": "Revenue Concentration Risk",
                    "narrative": f"The dataset reveals heavy concentration in {dom['dominant_metric']}, with the top 5 contributors accounting for {format_percentage(top_pct, precision=0)} of all value ({format_currency(total_value)} total). This concentration creates vulnerability - if these peak performers were to decline, the portfolio would face significant downside exposure.",
                    "chart_path": "eda_charts/contribution_" + top_contrib_data.get("metric", "unknown") + ".svg",
                    "interpretation": "Your business has dependency risk. A handful of high-performing periods drive most value.",
                    "action": "Investigate what makes top performers successful and replicate across other periods. Consider hedging strategies to protect against concentration risk."
                })

        # Insight 2: Distribution patterns and variability
        dist_analysis = synthesis.get("distribution_analysis", {})
        count = 0
        for col, stats in dist_analysis.items():
            if count >= 2:
                break

            # Skip ID columns
            if self._is_likely_id_column(col, stats):
                continue

            mean_val = stats.get("mean", 0)
            median_val = stats.get("median", 0)
            std_val = stats.get("std", 0)
            min_val = stats.get("min", 0)
            max_val = stats.get("max", 0)

            # Skip if no variation or if this is likely an ID column
            if std_val == 0 or max_val == 0:
                continue

            # Calculate coefficient of variation
            cv = (std_val / mean_val) if mean_val != 0 else 0

            col_display = FieldRegistry.beautify(col)

            # Generate business-focused insight based on variation
            if cv > 0.5:
                # High variation - significant heterogeneity
                range_val = max_val - min_val
                headline = f"{col_display} shows significant variation across records"
                summary = f"Values range from {format_number(min_val)} to {format_number(max_val)}, with {format_number(std_val)} standard deviation"
                narrative = f"The {col_display} metric exhibits substantial variation (CV: {cv:.0%}), indicating heterogeneity across the dataset. Median value ({format_number(median_val)}) differs from mean ({format_number(mean_val)}), suggesting the presence of outliers or distinct segments. This variation presents both opportunities and risks - understanding what drives high-performing segments could unlock significant value."
                interpretation = f"High variation suggests the presence of distinct segments or performance tiers. Not all records are created equal."
                action = f"Segment the data by {col_display} performance tiers (top/middle/bottom terciles) and identify characteristics of high performers. Investigate drivers of variation to replicate success factors."
            else:
                # Low variation - relatively homogeneous
                headline = f"{col_display} is relatively consistent across records"
                summary = f"Values cluster around {format_number(median_val)}, with limited variation"
                narrative = f"The {col_display} metric shows consistency across the dataset (CV: {cv:.0%}), with most values concentrated near {format_number(median_val)}. This suggests either: (1) a mature, stable process, or (2) limited differentiation opportunities. The tight distribution indicates predictability but may signal untapped potential for optimization."
                interpretation = f"Consistency can indicate stability, but may also reveal opportunities for strategic differentiation."
                action = f"Assess whether this consistency reflects optimal performance or missed opportunities. Consider targeted interventions to create positive outliers."

            insights.append({
                "headline": headline,
                "summary": summary,
                "title": f"{col_display} Distribution Pattern",
                "narrative": narrative,
                "chart_path": f"eda_charts/distribution_{col}.svg",
                "interpretation": interpretation,
                "action": action
            })
            count += 1
            if len(insights) >= 5:
                break

        # Insight 2b: Strong correlations (plain language)
        corr_data = synthesis.get("correlation_analysis", {})
        top_corrs = corr_data.get("top_correlations", [])
        if top_corrs and len(insights) < 5:
            # Get strongest correlation
            strongest = top_corrs[0]
            corr_val = strongest["correlation"]
            col1 = strongest["col1"]
            col2 = strongest["col2"]

            # Use beautified field names
            col1_display = FieldRegistry.beautify(col1)
            col2_display = FieldRegistry.beautify(col2)

            # Plain language translation
            if abs(corr_val) > 0.9:
                strength_desc = "nearly identical"
                narrative_strength = "almost perfectly aligned"
            elif abs(corr_val) > 0.7:
                strength_desc = "very closely"
                narrative_strength = "strongly connected"
            else:
                strength_desc = "somewhat"
                narrative_strength = "moderately related"

            direction_desc = "together" if corr_val > 0 else "in opposite directions"

            insights.append({
                "headline": f"{col1_display} and {col2_display} move {direction_desc}",
                "summary": f"These two metrics track {strength_desc} - when one changes, the other {'does too' if corr_val > 0 else 'moves the opposite way'}",
                "title": f"Key Relationship: {col1_display} ↔ {col2_display}",
                "narrative": f"We found that {col1_display} and {col2_display} are {narrative_strength}. When {col1_display} {'increases' if corr_val > 0 else 'decreases'}, {col2_display} {'typically increases' if corr_val > 0 else 'typically decreases'} as well. {f'In fact, they move so closely together that they essentially measure the same underlying phenomenon.' if abs(corr_val) > 0.9 else f'The relationship is strong enough to be predictive - knowing one tells you a lot about the other.' if abs(corr_val) > 0.7 else 'The relationship exists but leaves room for independent variation.'}",
                "chart_path": f"eda_charts/correlation_{col1}_{col2}.svg",
                "interpretation": f"{'These metrics are essentially measuring the same thing' if abs(corr_val) > 0.9 else 'These metrics capture overlapping information' if abs(corr_val) > 0.7 else 'These metrics share some common drivers'}.",
                "action": f"{'Pick one metric to focus on - using both adds complexity without adding insight' if abs(corr_val) > 0.9 else 'Consider whether you need both metrics, or if one captures most of the information' if abs(corr_val) > 0.7 else 'Investigate what drives both metrics - understanding the connection could reveal deeper insights'}"
            })

        # Insight 3: Missingness
        quality = synthesis.get("data_quality", {})
        missingness = quality.get("missingness", {})
        high_miss_cols = [col for col, pct in missingness.items() if pct > 10]
        if len(high_miss_cols) >= 3:
            insights.append({
                "headline": "Data completeness issues detected",
                "summary": f"{len(high_miss_cols)} columns have >10% missing data",
                "title": "Data Completeness Concerns",
                "narrative": f"{len(high_miss_cols)} columns have >10% missing data: {', '.join(high_miss_cols[:3])}, and others. This level of missingness can introduce bias in analysis and limit predictive accuracy. The pattern suggests data collection challenges or recent additions to the tracking system.",
                "chart_path": "eda_charts/missingness_heatmap.svg",
                "interpretation": "Data collection has gaps - either systematic issues or recent additions to tracking.",
                "action": "Either (1) drop high-missingness columns if not critical, (2) investigate why data is missing (systematic vs random), or (3) use imputation only if missing completely at random (MCAR)."
            })

        # Insight 4: Outliers
        outlier = synthesis.get("outlier_analysis", {})
        high_outlier_cols = [col for col, data in outlier.items() if data.get("percent", 0) > 10]
        if len(high_outlier_cols) >= 5:
            insights.append({
                "headline": "Widespread outlier activity",
                "summary": f"{len(high_outlier_cols)} columns show >10% outlier rates",
                "title": "Widespread Outlier Activity",
                "narrative": f"{len(high_outlier_cols)} columns show >10% outlier rates, indicating this dataset has frequent extreme events. This is common in financial time series (market shocks) or operational data (one-time events). Traditional statistical methods may be unreliable - robust methods are recommended.",
                "chart_path": None,
                "interpretation": "Extreme events are common in this dataset. Standard statistical assumptions may not hold.",
                "action": "Use robust statistical methods (median instead of mean, winsorization). Analyze outliers separately - they may contain the most valuable signal."
            })

        # Insight 5: Dimensionality
        col_rec = synthesis.get("column_recommendations", {})
        ignore_cols = col_rec.get("ignore", [])
        keep_cols = col_rec.get("keep", [])
        if len(ignore_cols) >= 10:
            insights.append({
                "headline": "Opportunity for dimensionality reduction",
                "summary": f"{len(ignore_cols)} columns provide minimal analytical value",
                "title": "Opportunity for Dimensionality Reduction",
                "narrative": f"{len(ignore_cols)} columns show little variation or are near-constant, providing minimal analytical value. Removing these will: (1) speed up analysis 3-5x, (2) reduce model overfitting risk, and (3) improve interpretability. Common culprits: ID columns, deprecated fields, or features with insufficient tracking history.",
                "chart_path": None,
                "interpretation": "High dimensionality creates noise and slows analysis.",
                "action": f"Drop {len(ignore_cols)} low-value columns before analysis. Focus modeling efforts on the {len(keep_cols)} high-signal columns identified."
            })

        return insights[:5]

    def _is_likely_id_column(self, col_name: str, stats: dict) -> bool:
        """
        Check if a column is likely an ID based on name and statistical properties.

        Args:
            col_name: Column name
            stats: Distribution statistics dict with min, max, mean, std

        Returns:
            True if column appears to be an ID
        """
        col_lower = col_name.lower()

        # Check for ID keywords in name
        id_keywords = ['id', 'key', 'index', 'uuid', 'guid', '_id', 'code', 'number']
        if any(kw in col_lower for kw in id_keywords):
            return True

        # Check if values are sequential or nearly sequential
        # (IDs often have min=1, max=N where N is close to row count)
        min_val = stats.get("min", 0)
        max_val = stats.get("max", 0)
        mean_val = stats.get("mean", 0)

        # If min is very small and max is very large with mean close to halfway,
        # it's likely a sequential ID (e.g., 1 to N)
        if min_val > 0 and max_val > 1000 and mean_val > 0:
            expected_mean_if_sequential = (min_val + max_val) / 2
            # If actual mean is within 10% of expected sequential mean, likely an ID
            if abs(mean_val - expected_mean_if_sequential) / expected_mean_if_sequential < 0.1:
                return True

        return False

    def _generate_quality_section(self, synthesis: dict, review: dict) -> list[str]:
        """Generate data quality summary table"""
        lines = []
        lines.append("## Data Quality Summary")
        lines.append("")

        overview = synthesis.get("dataset_overview", {})
        quality = synthesis.get("data_quality", {})
        col_rec = synthesis.get("column_recommendations", {})

        lines.append("| Metric | Value | Assessment |")
        lines.append("|--------|-------|------------|")
        lines.append(f"| Total Records | {format_number(overview.get('rows', 0), abbreviate=False)} | {'Small sample - statistical power limited' if overview.get('rows', 0) < 1000 else 'Adequate sample size'} |")
        lines.append(f"| Total Features | {overview.get('columns', 0)} | {'High dimensionality - reduce before modeling' if overview.get('columns', 0) > 50 else 'Reasonable feature count'} |")

        null_rate = quality.get("null_rate", 0) * 100
        lines.append(f"| Missing Data Rate | {format_percentage(null_rate / 100, precision=1)} | {'Low - excellent' if null_rate < 2 else 'Moderate - investigate patterns' if null_rate < 10 else 'High - significant concern'} |")

        dupes = quality.get("duplicates", 0)
        dupe_pct = dupes / max(overview.get('rows', 1), 1) * 100
        lines.append(f"| Duplicate Rows | {format_number(dupes, abbreviate=False)} ({format_percentage(dupe_pct / 100, precision=1)}) | {'Excellent - no duplicates detected' if dupes == 0 else 'Investigate duplicate sources'} |")

        ignore_count = len(col_rec.get("ignore", []))
        lines.append(f"| Constant Columns | {ignore_count} | {'Drop immediately - provide no signal' if ignore_count > 0 else 'None detected'} |")

        lines.append("")

        # Cleanup recommendations
        if ignore_count > 0 or null_rate > 5:
            lines.append("**Recommended Cleanup**:")
            if ignore_count > 0:
                lines.append(f"- Drop {ignore_count} constant columns (no variation)")
            missingness = quality.get("missingness", {})
            high_miss = [c for c, p in missingness.items() if p > 10]
            if high_miss:
                lines.append(f"- Investigate {len(high_miss)} columns with >10% missing data")
            if overview.get('columns', 0) > 50:
                lines.append(f"- Consider dimensionality reduction ({overview.get('columns', 0)} features is high for {overview.get('rows', 0)} rows)")
            lines.append("")

        lines.append("---")
        lines.append("")

        return lines

    def _generate_next_steps(self, synthesis: dict, bridge: dict) -> list[str]:
        """Generate recommended next steps"""
        lines = []
        lines.append("## Recommended Next Steps")
        lines.append("")

        lines.append("**1. Data Preparation**")
        col_rec = synthesis.get("column_recommendations", {})
        ignore_cols = col_rec.get("ignore", [])
        if ignore_cols:
            lines.append(f"- Remove {len(ignore_cols)} constant columns identified in analysis")

        quality = synthesis.get("data_quality", {})
        missingness = quality.get("missingness", {})
        if missingness:
            lines.append("- Handle missing data (drop, impute, or investigate root cause)")

        outlier = synthesis.get("outlier_analysis", {})
        if any(d.get("percent", 0) > 10 for d in outlier.values()):
            lines.append("- Consider winsorization for outlier-heavy columns")
        lines.append("")

        lines.append("**2. Analysis Approach**")
        dist_analysis = synthesis.get("distribution_analysis", {})
        has_skewed = any(abs(stats.get("skewness", 0)) > 1.0 for stats in dist_analysis.values())
        if has_skewed:
            lines.append("- Use robust statistical methods (median-based, resistant to outliers)")

        lines.append("- Consider time-series methods given temporal data structure")
        lines.append("- Ensemble methods (Random Forest, XGBoost) will handle non-normality well")
        lines.append("")

        lines.append("**3. Key Questions to Explore**")
        dom = synthesis.get("dominance_analysis", {})
        if dom.get("dominant_metric"):
            lines.append(f"- What makes the top-performing periods successful? Can we replicate those conditions?")

        if has_skewed:
            lines.append("- Is the asymmetry constant, or does risk profile change over time?")

        lines.append("- Which factors are most predictive of future performance?")
        lines.append("")

        return lines
