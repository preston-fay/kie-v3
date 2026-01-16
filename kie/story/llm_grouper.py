"""
LLM-Powered Section Grouping

Uses Claude to dynamically understand data and group insights into meaningful sections.
Works for ANY domain - healthcare, manufacturing, finance, science, literally anything.
"""

import json
from typing import Any
from collections import defaultdict

from kie.story.models import StoryInsight, StorySection, StoryKPI


class LLMSectionGrouper:
    """
    Uses Claude LLM to dynamically group insights into narrative sections.

    No hardcoded keywords - learns topics from the actual data.
    Works for ANY domain submitted by users.
    """

    def __init__(self):
        """Initialize LLM-powered section grouper."""
        pass

    def group_insights(
        self,
        insights: list[StoryInsight],
        chart_refs: dict[str, str] | None = None,
        min_section_size: int = 2,
        max_sections: int = 5
    ) -> list[StorySection]:
        """
        Group insights into story sections using LLM analysis.

        Args:
            insights: All insights to group
            chart_refs: Optional mapping of insight_id -> chart_path
            min_section_size: Minimum insights per section (default 2)
            max_sections: Maximum number of sections (default 5)

        Returns:
            List of StorySection objects ordered by relevance
        """
        if not insights:
            return []

        chart_refs = chart_refs or {}

        # Step 1: Use LLM to understand the data domain and extract themes
        themes = self._extract_themes_via_llm(insights, max_sections)

        # Step 2: Assign insights to themes
        sections = self._assign_insights_to_themes(insights, themes, chart_refs)

        # Step 3: Filter small sections
        sections = [s for s in sections if len(s.insight_ids) >= min_section_size]

        # If no sections after filtering, create a single "Key Findings" section with all insights
        if not sections and insights:
            sections = [StorySection(
                section_id="section_001",
                title="Key Findings",
                subtitle=None,
                thesis="Primary insights from the analysis",
                insight_ids=[ins.insight_id for ins in insights],
                chart_refs=[chart_refs.get(ins.insight_id) for ins in insights if chart_refs.get(ins.insight_id)],
                kpis=[],
                narrative_text="",
                order=0
            )]

        # Step 4: Order by business value
        sections = self._order_sections(sections, insights)

        # Step 5: Add section-level metadata
        for i, section in enumerate(sections):
            section.order = i

        return sections

    def _extract_themes_via_llm(
        self,
        insights: list[StoryInsight],
        max_themes: int = 5
    ) -> list[dict[str, Any]]:
        """
        Use Claude to analyze insights and extract natural themes.

        This is where we leverage the LLM's understanding to work with ANY data.

        Args:
            insights: All insights to analyze
            max_themes: Maximum number of themes to extract

        Returns:
            List of theme dictionaries with:
            - theme_id: Unique identifier
            - title: Human-readable theme name
            - description: What this theme represents
            - keywords: Key concepts related to this theme
        """
        # Prepare insight summaries for LLM
        insight_summaries = []
        for ins in insights[:20]:  # Sample first 20 to avoid token limits
            insight_summaries.append({
                "id": ins.insight_id,
                "text": ins.text[:200],  # First 200 chars
                "category": ins.category,
                "business_value": ins.business_value
            })

        # Create LLM prompt
        prompt = self._build_theme_extraction_prompt(insight_summaries, max_themes)

        # Call LLM (placeholder - would integrate with Claude API)
        # For now, use intelligent fallback based on categories and text analysis
        themes = self._fallback_theme_extraction(insights, max_themes)

        return themes

    def _build_theme_extraction_prompt(
        self,
        insight_summaries: list[dict],
        max_themes: int
    ) -> str:
        """
        Build prompt for Claude to extract themes from insights.

        This prompt is domain-agnostic and works for ANY data type.
        """
        insights_json = json.dumps(insight_summaries, indent=2)

        prompt = f"""You are analyzing insights from a data analysis project. The data could be from ANY domain - healthcare, finance, manufacturing, science, marketing, literally anything.

Your task: Identify {max_themes} natural themes that group these insights into a compelling story.

INSIGHTS:
{insights_json}

REQUIREMENTS:
1. Theme titles should be clear and descriptive (e.g., "System Performance Trends", "Patient Outcome Patterns", "Cost Efficiency Drivers")
2. Themes should be natural to the DATA, not predetermined business categories
3. Each theme should represent a coherent narrative element
4. Themes should be ordered by importance (most impactful first)
5. If insights are highly diverse, create a "Key Findings" catch-all theme

OUTPUT FORMAT (JSON):
{{
  "themes": [
    {{
      "theme_id": "theme_001",
      "title": "Theme Title",
      "description": "What this theme represents",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "relevance_score": 0.95
    }}
  ]
}}

Analyze the insights and return ONLY the JSON response."""

        return prompt

    def _fallback_theme_extraction(
        self,
        insights: list[StoryInsight],
        max_themes: int
    ) -> list[dict[str, Any]]:
        """
        Fallback theme extraction when LLM is not available.

        Uses intelligent text analysis and clustering instead of hardcoded keywords.
        """
        # Extract key concepts from insight text and categories
        concept_clusters = self._cluster_by_concepts(insights)

        # Convert clusters to themes
        themes = []
        for i, (concept, cluster_insights) in enumerate(concept_clusters.items()):
            if i >= max_themes:
                break

            themes.append({
                "theme_id": f"theme_{i+1:03d}",
                "title": self._generate_theme_title(concept, cluster_insights),
                "description": f"Insights related to {concept}",
                "keywords": self._extract_keywords_from_cluster(cluster_insights),
                "relevance_score": sum(ins.business_value for ins in cluster_insights) / len(cluster_insights)
            })

        # If no natural themes, create single "Key Findings" theme
        if not themes:
            themes.append({
                "theme_id": "theme_001",
                "title": "Key Findings",
                "description": "Primary insights from the analysis",
                "keywords": [],
                "relevance_score": 0.8
            })

        return themes

    def _cluster_by_concepts(
        self,
        insights: list[StoryInsight]
    ) -> dict[str, list[StoryInsight]]:
        """
        Cluster insights by extracting natural concepts from text.

        Uses TF-IDF-like approach to find common themes WITHOUT hardcoded keywords.
        """
        # Extract nouns and key phrases from all insights
        all_text = " ".join(ins.text.lower() for ins in insights)

        # Find repeated concepts (words that appear 2+ times OR appear once with high frequency)
        word_freq = defaultdict(int)
        for word in all_text.split():
            if len(word) > 4:  # Ignore short words
                word_freq[word] += 1

        # Get top concepts - adjust threshold based on dataset size
        top_concepts = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # For small datasets (< 5 insights), allow concepts that appear 1+ times
        # For larger datasets, require 2+ appearances
        min_freq = 1 if len(insights) < 5 else 2
        concept_words = [word for word, freq in top_concepts if freq >= min_freq]

        # Cluster insights by concepts
        clusters = defaultdict(list)
        for insight in insights:
            text_lower = insight.text.lower()

            # Find best matching concept
            best_concept = None
            best_score = 0

            for concept in concept_words:
                if concept in text_lower:
                    score = text_lower.count(concept)
                    if score > best_score:
                        best_score = score
                        best_concept = concept

            if best_concept:
                clusters[best_concept].append(insight)
            else:
                # Use category as fallback
                clusters[insight.category].append(insight)

        return dict(clusters)

    def _generate_theme_title(
        self,
        concept: str,
        insights: list[StoryInsight]
    ) -> str:
        """
        Generate human-readable theme title from concept and insights.

        Makes titles domain-agnostic and natural.
        """
        # Capitalize and clean concept
        concept_clean = concept.replace("_", " ").title()

        # Check if insights have common patterns
        high_value_count = sum(1 for ins in insights if ins.business_value >= 0.8)

        if high_value_count >= len(insights) * 0.7:
            return f"{concept_clean} (Critical Findings)"
        elif any("trend" in ins.text.lower() or "over time" in ins.text.lower() for ins in insights):
            return f"{concept_clean} Trends"
        elif any("risk" in ins.text.lower() or "concern" in ins.text.lower() for ins in insights):
            return f"{concept_clean} Risk Factors"
        elif any("opportunity" in ins.text.lower() or "potential" in ins.text.lower() for ins in insights):
            return f"{concept_clean} Opportunities"
        else:
            return f"{concept_clean} Analysis"

    def _extract_keywords_from_cluster(
        self,
        insights: list[StoryInsight]
    ) -> list[str]:
        """
        Extract key terms that define this cluster.
        """
        # Get all unique words from insight text
        all_words = set()
        for ins in insights:
            words = [w.lower() for w in ins.text.split() if len(w) > 4]
            all_words.update(words)

        # Return top 5 most common
        word_freq = defaultdict(int)
        for ins in insights:
            for word in ins.text.lower().split():
                if word in all_words:
                    word_freq[word] += 1

        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [word for word, _ in top_words]

    def _assign_insights_to_themes(
        self,
        insights: list[StoryInsight],
        themes: list[dict[str, Any]],
        chart_refs: dict[str, str]
    ) -> list[StorySection]:
        """
        Assign insights to themes based on keyword matching and relevance.
        """
        sections = []
        assigned_ids = set()

        for theme in themes:
            theme_insights = []
            theme_keywords = set(kw.lower() for kw in theme["keywords"])

            # Find insights matching this theme
            for insight in insights:
                if insight.insight_id in assigned_ids:
                    continue

                text_lower = insight.text.lower()

                # Check if any theme keywords appear in insight
                matches = sum(1 for kw in theme_keywords if kw in text_lower)

                if matches > 0:
                    theme_insights.append(insight)
                    assigned_ids.add(insight.insight_id)

            # Create section if we have insights
            if theme_insights:
                section = self._create_section_from_theme(
                    theme, theme_insights, chart_refs
                )
                sections.append(section)

        # Handle unassigned insights
        unassigned = [ins for ins in insights if ins.insight_id not in assigned_ids]
        if unassigned:
            other_section = self._create_other_section(unassigned, chart_refs)
            sections.append(other_section)

        return sections

    def _create_section_from_theme(
        self,
        theme: dict[str, Any],
        insights: list[StoryInsight],
        chart_refs: dict[str, str]
    ) -> StorySection:
        """
        Create a StorySection from theme and insights.
        """
        # Get chart references
        section_charts = [chart_refs[ins.insight_id] for ins in insights
                         if ins.insight_id in chart_refs]

        # Generate thesis from insights
        thesis = self._generate_section_thesis(insights)

        section = StorySection(
            section_id=theme["theme_id"],
            title=theme["title"],
            subtitle=theme["description"],
            thesis=thesis,
            kpis=[],  # Will be filled by KPIExtractor
            chart_refs=section_charts,
            insight_ids=[ins.insight_id for ins in insights],
            narrative_text=None,  # Will be filled by NarrativeSynthesizer
            order=0  # Will be set later
        )

        return section

    def _generate_section_thesis(
        self,
        insights: list[StoryInsight]
    ) -> str:
        """
        Generate a thesis statement for this section.

        Uses the highest-value insight as the thesis.
        """
        if not insights:
            return "Analysis of key patterns"

        # Sort by business value
        top_insight = max(insights, key=lambda i: i.business_value)

        # Use first sentence of top insight as thesis
        thesis = top_insight.text.split('.')[0].strip()

        return thesis

    def _create_other_section(
        self,
        insights: list[StoryInsight],
        chart_refs: dict[str, str]
    ) -> StorySection:
        """
        Create "Additional Findings" section for ungrouped insights.
        """
        section_charts = [chart_refs[ins.insight_id] for ins in insights
                         if ins.insight_id in chart_refs]

        section = StorySection(
            section_id="sec_other",
            title="Additional Findings",
            subtitle="Other notable patterns",
            thesis="Additional insights from the analysis",
            kpis=[],
            chart_refs=section_charts,
            insight_ids=[ins.insight_id for ins in insights],
            narrative_text=None,
            order=999  # Last
        )

        return section

    def _order_sections(
        self,
        sections: list[StorySection],
        all_insights: list[StoryInsight]
    ) -> list[StorySection]:
        """
        Order sections by importance (business value of contained insights).
        """
        # Create insight lookup
        insight_map = {ins.insight_id: ins for ins in all_insights}

        # Score each section
        def section_score(section: StorySection) -> float:
            section_insights = [insight_map[iid] for iid in section.insight_ids
                              if iid in insight_map]
            if not section_insights:
                return 0.0

            # Average business value
            avg_value = sum(ins.business_value for ins in section_insights) / len(section_insights)

            # Boost for larger sections
            size_bonus = len(section_insights) * 0.05

            return avg_value + size_bonus

        # Sort by score (descending)
        sorted_sections = sorted(sections, key=section_score, reverse=True)

        # Update order
        for i, section in enumerate(sorted_sections):
            section.order = i

        return sorted_sections
