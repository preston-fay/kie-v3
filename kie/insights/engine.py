"""
KIE Insight Engine

Extracts structured insights from data analysis and generates
presentation-ready content with evidence linkage.
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd

from kie.insights.schema import (
    Evidence,
    Insight,
    InsightCatalog,
    InsightCategory,
    InsightSeverity,
    InsightType,
)
from kie.insights.statistical import StatisticalAnalyzer
from kie.insights.intelligence import InsightIntelligenceEngine
from kie.formatting.field_registry import FieldRegistry
from kie.charts.formatting import format_number, format_currency, format_percentage, format_change

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

    def __init__(
        self,
        statistical_analyzer: StatisticalAnalyzer | None = None,
        intelligence_engine: InsightIntelligenceEngine | None = None
    ):
        """
        Initialize engine.

        Args:
            statistical_analyzer: Optional analyzer instance
            intelligence_engine: Optional intelligence engine for enrichment
        """
        self._insight_counter = 0
        self.stats = statistical_analyzer or StatisticalAnalyzer()
        self.intelligence = intelligence_engine or InsightIntelligenceEngine()
        self.rejection_log: list[dict[str, Any]] = []  # Track rejected insights with explanations

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
        evidence: list[Evidence] | None = None,
        suggested_slide_type: str = "content",
        tags: list[str] | None = None,
        confidence: float = 0.8,
        statistical_significance: float | None = None,
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

    def _validate_insight_data(self, insight_type: str, data: dict) -> bool:
        """Validate insight data before creating insight.

        This prevents mathematically impossible or nonsensical insights
        from reaching the output.

        Args:
            insight_type: Type of insight (comparison, concentration, outlier, etc.)
            data: Dict with insight-specific data to validate

        Returns:
            True if data is valid, False otherwise
        """
        if insight_type == "comparison":
            # Check for "0% of total" impossibility
            leader_share = data.get("leader_share", 0)
            if leader_share <= 0:
                logger.warning(f"Invalid comparison: leader share {leader_share}% <= 0")
                return False
            if leader_share > 100:
                logger.warning(f"Invalid comparison: leader share {leader_share}% > 100")
                return False

        elif insight_type == "concentration":
            top_n_share = data.get("top_n_share", 0)
            if top_n_share <= 0 or top_n_share > 100:
                logger.warning(f"Invalid concentration: {top_n_share}% out of valid range")
                return False

        elif insight_type == "outlier":
            count = data.get("outlier_count", 0)
            total = data.get("total_count", 1)
            if count > total * 0.3:  # More than 30% outliers is suspicious
                logger.warning(f"Suspicious outlier count: {count}/{total} ({format_percentage(count/total, precision=1)})")
                return False
            if count < 0 or total < 1:
                logger.warning(f"Invalid outlier data: count={count}, total={total}")
                return False

        elif insight_type == "correlation":
            corr = data.get("correlation", 0)
            if abs(corr) > 1.0:  # Correlation must be -1 to 1
                logger.warning(f"Invalid correlation: {corr} (must be -1 to 1)")
                return False

        return True

    def create_comparison_insight(
        self,
        metric_name: str,
        values: dict[str, float],
        chart_path: str | None = None,
    ) -> Insight | None:
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

        # Beautify metric name for client-facing output
        display_metric = FieldRegistry.beautify(metric_name)

        # Analyze the comparison
        total = sum(values.values())
        sorted_items = sorted(values.items(), key=lambda x: x[1], reverse=True)
        leader, leader_value = sorted_items[0]
        leader_share = (leader_value / total * 100) if total > 0 else 0

        # VALIDATE before creating insight
        if not self._validate_insight_data("comparison", {
            "leader_share": leader_share,
            "leader_value": leader_value
        }):
            # Return None instead of creating invalid insight
            logger.info(f"Skipping invalid comparison insight for {metric_name}")
            return None

        # Smart format the leader value
        formatted_value = format_number(leader_value)

        # Generate headline
        headline = f"{leader} Leads {display_metric} at {format_percentage(leader_share / 100)} Share"

        # Generate supporting text
        if len(sorted_items) > 1:
            runner_up, runner_up_value = sorted_items[1]
            gap = leader_value - runner_up_value
            gap_pct = (gap / runner_up_value * 100) if runner_up_value > 0 else 0
            supporting_text = (
                f"{leader} accounts for {format_percentage(leader_share / 100)} of total {display_metric.lower()}, "
                f"outpacing {runner_up} by {format_number(gap)} ({format_percentage(gap_pct / 100)}). "
            )
            if len(sorted_items) > 2:
                others = ", ".join([item[0] for item in sorted_items[2:4]])
                supporting_text += f"Other contributors include {others}."
        else:
            supporting_text = f"{leader} represents 100% of {display_metric.lower()}."

        # Build evidence
        evidence = [
            Evidence(
                evidence_type="metric",
                reference=f"{leader}_{metric_name}",
                value=formatted_value,
                label=f"{leader} {display_metric}",
            ),
            Evidence(
                evidence_type="metric",
                reference=f"{leader}_share",
                value=format_percentage(leader_share / 100),
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
                    label=f"{display_metric} comparison chart",
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
        periods: list,  # Accept any type - will be formatted appropriately
        values: list[float],
        chart_path: str | None = None,
    ) -> Insight:
        """
        Extract insight from a trend over time.

        Args:
            metric_name: What's trending (e.g., "Revenue")
            periods: Time period labels (datetime, str, int, etc.)
            values: Values for each period
            chart_path: Path to supporting chart if available

        Returns:
            Insight about the trend
        """
        if len(periods) != len(values) or len(values) < 2:
            raise ValueError("Need at least 2 periods with matching values")

        # Beautify metric name for client-facing output
        display_metric = FieldRegistry.beautify(metric_name)

        # Format periods for display (handle datetime, numeric, string)
        def format_period(p) -> str:
            if pd.isna(p):
                return "Unknown"
            elif hasattr(p, 'strftime'):  # datetime-like
                return p.strftime("%Y-%m-%d")
            elif isinstance(p, (int, float)):
                # Check if this looks like a year (1900-2100)
                if 1900 <= p <= 2100:
                    return str(int(p))
                # Otherwise format as number
                return format_number(p)
            else:
                return str(p)

        period_start = format_period(periods[0])
        period_end = format_period(periods[-1])

        # Use statistical analyzer for trend analysis
        trend = self.stats.analyze_trend(values, periods)

        # Check for error from validation OR special cases (no pct_change)
        if "error" in trend or "pct_change" not in trend:
            # Trend analysis rejected this data OR it's a special case (near-zero start value)
            if "error" in trend:
                rejection_reason = trend.get("reason", "unknown")
            else:
                # Special case: near-zero start value, only has absolute_change
                rejection_reason = trend.get("note", "Cannot calculate percentage change from near-zero starting value")

            logger.warning(f"Trend analysis rejected for {metric_name}: {rejection_reason}")

            # Generate consultant-grade explanation for rejection
            explanation = self.intelligence.explain_rejection(
                rejection_reason=rejection_reason,
                metric_name=metric_name,
                data_context={
                    "start_value": trend.get("start_value", 0),
                    "end_value": trend.get("end_value", 0),
                    "pct_change": trend.get("pct_change", 0),
                    "absolute_change": trend.get("absolute_change", 0)
                }
            )

            # Log rejection with explanation for reporting
            self.rejection_log.append({
                "metric": metric_name,
                "insight_type": "trend",
                "rejection_reason": rejection_reason,
                "explanation": explanation["explanation"],
                "next_steps": explanation["next_steps"]
            })

            return None

        # Generate headline based on trend
        # NOTE: pct_change from statistical.py is already in percentage form (e.g., -442.5 means -442.5%)
        pct_change = trend["pct_change"]
        if pct_change > 5:
            headline = f"{display_metric} Grows {format_percentage(abs(pct_change))} from {period_start} to {period_end}"
        elif pct_change < -5:
            headline = f"{display_metric} Declines {format_percentage(abs(pct_change))} from {period_start} to {period_end}"
        else:
            headline = f"{display_metric} Remains Stable Across {period_start}-{period_end}"

        # Generate supporting text with smart formatting
        start_formatted = format_number(trend['start_value'])
        end_formatted = format_number(trend['end_value'])

        supporting_text = (
            f"{display_metric} moved from {start_formatted} in {period_start} "
            f"to {end_formatted} in {period_end}. "
        )

        if trend["r_squared"] > 0.7:
            supporting_text += f"The trend is {trend['direction']} with high consistency (R²={format_number(trend['r_squared'], precision=2, abbreviate=False)})."
        elif trend["volatility"] > 15:
            supporting_text += f"Significant volatility observed (±{format_percentage(trend['volatility'] / 100)})."

        # Build evidence
        # NOTE: pct_change is already in percentage form from statistical.py (e.g., -442.5 means -442.5%)
        # format_change with as_percentage=False will just add +/- sign, then we append % manually
        evidence = [
            Evidence(
                evidence_type="metric",
                reference=f"{metric_name}_change",
                value=f"{format_change(pct_change, as_percentage=False)}%",  # Add % suffix manually
                label=f"{display_metric} change",
            ),
            Evidence(
                evidence_type="statistic",
                reference=f"{metric_name}_r_squared",
                value=trend['r_squared'],  # Keep as float for smart formatting later
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
                    label=f"{display_metric} trend chart",
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
        labels: pd.Series | None = None,
    ) -> Insight | None:
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

        # VALIDATE before creating insight
        if not self._validate_insight_data("outlier", {
            "outlier_count": n_outliers,
            "total_count": len(series)
        }):
            logger.info(f"Skipping invalid outlier insight for {metric_name}")
            return None

        # Beautify metric name for client-facing output
        display_metric = FieldRegistry.beautify(metric_name)

        # Get outlier labels if available
        if labels is not None and len(outliers["outlier_indices"]) > 0:
            outlier_labels = labels.iloc[outliers["outlier_indices"]].tolist()[:3]
            examples = ", ".join(str(label) for label in outlier_labels)
        else:
            examples = ", ".join(format_number(v) for v in outliers["outlier_values"][:3])

        headline = f"{n_outliers} Outliers Identified in {display_metric} ({format_percentage(pct / 100, precision=1)} of Data)"

        supporting_text = (
            f"{n_outliers} values fall outside normal range "
            f"({format_number(outliers['lower_bound'])} to {format_number(outliers['upper_bound'])}). "
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
                value=f"{format_number(outliers['lower_bound'])} - {format_number(outliers['upper_bound'])}",
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
        chart_path: str | None = None,
    ) -> Insight | None:
        """
        Extract insight about concentration risk.

        Args:
            dimension: What's concentrated (e.g., "Revenue by Product")
            top_item: The dominant item
            top_share: Share of top item (0-100)
            total_items: Total number of items
            chart_path: Path to supporting chart

        Returns:
            Insight about concentration, or None if validation fails
        """
        # VALIDATE before creating insight
        if not self._validate_insight_data("concentration", {
            "top_n_share": top_share
        }):
            logger.info(f"Skipping invalid concentration insight for {dimension}")
            return None

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
            f"{format_percentage(top_share / 100, precision=0)} of {dimension.lower()} depends on {top_item}, "
            f"with {total_items - 1} alternatives available. "
        )

        if top_share > 50:
            supporting_text += "Consider diversification to reduce single-source risk."

        evidence = [
            Evidence(
                evidence_type="metric",
                reference=f"{top_item}_concentration",
                value=format_percentage(top_share / 100, precision=0),
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
    ) -> Insight | None:
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

        # VALIDATE before creating insight
        if not self._validate_insight_data("correlation", {
            "correlation": correlation
        }):
            logger.info(f"Skipping invalid correlation insight for {var1_name} vs {var2_name}")
            return None
        strength = corr["strength"]
        direction = corr["direction"]

        headline = f"{strength.title()} {direction.title()} Correlation Between {var1_name} and {var2_name}"

        supporting_text = (
            f"{var1_name} and {var2_name} show a {strength} {direction} correlation "
            f"(r = {format_number(correlation, precision=2, abbreviate=False)}). "
        )

        if direction == "positive":
            supporting_text += f"As {var1_name} increases, {var2_name} tends to increase."
        else:
            supporting_text += f"As {var1_name} increases, {var2_name} tends to decrease."

        evidence = [
            Evidence(
                evidence_type="statistic",
                reference="correlation_coefficient",
                value=format_number(correlation, precision=3, abbreviate=False),
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
        supporting_insights: list[str] | None = None,
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
        group_column: str | None = None,
        time_column: str | None = None,
        label_column: str | None = None,
    ) -> list[Insight]:
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
                # Beautify field name for client-facing output
                display_column = FieldRegistry.beautify(value_column)

                insights.append(
                    self.create_insight(
                        headline=f"{display_column} is Highly Concentrated",
                        supporting_text=(
                            f"Top 3 bins contain {format_percentage(dist['top_3_bins_pct'] / 100, precision=0)} of values. "
                            f"Mean: {format_number(stats['mean'])}, Median: {format_number(stats['median'])}."
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
                    # Beautify dimension for client-friendly output
                    value_display = FieldRegistry.beautify(value_column)
                    group_display = FieldRegistry.beautify(group_column)
                    insights.append(
                        self.create_concentration_insight(
                            dimension=f"{value_display} by {group_display}",
                            top_item=comparison["leader"],
                            top_share=comparison["leader_share"],
                            total_items=comparison["n_groups"],
                        )
                    )

        # Trend analysis
        if time_column:
            sorted_df = df.sort_values(time_column)
            # Keep periods as their native type (datetime, int, etc.) for proper formatting
            periods = sorted_df[time_column].tolist()
            values = sorted_df[value_column].tolist()

            if len(values) >= 3:
                trend_insight = self.create_trend_insight(value_column, periods, values)
                if trend_insight:  # Only add if validation passed
                    insights.append(trend_insight)

        # Outlier detection
        labels = df[label_column] if label_column else None
        outlier_insight = self.create_outlier_insight(value_column, df[value_column], labels)
        if outlier_insight:
            insights.append(outlier_insight)

        return insights

    def auto_extract_comprehensive(
        self,
        df: pd.DataFrame,
        value_column: str,
        group_column: str | None = None,
        time_column: str | None = None,
        label_column: str | None = None,
        max_insights: int = 20,
        objective: str | None = None,
    ) -> list[Insight]:
        """
        Comprehensive insight extraction for rich datasets.

        Extracts 15-20+ insights by analyzing:
        - Multiple numeric columns (not just the primary value column)
        - Cross-column correlations
        - Multiple time periods and trends
        - Geographic patterns (if applicable)
        - Distribution patterns across columns

        Args:
            df: DataFrame to analyze
            value_column: Primary column with numeric values
            group_column: Optional column for grouping
            time_column: Optional column for time series
            label_column: Optional column for labels
            max_insights: Maximum number of insights to extract (default: 20)

        Returns:
            List of extracted insights (15-20+ for rich datasets)
        """
        insights = []

        # Start with basic insights from primary column
        basic_insights = self.auto_extract(
            df, value_column, group_column, time_column, label_column
        )
        insights.extend(basic_insights)

        # Get all numeric columns for additional analysis
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

        # Analyze additional numeric columns (beyond primary value_column)
        additional_cols = [col for col in numeric_cols if col != value_column][:4]

        for col in additional_cols:
            # Distribution insight for each additional column
            stats = self.stats.describe(df[col])
            if "error" not in stats:
                dist = self.stats.analyze_distribution(df[col])
                if "error" not in dist:
                    # Check for interesting patterns
                    display_col = FieldRegistry.beautify(col)
                    if dist.get("is_concentrated"):
                        insights.append(
                            self.create_insight(
                                headline=f"{display_col} Shows Concentrated Distribution",
                                supporting_text=(
                                    f"Top 3 bins contain {format_percentage(dist['top_3_bins_pct'] / 100)} of values. "
                                    f"Mean: {format_number(stats['mean'])}, Median: {format_number(stats['median'])}."
                                ),
                                insight_type=InsightType.DISTRIBUTION,
                                severity=InsightSeverity.SUPPORTING,
                                tags=["distribution", col.lower()],
                            )
                        )

                    # High variance insight
                    if stats.get('std', 0) > stats.get('mean', 1):
                        insights.append(
                            self.create_insight(
                                headline=f"{display_col} Exhibits High Variability",
                                supporting_text=(
                                    f"{display_col} has high volatility with standard deviation "
                                    f"({format_number(stats['std'])}) exceeding mean ({format_number(stats['mean'])}). "
                                    f"Range: {format_number(stats['min'])} to {format_number(stats['max'])}."
                                ),
                                insight_type=InsightType.DISTRIBUTION,
                                severity=InsightSeverity.SUPPORTING,
                                tags=["volatility", col.lower()],
                            )
                        )

            # Group comparison for additional columns
            if group_column and col in df.columns:
                comparison = self.stats.compare_groups(df, col, group_column)
                if "error" not in comparison and comparison.get("n_groups", 0) > 1:
                    values_dict = {
                        name: stats["sum"] for name, stats in comparison["groups"].items()
                    }
                    insights.append(self.create_comparison_insight(col, values_dict))

            # Time trend for additional columns
            if time_column and col in df.columns and len(df) >= 3:
                try:
                    sorted_df = df.sort_values(time_column)
                    # Keep periods as their native type for proper formatting
                    periods = sorted_df[time_column].tolist()
                    values = sorted_df[col].tolist()

                    if len(values) >= 3 and not all(pd.isna(v) for v in values):
                        trend_insight = self.create_trend_insight(col, periods, values)
                        if trend_insight:  # Only add if validation passed
                            insights.append(trend_insight)
                except Exception:
                    pass  # Skip if conversion fails

        # Cross-column correlations (find related metrics)
        if len(numeric_cols) >= 2:
            try:
                corr_matrix = df[numeric_cols].corr()

                # If objective contains relationship keywords, prioritize those columns
                objective_keywords = []
                if objective:
                    objective_lower = objective.lower()
                    # Extract meaningful keywords from objective
                    import re
                    words = re.findall(r'\b[a-z_]+\b', objective_lower)
                    # Filter stop words
                    stop_words = {'the', 'and', 'or', 'between', 'relationship', 'correlation', 'of', 'in', 'to', 'a', 'an'}
                    objective_keywords = [w for w in words if w not in stop_words and len(w) > 2]

                # Find columns matching objective keywords
                priority_cols = []
                if objective_keywords:
                    for col in numeric_cols:
                        col_lower = col.lower()
                        if any(keyword in col_lower for keyword in objective_keywords):
                            priority_cols.append(col)

                # If we have priority columns, focus correlations there
                if priority_cols:
                    cols_to_check = priority_cols[:6]  # Check up to 6 objective-relevant columns
                else:
                    cols_to_check = numeric_cols[:6]  # Fall back to first 6 columns

                # Find strong correlations among priority columns
                for i, col1 in enumerate(cols_to_check):
                    for col2 in cols_to_check[i+1:]:
                        if col1 in corr_matrix.columns and col2 in corr_matrix.columns:
                            if col1 in df.columns and col2 in df.columns:
                                corr_value = corr_matrix.loc[col1, col2]

                                if abs(corr_value) > 0.7 and not pd.isna(corr_value):
                                    # Use existing create_correlation_insight method
                                    display_col1 = FieldRegistry.beautify(col1)
                                    display_col2 = FieldRegistry.beautify(col2)

                                    corr_insight = self.create_correlation_insight(
                                        var1_name=display_col1,
                                        var2_name=display_col2,
                                        var1=df[col1],
                                        var2=df[col2]
                                    )
                                    if corr_insight:
                                        insights.append(corr_insight)
            except Exception:
                pass  # Skip correlation analysis if it fails

        # Time-based patterns (if time column exists)
        if time_column and len(df) >= 10:
            try:
                # Recent vs historical comparison
                sorted_df = df.sort_values(time_column)
                mid_point = len(sorted_df) // 2

                recent_mean = sorted_df[value_column].iloc[mid_point:].mean()
                historical_mean = sorted_df[value_column].iloc[:mid_point].mean()

                if not pd.isna(recent_mean) and not pd.isna(historical_mean) and historical_mean != 0:
                    change_pct = ((recent_mean - historical_mean) / abs(historical_mean)) * 100

                    if abs(change_pct) > 10:
                        direction = "increased" if change_pct > 0 else "decreased"
                        display_value_col = FieldRegistry.beautify(value_column)
                        insights.append(
                            self.create_insight(
                                headline=f"{display_value_col} {direction.title()} in Recent Period",
                                supporting_text=(
                                    f"Recent average ({format_number(recent_mean)}) {direction} "
                                    f"{format_percentage(abs(change_pct) / 100)} compared to historical average "
                                    f"({format_number(historical_mean)})."
                                ),
                                insight_type=InsightType.TREND,
                                severity=InsightSeverity.KEY if abs(change_pct) > 50 else InsightSeverity.SUPPORTING,
                                tags=["trend", "period_comparison", value_column.lower()],
                            )
                        )
            except Exception:
                pass  # Skip if time-based analysis fails

        # Limit to max_insights
        return insights[:max_insights]

    def build_catalog(
        self,
        insights: list[Insight],
        business_question: str,
        data_summary: dict[str, Any] | None = None,
        objective: str | None = None
    ) -> InsightCatalog:
        """
        Build an insight catalog with narrative structure.

        Args:
            insights: List of insights to include
            business_question: The question being answered
            data_summary: Optional summary of source data
            objective: Optional project objective for contextualization

        Returns:
            InsightCatalog with narrative arc and synthesis
        """
        # Generate cross-insight synthesis using Intelligence Engine
        synthesis = self.intelligence.synthesize_insights(insights, objective or business_question)

        # Add synthesis to data summary
        if data_summary is None:
            data_summary = {}

        data_summary["executive_synthesis"] = synthesis["narrative"]
        data_summary["synthesis_themes"] = synthesis.get("themes", [])
        data_summary["synthesis_confidence"] = synthesis.get("confidence", 0.7)

        # Log rejection explanations for transparency
        if self.rejection_log:
            data_summary["rejection_log"] = self.rejection_log
            logger.info(f"Logged {len(self.rejection_log)} rejected insights with explanations")

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

    def rank_insights(self, insights: list[Insight]) -> list[Insight]:
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

    def to_slide_sequence(self, catalog: InsightCatalog) -> list[dict[str, Any]]:
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

    def _insight_to_slide_spec(self, insight: Insight) -> dict[str, Any]:
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
