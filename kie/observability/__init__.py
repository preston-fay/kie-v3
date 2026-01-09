"""
KIE Observability System

Provides universal observability for all CLI command executions.
This module implements STEP 1: OBSERVABILITY from the Skills & Hooks governance contract.

Key components:
- Evidence Ledger: Machine-readable audit trail
- Observability Hooks: Non-blocking pre/post-action observation
- Run Summary: Human-readable output formatter

CRITICAL: This module is observation-only. It NEVER blocks, enforces, or mutates state.
"""

from kie.observability.evidence_ledger import EvidenceLedger, create_ledger
from kie.observability.hooks import ObservabilityHooks
from kie.observability.run_summary import RunSummary

__all__ = [
    "EvidenceLedger",
    "create_ledger",
    "ObservabilityHooks",
    "RunSummary",
]
