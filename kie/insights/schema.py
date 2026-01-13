"""
KIE Insight Types

Core data structures for insights, evidence, and catalogs.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class InsightType(Enum):
    """Types of insights that can be generated."""
    # Core insight types (8 existing)
    COMPARISON = "comparison"
    TREND = "trend"
    DISTRIBUTION = "distribution"
    CORRELATION = "correlation"
    OUTLIER = "outlier"
    CONCENTRATION = "concentration"
    VARIANCE = "variance"
    BENCHMARK = "benchmark"

    # Sophisticated chart types (4 new - Chart Excellence Plan)
    COMPOSITION = "composition"      # Part-to-whole by category (stacked bar/pie)
    DUAL_METRIC = "dual_metric"      # Two scales (combo chart: bar + line)
    CONTRIBUTION = "contribution"    # Sequential changes (waterfall chart)
    DRIVER = "driver"                # Causal analysis (scatter with trend line)


class InsightSeverity(Enum):
    """Importance level of an insight."""
    KEY = "key"  # Critical finding, must be in executive summary
    SUPPORTING = "supporting"  # Important but not critical
    CONTEXT = "context"  # Background information


class InsightCategory(Enum):
    """Category of insight in narrative structure."""
    FINDING = "finding"
    IMPLICATION = "implication"
    RECOMMENDATION = "recommendation"


@dataclass
class Evidence:
    """Supporting evidence for an insight."""
    evidence_type: str  # "chart", "metric", "data_point", "comparison", "statistic"
    reference: str  # Path to chart or metric identifier
    value: Any  # The actual value/data
    label: str | None = None  # Human-readable label
    confidence: float = 1.0  # Statistical confidence if applicable

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.evidence_type,
            "reference": self.reference,
            "value": self.value,
            "label": self.label,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        return cls(
            evidence_type=data.get("type", "metric"),
            reference=data.get("reference", ""),
            value=data.get("value"),
            label=data.get("label"),
            confidence=data.get("confidence", 1.0),
        )


@dataclass
class Insight:
    """A structured insight with evidence and metadata."""
    id: str
    headline: str  # Action title format (e.g., "Northeast Drives 60% of Growth")
    supporting_text: str  # 2-3 sentence explanation
    insight_type: InsightType = InsightType.COMPARISON
    severity: InsightSeverity = InsightSeverity.SUPPORTING
    category: InsightCategory = InsightCategory.FINDING
    evidence: list[Evidence] = field(default_factory=list)
    suggested_slide_type: str = "content"
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.8  # Overall confidence 0-1
    statistical_significance: float | None = None  # p-value if applicable

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "headline": self.headline,
            "supporting_text": self.supporting_text,
            "insight_type": self.insight_type.value,
            "severity": self.severity.value,
            "category": self.category.value,
            "evidence": [e.to_dict() for e in self.evidence],
            "suggested_slide_type": self.suggested_slide_type,
            "tags": self.tags,
            "confidence": self.confidence,
            "statistical_significance": self.statistical_significance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Insight":
        return cls(
            id=data["id"],
            headline=data["headline"],
            supporting_text=data["supporting_text"],
            insight_type=InsightType(data.get("insight_type", "comparison")),
            severity=InsightSeverity(data.get("severity", "supporting")),
            category=InsightCategory(data.get("category", "finding")),
            evidence=[Evidence.from_dict(e) for e in data.get("evidence", [])],
            suggested_slide_type=data.get("suggested_slide_type", "content"),
            tags=data.get("tags", []),
            confidence=data.get("confidence", 0.8),
            statistical_significance=data.get("statistical_significance"),
        )

    @property
    def is_statistically_significant(self) -> bool:
        """Check if insight is statistically significant (p < 0.05)."""
        if self.statistical_significance is None:
            return True  # Assume significant if no p-value
        return self.statistical_significance < 0.05


@dataclass
class InsightCatalog:
    """Collection of insights with narrative structure."""
    generated_at: str
    business_question: str
    insights: list[Insight]
    narrative_arc: dict[str, Any] = field(default_factory=dict)
    data_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "business_question": self.business_question,
            "insights": [i.to_dict() for i in self.insights],
            "narrative_arc": self.narrative_arc,
            "data_summary": self.data_summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InsightCatalog":
        return cls(
            generated_at=data["generated_at"],
            business_question=data["business_question"],
            insights=[Insight.from_dict(i) for i in data.get("insights", [])],
            narrative_arc=data.get("narrative_arc", {}),
            data_summary=data.get("data_summary", {}),
        )

    def save(self, path: str) -> Path:
        """Save catalog to YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
        return path

    @classmethod
    def load(cls, path: str) -> "InsightCatalog":
        """Load catalog from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    def get_key_insights(self) -> list[Insight]:
        """Get insights marked as key."""
        return [i for i in self.insights if i.severity == InsightSeverity.KEY]

    def get_by_category(self, category: InsightCategory) -> list[Insight]:
        """Get insights by category."""
        return [i for i in self.insights if i.category == category]

    def get_by_type(self, insight_type: InsightType) -> list[Insight]:
        """Get insights by type."""
        return [i for i in self.insights if i.insight_type == insight_type]

    def get_findings(self) -> list[Insight]:
        """Get finding insights."""
        return self.get_by_category(InsightCategory.FINDING)

    def get_recommendations(self) -> list[Insight]:
        """Get recommendation insights."""
        return self.get_by_category(InsightCategory.RECOMMENDATION)

    def get_significant_insights(self) -> list[Insight]:
        """Get statistically significant insights."""
        return [i for i in self.insights if i.is_statistically_significant]

    @property
    def summary(self) -> str:
        """Get a brief summary of the catalog."""
        key_count = len(self.get_key_insights())
        total = len(self.insights)
        recs = len(self.get_recommendations())
        return f"{total} insights ({key_count} key, {recs} recommendations)"
