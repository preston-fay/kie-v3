"""
KIE Insight Engine

Extracts structured insights from data analysis and generates
presentation-ready content with evidence linkage.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from kie.insights.types import (
    Evidence,
    Insight,
    InsightCatalog,
    InsightCategory,
    InsightSeverity,
    InsightType,
)
from kie.insights.statistical import StatisticalAnalyzer

logger = logging.getLogger(__name__)


class InsightEngine:
    """
    Engine for extracting and structuring insights from data analysis.

    The engine takes analysis results (metrics, comparisons, trends) and
    transforms them into structured insights suitable for presentations.

    Usage:
        engine = InsightEngine()

        # Create insights manually
        insight = engine.create_comparison_insight(
            metric_name="Revenue",
            values={"North": 100, "South": 80, "East": 60}
        )

        # Or auto-extract from DataFrame
        insights = engine.auto_extract(df, value_col="revenue", group_col="region")

        # Build catalog
        catalog = engine.build_catalog(insights, "What drives revenue?")
    """

    def __init__(self, statistical_analyzer: Optional[StatisticalAnalyzer] = None):
        """
        Initialize engine.

        Args:
            statistical_analyzer: Optional analyzer instance
        """
        self._insight_counter = 0
        self.stats = statistical_analyzer or StatisticalAnalyzer()

    def _generate_id(self) -> str:
        """Generate unique insight ID."""
        self._insight_counter += 1
        return f"insight_{self._insight_counter:03d}"

    def create_insight(
        self,
        headline: str,
        supporting_text: str,
        insight_type: InsightType = InsightType.COMPARISON,
        severity: InsightSeverity = InsightSeverity.SUPPORTING,
        category: InsightCategory = InsightCategory.FINDING,
        evidence: Optional[List[Evidence]] = None,
        suggested_slide_type: str = "content",
        tags: Optional[List[str]] = None,
        confidence: float = 0.8,
        statistical_significance: Optional[float] = None,
    ) -> Insight:
        """
        Create a new insight with generated ID.

        Args:
            headline: Action title (insight as a statement)
            supporting_text: 2-3 sentence explanation
            insight_type: Type of insight
            severity: Importance level
            category: Narrative category
            evidence: List of supporting evidence
            suggested_slide_type: Recommended slide layout
            tags: Classification tags
            confidence: Confidence score 0-1
            statistical_significance: P-value if applicable

        Returns:
            New Insight object
        """
        return Insight(
            id=self._generate_id(),
            headline=headline,
            supporting_text=supporting_text,
            insight_type=insight_type,
            severity=severity,
            category=category,
            evidence=evidence or [],
            suggested_slide_type=suggested_slide_type,
            tags=tags or [],
            confidence=confidence,
            statistical_significance=statistical_significance,
        )

    def create_comparison_insight(
        self,
        metric_name: str,
        values: Dict[str, float],
        chart_path: Optional[str] = None,
    ) -> Insight:
        """
        Extract insight from a comparison of values.

        Args:
            metric_name: What's being compared (e.g., "Revenue")
            values: Dict of label -> value
            chart_path: Path to supporting chart if available

        Returns:
            Insight about the comparison
        """
        if not values:
            raise ValueError("Values dict cannot be empty")

        # Analyze the comparison
        total = sum(values.values())
        sorted_items = sorted(values.items(), key=lambda x: x[1], reverse=True)
        leader, leader_value = sorted_items[0]
        leader_share = (leader_value / total * 100) if total > 0 else 0

        # Generate headline
        headline = f"{leader} Leads {metric_name} at {leader_share:.0f}% Share"

        # Generate supporting text
        if len(sorted_items) > 1:
            runner_up, runner_up_value = sorted_items[1]
            gap = leader_value - runner_up_value
            gap_pct = (gap / runner_up_value * 100) if runner_up_value > 0 else 0
            supporting_text = (
                f"{leader} accounts for {leader_share:.0f}% of total {metric_name.lower()}, "
                f"outpacing {runner_up} by {gap:,.0f} ({gap_pct:.0f}%). "
            )
            if len(sorted_items) > 2:
                others = ", ".join([item[0] for item in sorted_items[2:4]])
                supporting_text += f"Other contributors include {others}."
        else:
            supporting_text = f"{leader} represents 100% of {metric_name.lower()}."

        # Build evidence
        evidence = [
            Evidence(
                evidence_type="metric",
                reference=f"{leader}_{metric_name}",
                value=leader_value,
                label=f"{leader} {metric_name}",
            ),
            Evidence(
                evidence_type="metric",
                reference=f"{leader}_share",
                value=f"{leader_share:.0f}%",
                label=f"{leader} share of total",
            ),
        ]

        if chart_path:
            evidence.insert(
                0,
                Evidence(
                    evidence_type="chart",
                    reference=chart_path,
                    value=None,
                    label=f"{metric_name} comparison chart",
                ),
            )

        return self.create_insight(
            headline=headline,
            supporting_text=supporting_text,
            insight_type=InsightType.COMPARISON,
            severity=InsightSeverity.KEY if leader_share > 40 else InsightSeverity.SUPPORTING,
            category=InsightCategory.FINDING,
            evidence=evidence,
            suggested_slide_type="chart" if chart_path else "content",
            tags=["comparison", metric_name.lower()],
        )

    def create_trend_insight(
        self,
        metric_name: str,
        periods: List[str],
        values: List[float],
        chart_path: Optional[str] = None,
    ) -> Insight:
        """
        Extract insight from a trend over time.

        Args:
            metric_name: What's trending (e.g., "Revenue")
            periods: Time period labels
            values: Values for each period
            chart_path: Path to supporting chart if available

        Returns:
            Insight about the trend
        """
        if len(periods) != len(values) or len(values) < 2:
            raise ValueError("Need at least 2 periods with matching values")

        # Use statistical analyzer for trend analysis
        trend = self.stats.analyze_trend(values, periods)

        # Generate headline based on trend
        pct_change = trend["pct_change"]
        if pct_change > 5:
            headline = f"{metric_name} Grows {abs(pct_change):.0f}% from {periods[0]} to {periods[-1]}"
        elif pct_change < -5:
            headline = f"{metric_name} Declines {abs(pct_change):.0f}% from {periods[0]} to {periods[-1]}"
        else:
            headline = f"{metric_name} Remains Stable Across {periods[0]}-{periods[-1]}"

        # Generate supporting text
        supporting_text = (
            f"{metric_name} moved from {trend['start_value']:,.0f} in {periods[0]} "
            f"to {trend['end_value']:,.0f} in {periods[-1]}. "
        )

        if trend["r_squared"] > 0.7:
            supporting_text += f"The trend is {trend['direction']} with high consistency (R²={trend['r_squared']:.2f})."
        elif trend["volatility"] > 15:
            supporting_text += f"Significant volatility observed (±{trend['volatility']:.0f}%)."

        # Build evidence
        evidence = [
            Evidence(
                evidence_type="metric",
                reference=f"{metric_name}_change",
                value=f"{pct_change:+.1f}%",
                label=f"{metric_name} change",
            ),
            Evidence(
                evidence_type="statistic",
                reference=f"{metric_name}_r_squared",
                value=f"{trend['r_squared']:.2f}",
                label="Trend fit (R²)",
            ),
        ]

        if chart_path:
            evidence.insert(
                0,
                Evidence(
                    evidence_type="chart",
                    reference=chart_path,
                    value=None,
                    label=f"{metric_name} trend chart",
                ),
            )

        return self.create_insight(
            headline=headline,
            supporting_text=supporting_text,
            insight_type=InsightType.TREND,
            severity=InsightSeverity.KEY if abs(pct_change) > 15 else InsightSeverity.SUPPORTING,
            category=InsightCategory.FINDING,
            evidence=evidence,
            suggested_slide_type="chart" if chart_path else "content",
            tags=["trend", metric_name.lower()],
            confidence=min(0.95, 0.5 + trend["r_squared"] * 0.5),
        )

    def create_outlier_insight(
        self,
        metric_name: str,
        series: pd.Series,
        labels: Optional[pd.Series] = None,
    ) -> Optional[Insight]:
        """
        Extract insight about outliers in data.

        Args:
            metric_name: What's being analyzed
            series: Numeric series
            labels: Optional labels for the values

        Returns:
            Insight about outliers, or None if no significant outliers
        """
        outliers = self.stats.detect_outliers(series)

        if outliers["total_outliers"] == 0:
            return None

        n_outliers = outliers["total_outliers"]
        pct = outliers["outlier_percentage"]

        # Get outlier labels if available
        if labels is not None and len(outliers["outlier_indices"]) > 0:
            outlier_labels = labels.iloc[outliers["outlier_indices"]].tolist()[:3]
            examples = ", ".join(str(l) for l in outlier_labels)
        else:
            examples = ", ".join(f"{v:,.0f}" for v in outliers["outlier_values"][:3])

        headline = f"{n_outliers} Outliers Identified in {metric_name} ({pct:.1f}% of Data)"

        supporting_text = (
            f"{n_outliers} values fall outside normal range "
            f"({outliers['lower_bound']:,.0f} to {outliers['upper_bound']:,.0f}). "
            f"Notable examples: {examples}."
        )

        evidence = [
            Evidence(
                evidence_type="statistic",
                reference=f"{metric_name}_outliers",
                value=n_outliers,
                label="Outlier count",
            ),
            Evidence(
                evidence_type="metric",
                reference=f"{metric_name}_bounds",
                value=f"{outliers['lower_bound']:,.0f} - {outliers['upper_bound']:,.0f}",
                label="Normal range",
            ),
        ]

        return self.create_insight(
            headline=headline,
            supporting_text=supporting_text,
            insight_type=InsightType.OUTLIER,
            severity=InsightSeverity.KEY if pct > 5 else InsightSeverity.SUPPORTING,
            category=InsightCategory.FINDING,
            evidence=evidence,
            suggested_slide_type="content",
            tags=["outlier", metric_name.lower()],
        )

    def create_concentration_insight(
        self,
        dimension: str,
        top_item: str,
        top_share: float,
        total_items: int,
        chart_path: Optional[str] = None,
    ) -> Insight:
        """
        Extract insight about concentration risk.

        Args:
            dimension: What's concentrated (e.g., "Revenue by Product")
            top_item: The dominant item
            top_share: Share of top item (0-100)
            total_items: Total number of items
            chart_path: Path to supporting chart

        Returns:
            Insight about concentration
        """
        # Determine risk level
        if top_share > 70:
            risk_level = "High"
            severity = InsightSeverity.KEY
        elif top_share > 50:
            risk_level = "Moderate"
            severity = InsightSeverity.KEY
        else:
            risk_level = "Low"
            severity = InsightSeverity.SUPPORTING

        headline = f"{top_item} Concentration Creates {risk_level} Dependency Risk"

        supporting_text = (
            f"{top_share:.0f}% of {dimension.lower()} depends on {top_item}, "
            f"with {total_items - 1} alternatives available. "
        )

        if top_share > 50:
            supporting_text += "Consider diversification to reduce single-source risk."

        evidence = [
            Evidence(
                evidence_type="metric",
                reference=f"{top_item}_concentration",
                value=f"{top_share:.0f}%",
                label=f"{top_item} share",
            ),
            Evidence(
                evidence_type="metric",
                reference="alternative_count",
                value=total_items - 1,
                label="Alternatives",
            ),
        ]

        if chart_path:
            evidence.insert(
                0,
                Evidence(
                    evidence_type="chart",
                    reference=chart_path,
                    value=None,
                    label="Concentration chart",
                ),
            )

        return self.create_insight(
            headline=headline,
            supporting_text=supporting_text,
            insight_type=InsightType.CONCENTRATION,
            severity=severity,
            category=InsightCategory.IMPLICATION,
            evidence=evidence,
            suggested_slide_type="chart" if chart_path else "content",
            tags=["concentration", "risk", dimension.lower()],
        )

    def create_correlation_insight(
        self,
        var1_name: str,
        var2_name: str,
        var1: pd.Series,
        var2: pd.Series,
    ) -> Optional[Insight]:
        """
        Extract insight about correlation between variables.

        Args:
            var1_name: Name of first variable
            var2_name: Name of second variable
            var1: First variable series
            var2: Second variable series

        Returns:
            Insight about correlation, or None if negligible
        """
        corr = self.stats.analyze_correlation(var1, var2)

        if corr.get("error") or corr["strength"] == "negligible":
            return None

        correlation = corr["correlation"]
        strength = corr["strength"]
        direction = corr["direction"]

        headline = f"{strength.title()} {direction.title()} Correlation Between {var1_name} and {var2_name}"

        supporting_text = (
            f"{var1_name} and {var2_name} show a {strength} {direction} correlation "
            f"(r = {correlation:.2f}). "
        )

        if direction == "positive":
            supporting_text += f"As {var1_name} increases, {var2_name} tends to increase."
        else:
            supporting_text += f"As {var1_name} increases, {var2_name} tends to decrease."

        evidence = [
            Evidence(
                evidence_type="statistic",
                reference="correlation_coefficient",
                value=f"{correlation:.3f}",
                label="Correlation (r)",
            ),
            Evidence(
                evidence_type="metric",
                reference="n_observations",
                value=corr["n_observations"],
                label="Sample size",
            ),
        ]

        return self.create_insight(
            headline=headline,
            supporting_text=supporting_text,
            insight_type=InsightType.CORRELATION,
            severity=InsightSeverity.KEY if abs(correlation) > 0.6 else InsightSeverity.SUPPORTING,
            category=InsightCategory.FINDING,
            evidence=evidence,
            suggested_slide_type="content",
            tags=["correlation", var1_name.lower(), var2_name.lower()],
            confidence=min(0.95, 0.5 + abs(correlation) * 0.5),
        )

    def create_recommendation(
        self,
        action: str,
        rationale: str,
        expected_impact: str,
        supporting_insights: Optional[List[str]] = None,
        priority: str = "medium",
    ) -> Insight:
        """
        Create a recommendation insight.

        Args:
            action: What should be done
            rationale: Why it should be done
            expected_impact: Expected outcome
            supporting_insights: IDs of supporting insights
            priority: "high", "medium", or "low"

        Returns:
            Recommendation insight
        """
        headline = action

        supporting_text = f"{rationale} {expected_impact}"

        evidence = []
        if supporting_insights:
            evidence.append(
                Evidence(
                    evidence_type="insight_reference",
                    reference=",".join(supporting_insights),
                    value=None,
                    label="Supporting findings",
                )
            )

        return self.create_insight(
            headline=headline,
            supporting_text=supporting_text,
            insight_type=InsightType.COMPARISON,  # Recommendations don't have specific type
            severity=InsightSeverity.KEY if priority == "high" else InsightSeverity.SUPPORTING,
            category=InsightCategory.RECOMMENDATION,
            evidence=evidence,
            suggested_slide_type="content",
            tags=["recommendation", priority],
            confidence=0.7,
        )

    def auto_extract(
        self,
        df: pd.DataFrame,
        value_column: str,
        group_column: Optional[str] = None,
        time_column: Optional[str] = None,
        label_column: Optional[str] = None,
    ) -> List[Insight]:
        """
        Automatically extract insights from a DataFrame.

        Args:
            df: DataFrame to analyze
            value_column: Column with numeric values
            group_column: Optional column for grouping
            time_column: Optional column for time series
            label_column: Optional column for labels

        Returns:
            List of extracted insights
        """
        insights = []

        # Basic statistics insight
        stats = self.stats.describe(df[value_column])
        if "error" not in stats:
            # Distribution insight
            dist = self.stats.analyze_distribution(df[value_column])
            if "error" not in dist and dist.get("is_concentrated"):
                insights.append(
                    self.create_insight(
                        headline=f"{value_column} is Highly Concentrated",
                        supporting_text=(
                            f"Top 3 bins contain {dist['top_3_bins_pct']:.0f}% of values. "
                            f"Mean: {stats['mean']:,.0f}, Median: {stats['median']:,.0f}."
                        ),
                        insight_type=InsightType.DISTRIBUTION,
                        tags=["distribution", value_column.lower()],
                    )
                )

        # Group comparison
        if group_column:
            comparison = self.stats.compare_groups(df, value_column, group_column)
            if "error" not in comparison:
                values_dict = {
                    name: stats["sum"] for name, stats in comparison["groups"].items()
                }
                insights.append(self.create_comparison_insight(value_column, values_dict))

                # Concentration insight if warranted
                if comparison["is_concentrated"]:
                    insights.append(
                        self.create_concentration_insight(
                            dimension=f"{value_column} by {group_column}",
                            top_item=comparison["leader"],
                            top_share=comparison["leader_share"],
                            total_items=comparison["n_groups"],
                        )
                    )

        # Trend analysis
        if time_column:
            sorted_df = df.sort_values(time_column)
            periods = sorted_df[time_column].astype(str).tolist()
            values = sorted_df[value_column].tolist()

            if len(values) >= 3:
                insights.append(
                    self.create_trend_insight(value_column, periods, values)
                )

        # Outlier detection
        labels = df[label_column] if label_column else None
        outlier_insight = self.create_outlier_insight(value_column, df[value_column], labels)
        if outlier_insight:
            insights.append(outlier_insight)

        return insights

    def build_catalog(
        self,
        insights: List[Insight],
        business_question: str,
        data_summary: Optional[Dict[str, Any]] = None,
    ) -> InsightCatalog:
        """
        Build an insight catalog with narrative structure.

        Args:
            insights: List of insights to include
            business_question: The question being answered
            data_summary: Optional summary of source data

        Returns:
            InsightCatalog with narrative arc
        """
        # Organize by category
        findings = [i for i in insights if i.category == InsightCategory.FINDING]
        implications = [i for i in insights if i.category == InsightCategory.IMPLICATION]
        recommendations = [i for i in insights if i.category == InsightCategory.RECOMMENDATION]

        # Sort within categories by severity
        severity_order = {
            InsightSeverity.KEY: 0,
            InsightSeverity.SUPPORTING: 1,
            InsightSeverity.CONTEXT: 2,
        }
        findings.sort(key=lambda x: severity_order.get(x.severity, 1))
        implications.sort(key=lambda x: severity_order.get(x.severity, 1))
        recommendations.sort(key=lambda x: severity_order.get(x.severity, 1))

        # Build narrative arc
        narrative_arc = {
            "opening": f"Analysis addressing: {business_question}",
            "key_findings": [i.id for i in findings if i.severity == InsightSeverity.KEY],
            "supporting_findings": [i.id for i in findings if i.severity != InsightSeverity.KEY],
            "implications": [i.id for i in implications],
            "recommendations": [i.id for i in recommendations],
            "structure": ["findings", "implications", "recommendations"],
        }

        return InsightCatalog(
            generated_at=datetime.now().isoformat(),
            business_question=business_question,
            insights=insights,
            narrative_arc=narrative_arc,
            data_summary=data_summary or {},
        )

    def rank_insights(self, insights: List[Insight]) -> List[Insight]:
        """
        Rank insights by importance.

        Considers: severity, category, confidence, statistical significance
        """

        def score(insight: Insight) -> float:
            severity_scores = {
                InsightSeverity.KEY: 3,
                InsightSeverity.SUPPORTING: 2,
                InsightSeverity.CONTEXT: 1,
            }
            category_scores = {
                InsightCategory.FINDING: 1.2,
                InsightCategory.IMPLICATION: 1.1,
                InsightCategory.RECOMMENDATION: 1.0,
            }

            base = severity_scores.get(insight.severity, 1)
            multiplier = category_scores.get(insight.category, 1.0)
            confidence = insight.confidence

            # Bonus for statistical significance
            sig_bonus = 1.1 if insight.is_statistically_significant else 1.0

            return base * multiplier * confidence * sig_bonus

        return sorted(insights, key=score, reverse=True)

    def to_slide_sequence(self, catalog: InsightCatalog) -> List[Dict[str, Any]]:
        """
        Convert insight catalog to slide specifications.

        Returns list of slide specs suitable for Presentation.
        """
        slides = []
        arc = catalog.narrative_arc

        # Key findings section
        key_findings = arc.get("key_findings", [])
        if key_findings:
            slides.append(
                {
                    "type": "section",
                    "title": "Key Findings",
                    "section_number": 1,
                }
            )
            for insight_id in key_findings:
                insight = next((i for i in catalog.insights if i.id == insight_id), None)
                if insight:
                    slides.append(self._insight_to_slide_spec(insight))

        # Supporting findings
        supporting = arc.get("supporting_findings", [])
        if supporting:
            slides.append(
                {
                    "type": "section",
                    "title": "Supporting Analysis",
                    "section_number": 2,
                }
            )
            for insight_id in supporting[:3]:  # Limit to top 3
                insight = next((i for i in catalog.insights if i.id == insight_id), None)
                if insight:
                    slides.append(self._insight_to_slide_spec(insight))

        # Implications
        implications = arc.get("implications", [])
        if implications:
            slides.append(
                {
                    "type": "section",
                    "title": "Implications",
                    "section_number": 3,
                }
            )
            for insight_id in implications:
                insight = next((i for i in catalog.insights if i.id == insight_id), None)
                if insight:
                    slides.append(self._insight_to_slide_spec(insight))

        # Recommendations
        recommendations = arc.get("recommendations", [])
        if recommendations:
            slides.append(
                {
                    "type": "section",
                    "title": "Recommendations",
                    "section_number": 4,
                }
            )
            for insight_id in recommendations:
                insight = next((i for i in catalog.insights if i.id == insight_id), None)
                if insight:
                    slides.append(self._insight_to_slide_spec(insight))

        return slides

    def _insight_to_slide_spec(self, insight: Insight) -> Dict[str, Any]:
        """Convert single insight to slide spec."""
        # Find chart evidence if any
        chart_evidence = next(
            (e for e in insight.evidence if e.evidence_type == "chart"), None
        )

        if chart_evidence:
            return {
                "type": "chart",
                "title": insight.headline,
                "chart_path": chart_evidence.reference,
                "caption": insight.supporting_text[:200],
            }
        else:
            return {
                "type": "content",
                "title": insight.headline,
                "bullets": [insight.supporting_text],
            }
