"""
Run Summary

Human-readable output formatter for command executions.
Provides clear, actionable feedback to consultants.

CRITICAL: Summaries must be truthful. No "success" without artifacts.
"""

from pathlib import Path
from typing import Any

from kie.observability.evidence_ledger import EvidenceLedger


class RunSummary:
    """
    Formats human-readable run summaries.

    Provides clear feedback about what happened, what exists, and what to do next.
    """

    @staticmethod
    def format(ledger: EvidenceLedger, result: dict[str, Any]) -> str:
        """
        Format a run summary from evidence ledger and result.

        Args:
            ledger: Evidence ledger
            result: Command result dictionary

        Returns:
            Formatted summary string
        """
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append(f"Command: /{ledger.command}")
        lines.append(f"Status: {'✓ SUCCESS' if ledger.success else '✗ FAILED'}")
        lines.append("=" * 60)
        lines.append("")

        # Rails stage
        if ledger.rails_stage_after:
            lines.append(f"Current Stage: {ledger.rails_stage_after}")
            lines.append("")

        # Outputs
        if ledger.outputs:
            lines.append("Outputs:")
            for output in ledger.outputs:
                path = output["path"]
                file_hash = output["hash"]
                if file_hash:
                    lines.append(f"  ✓ {path}")
                else:
                    lines.append(f"  ⚠️  {path} (unreadable)")
            lines.append("")

        # Warnings
        if ledger.warnings:
            lines.append("Warnings:")
            for warning in ledger.warnings:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")

        # Errors
        if ledger.errors:
            lines.append("Errors:")
            for error in ledger.errors:
                lines.append(f"  ✗ {error}")
            lines.append("")

        # Next steps from result
        if "next_steps" in result and result["next_steps"]:
            lines.append("Next Steps:")
            for step in result["next_steps"]:
                lines.append(f"  {step}")
            lines.append("")

        # Evidence ledger location
        lines.append(f"Evidence: project_state/evidence_ledger/{ledger.run_id}.yaml")
        lines.append("=" * 60)

        return "\n".join(lines)

    @staticmethod
    def format_compact(ledger: EvidenceLedger) -> str:
        """
        Format a compact one-line summary.

        Args:
            ledger: Evidence ledger

        Returns:
            Compact summary string
        """
        status = "✓" if ledger.success else "✗"
        output_count = len(ledger.outputs)
        warning_count = len(ledger.warnings)
        error_count = len(ledger.errors)

        parts = [
            f"{status} /{ledger.command}",
            f"{output_count} outputs",
        ]

        if warning_count > 0:
            parts.append(f"{warning_count} warnings")

        if error_count > 0:
            parts.append(f"{error_count} errors")

        return " | ".join(parts)
