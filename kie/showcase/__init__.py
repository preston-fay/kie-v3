"""
KIE Showcase Mode

First-run activation experience that demonstrates KIE's unique value
in under 60 seconds using clearly-labeled demo data.

CRITICAL CONSTRAINTS:
- Activates ONLY when explicitly triggered (KIE_SHOWCASE=1 or first-ever run)
- Auto-disables permanently once real data/spec exists
- All outputs clearly labeled DEMO
- No writes to real data/ directory
- Evidence Ledger and Trust Bundle still generated (for demo artifacts)
- Exits with clear next-steps message
"""

from kie.showcase.detector import should_activate_showcase, mark_showcase_completed
from kie.showcase.runner import run_showcase

__all__ = [
    "should_activate_showcase",
    "mark_showcase_completed",
    "run_showcase",
]
