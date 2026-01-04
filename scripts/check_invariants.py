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
    - No __pycache__/ directories
    - No *.egg-info directories
    - No .DS_Store files
    - No build/ or dist/ directories

    Returns:
        List of violation messages (empty if no violations)
    """
    violations = []

    # Find __pycache__ directories
    pycache_dirs = list(REPO_ROOT.rglob("__pycache__"))
    if pycache_dirs:
        for d in pycache_dirs[:3]:  # Show first 3
            violations.append(f"❌ Generated artifact: {d.relative_to(REPO_ROOT)}")
        if len(pycache_dirs) > 3:
            violations.append(f"   ... and {len(pycache_dirs) - 3} more __pycache__ dirs")

    # Find .egg-info directories
    egg_info_dirs = list(REPO_ROOT.glob("*.egg-info"))
    if egg_info_dirs:
        for d in egg_info_dirs:
            violations.append(f"❌ Generated artifact: {d.relative_to(REPO_ROOT)}")

    # Find .DS_Store files
    ds_store_files = list(REPO_ROOT.rglob(".DS_Store"))
    if ds_store_files:
        violations.append(f"❌ Found {len(ds_store_files)} .DS_Store file(s)")

    # Check for build/dist directories
    for folder in ["build", "dist"]:
        folder_path = REPO_ROOT / folder
        if folder_path.exists():
            violations.append(f"❌ Generated artifact: {folder}/")

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
