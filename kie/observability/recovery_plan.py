"""
Recovery Plan Generator

Creates deterministic, tiered recovery plans when commands WARN, BLOCK, or FAIL.
Provides CLI-only, non-destructive recovery guidance for consultants.

CRITICAL: Recovery plan generation NEVER fails a run. Missing data produces minimal plan.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from kie.observability.evidence_ledger import EvidenceLedger


def should_generate_recovery_plan(
    ledger: EvidenceLedger,
    result: dict[str, Any]
) -> bool:
    """
    Determine if a recovery plan should be generated.

    Recovery plans are generated for:
    - BLOCK (enforcement blocked execution)
    - WARN (enforcement warning)
    - FAIL (command failed naturally)

    Args:
        ledger: Evidence ledger
        result: Command result dictionary

    Returns:
        True if recovery plan should be generated

    CRITICAL: NEVER raises exceptions.
    """
    try:
        # Check for block
        if result.get("blocked"):
            return True

        # Check for enforcement decision
        if "enforcement_result" in result:
            enforcement = result["enforcement_result"]
            decision = enforcement.get("decision")
            if decision in ["BLOCK", "WARN"]:
                return True

        # Check for failure
        if not ledger.success:
            return True

        # Check for errors in ledger
        if ledger.errors:
            return True

        return False

    except Exception:
        return False  # Silent failure


def generate_recovery_plan(
    ledger: EvidenceLedger,
    result: dict[str, Any],
    project_root: Path
) -> str:
    """
    Generate recovery plan markdown.

    Args:
        ledger: Evidence ledger with command execution data
        result: Command result dictionary
        project_root: Project root directory

    Returns:
        Recovery plan markdown content

    CRITICAL: This function NEVER raises exceptions.
    """
    try:
        # Build recovery plan data
        plan_data = _build_recovery_plan_data(ledger, result, project_root)

        # Format as markdown
        markdown = _format_recovery_plan_markdown(plan_data, ledger, project_root)

        return markdown

    except Exception as e:
        # Return minimal recovery plan on failure
        return _minimal_recovery_plan(ledger, str(e))


def save_recovery_plan(
    markdown: str,
    project_root: Path
) -> Path | None:
    """
    Save recovery plan to disk.

    Args:
        markdown: Recovery plan markdown content
        project_root: Project root directory

    Returns:
        Path to saved recovery plan, or None if save failed

    CRITICAL: This function NEVER raises exceptions or fails a run.
    """
    try:
        plan_dir = project_root / "project_state"
        plan_dir.mkdir(parents=True, exist_ok=True)

        plan_path = plan_dir / "recovery_plan.md"
        plan_path.write_text(markdown)

        return plan_path

    except Exception:
        # Silent failure - recovery plan is advisory only
        return None


def get_recovery_message(plan_path: Path, tier1_command: str) -> str:
    """
    Get one-screen recovery message to print to console.

    Args:
        plan_path: Path to recovery plan file
        tier1_command: First Tier 1 recovery command

    Returns:
        Formatted recovery message

    CRITICAL: NEVER raises exceptions.
    """
    try:
        lines = [
            "",
            "=" * 70,
            "⚠️  RECOVERY PLAN AVAILABLE",
            "=" * 70,
            "",
            f"Recovery plan: {plan_path}",
            "",
            "First action:",
            f"  {tier1_command}",
            "",
            "=" * 70,
        ]
        return "\n".join(lines)

    except Exception:
        return "\n⚠️  Recovery plan available at project_state/recovery_plan.md\n"


def _build_recovery_plan_data(
    ledger: EvidenceLedger,
    result: dict[str, Any],
    project_root: Path
) -> dict[str, Any]:
    """
    Build recovery plan data structure.

    NEVER raises exceptions.
    """
    try:
        # Determine what happened
        what_happened = _determine_what_happened(ledger, result)

        # Determine why it happened
        why_happened = _determine_why_happened(ledger, result, project_root)

        # Generate tier 1: Fix it now
        tier1_commands = _generate_tier1_fix(ledger, result, project_root)

        # Generate tier 2: Validate
        tier2_commands = _generate_tier2_validate(ledger, project_root)

        # Generate tier 3: Diagnose environment
        tier3_commands = _generate_tier3_diagnose(ledger, result)

        # Generate tier 4: Escalate safely
        tier4_info = _generate_tier4_escalate(ledger, project_root)

        return {
            "what_happened": what_happened,
            "why_happened": why_happened,
            "tier1_fix": tier1_commands,
            "tier2_validate": tier2_commands,
            "tier3_diagnose": tier3_commands,
            "tier4_escalate": tier4_info,
        }

    except Exception:
        return {
            "what_happened": "Command execution encountered an issue",
            "why_happened": ["Recovery plan generation encountered an error"],
            "tier1_fix": ["python3 -m kie.cli status"],
            "tier2_validate": ["python3 -m kie.cli rails"],
            "tier3_diagnose": ["python3 -m kie.cli doctor"],
            "tier4_escalate": {
                "what_to_share": ["project_state/trust_bundle.md", "project_state/rails_state.json"],
            },
        }


def _determine_what_happened(ledger: EvidenceLedger, result: dict[str, Any]) -> str:
    """
    Determine one-sentence summary of what happened.

    NEVER raises exceptions.
    """
    try:
        # Check for block
        if result.get("blocked"):
            return "Command was blocked by enforcement policy"

        # Check for enforcement decision
        if "enforcement_result" in result:
            enforcement = result["enforcement_result"]
            decision = enforcement.get("decision")
            if decision == "BLOCK":
                return "Command was blocked by enforcement policy"
            elif decision == "WARN":
                return "Command completed with enforcement warnings"

        # Check for failure
        if not ledger.success:
            if ledger.errors:
                return f"Command failed: {ledger.errors[0]}"
            return "Command execution failed"

        return "Command completed with issues"

    except Exception:
        return "Command execution encountered an issue"


def _determine_why_happened(
    ledger: EvidenceLedger,
    result: dict[str, Any],
    project_root: Path
) -> list[str]:
    """
    Determine why the issue happened (proof-backed).

    NEVER raises exceptions.
    """
    try:
        reasons = []

        # Check for enforcement violations
        if "enforcement_result" in result:
            enforcement = result["enforcement_result"]
            message = enforcement.get("message")
            if message:
                reasons.append(f"Policy violation: {message}")

            # Add violated invariant
            violated_invariant = enforcement.get("violated_invariant")
            if violated_invariant:
                reasons.append(f"Violated invariant: {violated_invariant}")

        # Check for block reason
        if result.get("blocked"):
            block_reason = result.get("block_reason")
            if block_reason:
                reasons.append(f"Block reason: {block_reason}")

        # Check for missing prerequisites
        if ledger.proof_references.get("missing_workspace_dirs"):
            missing = ledger.proof_references["missing_workspace_dirs"]
            reasons.append(f"Missing workspace directories: {', '.join(missing)}")

        if not ledger.proof_references.get("has_data"):
            reasons.append("No data files found in data/ directory")

        # Check for errors in ledger
        if ledger.errors:
            reasons.extend([f"Error: {error}" for error in ledger.errors[:3]])

        # Reference evidence
        reasons.append(f"Evidence: project_state/evidence_ledger/{ledger.run_id}.yaml")
        reasons.append(f"Trust Bundle: project_state/trust_bundle.md")

        return reasons if reasons else ["Reason could not be determined"]

    except Exception:
        return ["Reason could not be determined"]


def _generate_tier1_fix(
    ledger: EvidenceLedger,
    result: dict[str, Any],
    project_root: Path
) -> list[str]:
    """
    Generate Tier 1: Fix it now commands.

    These are exact CLI commands for minimum viable recovery.

    NEVER raises exceptions.
    """
    try:
        commands = []

        # Check for recovery commands from enforcement
        if "recovery_commands" in result and result["recovery_commands"]:
            commands.extend(result["recovery_commands"])
            return commands

        # Check enforcement result for recovery
        if "enforcement_result" in result:
            enforcement = result["enforcement_result"]
            if enforcement.get("recovery_commands"):
                commands.extend(enforcement["recovery_commands"])
                return commands

        # Check for specific missing prerequisites
        if not ledger.proof_references.get("has_data"):
            commands.append("# Add CSV, Excel, Parquet, or JSON file to data/ directory")
            commands.append("python3 -m kie.cli eda")
            return commands

        # Check if spec is missing
        spec_path = project_root / "project_state" / "spec.yaml"
        if not spec_path.exists():
            commands.append("python3 -m kie.cli spec --init")
            return commands

        # Generic failure recovery
        if not ledger.success:
            commands.append(f"# Review error and fix prerequisites")
            commands.append(f"python3 -m kie.cli {ledger.command}")
            return commands

        # Fallback
        commands.append("python3 -m kie.cli status")
        return commands

    except Exception:
        return ["python3 -m kie.cli status"]


def _generate_tier2_validate(ledger: EvidenceLedger, project_root: Path) -> list[str]:
    """
    Generate Tier 2: Validate commands.

    These confirm recovery was successful.

    NEVER raises exceptions.
    """
    try:
        commands = [
            "python3 -m kie.cli rails",
            "python3 -m kie.cli validate",
        ]
        return commands

    except Exception:
        return ["python3 -m kie.cli status"]


def _generate_tier3_diagnose(ledger: EvidenceLedger, result: dict[str, Any]) -> list[str]:
    """
    Generate Tier 3: Diagnose environment commands.

    NEVER raises exceptions.
    """
    try:
        commands = [
            "python3 -m kie.cli doctor",
        ]

        # Add Node guidance only if dashboard-related
        if ledger.command in ["build", "preview"] or "dashboard" in str(result):
            commands.append("# If dashboard issues: check Node.js version (need 18+)")
            commands.append("node --version")

        return commands

    except Exception:
        return ["python3 -m kie.cli doctor"]


def _generate_tier4_escalate(ledger: EvidenceLedger, project_root: Path) -> dict[str, list[str]]:
    """
    Generate Tier 4: Escalate safely information.

    NEVER raises exceptions.
    """
    try:
        what_to_share = [
            "project_state/trust_bundle.md",
            f"project_state/evidence_ledger/{ledger.run_id}.yaml",
            "project_state/rails_state.json",
        ]

        return {
            "what_to_share": what_to_share,
            "instructions": [
                "Share these files with support (no secrets included)",
                "Do NOT share data/ directory contents",
                "Do NOT share .env files or credentials",
            ],
        }

    except Exception:
        return {
            "what_to_share": ["project_state/trust_bundle.md"],
            "instructions": ["Share with support for assistance"],
        }


def _format_recovery_plan_markdown(
    plan_data: dict[str, Any],
    ledger: EvidenceLedger,
    project_root: Path
) -> str:
    """
    Format recovery plan as markdown.

    NEVER raises exceptions.
    """
    try:
        lines = []

        lines.append("# Recovery Plan")
        lines.append("")
        lines.append(f"Generated: {datetime.utcnow().isoformat()}Z")
        lines.append(f"Run ID: {ledger.run_id}")
        lines.append(f"Command: /{ledger.command}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. What happened
        lines.append("## 1. What happened")
        lines.append("")
        lines.append(plan_data["what_happened"])
        lines.append("")

        # 2. Why it happened
        lines.append("## 2. Why it happened (proof-backed)")
        lines.append("")
        for reason in plan_data["why_happened"]:
            lines.append(f"- {reason}")
        lines.append("")

        # 3. Fix it now (Tier 1)
        lines.append("## 3. Fix it now (Tier 1)")
        lines.append("")
        lines.append("Run these commands immediately:")
        lines.append("")
        lines.append("```bash")
        for cmd in plan_data["tier1_fix"]:
            lines.append(cmd)
        lines.append("```")
        lines.append("")

        # 4. Validate (Tier 2)
        lines.append("## 4. Validate (Tier 2)")
        lines.append("")
        lines.append("Confirm recovery was successful:")
        lines.append("")
        lines.append("```bash")
        for cmd in plan_data["tier2_validate"]:
            lines.append(cmd)
        lines.append("```")
        lines.append("")

        # 5. Diagnose environment (Tier 3)
        lines.append("## 5. Diagnose environment (Tier 3)")
        lines.append("")
        lines.append("If issue persists, check environment:")
        lines.append("")
        lines.append("```bash")
        for cmd in plan_data["tier3_diagnose"]:
            lines.append(cmd)
        lines.append("```")
        lines.append("")

        # 6. Escalate safely (Tier 4)
        lines.append("## 6. Escalate safely (Tier 4)")
        lines.append("")
        lines.append("If issue still not resolved, share these files with support:")
        lines.append("")
        escalate = plan_data["tier4_escalate"]
        for item in escalate["what_to_share"]:
            lines.append(f"- `{item}`")
        lines.append("")
        if "instructions" in escalate:
            for instruction in escalate["instructions"]:
                lines.append(f"⚠️  {instruction}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*This recovery plan is deterministic and CLI-only.*")
        lines.append("*All commands are non-destructive and safe to run.*")

        return "\n".join(lines)

    except Exception:
        return "# Recovery Plan\n\nError: Failed to format recovery plan"


def _minimal_recovery_plan(ledger: EvidenceLedger, error_msg: str) -> str:
    """
    Generate minimal recovery plan when full generation fails.

    NEVER raises exceptions.
    """
    try:
        lines = [
            "# Recovery Plan",
            "",
            f"Generated: {datetime.utcnow().isoformat()}Z",
            f"Run ID: {ledger.run_id}",
            f"Command: /{ledger.command}",
            "",
            "---",
            "",
            "## 1. What happened",
            "",
            "Command execution encountered an issue",
            "",
            "## Error",
            "",
            f"Recovery plan generation encountered an error: {error_msg}",
            "",
            "## 3. Fix it now (Tier 1)",
            "",
            "```bash",
            "python3 -m kie.cli status",
            "```",
            "",
            "## 6. Escalate safely (Tier 4)",
            "",
            "- `project_state/trust_bundle.md`",
            "- `project_state/rails_state.json`",
            "",
            "---",
        ]

        return "\n".join(lines)

    except Exception:
        return "# Recovery Plan\n\nCritical error in recovery plan generation"
