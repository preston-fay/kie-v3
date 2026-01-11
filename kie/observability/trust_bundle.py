"""
Trust Bundle Generator

Creates deterministic, consultant-facing artifacts that make outputs self-evidently real.
Generated from existing artifacts + Evidence Ledger only.

CRITICAL: Trust Bundle generation NEVER fails a run. Missing data is recorded as "None".
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.observability.evidence_ledger import EvidenceLedger, compute_file_hash, read_rails_stage


def generate_trust_bundle(
    ledger: EvidenceLedger,
    result: dict[str, Any],
    project_root: Path
) -> tuple[str, dict[str, Any]]:
    """
    Generate Trust Bundle markdown and JSON from evidence ledger.

    Args:
        ledger: Evidence ledger with command execution data
        result: Command result dictionary
        project_root: Project root directory

    Returns:
        Tuple of (markdown_content, json_data)

    CRITICAL: This function NEVER raises exceptions.
    """
    try:
        # Build trust bundle data
        bundle_data = _build_trust_bundle_data(ledger, result, project_root)

        # Format as markdown
        markdown = _format_trust_bundle_markdown(bundle_data)

        return markdown, bundle_data

    except Exception as e:
        # Return minimal trust bundle on failure
        return _minimal_trust_bundle(ledger, str(e)), {"error": str(e)}


def save_trust_bundle(
    markdown: str,
    json_data: dict[str, Any],
    project_root: Path
) -> tuple[Path | None, Path | None]:
    """
    Save Trust Bundle to disk.

    Args:
        markdown: Trust Bundle markdown content
        json_data: Trust Bundle JSON data
        project_root: Project root directory

    Returns:
        Tuple of (markdown_path, json_path)

    CRITICAL: This function NEVER raises exceptions or fails a run.
    """
    md_path = None
    json_path = None

    try:
        bundle_dir = project_root / "project_state"
        bundle_dir.mkdir(parents=True, exist_ok=True)

        # Save markdown
        md_path = bundle_dir / "trust_bundle.md"
        md_path.write_text(markdown)

        # Save JSON
        json_path = bundle_dir / "trust_bundle.json"
        json_path.write_text(json.dumps(json_data, indent=2))

    except Exception:
        # Silent failure - trust bundle is advisory only
        pass

    return md_path, json_path


def _build_trust_bundle_data(
    ledger: EvidenceLedger,
    result: dict[str, Any],
    project_root: Path
) -> dict[str, Any]:
    """
    Build trust bundle data structure.

    NEVER raises exceptions.
    """
    try:
        bundle = {
            "run_identity": {
                "run_id": ledger.run_id,
                "timestamp": ledger.timestamp,
                "command": ledger.command,
                "args": ledger.args,
            },
            "workflow_state": {
                "stage_before": ledger.rails_stage_before or "None",
                "stage_after": ledger.rails_stage_after or "None",
                "rails_state_file": "project_state/rails_state.json",
            },
            "output_preferences": {
                "theme": _get_output_theme(project_root),
            },
            "execution_mode": _get_execution_mode(project_root),
            "what_executed": {
                "command": f"/{ledger.command}",
                "success": ledger.success,
            },
            "evidence_ledger": {
                "ledger_id": ledger.run_id,
                "ledger_path": f"project_state/evidence_ledger/{ledger.run_id}.yaml",
            },
            "artifacts_produced": _collect_artifacts(ledger, project_root),
            "skills_executed": _collect_skills(ledger),
            "warnings_blocks": _collect_warnings_blocks(ledger, result),
            "whats_missing": _collect_missing(ledger, result, project_root),
            "next_cli_actions": _collect_next_actions(ledger, result, project_root),
        }

        return bundle

    except Exception:
        # Return minimal bundle on error
        return {
            "run_identity": {"run_id": ledger.run_id, "error": "Failed to build bundle"},
            "error": "Trust bundle generation failed",
        }


def _collect_artifacts(ledger: EvidenceLedger, project_root: Path) -> list[dict[str, str]]:
    """
    Collect artifacts with hashes.

    NEVER raises exceptions.
    """
    try:
        artifacts = []

        for output in ledger.outputs:
            path = output.get("path")
            file_hash = output.get("hash")

            # Make path relative to project root
            try:
                abs_path = Path(path)
                if abs_path.is_absolute():
                    rel_path = abs_path.relative_to(project_root)
                else:
                    rel_path = Path(path)
            except Exception:
                rel_path = Path(path)

            artifacts.append({
                "path": str(rel_path),
                "hash": file_hash or "unavailable",
            })

        # Add skill artifacts
        skills_executed = ledger.proof_references.get("skills_executed", [])
        for skill_result in skills_executed:
            skill_artifacts = skill_result.get("artifacts", {})
            for name, path in skill_artifacts.items():
                try:
                    abs_path = Path(path)
                    if abs_path.is_absolute():
                        rel_path = abs_path.relative_to(project_root)
                    else:
                        rel_path = Path(path)

                    file_hash = compute_file_hash(abs_path)
                    artifacts.append({
                        "path": str(rel_path),
                        "hash": file_hash or "unavailable",
                        "skill": skill_result.get("skill_id"),
                    })
                except Exception:
                    continue

        return artifacts if artifacts else []

    except Exception:
        return []


def _collect_skills(ledger: EvidenceLedger) -> list[dict[str, Any]]:
    """
    Collect skills execution info.

    NEVER raises exceptions.
    """
    try:
        skills_executed = ledger.proof_references.get("skills_executed", [])

        if not skills_executed:
            return []

        skills = []
        for skill_result in skills_executed:
            skills.append({
                "skill_id": skill_result.get("skill_id", "unknown"),
                "success": skill_result.get("success", False),
                "artifacts": skill_result.get("artifacts", {}),
            })

        return skills

    except Exception:
        return []


def _collect_warnings_blocks(ledger: EvidenceLedger, result: dict[str, Any]) -> dict[str, list[str]]:
    """
    Collect warnings and blocks.

    NEVER raises exceptions.
    """
    try:
        warnings = ledger.warnings.copy() if ledger.warnings else []
        errors = ledger.errors.copy() if ledger.errors else []
        blocks = []

        # Check for enforcement blocks in result
        if "blocked" in result and result["blocked"]:
            block_reason = result.get("block_reason", "Unknown block")
            blocks.append(block_reason)

        if "enforcement_result" in result:
            enforcement = result["enforcement_result"]
            if enforcement.get("blocked"):
                blocks.append(enforcement.get("message", "Enforcement block"))

        return {
            "warnings": warnings,
            "errors": errors,
            "blocks": blocks,
        }

    except Exception:
        return {"warnings": [], "errors": [], "blocks": []}


def _collect_missing(ledger: EvidenceLedger, result: dict[str, Any], project_root: Path) -> list[str]:
    """
    Collect explicit list of what's missing.

    NEVER raises exceptions.
    """
    try:
        missing = []

        # Missing workspace dirs
        missing_dirs = ledger.proof_references.get("missing_workspace_dirs", [])
        for dir_name in missing_dirs:
            missing.append(f"Directory: {dir_name}/")

        # Missing data
        has_data = ledger.proof_references.get("has_data", True)
        if not has_data:
            missing.append("Data files in data/ directory")

        # Missing spec
        spec_path = project_root / "project_state" / "spec.yaml"
        if not spec_path.exists():
            missing.append("Specification: project_state/spec.yaml")

        # Check for missing from result
        if "missing" in result:
            missing_from_result = result["missing"]
            if isinstance(missing_from_result, list):
                missing.extend(missing_from_result)
            elif isinstance(missing_from_result, str):
                missing.append(missing_from_result)

        return missing if missing else []

    except Exception:
        return []


def _collect_next_actions(ledger: EvidenceLedger, result: dict[str, Any], project_root: Path) -> list[str]:
    """
    Collect exact next CLI actions.

    This is NEVER empty - blocked commands get recovery actions.

    NEVER raises exceptions.
    """
    try:
        next_actions = []

        # Check for next_steps in result (from NextStepsAdvisor)
        if "next_steps" in result and result["next_steps"]:
            next_actions.extend(result["next_steps"])

        # Check for recovery_commands (from enforcement)
        if "recovery_commands" in result and result["recovery_commands"]:
            next_actions.extend(result["recovery_commands"])

        # If blocked, suggest recovery
        if "blocked" in result and result["blocked"]:
            if not next_actions:
                next_actions.append("python3 -m kie.cli status")
                next_actions.append("# Review block reason and resolve prerequisite")

        # Fallback: suggest /status
        if not next_actions:
            next_actions.append("python3 -m kie.cli status")

        return next_actions

    except Exception:
        return ["python3 -m kie.cli status"]


def _format_trust_bundle_markdown(bundle_data: dict[str, Any]) -> str:
    """
    Format trust bundle as markdown.

    NEVER raises exceptions.
    """
    try:
        lines = []

        lines.append("# Trust Bundle")
        lines.append("")
        lines.append(f"Generated: {datetime.utcnow().isoformat()}Z")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1) Run Identity
        lines.append("## 1. Run Identity")
        lines.append("")
        run_identity = bundle_data.get("run_identity", {})
        lines.append(f"- **Run ID**: `{run_identity.get('run_id', 'unknown')}`")
        lines.append(f"- **Timestamp**: {run_identity.get('timestamp', 'unknown')}")
        lines.append(f"- **Command**: `/{run_identity.get('command', 'unknown')}`")
        if run_identity.get("args"):
            lines.append(f"- **Arguments**: {json.dumps(run_identity['args'])}")
        lines.append("")

        # 2) Current Workflow State
        lines.append("## 2. Current Workflow State")
        lines.append("")
        workflow = bundle_data.get("workflow_state", {})
        lines.append(f"- **Stage Before**: {workflow.get('stage_before', 'None')}")
        lines.append(f"- **Stage After**: {workflow.get('stage_after', 'None')}")
        lines.append(f"- **Rails State File**: `{workflow.get('rails_state_file', 'None')}`")
        lines.append("")

        # 3) What Executed
        lines.append("## 3. What Executed")
        lines.append("")
        executed = bundle_data.get("what_executed", {})
        status = "✓ SUCCESS" if executed.get("success") else "✗ FAILED"
        lines.append(f"- **Command**: `{executed.get('command', 'unknown')}`")
        lines.append(f"- **Status**: {status}")
        lines.append("")

        # 4) Evidence Ledger
        lines.append("## 4. Evidence Ledger")
        lines.append("")
        evidence = bundle_data.get("evidence_ledger", {})
        lines.append(f"- **Ledger ID**: `{evidence.get('ledger_id', 'unknown')}`")
        lines.append(f"- **Ledger Path**: `{evidence.get('ledger_path', 'unknown')}`")
        lines.append("")

        # 5) Artifacts Produced
        lines.append("## 5. Artifacts Produced")
        lines.append("")
        artifacts = bundle_data.get("artifacts_produced", [])
        if artifacts:
            for artifact in artifacts:
                path = artifact.get("path", "unknown")
                file_hash = artifact.get("hash", "unavailable")
                skill = artifact.get("skill")
                if skill:
                    lines.append(f"- `{path}`")
                    lines.append(f"  - Hash: `{file_hash[:16]}...`" if len(file_hash) > 16 else f"  - Hash: `{file_hash}`")
                    lines.append(f"  - Skill: `{skill}`")
                else:
                    lines.append(f"- `{path}`")
                    lines.append(f"  - Hash: `{file_hash[:16]}...`" if len(file_hash) > 16 else f"  - Hash: `{file_hash}`")
        else:
            lines.append("None")
        lines.append("")

        # 6) Skills Executed
        lines.append("## 6. Skills Executed")
        lines.append("")
        skills = bundle_data.get("skills_executed", [])
        if skills:
            for skill in skills:
                skill_id = skill.get("skill_id", "unknown")
                success = skill.get("success", False)
                status = "✓" if success else "✗"
                lines.append(f"- {status} `{skill_id}`")
                artifacts_dict = skill.get("artifacts", {})
                for name, path in artifacts_dict.items():
                    lines.append(f"  - {name}: `{path}`")
        else:
            lines.append("None")
        lines.append("")

        # 7) Warnings / Blocks
        lines.append("## 7. Warnings / Blocks")
        lines.append("")
        warnings_blocks = bundle_data.get("warnings_blocks", {})
        warnings = warnings_blocks.get("warnings", [])
        errors = warnings_blocks.get("errors", [])
        blocks = warnings_blocks.get("blocks", [])

        if warnings:
            lines.append("**Warnings:**")
            for warning in warnings:
                lines.append(f"- ⚠️  {warning}")
            lines.append("")

        if errors:
            lines.append("**Errors:**")
            for error in errors:
                lines.append(f"- ✗ {error}")
            lines.append("")

        if blocks:
            lines.append("**Blocks:**")
            for block in blocks:
                lines.append(f"- 🚫 {block}")
            lines.append("")

        if not warnings and not errors and not blocks:
            lines.append("None")
            lines.append("")

        # 8) What's Missing
        lines.append("## 8. What's Missing")
        lines.append("")
        missing = bundle_data.get("whats_missing", [])
        if missing:
            for item in missing:
                lines.append(f"- {item}")
        else:
            lines.append("None")
        lines.append("")

        # 9) Next CLI Actions
        lines.append("## 9. Next CLI Actions")
        lines.append("")
        next_actions = bundle_data.get("next_cli_actions", [])
        if next_actions:
            lines.append("```bash")
            for action in next_actions:
                lines.append(action)
            lines.append("```")
        else:
            lines.append("```bash")
            lines.append("python3 -m kie.cli status")
            lines.append("```")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*This Trust Bundle is a deterministic artifact generated from the Evidence Ledger.*")
        lines.append("*All claims are backed by recorded evidence.*")

        return "\n".join(lines)

    except Exception:
        return "# Trust Bundle\n\nError: Failed to format trust bundle"


def _minimal_trust_bundle(ledger: EvidenceLedger, error_msg: str) -> str:
    """
    Generate minimal trust bundle when full generation fails.

    NEVER raises exceptions.
    """
    try:
        lines = [
            "# Trust Bundle",
            "",
            f"Generated: {datetime.utcnow().isoformat()}Z",
            "",
            "---",
            "",
            "## 1. Run Identity",
            "",
            f"- **Run ID**: `{ledger.run_id}`",
            f"- **Command**: `/{ledger.command}`",
            "",
            "## Error",
            "",
            f"Trust Bundle generation encountered an error: {error_msg}",
            "",
            "## 9. Next CLI Actions",
            "",
            "```bash",
            "python3 -m kie.cli status",
            "```",
            "",
            "---",
        ]

        return "\n".join(lines)

    except Exception:
        return "# Trust Bundle\n\nCritical error in trust bundle generation"


def _get_output_theme(project_root: Path) -> str:
    """
    Get output theme preference.

    Returns:
        Theme value ('light', 'dark', or 'not_set')

    NEVER raises exceptions.
    """
    try:
        from kie.preferences import OutputPreferences
        prefs = OutputPreferences(project_root)
        theme = prefs.get_theme()
        return theme if theme else "not_set"
    except Exception:
        return "not_set"


def _get_execution_mode(project_root: Path) -> str:
    """
    Get execution mode.

    Returns:
        Execution mode ('rails' or 'freeform')

    NEVER raises exceptions.
    """
    try:
        from kie.execution_policy import ExecutionPolicy
        policy = ExecutionPolicy(project_root)
        mode = policy.get_mode()
        return mode
    except Exception:
        return "rails"
