"""
Thesis Extraction Engine

Analyzes insights to identify the core narrative thesis, paradox, or central theme.
Transforms raw insights into compelling story hooks with business implications.
"""

from typing import Any
import re

from kie.story.models import StoryInsight
from kie.story.models import StoryThesis


class ThesisExtractor:
    """
    Extracts narrative thesis from a collection of insights.

    Identifies:
    - Contradictions/paradoxes (high X but low Y)
    - Dominant themes (most insights cluster around topic)
    - Surprising patterns (unexpected correlations)
    - Business tensions (competing priorities)
    """

    def __init__(self):
        """Initialize thesis extractor."""
        pass

    def extract_thesis(
        self,
        insights: list[StoryInsight],
        project_name: str,
        objective: str | None = None,
    ) -> StoryThesis:
        """
        Extract the core narrative thesis from insights.

        Args:
            insights: List of insights to analyze
            project_name: Project name for context
            objective: Optional project objective to frame thesis

        Returns:
            StoryThesis with title, hook, summary, implication
        """
        if not insights:
            return self._create_default_thesis(project_name)

        # Analyze insight patterns
        patterns = self._analyze_patterns(insights)

        # Generate thesis based on strongest pattern
        if patterns.get("paradox"):
            return self._create_paradox_thesis(patterns["paradox"], insights, project_name)
        elif patterns.get("dominant_theme"):
            return self._create_theme_thesis(patterns["dominant_theme"], insights, project_name)
        elif patterns.get("surprise"):
            return self._create_surprise_thesis(patterns["surprise"], insights, project_name)
        else:
            return self._create_summary_thesis(insights, project_name)

    def _analyze_patterns(self, insights: list[StoryInsight]) -> dict[str, Any]:
        """
        Analyze insights to identify narrative patterns.

        Returns:
            Dict with pattern types and evidence:
            - paradox: Contradictory insights
            - dominant_theme: Most common topic
            - surprise: Unexpected findings
        """
        patterns = {}

        # Look for paradoxes (contradictory high/low patterns)
        paradox = self._detect_paradox(insights)
        if paradox:
            patterns["paradox"] = paradox

        # Identify dominant theme
        theme = self._identify_dominant_theme(insights)
        if theme:
            patterns["dominant_theme"] = theme

        # Find surprising patterns
        surprise = self._detect_surprise(insights)
        if surprise:
            patterns["surprise"] = surprise

        return patterns

    def _detect_paradox(self, insights: list[StoryInsight]) -> dict[str, Any] | None:
        """
        Detect contradictory patterns (e.g., "high satisfaction but high switching intent").

        Returns:
            Dict with paradox details or None
        """
        # Look for insights with opposing signals
        high_positive = []
        high_negative = []

        for insight in insights:
            text_lower = insight.text.lower()

            # Positive signals
            if any(word in text_lower for word in ["high", "strong", "satisfied", "positive", "growth"]):
                high_positive.append(insight)

            # Negative signals
            if any(word in text_lower for word in ["low", "weak", "risk", "concern", "switching", "price sensitivity"]):
                high_negative.append(insight)

        # If we have both high positive and high negative, we have a paradox
        if high_positive and high_negative:
            return {
                "positive": high_positive[0],
                "negative": high_negative[0],
                "type": "satisfaction_vulnerability"
            }

        return None

    def _identify_dominant_theme(self, insights: list[StoryInsight]) -> dict[str, Any] | None:
        """
        Identify the most common theme across insights.

        Returns:
            Dict with theme details or None
        """
        # Count topic keywords
        theme_counts: dict[str, int] = {}
        theme_insights: dict[str, list[StoryInsight]] = {}

        themes = {
            "satisfaction": ["satisfaction", "satisfied", "happy", "pleased"],
            "price": ["price", "cost", "pricing", "expensive", "cheap"],
            "trust": ["trust", "reliable", "confidence", "reputation"],
            "loyalty": ["loyalty", "switching", "retention", "churn"],
            "quality": ["quality", "performance", "reliability"],
        }

        for insight in insights:
            text_lower = insight.text.lower()
            for theme_name, keywords in themes.items():
                if any(kw in text_lower for kw in keywords):
                    theme_counts[theme_name] = theme_counts.get(theme_name, 0) + 1
                    if theme_name not in theme_insights:
                        theme_insights[theme_name] = []
                    theme_insights[theme_name].append(insight)

        if not theme_counts:
            return None

        # Get dominant theme
        dominant = max(theme_counts.items(), key=lambda x: x[1])
        if dominant[1] >= 2:  # At least 2 insights on this theme
            return {
                "name": dominant[0],
                "count": dominant[1],
                "insights": theme_insights[dominant[0]]
            }

        return None

    def _detect_surprise(self, insights: list[StoryInsight]) -> dict[str, Any] | None:
        """
        Detect surprising or unexpected patterns.

        Returns:
            Dict with surprise details or None
        """
        # Look for insights with surprise keywords
        surprise_keywords = ["unexpected", "surprising", "contrary", "despite", "however", "although"]

        for insight in insights:
            text_lower = insight.text.lower()
            if any(kw in text_lower for kw in surprise_keywords):
                return {
                    "insight": insight,
                    "type": "unexpected_pattern"
                }

        # Look for high confidence + high impact = surprising finding
        high_value_insights = [
            i for i in insights
            if i.confidence >= 0.8 and i.business_value >= 0.8
        ]
        if high_value_insights:
            return {
                "insight": high_value_insights[0],
                "type": "high_value_finding"
            }

        return None

    def _create_paradox_thesis(
        self,
        paradox: dict[str, Any],
        insights: list[StoryInsight],
        project_name: str
    ) -> StoryThesis:
        """Create thesis for paradox pattern."""
        pos_text = paradox["positive"].text
        neg_text = paradox["negative"].text

        # Extract key phrases
        pos_phrase = self._extract_key_phrase(pos_text)
        neg_phrase = self._extract_key_phrase(neg_text)

        title = f"The {project_name} Paradox"
        hook = f"{pos_phrase}, yet {neg_phrase}"

        summary = (
            f"Analysis reveals a critical tension: {pos_text.split('.')[0]}. "
            f"However, {neg_text.split('.')[0]}. This paradox suggests underlying "
            f"vulnerabilities that require strategic attention."
        )

        implication = (
            "This paradox indicates that surface-level performance metrics may mask "
            "deeper structural risks. Organizations should investigate root causes "
            "and implement targeted interventions before vulnerabilities materialize."
        )

        return StoryThesis(
            title=title,
            hook=hook,
            summary=summary,
            implication=implication,
            confidence=min(paradox["positive"].confidence, paradox["negative"].confidence),
            supporting_insight_ids=[paradox["positive"].insight_id, paradox["negative"].insight_id]
        )

    def _create_theme_thesis(
        self,
        theme: dict[str, Any],
        insights: list[StoryInsight],
        project_name: str
    ) -> StoryThesis:
        """Create thesis for dominant theme pattern."""
        theme_name = theme["name"].title()
        theme_insights = theme["insights"]

        title = f"{theme_name} Leadership in {project_name}"
        hook = f"{theme_name} emerges as the defining factor across {theme['count']} key dimensions"

        summary = (
            f"Analysis reveals {theme_name.lower()} as the dominant theme, appearing in "
            f"{theme['count']} major insights. {theme_insights[0].text} This pattern "
            f"suggests {theme_name.lower()} is the critical lever for strategic outcomes."
        )

        implication = (
            f"Organizations should prioritize {theme_name.lower()}-focused initiatives "
            f"to drive measurable impact. This theme's dominance indicates it's the "
            f"primary driver of business outcomes in this context."
        )

        avg_confidence = sum(i.confidence for i in theme_insights) / len(theme_insights)

        return StoryThesis(
            title=title,
            hook=hook,
            summary=summary,
            implication=implication,
            confidence=avg_confidence,
            supporting_insight_ids=[i.insight_id for i in theme_insights]
        )

    def _create_surprise_thesis(
        self,
        surprise: dict[str, Any],
        insights: list[StoryInsight],
        project_name: str
    ) -> StoryThesis:
        """Create thesis for surprising pattern."""
        surprise_insight = surprise["insight"]

        title = f"Unexpected Patterns in {project_name}"
        hook = surprise_insight.text.split('.')[0]

        summary = (
            f"Analysis uncovers surprising patterns that challenge conventional assumptions. "
            f"{surprise_insight.text} This unexpected finding suggests the need to "
            f"reconsider traditional approaches."
        )

        implication = (
            "These surprising patterns indicate that standard playbooks may not apply. "
            "Organizations should investigate these anomalies further and consider "
            "adaptive strategies that account for non-obvious dynamics."
        )

        return StoryThesis(
            title=title,
            hook=hook,
            summary=summary,
            implication=implication,
            confidence=surprise_insight.confidence,
            supporting_insight_ids=[surprise_insight.insight_id]
        )

    def _create_summary_thesis(
        self,
        insights: list[StoryInsight],
        project_name: str
    ) -> StoryThesis:
        """Create general summary thesis when no strong pattern emerges."""
        top_insights = sorted(insights, key=lambda i: i.business_value, reverse=True)[:3]

        title = f"{project_name} Key Findings"
        hook = f"Analysis reveals {len(insights)} actionable insights across multiple dimensions"

        summary = (
            f"Comprehensive analysis of {project_name} identifies critical patterns "
            f"and opportunities. {top_insights[0].text if top_insights else ''}"
        )

        implication = (
            "These findings provide a foundation for strategic decision-making. "
            "Organizations should prioritize high-value opportunities and monitor "
            "emerging trends for competitive advantage."
        )

        avg_confidence = sum(i.confidence for i in insights) / len(insights) if insights else 0.5

        return StoryThesis(
            title=title,
            hook=hook,
            summary=summary,
            implication=implication,
            confidence=avg_confidence,
            supporting_insight_ids=[i.insight_id for i in top_insights]
        )

    def _create_default_thesis(self, project_name: str) -> StoryThesis:
        """Create default thesis when no insights available."""
        return StoryThesis(
            title=f"{project_name} Analysis",
            hook="Initial analysis underway",
            summary="Analysis in progress. Additional insights needed for comprehensive narrative.",
            implication="Further investigation required to identify strategic opportunities.",
            confidence=0.3,
            supporting_insight_ids=[]
        )

    def _extract_key_phrase(self, text: str) -> str:
        """Extract key phrase from insight text (for hooks)."""
        # Remove leading numbers and percentages for cleaner hooks
        text = re.sub(r'^\d+\.?\d*%?\s*', '', text)

        # Take first clause (up to comma or period)
        match = re.match(r'^([^,\.]+)', text)
        if match:
            phrase = match.group(1).strip()
            # Lowercase first word unless it's a proper noun
            words = phrase.split()
            if words and words[0][0].isupper() and words[0] not in ['North', 'South', 'East', 'West']:
                words[0] = words[0].lower()
            return ' '.join(words)

        return text[:50]  # Fallback: first 50 chars
