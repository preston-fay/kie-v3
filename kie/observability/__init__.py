"""
KIE Observability System

Provides universal observability for all CLI command executions.
Implements STEP 1: OBSERVABILITY and STEP 2: ENFORCEMENT from the Skills & Hooks governance contract.

Key components:
- Evidence Ledger: Machine-readable audit trail (STEP 1)
- Observability Hooks: Non-blocking pre/post-action observation (STEP 1)
- Run Summary: Human-readable output formatter (STEP 1)
- Policy Engine: Enforcement of Rails invariants (STEP 2)

CRITICAL: Enforcement blocks INVALID actions only. Valid failures are permitted.
"""

from kie.observability.evidence_ledger import EvidenceLedger, create_ledger
from kie.observability.hooks import ObservabilityHooks
from kie.observability.policy_engine import PolicyEngine, PolicyResult, PolicyDecision, generate_recovery_message
from kie.observability.run_summary import RunSummary

__all__ = [
    "EvidenceLedger",
    "create_ledger",
    "ObservabilityHooks",
    "PolicyEngine",
    "PolicyResult",
    "PolicyDecision",
    "generate_recovery_message",
    "RunSummary",
]
