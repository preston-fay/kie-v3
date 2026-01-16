"""
KPI Extraction & Ranking System

Surfaces the most impactful numbers from insights for large visual display.
Ranks KPIs by business relevance and formats for consultant-grade presentation.
"""

import re
from typing import Any

from kie.story.models import StoryInsight
from kie.story.models import StoryKPI, KPIType
from kie.charts.formatting import format_number, format_percentage


class KPIExtractor:
    """
    Extracts and ranks KPIs from insights.

    Identifies:
    - Headline numbers (main story metric)
    - Supporting metrics (context)
    - Delta/change metrics (trends)
    - Count metrics (sample sizes, totals)
    """

    def __init__(self):
        """Initialize KPI extractor."""
        pass

    def extract_kpis(
        self,
        insights: list[StoryInsight],
        max_kpis: int = 5,
        context_str: str = ""
    ) -> list[StoryKPI]:
        """
        Extract top KPIs from insights.

        Args:
            insights: List of insights to extract from
            max_kpis: Maximum number of KPIs to return
            context_str: Optional context string (e.g., "n=511 growers")

        Returns:
            List of ranked StoryKPI objects
        """
        if not insights:
            return []

        # Extract all candidate KPIs
        candidates = []
        for insight in insights:
            kpis = self._extract_kpis_from_insight(insight, context_str)
            candidates.extend(kpis)

        # Rank and deduplicate
        ranked = self._rank_kpis(candidates, insights)

        # Return top N
        return ranked[:max_kpis]

    def _extract_kpis_from_insight(
        self,
        insight: StoryInsight,
        context_str: str
    ) -> list[StoryKPI]:
        """
        Extract KPI candidates from a single insight.

        Returns:
            List of StoryKPI candidates
        """
        kpis = []
        text = insight.text

        # Extract percentages
        pct_matches = re.finditer(r'(\d+\.?\d*)%', text)
        for match in pct_matches:
            value_str = match.group(1)
            value_float = float(value_str)

            # Determine if this is a headline KPI (>50% typically means majority)
            kpi_type = KPIType.HEADLINE if value_float >= 50 else KPIType.SUPPORTING

            # Extract label (text around the percentage)
            start_idx = max(0, match.start() - 50)
            end_idx = min(len(text), match.end() + 50)
            context_text = text[start_idx:end_idx]

            # Clean up label
            label = self._extract_label(context_text, match.group(0))

            kpis.append(StoryKPI(
                value=f"{value_str}%",
                label=label,
                context=context_str,
                kpi_type=kpi_type,
                rank=0,  # Will be set during ranking
                insight_id=insight.insight_id
            ))

        # Extract large numbers (for counts, totals)
        num_matches = re.finditer(r'\b(\d{1,3}(?:,\d{3})+|\d{4,})\b', text)
        for match in num_matches:
            num_str = match.group(1).replace(',', '')
            num_val = int(num_str)

            # Only keep substantial numbers (>100)
            if num_val > 100:
                # Format with smart abbreviation
                formatted = format_number(num_val, abbreviate=True)

                # Extract label
                start_idx = max(0, match.start() - 50)
                end_idx = min(len(text), match.end() + 50)
                context_text = text[start_idx:end_idx]
                label = self._extract_label(context_text, match.group(0))

                kpis.append(StoryKPI(
                    value=formatted,
                    label=label,
                    context=context_str,
                    kpi_type=KPIType.COUNT,
                    rank=0,
                    insight_id=insight.insight_id
                ))

        # Extract delta/change patterns ("+8.8 pts", "increased by X")
        delta_patterns = [
            r'(\+|-)\s*(\d+\.?\d*)\s*(pts|points|%|percentage points)',
            r'increased by (\d+\.?\d*)%',
            r'decreased by (\d+\.?\d*)%',
            r'growth of (\d+\.?\d*)%',
        ]

        for pattern in delta_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract change value
                if match.group(1) in ['+', '-']:
                    sign = match.group(1)
                    value_str = match.group(2)
                    unit = match.group(3) if len(match.groups()) >= 3 else ''
                    formatted = f"{sign}{value_str} {unit}".strip()
                else:
                    value_str = match.group(1)
                    formatted = f"+{value_str}%"

                # Extract label
                start_idx = max(0, match.start() - 50)
                end_idx = min(len(text), match.end() + 50)
                context_text = text[start_idx:end_idx]
                label = self._extract_label(context_text, match.group(0))

                kpis.append(StoryKPI(
                    value=formatted,
                    label=label,
                    context=context_str,
                    kpi_type=KPIType.DELTA,
                    rank=0,
                    insight_id=insight.insight_id
                ))

        return kpis

    def _extract_label(self, context_text: str, matched_value: str) -> str:
        """
        Extract descriptive label for a KPI from surrounding text.

        Args:
            context_text: Text surrounding the matched value
            matched_value: The matched numeric value

        Returns:
            Clean label string
        """
        # Remove the matched value from context
        text = context_text.replace(matched_value, '').strip()

        # Remove leading/trailing punctuation and numbers
        text = re.sub(r'^[^\w]+', '', text)
        text = re.sub(r'[^\w]+$', '', text)

        # Extract meaningful phrase (prefer text after "of", "in", "for")
        patterns = [
            r'(?:of|in|for|with|showing|report|rated)\s+([^,\.]{10,60})',
            r'([A-Z][^,\.]{10,60})',  # Capitalized phrases
            r'([a-z][^,\.]{10,60})',  # Any phrase
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                label = match.group(1).strip()
                # Clean up common artifacts
                label = re.sub(r'\s+', ' ', label)
                label = label[:80]  # Max 80 chars
                return label

        # Fallback: first 60 chars
        return text[:60].strip()

    def _rank_kpis(
        self,
        candidates: list[StoryKPI],
        insights: list[StoryInsight]
    ) -> list[StoryKPI]:
        """
        Rank KPIs by business relevance.

        Ranking factors:
        1. KPI type (HEADLINE > DELTA > SUPPORTING > COUNT)
        2. Source insight business_value
        3. Source insight confidence
        4. Numeric magnitude (for percentages, higher is more impactful)
        """
        # Create insight lookup
        insight_map = {i.insight_id: i for i in insights}

        # Score each KPI
        scored = []
        for kpi in candidates:
            score = self._score_kpi(kpi, insight_map)
            scored.append((score, kpi))

        # Sort by score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Assign ranks and deduplicate
        seen_values = set()
        ranked = []
        rank = 1

        for score, kpi in scored:
            # Skip near-duplicates (same value)
            if kpi.value in seen_values:
                continue

            kpi.rank = rank
            ranked.append(kpi)
            seen_values.add(kpi.value)
            rank += 1

        return ranked

    def _score_kpi(
        self,
        kpi: StoryKPI,
        insight_map: dict[str, StoryInsight]
    ) -> float:
        """
        Calculate relevance score for a KPI.

        Returns:
            Float score (higher = more relevant)
        """
        score = 0.0

        # Factor 1: KPI type weight
        type_weights = {
            KPIType.HEADLINE: 10.0,
            KPIType.DELTA: 7.0,
            KPIType.SUPPORTING: 5.0,
            KPIType.COUNT: 3.0,
        }
        score += type_weights.get(kpi.kpi_type, 1.0)

        # Factor 2: Source insight quality
        if kpi.insight_id and kpi.insight_id in insight_map:
            insight = insight_map[kpi.insight_id]
            score += insight.business_value * 5.0
            score += insight.confidence * 3.0

        # Factor 3: Numeric magnitude (for percentages)
        if '%' in kpi.value:
            try:
                pct_val = float(re.search(r'(\d+\.?\d*)', kpi.value).group(1))
                # Higher percentages are more impactful (especially >50%)
                if pct_val >= 70:
                    score += 5.0
                elif pct_val >= 50:
                    score += 3.0
                elif pct_val >= 30:
                    score += 1.0
            except (AttributeError, ValueError):
                pass

        # Factor 4: Label quality (longer, more descriptive = better)
        label_length = len(kpi.label)
        if label_length >= 20:
            score += 2.0
        elif label_length >= 10:
            score += 1.0

        return score

    def extract_section_kpis(
        self,
        section_insights: list[StoryInsight],
        max_kpis: int = 3,
        context_str: str = ""
    ) -> list[StoryKPI]:
        """
        Extract KPIs for a specific story section.

        Args:
            section_insights: StoryInsights belonging to this section
            max_kpis: Maximum KPIs to extract (default 3 for sections)
            context_str: Optional context string

        Returns:
            List of ranked StoryKPI objects for this section
        """
        return self.extract_kpis(section_insights, max_kpis=max_kpis, context_str=context_str)
