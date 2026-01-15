"""
KIE Insight Intelligence Engine

Transforms statistical analysis into consultant-grade insights by adding:
- Metric semantic understanding (context-aware interpretation)
- Data quality explanations (why rejections happen)
- Cross-insight synthesis (connecting insights into narratives)
- Actionability generation (specific recommendations)
- Confidence assessment (with reasoning)
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd

from kie.insights.schema import Insight
from kie.charts.formatting import format_number, format_percentage

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Semantic categories for metrics."""
    FINANCIAL_RATE = "financial_rate"  # Margins, returns, growth rates
    ABSOLUTE_FINANCIAL = "absolute_financial"  # Revenue, cost, profit
    PERCENTAGE = "percentage"  # Percentages, ratios, shares
    COUNT = "count"  # Counts, volumes, quantities
    VOLATILITY = "volatility"  # Variance, standard deviation
    TECHNICAL = "technical"  # RSI, MACD, technical indicators
    RISK = "risk"  # Risk scores, probability measures
    TIME_PERIOD = "time_period"  # Dates, periods
    CATEGORICAL = "categorical"  # Categories, segments
    UNKNOWN = "unknown"


@dataclass
class MetricContext:
    """Rich context about a metric."""
    metric_name: str
    metric_type: MetricType
    typical_range: tuple[float, float] | None
    interpretation_rules: dict[str, str]
    benchmark_context: str | None
    unit: str | None


@dataclass
class InsightQualityAssessment:
    """Assessment of insight quality and confidence."""
    confidence: float  # 0.0 to 1.0
    confidence_reason: str
    data_quality_issues: list[str]
    limitations: list[str]
    strength_indicators: list[str]


class MetricSemantics:
    """Understands metric meaning in context."""

    def __init__(self):
        """Initialize semantic understanding rules."""
        self.patterns = self._build_semantic_patterns()

    def _build_semantic_patterns(self) -> dict[MetricType, dict[str, Any]]:
        """Build pattern matching rules for metric types."""
        return {
            MetricType.FINANCIAL_RATE: {
                "keywords": ["return", "margin", "rate", "yield", "growth", "roi", "roa", "roe"],
                "typical_range": (-1.0, 1.0),  # -100% to +100%
                "format": "percentage",
                "interpretation": {
                    "positive": "gain/profit/growth",
                    "negative": "loss/decline/contraction",
                    "near_zero": "stagnation or equilibrium"
                }
            },
            MetricType.ABSOLUTE_FINANCIAL: {
                "keywords": ["revenue", "sales", "cost", "expense", "profit", "loss", "value", "price", "income"],
                "typical_range": (0, float('inf')),
                "format": "currency",
                "interpretation": {
                    "increasing": "growth in financial scale",
                    "decreasing": "declining financial scale",
                    "volatile": "unstable financial performance"
                }
            },
            MetricType.VOLATILITY: {
                "keywords": ["volatility", "std", "variance", "deviation", "variability"],
                "typical_range": (0, float('inf')),
                "format": "number",
                "interpretation": {
                    "high": "unstable/risky/unpredictable",
                    "low": "stable/predictable/consistent",
                    "increasing": "growing uncertainty/risk",
                    "decreasing": "stabilizing/maturing"
                }
            },
            MetricType.TECHNICAL: {
                "keywords": ["rsi", "macd", "sma", "ema", "bb_position", "momentum"],
                "typical_range": None,  # Varies by indicator
                "format": "number",
                "interpretation": {
                    "rsi_high": "overbought condition (>70)",
                    "rsi_low": "oversold condition (<30)",
                    "macd_positive": "bullish momentum",
                    "macd_negative": "bearish momentum"
                }
            },
            MetricType.RISK: {
                "keywords": ["risk", "probability", "likelihood", "exposure"],
                "typical_range": (0, 1.0),
                "format": "percentage",
                "interpretation": {
                    "high": "elevated risk requiring mitigation",
                    "low": "acceptable risk level",
                    "increasing": "deteriorating risk profile"
                }
            },
            MetricType.PERCENTAGE: {
                "keywords": ["pct", "percent", "ratio", "share", "proportion"],
                "typical_range": (0, 1.0),
                "format": "percentage",
                "interpretation": {
                    "high": "dominant/concentrated",
                    "low": "minor/fragmented",
                    "balanced": "diversified"
                }
            },
            MetricType.COUNT: {
                "keywords": ["count", "number", "quantity", "volume", "total"],
                "typical_range": (0, float('inf')),
                "format": "integer",
                "interpretation": {
                    "increasing": "growing scale/activity",
                    "decreasing": "contracting scale/activity"
                }
            }
        }

    def classify_metric(self, metric_name: str) -> MetricContext:
        """Classify metric and provide rich context."""
        metric_lower = metric_name.lower()

        # Match against patterns
        for metric_type, rules in self.patterns.items():
            if any(kw in metric_lower for kw in rules["keywords"]):
                return MetricContext(
                    metric_name=metric_name,
                    metric_type=metric_type,
                    typical_range=rules.get("typical_range"),
                    interpretation_rules=rules.get("interpretation", {}),
                    benchmark_context=None,
                    unit=rules.get("format")
                )

        # Default to unknown
        return MetricContext(
            metric_name=metric_name,
            metric_type=MetricType.UNKNOWN,
            typical_range=None,
            interpretation_rules={},
            benchmark_context=None,
            unit=None
        )

    def interpret_value(
        self,
        metric_context: MetricContext,
        value: float,
        comparison_value: float | None = None
    ) -> str:
        """Interpret what a metric value means in context."""
        metric_type = metric_context.metric_type

        # Financial rates (returns, margins, growth)
        if metric_type == MetricType.FINANCIAL_RATE:
            if abs(value) < 0.01:  # < 1%
                return "near-zero performance (stagnation)"
            elif value > 0.20:  # > 20%
                return "exceptional positive performance"
            elif value > 0.10:  # > 10%
                return "strong positive performance"
            elif value > 0:
                return "modest positive performance"
            elif value > -0.10:
                return "modest negative performance"
            else:
                return "significant negative performance"

        # Volatility
        elif metric_type == MetricType.VOLATILITY:
            if comparison_value and value > comparison_value * 1.5:
                return "elevated volatility (50%+ increase from baseline)"
            elif value > 0.20:
                return "high volatility (unstable conditions)"
            elif value > 0.10:
                return "moderate volatility"
            else:
                return "low volatility (stable conditions)"

        # Risk
        elif metric_type == MetricType.RISK:
            if value > 0.70:
                return "critical risk level requiring immediate action"
            elif value > 0.50:
                return "elevated risk requiring monitoring"
            elif value > 0.30:
                return "moderate risk within acceptable range"
            else:
                return "low risk"

        # Percentages/shares
        elif metric_type == MetricType.PERCENTAGE:
            if value > 0.50:
                return "majority/dominant position"
            elif value > 0.30:
                return "significant share"
            elif value > 0.10:
                return "moderate share"
            else:
                return "minor share"

        return "value observed"


class DataQualityExplainer:
    """Explains why insights are rejected and what it means."""

    def explain_rejection(
        self,
        rejection_reason: str,
        data_context: dict[str, Any]
    ) -> str:
        """Provide consultant-grade explanation for why insight was rejected."""

        # Sign change rejection
        if "sign change" in rejection_reason.lower() or "across zero" in rejection_reason.lower():
            start = data_context.get("start_value", 0)
            end = data_context.get("end_value", 0)
            return (
                f"This metric crosses from {'negative' if start < 0 else 'positive'} "
                f"({format_number(start, precision=4, abbreviate=False)}) to {'negative' if end < 0 else 'positive'} ({format_number(end, precision=4, abbreviate=False)}) territory. "
                "Percentage changes across zero are mathematically valid but contextually "
                "misleading. This suggests either (1) a fundamental regime shift, "
                "(2) a difference metric (profit/loss), or (3) data quality issues. "
                "**Recommendation**: Investigate the underlying cause and use absolute changes "
                "instead of percentages for this metric."
            )

        # Extreme percentage
        elif "exceeds reasonable threshold" in rejection_reason.lower():
            pct_change = data_context.get("pct_change", 0)
            return (
                f"The calculated change ({format_percentage(pct_change / 100, precision=1)}) exceeds realistic bounds. "
                "This typically indicates: (1) division by near-zero values creating "
                "mathematical artifacts, (2) data entry errors, (3) unit mismatches, "
                "or (4) structural breaks in the time series. "
                "**Recommendation**: Verify data quality and consider using absolute "
                "changes or log-transforms for highly volatile metrics."
            )

        # Near zero
        elif "near zero" in rejection_reason.lower():
            return (
                "Values are too close to zero for reliable percentage calculations. "
                "This could indicate: (1) initialization/startup data, (2) measurement "
                "precision issues, (3) genuine equilibrium state, or (4) wrong metric selection. "
                "**Recommendation**: Use absolute changes or verify this is the correct "
                "metric for your analysis objective."
            )

        # Invalid share/concentration
        elif "share" in rejection_reason.lower() or "concentration" in rejection_reason.lower():
            share = data_context.get("leader_share", data_context.get("top_n_share", 0))
            return (
                f"The calculated share ({format_percentage(share / 100, precision=1)}) falls outside valid range (0-100%). "
                "This indicates a calculation error, likely from: (1) negative values in data, "
                "(2) incorrect aggregation logic, or (3) division by wrong total. "
                "**Recommendation**: Review source data for negative values and verify "
                "aggregation method is appropriate for this metric type."
            )

        # Suspicious outlier count
        elif "outlier" in rejection_reason.lower():
            count = data_context.get("outlier_count", 0)
            total = data_context.get("total_count", 1)
            pct = (count / total * 100) if total > 0 else 0
            return (
                f"Detected {count} outliers ({format_percentage(pct / 100, precision=1)} of data), exceeding the 30% threshold. "
                "When more than 30% of data are 'outliers', the distribution is likely: "
                "(1) non-normal (consider alternative distributions), (2) multi-modal "
                "(multiple distinct populations), or (3) contaminated with bad data. "
                "**Recommendation**: Investigate data generating process and consider "
                "segmentation analysis instead of outlier removal."
            )

        # Invalid correlation
        elif "correlation" in rejection_reason.lower():
            corr = data_context.get("correlation", 0)
            return (
                f"Correlation value ({format_number(corr, precision=2, abbreviate=False)}) exceeds valid range [-1, 1]. "
                "This is a calculation error, likely from: (1) insufficient data points, "
                "(2) constant values in one variable, or (3) implementation bug. "
                "**Recommendation**: Verify both variables have variation and sufficient "
                "non-null observations."
            )

        # Generic fallback
        return (
            f"Insight rejected: {rejection_reason}. This indicates a data quality or "
            "calculation issue requiring investigation before reliable insights can be generated."
        )


class CrossInsightSynthesizer:
    """Connects individual insights into coherent narrative."""

    def synthesize(
        self,
        insights: list[Insight],
        objective: str | None = None
    ) -> dict[str, Any]:
        """Generate executive synthesis from multiple insights."""

        if not insights:
            return {
                "narrative": "Insufficient data quality to generate reliable insights.",
                "themes": [],
                "implications": []
            }

        # Categorize insights
        from kie.insights.schema import InsightType

        trends = [i for i in insights if i.insight_type == InsightType.TREND]
        comparisons = [i for i in insights if i.insight_type == InsightType.COMPARISON]
        outliers = [i for i in insights if i.insight_type == InsightType.OUTLIER]
        volatility = [i for i in insights if "volatility" in i.headline.lower()]

        # Identify themes
        themes = []

        # Theme 1: Stability/Volatility
        if len(volatility) > 0 and len(outliers) > 0:
            themes.append({
                "theme": "Unstable Operating Environment",
                "evidence": f"{len(volatility)} volatility indicators, {len(outliers)} outlier patterns",
                "implication": "High variance creates planning difficulty and risk exposure"
            })
        elif len(volatility) > 0:
            themes.append({
                "theme": "Changing Dynamics",
                "evidence": f"{len(volatility)} metrics showing increased variation",
                "implication": "System in transition - monitor for new equilibrium"
            })

        # Theme 2: Concentration/Distribution
        if len(comparisons) > 0:
            # Check if showing concentration
            concentrated = [c for c in comparisons if "leads" in c.headline.lower()]
            if len(concentrated) > 0:
                themes.append({
                    "theme": "Concentration Risk",
                    "evidence": f"{len(concentrated)} metrics dominated by single factors",
                    "implication": "Heavy reliance on few drivers creates vulnerability"
                })

        # Theme 3: Directional Movement
        if len(trends) > 0:
            positive_trends = [t for t in trends if "grow" in t.headline.lower() or "increase" in t.headline.lower()]
            negative_trends = [t for t in trends if "decline" in t.headline.lower() or "decrease" in t.headline.lower()]

            if len(positive_trends) > len(negative_trends):
                themes.append({
                    "theme": "Positive Momentum",
                    "evidence": f"{len(positive_trends)} upward trends, {len(negative_trends)} downward",
                    "implication": "Overall trajectory is favorable but monitor sustainability"
                })
            elif len(negative_trends) > len(positive_trends):
                themes.append({
                    "theme": "Declining Performance",
                    "evidence": f"{len(negative_trends)} downward trends, {len(positive_trends)} upward",
                    "implication": "Deteriorating conditions require intervention"
                })

        # Generate narrative
        narrative = self._generate_narrative(themes, objective)

        return {
            "narrative": narrative,
            "themes": themes,
            "insight_count": len(insights),
            "confidence": self._calculate_synthesis_confidence(insights)
        }

    def _generate_narrative(self, themes: list[dict], objective: str | None) -> str:
        """Generate executive narrative from themes."""
        if not themes:
            return (
                "Analysis reveals a mixed pattern without clear dominant themes. "
                "This suggests either balanced conditions or data limitations preventing "
                "deeper pattern detection."
            )

        # Lead with strongest theme
        lead_theme = themes[0]
        narrative = f"{lead_theme['theme']} has emerged as the critical challenge. "
        narrative += f"{lead_theme['implication']}. "

        # Add supporting themes
        if len(themes) > 1:
            narrative += "\n\nAdditionally, "
            for theme in themes[1:]:
                narrative += f"{theme['theme'].lower()} is evident, with {theme['evidence']}. "

        # Connect to objective if provided
        if objective:
            narrative += f"\n\nGiven the objective of \"{objective}\", these patterns suggest "
            narrative += "a need for strategic response to address underlying drivers."

        return narrative

    def _calculate_synthesis_confidence(self, insights: list[Insight]) -> float:
        """Calculate confidence in the synthesis."""
        if not insights:
            return 0.0

        # Average insight confidence
        avg_confidence = sum(i.confidence for i in insights) / len(insights)

        # Penalty for low insight count
        count_factor = min(len(insights) / 10.0, 1.0)  # Full confidence at 10+ insights

        return avg_confidence * count_factor


class ActionabilityGenerator:
    """Generates specific, actionable recommendations."""

    def __init__(self, metric_semantics: MetricSemantics):
        """Initialize with metric understanding."""
        self.metric_semantics = metric_semantics

    def generate_recommendations(
        self,
        insight: Insight,
        metric_context: MetricContext,
        objective: str | None = None
    ) -> list[str]:
        """Generate specific recommendations for an insight."""
        recommendations = []

        # Trend insights
        from kie.insights.schema import InsightType
        if insight.insight_type == InsightType.TREND:
            trend_direction = "increasing" if "grow" in insight.headline.lower() else "decreasing"
            metric_type = metric_context.metric_type

            if metric_type == MetricType.VOLATILITY:
                if trend_direction == "increasing":
                    recommendations.append(
                        "Implement risk management controls: Consider hedging strategies, "
                        "increase reserves, or adjust operating leverage to buffer against uncertainty."
                    )
                    recommendations.append(
                        "Monitor leading indicators: Identify early warning signals to anticipate "
                        "volatility spikes before they impact operations."
                    )
                else:
                    recommendations.append(
                        "Capitalize on stability: Now is an opportune time for strategic investments "
                        "or initiatives that require predictable conditions."
                    )

            elif metric_type == MetricType.FINANCIAL_RATE:
                if trend_direction == "increasing":
                    recommendations.append(
                        "Sustain momentum: Analyze drivers of positive trend and allocate resources "
                        "to reinforce these factors."
                    )
                    recommendations.append(
                        "Set realistic targets: Extrapolate trend to establish achievable goals "
                        "while accounting for potential reversion to mean."
                    )
                else:
                    recommendations.append(
                        "Root cause analysis required: Identify and address underlying drivers "
                        "of declining performance before conditions deteriorate further."
                    )
                    recommendations.append(
                        "Scenario planning: Model downside cases to prepare contingency responses."
                    )

        # Outlier insights
        elif insight.insight_type == InsightType.OUTLIER:
            recommendations.append(
                "Investigate outliers individually: Each extreme case may represent (1) data errors "
                "requiring correction, (2) special circumstances offering learning opportunities, "
                "or (3) high-value opportunities for targeted action."
            )
            recommendations.append(
                "Establish outlier handling protocol: Define criteria for when to exclude vs. "
                "investigate outliers to ensure consistent treatment across analyses."
            )

        # Concentration insights
        elif insight.insight_type == InsightType.CONCENTRATION:
            recommendations.append(
                "Diversification strategy: Reduce dependency on dominant factors by developing "
                "alternative sources, markets, or capabilities."
            )
            recommendations.append(
                "Risk mitigation: Create contingency plans for scenarios where concentrated "
                "factors underperform or become unavailable."
            )

        # Comparison insights (leadership)
        elif insight.insight_type == InsightType.COMPARISON:
            if "lead" in insight.headline.lower():
                recommendations.append(
                    "Protect leadership position: Invest in sustaining advantages that enable "
                    "the leading factor's dominance."
                )
                recommendations.append(
                    "Develop succession pipeline: Identify and cultivate next-generation leaders "
                    "to ensure continuity if current leader declines."
                )

        # Generic fallback
        if not recommendations:
            recommendations.append(
                "Further investigation recommended: Consult domain experts to determine "
                "appropriate actions for this finding."
            )

        return recommendations


class InsightIntelligenceEngine:
    """Main engine coordinating all intelligence components."""

    def __init__(self):
        """Initialize intelligence engine with all components."""
        self.metric_semantics = MetricSemantics()
        self.data_quality_explainer = DataQualityExplainer()
        self.synthesizer = CrossInsightSynthesizer()
        self.actionability_generator = ActionabilityGenerator(self.metric_semantics)

    def enrich_insight(
        self,
        insight: Insight,
        data: pd.Series,
        objective: str | None = None
    ) -> Insight:
        """Enrich insight with intelligence layer."""

        # Get metric context
        metric_context = self.metric_semantics.classify_metric(insight.metric)

        # Enhance interpretation
        if hasattr(insight, 'supporting_evidence'):
            evidence = insight.supporting_evidence
            if 'value' in evidence:
                value_interpretation = self.metric_semantics.interpret_value(
                    metric_context,
                    evidence['value']
                )
                insight.interpretation = f"{insight.interpretation} ({value_interpretation})"

        # Generate recommendations
        recommendations = self.actionability_generator.generate_recommendations(
            insight,
            metric_context,
            objective
        )

        # Add recommendations to insight
        if not hasattr(insight, 'recommendations'):
            insight.recommendations = recommendations

        return insight

    def explain_rejection(
        self,
        rejection_reason: str,
        metric_name: str,
        data_context: dict[str, Any]
    ) -> dict[str, str]:
        """Explain why an insight was rejected."""

        metric_context = self.metric_semantics.classify_metric(metric_name)
        explanation = self.data_quality_explainer.explain_rejection(
            rejection_reason,
            data_context
        )

        return {
            "metric": metric_name,
            "metric_type": metric_context.metric_type.value,
            "rejection_reason": rejection_reason,
            "explanation": explanation,
            "next_steps": "Address data quality issues before re-analyzing."
        }

    def synthesize_insights(
        self,
        insights: list[Insight],
        objective: str | None = None
    ) -> dict[str, Any]:
        """Synthesize insights into executive narrative."""
        return self.synthesizer.synthesize(insights, objective)

    def assess_quality(
        self,
        insight: Insight,
        data: pd.Series,
        data_profile: dict[str, Any]
    ) -> InsightQualityAssessment:
        """Assess insight quality and provide reasoning."""

        confidence = insight.confidence
        issues = []
        limitations = []
        strengths = []

        # Check data quality
        if data_profile.get("null_percent", 0) > 20:
            issues.append(f"{format_percentage(data_profile['null_percent'] / 100, precision=1)} missing data")
            confidence *= 0.8

        if data_profile.get("outlier_percent", 0) > 10:
            issues.append(f"{format_percentage(data_profile['outlier_percent'] / 100, precision=1)} outliers")
            limitations.append("Outliers may skew results")

        # Check sample size
        sample_size = data_profile.get("sample_size", len(data))
        if sample_size < 30:
            issues.append(f"Small sample size (n={sample_size})")
            limitations.append("Limited statistical power")
            confidence *= 0.7

        # Check for strengths
        if insight.type == "trend" and hasattr(insight, 'supporting_evidence'):
            r_squared = insight.supporting_evidence.get('r_squared', 0)
            if r_squared > 0.7:
                strengths.append(f"Strong trend fit (R²={format_number(r_squared, precision=2, abbreviate=False)})")
            elif r_squared < 0.3:
                limitations.append(f"Weak trend fit (R²={format_number(r_squared, precision=2, abbreviate=False)})")
                confidence *= 0.8

        # Generate confidence reasoning
        if confidence > 0.8:
            reason = "High confidence: Strong statistical evidence with good data quality"
        elif confidence > 0.6:
            reason = "Moderate confidence: Reasonable evidence but some limitations present"
        elif confidence > 0.4:
            reason = "Low confidence: Significant data quality issues or weak statistical support"
        else:
            reason = "Very low confidence: Substantial concerns about data quality and statistical validity"

        return InsightQualityAssessment(
            confidence=confidence,
            confidence_reason=reason,
            data_quality_issues=issues,
            limitations=limitations,
            strength_indicators=strengths
        )
