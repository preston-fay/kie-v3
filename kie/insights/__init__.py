"""
KIE v3 Insights Module

Automatic insight extraction and statistical analysis.
"""

from .engine import InsightEngine
from .schema import (
    Evidence,
    Insight,
    InsightCatalog,
    InsightCategory,
    InsightSeverity,
    InsightType,
)
from .statistical import StatisticalAnalyzer

__all__ = [
    "Insight",
    "InsightType",
    "InsightSeverity",
    "InsightCategory",
    "Evidence",
    "InsightCatalog",
    "StatisticalAnalyzer",
    "InsightEngine",
]
