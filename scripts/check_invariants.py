#!/usr/bin/env python3
"""
Repository Invariants Checker

Enforces critical structural invariants for the KIE v3 repository.
Run in CI or pre-commit hooks to prevent accidental violations.

INVARIANTS ENFORCED:
1. Package name is 'kie' (never 'kie-v3', 'kie_v3', etc.)
2. Product repo contains no workspace state (project_state/)
3. No generated artifacts committed (__pycache__, *.egg-info)
4. Only one implementation of each capability (no parallel implementations)
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Root of the repo
REPO_ROOT = Path(__file__).parent.parent


class InvariantViolation(Exception):
    """Raised when a repository invariant is violated."""
    pass


def check_package_name() -> List[str]:
    """
    INVARIANT 1: Package name must be 'kie'

    Checks:
    - pyproject.toml defines name = "kie"
    - Package directory is kie/ (not kie-v3/, kie_v3/)
    - No imports from old names (core, core_v3)

    Returns:
        List of violation messages (empty if no violations)
    """
    violations = []

    # Check pyproject.toml
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists():
        violations.append("❌ pyproject.toml not found")
    else:
        content = pyproject.read_text()
        if 'name = "kie"' not in content:
            violations.append("❌ pyproject.toml: package name is not 'kie'")

    # Check package directory exists and is named correctly
    kie_dir = REPO_ROOT / "kie"
    if not kie_dir.exists() or not kie_dir.is_dir():
        violations.append("❌ Package directory 'kie/' does not exist")

    # Check for wrong package names
    wrong_names = ["kie-v3", "kie_v3", "core", "core_v3"]
    for wrong_name in wrong_names:
        wrong_dir = REPO_ROOT / wrong_name
        if wrong_dir.exists() and wrong_dir.is_dir():
            violations.append(f"❌ Found incorrect package directory: {wrong_name}/")

    # Check for imports from old names in kie/ package
    if kie_dir.exists():
        old_imports = ["from core import", "from core.", "from core_v3 import", "from core_v3."]
        for py_file in kie_dir.rglob("*.py"):
            content = py_file.read_text()
            for old_import in old_imports:
                if old_import in content:
                    violations.append(f"❌ {py_file.relative_to(REPO_ROOT)}: Found old import '{old_import}'")
                    break  # One violation per file is enough

    return violations


def check_no_workspace_state() -> List[str]:
    """
    INVARIANT 2: Product repo must not contain workspace state

    Checks:
    - No project_state/ directory at repo root
    - No data/, outputs/, exports/ at repo root (workspace folders)

    Returns:
        List of violation messages (empty if no violations)
    """
    violations = []

    # Workspace folders that belong in project workspaces, not product repo
    workspace_folders = ["project_state", "data", "outputs", "exports"]

    for folder in workspace_folders:
        folder_path = REPO_ROOT / folder
        if folder_path.exists():
            violations.append(f"❌ Found workspace folder in product repo: {folder}/")

    return violations


def check_no_generated_artifacts() -> List[str]:
    """
    INVARIANT 3: No generated artifacts committed

    Checks:
    - No __pycache__/ directories (git-tracked)
    - No *.egg-info directories (git-tracked)
    - No .DS_Store files (git-tracked)
    - No build/ or dist/ directories (git-tracked)

    Only fails if artifacts are tracked by git. Untracked local caches are allowed.

    Returns:
        List of violation messages (empty if no violations)
    """
    import subprocess

    violations = []

    # Get list of all git-tracked files
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        tracked_files = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
    except subprocess.CalledProcessError:
        # If git command fails, fall back to filesystem checks with warning
        violations.append("⚠️  WARNING: Could not check git-tracked files (not a git repo?)")
        return violations

    # Check for tracked __pycache__ files
    pycache_tracked = [f for f in tracked_files if "__pycache__" in f]
    if pycache_tracked:
        for f in pycache_tracked[:3]:
            violations.append(f"❌ Tracked generated artifact: {f}")
        if len(pycache_tracked) > 3:
            violations.append(f"   ... and {len(pycache_tracked) - 3} more __pycache__ files")

    # Check for tracked .egg-info files
    egg_info_tracked = [f for f in tracked_files if ".egg-info" in f]
    if egg_info_tracked:
        for f in egg_info_tracked[:3]:
            violations.append(f"❌ Tracked generated artifact: {f}")
        if len(egg_info_tracked) > 3:
            violations.append(f"   ... and {len(egg_info_tracked) - 3} more .egg-info files")

    # Check for tracked .DS_Store files
    ds_store_tracked = [f for f in tracked_files if ".DS_Store" in f]
    if ds_store_tracked:
        for f in ds_store_tracked:
            violations.append(f"❌ Tracked generated artifact: {f}")

    # Check for tracked build/dist files
    build_dist_tracked = [f for f in tracked_files if f.startswith("build/") or f.startswith("dist/")]
    if build_dist_tracked:
        for f in build_dist_tracked[:3]:
            violations.append(f"❌ Tracked generated artifact: {f}")
        if len(build_dist_tracked) > 3:
            violations.append(f"   ... and {len(build_dist_tracked) - 3} more build/dist files")

    return violations


def check_no_parallel_implementations() -> List[str]:
    """
    INVARIANT 4: Only one implementation of each capability

    Checks:
    - No kie/slides/ (use kie/powerpoint/)
    - No kie/migrate/ (empty stub directories)

    Returns:
        List of violation messages (empty if no violations)
    """
    violations = []

    # Check for parallel implementations
    parallel_impls = {
        "kie/slides": "Use kie/powerpoint/ instead",
        "kie/migrate": "Empty stub - should not exist",
    }

    for path, reason in parallel_impls.items():
        full_path = REPO_ROOT / path
        if full_path.exists():
            violations.append(f"❌ Parallel implementation found: {path}/ ({reason})")

    return violations


def run_all_checks() -> Tuple[bool, List[str]]:
    """
    Run all invariant checks.

    Returns:
        Tuple of (passed: bool, violations: List[str])
    """
    all_violations = []

    all_violations.extend(check_package_name())
    all_violations.extend(check_no_workspace_state())
    all_violations.extend(check_no_generated_artifacts())
    all_violations.extend(check_no_parallel_implementations())

    passed = len(all_violations) == 0
    return passed, all_violations


def main():
    """Main entry point."""
    print("=" * 60)
    print("KIE v3 Repository Invariants Check")
    print("=" * 60)
    print()

    passed, violations = run_all_checks()

    if passed:
        print("✅ All invariants passed!")
        print()
        print("Checked:")
        print("  ✓ Package name is 'kie'")
        print("  ✓ No workspace state in product repo")
        print("  ✓ No generated artifacts committed")
        print("  ✓ No parallel implementations")
        sys.exit(0)
    else:
        print("❌ Invariant violations detected:")
        print()
        for violation in violations:
            print(f"  {violation}")
        print()
        print(f"Total violations: {len(violations)}")
        print()
        print("Fix these issues before committing/merging.")
        sys.exit(1)


if __name__ == "__main__":
    main()
