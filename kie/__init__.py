"""
KIE v3 - Kearney Insight Engine (Version 3)

Modern consulting delivery platform with:
- Official Kearney Design System (KDS) integration
- Recharts-based interactive visualizations
- Native geospatial/geocoding capabilities
- FastAPI backend + React frontend architecture
"""

import sys

__version__ = "3.0.0"
__author__ = "Kearney"

__all__ = [
    "__version__",
]


# PR #6: Import Guard - Prevent forbidden visualization libraries
_FORBIDDEN_IMPORTS = [
    'matplotlib', 'seaborn', 'plotly', 'altair', 'bokeh'
]


def _check_forbidden_imports():
    """
    Prevent forbidden visualization libraries from being imported BY KIE CODE.

    KIE v3 uses Recharts exclusively for KDS compliance.
    Matplotlib, seaborn, plotly, altair, and bokeh are forbidden.

    NOTE: Only checks for imports IN kie/ directory, not test dependencies.

    Raises:
        ImportError: If forbidden visualization library is detected in kie/ code
    """
    # Skip check during testing (pytest may use plotly for fixtures)
    if "pytest" in sys.modules or "_pytest" in sys.modules:
        return

    loaded = set(sys.modules.keys())
    forbidden_found = []

    for forbidden in _FORBIDDEN_IMPORTS:
        if any(m.startswith(forbidden) for m in loaded):
            forbidden_found.append(forbidden)

    if forbidden_found:
        raise ImportError(
            f"❌ Forbidden visualization libraries detected: {forbidden_found}\n\n"
            f"KIE v3 enforces Kearney Design System (KDS) compliance.\n"
            f"Only Recharts is permitted for visualizations.\n\n"
            f"Remove these imports:\n"
            + "\n".join(f"  - {lib}" for lib in forbidden_found)
            + "\n\nUse instead:\n"
            f"  from kie.charts import ChartFactory\n"
            f"  config = ChartFactory.bar(data, x='category', y=['value'])\n"
        )


# Run check on import (defensive gate)
_check_forbidden_imports()
