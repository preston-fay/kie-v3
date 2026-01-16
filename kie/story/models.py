"""
Story-First Data Models

Core data structures for consultant-grade storytelling.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from pathlib import Path
import json


@dataclass
class StoryInsight:
    """
    Simplified insight model for story architecture.

    Adapts from kie.insights.schema.Insight for story processing.
    Uses simple field names that match the insights.yaml structure.
    """
    insight_id: str
    text: str  # Combined headline + supporting_text
    category: str
    confidence: float
    business_value: float
    actionability: float
    supporting_data: dict[str, Any] = field(default_factory=dict)


class NarrativeMode(Enum):
    """Narrative synthesis modes for different audiences."""

    EXECUTIVE = "executive"  # Business impact, recommendations, ROI
    ANALYST = "analyst"  # Detailed findings, cross-correlations, patterns
    TECHNICAL = "technical"  # Methodology, confidence, statistical rigor


class KPIType(Enum):
    """Types of KPIs for visual hierarchy."""

    HEADLINE = "headline"  # Main story number (e.g., "68.7%")
    SUPPORTING = "supporting"  # Secondary metric
    DELTA = "delta"  # Change metric (e.g., "+8.8 pts")
    COUNT = "count"  # Absolute count (e.g., "419 of 511")


@dataclass
class StoryThesis:
    """
    The core narrative thesis/paradox extracted from insights.

    Examples:
    - "The Agricultural Retail Paradox"
    - "High Satisfaction Masks Price Vulnerability"
    - "Trust Leadership Battle Between Independent and Retail"
    """

    title: str  # e.g., "The Agricultural Retail Paradox"
    hook: str  # 1-sentence story hook
    summary: str  # 2-3 sentence executive summary
    implication: str  # "So what?" - business impact
    confidence: float  # 0.0-1.0 confidence in thesis
    supporting_insight_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "title": self.title,
            "hook": self.hook,
            "summary": self.summary,
            "implication": self.implication,
            "confidence": self.confidence,
            "supporting_insight_ids": self.supporting_insight_ids,
        }


@dataclass
class StoryKPI:
    """
    Key Performance Indicator callout.

    Designed for large visual display (like "68.7%" in examples).
    """

    value: str  # Formatted value (e.g., "68.7%", "419", "+8.8 pts")
    label: str  # Description (e.g., "Very/Extremely Satisfied")
    context: str  # Additional context (e.g., "n=511 growers")
    kpi_type: KPIType
    rank: int  # Priority rank (1 = most important)
    insight_id: str | None = None  # Source insight

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "value": self.value,
            "label": self.label,
            "context": self.context,
            "type": self.kpi_type.value,
            "rank": self.rank,
            "insight_id": self.insight_id,
        }


@dataclass
class StorySection:
    """
    A narrative section grouping related insights.

    Each section has:
    - Title (e.g., "Overall Satisfaction")
    - Thesis (section-level story)
    - KPIs (callouts for this section)
    - Charts (visualizations)
    - Insights (bullet points)
    """

    section_id: str
    title: str  # e.g., "Overall Satisfaction"
    subtitle: str | None  # Optional subtitle
    thesis: str  # Section-level story (1-2 sentences)
    kpis: list[StoryKPI] = field(default_factory=list)
    chart_refs: list[str] = field(default_factory=list)  # Chart JSON file names
    insight_ids: list[str] = field(default_factory=list)
    narrative_text: str | None = None  # Optional long-form narrative
    order: int = 0  # Display order

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "section_id": self.section_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "thesis": self.thesis,
            "kpis": [kpi.to_dict() for kpi in self.kpis],
            "chart_refs": self.chart_refs,
            "insight_ids": self.insight_ids,
            "narrative_text": self.narrative_text,
            "order": self.order,
        }


@dataclass
class StoryManifest:
    """
    Complete story manifest for consultant-grade output.

    This is the "source of truth" for all deliverables (PPTX, HTML, PDF).
    """

    story_id: str
    project_name: str
    thesis: StoryThesis
    top_kpis: list[StoryKPI]  # Top 3-5 KPIs for hero section
    sections: list[StorySection]
    narrative_mode: NarrativeMode
    executive_summary: str  # Synthesized executive summary
    key_findings: list[str]  # Bullet points for summary slide
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "story_id": self.story_id,
            "project_name": self.project_name,
            "thesis": self.thesis.to_dict(),
            "top_kpis": [kpi.to_dict() for kpi in self.top_kpis],
            "sections": [section.to_dict() for section in self.sections],
            "narrative_mode": self.narrative_mode.value,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "metadata": self.metadata,
        }

    def save(self, output_path: Path) -> None:
        """Save story manifest to JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, input_path: Path) -> "StoryManifest":
        """Load story manifest from JSON."""
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)

        # Reconstruct dataclasses
        thesis = StoryThesis(**data["thesis"])
        top_kpis = [
            StoryKPI(
                value=kpi["value"],
                label=kpi["label"],
                context=kpi["context"],
                kpi_type=KPIType(kpi["type"]),
                rank=kpi["rank"],
                insight_id=kpi.get("insight_id"),
            )
            for kpi in data["top_kpis"]
        ]
        sections = [
            StorySection(
                section_id=sec["section_id"],
                title=sec["title"],
                subtitle=sec.get("subtitle"),
                thesis=sec["thesis"],
                kpis=[
                    StoryKPI(
                        value=kpi["value"],
                        label=kpi["label"],
                        context=kpi["context"],
                        kpi_type=KPIType(kpi["type"]),
                        rank=kpi["rank"],
                        insight_id=kpi.get("insight_id"),
                    )
                    for kpi in sec["kpis"]
                ],
                chart_refs=sec["chart_refs"],
                insight_ids=sec["insight_ids"],
                narrative_text=sec.get("narrative_text"),
                order=sec["order"],
            )
            for sec in data["sections"]
        ]

        return cls(
            story_id=data["story_id"],
            project_name=data["project_name"],
            thesis=thesis,
            top_kpis=top_kpis,
            sections=sections,
            narrative_mode=NarrativeMode(data["narrative_mode"]),
            executive_summary=data["executive_summary"],
            key_findings=data["key_findings"],
            metadata=data.get("metadata", {}),
        )
