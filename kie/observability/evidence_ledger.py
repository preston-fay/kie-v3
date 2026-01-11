"""
Evidence Ledger

Machine-readable audit trail for all KIE command executions.
Records what happened, what was produced, and what the environment looked like.

CRITICAL: Ledger creation NEVER fails a run. Missing data is recorded as null.
"""

import hashlib
import json
import platform
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EvidenceLedger:
    """
    Evidence Ledger for a single command execution.

    This is the authoritative record of what happened during a command run.
    All claims must be backed by ledger entries.
    """

    run_id: str
    timestamp: str
    command: str
    args: dict[str, Any] = field(default_factory=dict)
    execution_mode: str = "rails"  # Mode Gate: track if rails or freeform
    rails_stage_before: str | None = None
    rails_stage_after: str | None = None
    environment: dict[str, Any] = field(default_factory=dict)
    inputs: list[dict[str, str]] = field(default_factory=list)
    outputs: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    success: bool = True
    proof_references: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "command": self.command,
            "args": self.args,
            "execution_mode": self.execution_mode,
            "rails_stage_before": self.rails_stage_before,
            "rails_stage_after": self.rails_stage_after,
            "environment": self.environment,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "warnings": self.warnings,
            "errors": self.errors,
            "success": self.success,
            "proof_references": self.proof_references,
        }

    def to_yaml(self) -> str:
        """Convert to YAML format."""
        import yaml
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def to_json(self) -> str:
        """Convert to JSON format."""
        return json.dumps(self.to_dict(), indent=2)

    def save(self, ledger_dir: Path) -> Path:
        """
        Save ledger to disk.

        CRITICAL: This method NEVER raises exceptions. If saving fails,
        it logs the error but does not interrupt the command flow.

        Returns:
            Path to saved ledger file, or None if save failed
        """
        try:
            ledger_dir.mkdir(parents=True, exist_ok=True)
            ledger_path = ledger_dir / f"{self.run_id}.yaml"
            ledger_path.write_text(self.to_yaml())
            return ledger_path
        except Exception as e:
            # Log error but do not fail
            print(f"Warning: Could not save evidence ledger: {e}")
            return None


def create_ledger(
    command: str,
    args: dict[str, Any] | None = None,
    project_root: Path | None = None
) -> EvidenceLedger:
    """
    Create a new Evidence Ledger for a command execution.

    Args:
        command: Command name (e.g., "eda", "analyze")
        args: Command arguments
        project_root: Project root directory for context

    Returns:
        EvidenceLedger instance
    """
    run_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Capture environment
    environment = capture_environment()

    # Capture Rails state if available
    rails_stage_before = None
    execution_mode = "rails"  # Default
    if project_root:
        rails_stage_before = read_rails_stage(project_root)
        # Capture execution mode
        try:
            from kie.state import ExecutionPolicy
            policy = ExecutionPolicy(project_root)
            execution_mode = policy.get_mode().value
        except Exception:
            execution_mode = "rails"

    ledger = EvidenceLedger(
        run_id=run_id,
        timestamp=timestamp,
        command=command,
        args=args or {},
        execution_mode=execution_mode,
        rails_stage_before=rails_stage_before,
        environment=environment,
    )

    return ledger


def capture_environment() -> dict[str, Any]:
    """
    Capture current environment snapshot.

    Returns environment details that matter for reproducibility.
    Missing data is recorded as null.
    """
    env = {
        "os": platform.system(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "node_version": None,  # Populated by hooks if available
    }

    return env


def read_rails_stage(project_root: Path) -> str | None:
    """
    Read current Rails stage from rails_state.json.

    Returns None if rails_state.json doesn't exist or can't be read.
    NEVER raises exceptions.
    """
    try:
        rails_state_path = project_root / "project_state" / "rails_state.json"
        if not rails_state_path.exists():
            return None

        with open(rails_state_path) as f:
            rails_state = json.load(f)

        return rails_state.get("current_stage")
    except Exception:
        return None


def compute_file_hash(file_path: Path) -> str | None:
    """
    Compute SHA-256 hash of a file.

    Returns None if file doesn't exist or can't be read.
    NEVER raises exceptions.
    """
    try:
        if not file_path.exists():
            return None

        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)

        return sha256.hexdigest()
    except Exception:
        return None


def record_artifacts(
    ledger: EvidenceLedger,
    artifact_paths: list[Path],
    artifact_type: str = "output"
) -> None:
    """
    Record artifacts in the ledger.

    Args:
        ledger: Evidence ledger to update
        artifact_paths: List of paths to artifacts
        artifact_type: "input" or "output"

    CRITICAL: This method NEVER raises exceptions.
    Missing or unreadable files are recorded with null hashes.
    """
    target_list = ledger.inputs if artifact_type == "input" else ledger.outputs

    for path in artifact_paths:
        try:
            file_hash = compute_file_hash(path)
            target_list.append({
                "path": str(path),
                "hash": file_hash,
            })
        except Exception:
            # Record the path with null hash
            target_list.append({
                "path": str(path),
                "hash": None,
            })
