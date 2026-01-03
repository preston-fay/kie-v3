"""
KIE v3 Insights Module

Automatic insight extraction and statistical analysis.
"""

from .schema import (
    Insight,
    InsightType,
    InsightSeverity,
    InsightCategory,
    Evidence,
    InsightCatalog,
)
from .statistical import StatisticalAnalyzer
from .engine import InsightEngine

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
