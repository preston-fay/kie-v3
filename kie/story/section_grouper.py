"""
Story Section Grouping Logic

Groups insights into coherent narrative sections with clear themes.
Each section has title, thesis, KPIs, and chart references.
"""

import re
from typing import Any
from collections import defaultdict

from kie.story.models import StoryInsight
from kie.story.models import StorySection, StoryKPI


class SectionGrouper:
    """
    Groups insights into narrative sections.

    Grouping strategies:
    1. Topic clustering (satisfaction, price, trust, etc.)
    2. Metric similarity (all revenue insights together)
    3. Temporal grouping (Q1 vs Q2 vs Q3)
    4. Segmentation grouping (North vs South vs East vs West)
    """

    def __init__(self):
        """Initialize section grouper."""
        # Define topic keywords for clustering
        self.topic_keywords = {
            "satisfaction": ["satisfaction", "satisfied", "happy", "pleased", "content"],
            "price": ["price", "pricing", "cost", "expensive", "cheap", "value"],
            "trust": ["trust", "reliable", "confidence", "reputation", "credibility"],
            "loyalty": ["loyalty", "switching", "retention", "churn", "stay", "leave"],
            "quality": ["quality", "performance", "reliability", "standards"],
            "service": ["service", "support", "assistance", "help", "response"],
            "product": ["product", "offering", "features", "capabilities"],
            "demographics": ["age", "gender", "income", "education", "demographic"],
            "geography": ["region", "location", "geographic", "north", "south", "east", "west"],
            "time": ["trend", "over time", "growth", "decline", "year", "quarter", "month"],
        }

    def group_insights(
        self,
        insights: list[StoryInsight],
        chart_refs: dict[str, str] | None = None,
        min_section_size: int = 2
    ) -> list[StorySection]:
        """
        Group insights into story sections.

        Args:
            insights: All insights to group
            chart_refs: Optional mapping of insight_id -> chart_path
            min_section_size: Minimum insights per section (default 2)

        Returns:
            List of StorySection objects ordered by relevance
        """
        if not insights:
            return []

        chart_refs = chart_refs or {}

        # Try multiple grouping strategies
        sections = []

        # Strategy 1: Topic clustering (primary)
        topic_sections = self._group_by_topic(insights, chart_refs)
        sections.extend(topic_sections)

        # Strategy 2: Catch ungrouped insights
        grouped_ids = {iid for section in sections for iid in section.insight_ids}
        ungrouped = [i for i in insights if i.insight_id not in grouped_ids]

        if ungrouped:
            # Try metric similarity for ungrouped
            metric_sections = self._group_by_metric(ungrouped, chart_refs)
            sections.extend(metric_sections)

            # Still ungrouped? Create "other findings" section
            grouped_ids = {iid for section in sections for iid in section.insight_ids}
            still_ungrouped = [i for i in insights if i.insight_id not in grouped_ids]

            if still_ungrouped and len(still_ungrouped) >= min_section_size:
                other_section = self._create_other_section(still_ungrouped, chart_refs)
                sections.append(other_section)

        # Filter out small sections
        sections = [s for s in sections if len(s.insight_ids) >= min_section_size]

        # Order sections by importance
        sections = self._order_sections(sections, insights)

        return sections

    def _group_by_topic(
        self,
        insights: list[StoryInsight],
        chart_refs: dict[str, str]
    ) -> list[StorySection]:
        """Group insights by topic clusters."""
        # Map insights to topics
        topic_insights: dict[str, list[StoryInsight]] = defaultdict(list)

        for insight in insights:
            text_lower = insight.text.lower()
            matched = False

            for topic, keywords in self.topic_keywords.items():
                if any(kw in text_lower for kw in keywords):
                    topic_insights[topic].append(insight)
                    matched = True
                    break  # Only assign to first matching topic

        # Create sections from topics
        sections = []
        for topic, topic_ins in topic_insights.items():
            if len(topic_ins) >= 2:  # At least 2 insights
                section = self._create_topic_section(topic, topic_ins, chart_refs)
                sections.append(section)

        return sections

    def _group_by_metric(
        self,
        insights: list[StoryInsight],
        chart_refs: dict[str, str]
    ) -> list[StorySection]:
        """Group insights by metric similarity."""
        # Extract metric types (revenue, cost, margin, count, etc.)
        metric_insights: dict[str, list[StoryInsight]] = defaultdict(list)

        metric_patterns = {
            "revenue": r'\$[\d,]+|revenue|\bmoney\b|sales|income',
            "cost": r'cost|expense|spending|budget',
            "margin": r'margin|profit|markup',
            "count": r'\bcount\b|number of|total|quantity',
            "rate": r'rate|ratio|percentage|proportion',
        }

        for insight in insights:
            text_lower = insight.text.lower()
            matched = False

            for metric_type, pattern in metric_patterns.items():
                if re.search(pattern, text_lower):
                    metric_insights[metric_type].append(insight)
                    matched = True
                    break

        # Create sections
        sections = []
        for metric_type, metric_ins in metric_insights.items():
            if len(metric_ins) >= 2:
                section = self._create_metric_section(metric_type, metric_ins, chart_refs)
                sections.append(section)

        return sections

    def _create_topic_section(
        self,
        topic: str,
        insights: list[StoryInsight],
        chart_refs: dict[str, str]
    ) -> StorySection:
        """Create a section for a topic cluster."""
        # Generate section title
        title = self._format_topic_title(topic)

        # Generate section thesis
        thesis = self._generate_topic_thesis(topic, insights)

        # Get chart refs for this section
        section_charts = [chart_refs[i.insight_id] for i in insights if i.insight_id in chart_refs]

        # Extract section ID
        section_id = f"section_{topic}"

        return StorySection(
            section_id=section_id,
            title=title,
            subtitle=f"{len(insights)} key findings",
            thesis=thesis,
            kpis=[],  # Will be populated later by KPIExtractor
            chart_refs=section_charts,
            insight_ids=[i.insight_id for i in insights],
            narrative_text=None,  # Will be populated by NarrativeSynthesizer
            order=0  # Will be set during ordering
        )

    def _create_metric_section(
        self,
        metric_type: str,
        insights: list[StoryInsight],
        chart_refs: dict[str, str]
    ) -> StorySection:
        """Create a section for metric-based grouping."""
        title = f"{metric_type.title()} Analysis"
        thesis = f"Analysis reveals {len(insights)} key patterns in {metric_type} metrics."

        section_charts = [chart_refs[i.insight_id] for i in insights if i.insight_id in chart_refs]
        section_id = f"section_metric_{metric_type}"

        return StorySection(
            section_id=section_id,
            title=title,
            subtitle=f"{metric_type.title()} metrics",
            thesis=thesis,
            kpis=[],
            chart_refs=section_charts,
            insight_ids=[i.insight_id for i in insights],
            narrative_text=None,
            order=0
        )

    def _create_other_section(
        self,
        insights: list[StoryInsight],
        chart_refs: dict[str, str]
    ) -> StorySection:
        """Create a section for ungrouped insights."""
        title = "Additional Findings"
        thesis = f"Analysis identified {len(insights)} additional patterns of interest."

        section_charts = [chart_refs[i.insight_id] for i in insights if i.insight_id in chart_refs]

        return StorySection(
            section_id="section_other",
            title=title,
            subtitle="Supplementary analysis",
            thesis=thesis,
            kpis=[],
            chart_refs=section_charts,
            insight_ids=[i.insight_id for i in insights],
            narrative_text=None,
            order=999  # Push to end
        )

    def _format_topic_title(self, topic: str) -> str:
        """Format topic into section title."""
        # Map topics to consultant-friendly titles
        title_map = {
            "satisfaction": "Overall Satisfaction",
            "price": "Price & Value Perception",
            "trust": "Trust & Credibility",
            "loyalty": "Customer Loyalty & Retention",
            "quality": "Quality & Performance",
            "service": "Service Experience",
            "product": "Product Assessment",
            "demographics": "Demographic Insights",
            "geography": "Geographic Patterns",
            "time": "Trends Over Time",
        }
        return title_map.get(topic, topic.title())

    def _generate_topic_thesis(self, topic: str, insights: list[StoryInsight]) -> str:
        """Generate section thesis for a topic."""
        # Use the highest-value insight as basis
        top_insight = max(insights, key=lambda i: i.business_value)

        # Generate thesis based on topic
        thesis_templates = {
            "satisfaction": f"{topic.title()} analysis reveals critical patterns. {top_insight.text.split('.')[0]}.",
            "price": f"Pricing dynamics show significant impact on behavior. {top_insight.text.split('.')[0]}.",
            "trust": f"Trust factors emerge as key differentiators. {top_insight.text.split('.')[0]}.",
            "loyalty": f"Loyalty patterns indicate strategic opportunities. {top_insight.text.split('.')[0]}.",
            "quality": f"Quality perceptions drive core outcomes. {top_insight.text.split('.')[0]}.",
            "service": f"Service experience shapes customer relationships. {top_insight.text.split('.')[0]}.",
            "product": f"Product attributes influence satisfaction. {top_insight.text.split('.')[0]}.",
            "demographics": f"Demographic segmentation reveals distinct patterns. {top_insight.text.split('.')[0]}.",
            "geography": f"Geographic analysis uncovers regional differences. {top_insight.text.split('.')[0]}.",
            "time": f"Temporal analysis identifies evolving trends. {top_insight.text.split('.')[0]}.",
        }

        return thesis_templates.get(
            topic,
            f"{topic.title()} analysis shows important patterns. {top_insight.text.split('.')[0]}."
        )

    def _order_sections(
        self,
        sections: list[StorySection],
        all_insights: list[StoryInsight]
    ) -> list[StorySection]:
        """Order sections by importance/relevance."""
        # Create insight lookup
        insight_map = {i.insight_id: i for i in all_insights}

        # Score each section
        scored = []
        for section in sections:
            score = self._score_section(section, insight_map)
            scored.append((score, section))

        # Sort by score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Assign order
        for idx, (score, section) in enumerate(scored):
            section.order = idx

        return [section for score, section in scored]

    def _score_section(
        self,
        section: StorySection,
        insight_map: dict[str, StoryInsight]
    ) -> float:
        """Score section by importance."""
        score = 0.0

        # Get insights for this section
        section_insights = [insight_map[iid] for iid in section.insight_ids if iid in insight_map]

        if not section_insights:
            return 0.0

        # Factor 1: Average business value
        avg_bv = sum(i.business_value for i in section_insights) / len(section_insights)
        score += avg_bv * 10.0

        # Factor 2: Average confidence
        avg_conf = sum(i.confidence for i in section_insights) / len(section_insights)
        score += avg_conf * 5.0

        # Factor 3: Section size (more insights = more important)
        score += len(section_insights) * 1.0

        # Factor 4: Topic priority (satisfaction > price > others)
        topic_priority = {
            "satisfaction": 5.0,
            "price": 4.0,
            "loyalty": 4.0,
            "trust": 3.0,
            "quality": 3.0,
        }

        for topic, priority in topic_priority.items():
            if topic in section.section_id:
                score += priority

        return score
