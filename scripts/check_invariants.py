#!/usr/bin/env python3
"""
KIE v3 Invariant Checker

Enforces architecture rules that must never be violated:
1. Forbidden dependencies (matplotlib, streamlit, etc.)
2. Forbidden strings in templates (matplotlib code, repo paths)
3. No repo-relative paths in provisioned content

Exit 0 if all checks pass.
Exit 1 if any violation found.
"""

import sys
from pathlib import Path
from typing import List, Tuple

# FORBIDDEN DEPENDENCIES
# These must NEVER appear in pyproject.toml, requirements.txt, or setup.py
FORBIDDEN_DEPS = [
    'matplotlib',
    'seaborn',
    'plotly',
    'altair',
    'bokeh',
    'streamlit',
    'dash',  # Dash is also forbidden (React/Recharts only)
]

# FORBIDDEN STRINGS IN TEMPLATES
# These indicate leaked implementation details or wrong tech stack
FORBIDDEN_TEMPLATE_STRINGS = [
    'matplotlib',
    'pyplot',
    'plt.',
    'import matplotlib',
    'import streamlit',
    'streamlit.',
    ' st.',  # Streamlit API (space before to avoid "first." etc.)
]

# FORBIDDEN PATH PATTERNS
# Repo-relative paths must never leak into templates
FORBIDDEN_PATH_PATTERNS = [
    '/Users/',
    'OneDrive-Kearney',
    'kie-v3-v11',
    '/Projects/kie-v3',
]


def check_dependencies() -> List[str]:
    """Check for forbidden dependencies in package config files."""
    violations = []

    config_files = [
        'pyproject.toml',
        'requirements.txt',
        'setup.py',
        'setup.cfg',
    ]

    repo_root = Path(__file__).parent.parent

    for config_file in config_files:
        file_path = repo_root / config_file
        if not file_path.exists():
            continue

        # Read file and filter out comments
        lines = file_path.read_text().lower().splitlines()
        # Remove lines that are pure comments (start with #)
        content_lines = [line for line in lines if not line.strip().startswith('#')]
        content = '\n'.join(content_lines)

        for forbidden in FORBIDDEN_DEPS:
            # Check for dependency declarations
            patterns = [
                f'"{forbidden}',  # "matplotlib>=1.0"
                f"'{forbidden}",  # 'matplotlib>=1.0'
                f' {forbidden}',  # matplotlib>=1.0 (bare)
                f'={forbidden}',  # install_requires=[...matplotlib...]
            ]

            for pattern in patterns:
                if pattern in content:
                    violations.append(
                        f"❌ FORBIDDEN DEPENDENCY: '{forbidden}' found in {config_file}"
                    )
                    break  # Only report once per dep per file

    return violations


def check_template_strings() -> List[str]:
    """Check for forbidden strings in template files."""
    violations = []

    repo_root = Path(__file__).parent.parent

    # Check template directories
    # Only check kie/templates/ - these get provisioned into workspaces
    # Do NOT check .claude/commands/ in product repo - those are for development
    template_dirs = [
        repo_root / 'kie' / 'templates',
    ]

    for template_dir in template_dirs:
        if not template_dir.exists():
            continue

        for template_file in template_dir.rglob('*.md'):
            content = template_file.read_text()

            for forbidden in FORBIDDEN_TEMPLATE_STRINGS:
                if forbidden in content:
                    rel_path = template_file.relative_to(repo_root)
                    violations.append(
                        f"❌ FORBIDDEN STRING: '{forbidden}' found in {rel_path}"
                    )

    return violations


def check_repo_paths() -> List[str]:
    """Check for hardcoded repo paths in templates."""
    violations = []

    repo_root = Path(__file__).parent.parent

    template_dirs = [
        repo_root / 'kie' / 'templates',
    ]

    for template_dir in template_dirs:
        if not template_dir.exists():
            continue

        for template_file in template_dir.rglob('*'):
            if not template_file.is_file():
                continue
            if template_file.suffix not in ['.md', '.py', '.txt', '.yaml', '.yml']:
                continue

            try:
                content = template_file.read_text()
            except Exception:
                continue  # Skip binary files

            for forbidden_path in FORBIDDEN_PATH_PATTERNS:
                if forbidden_path in content:
                    rel_path = template_file.relative_to(repo_root)
                    violations.append(
                        f"❌ REPO PATH LEAKED: '{forbidden_path}' found in {rel_path}"
                    )

    return violations


def main():
    """Run all invariant checks."""
    print("KIE v3 Invariant Checker")
    print("=" * 60)

    all_violations = []

    # Check 1: Dependencies
    print("\n[1] Checking for forbidden dependencies...")
    dep_violations = check_dependencies()
    if dep_violations:
        all_violations.extend(dep_violations)
        for v in dep_violations:
            print(f"  {v}")
    else:
        print("  ✓ No forbidden dependencies found")

    # Check 2: Template strings
    print("\n[2] Checking for forbidden strings in templates...")
    string_violations = check_template_strings()
    if string_violations:
        all_violations.extend(string_violations)
        for v in string_violations:
            print(f"  {v}")
    else:
        print("  ✓ No forbidden strings found")

    # Check 3: Repo paths
    print("\n[3] Checking for leaked repo paths...")
    path_violations = check_repo_paths()
    if path_violations:
        all_violations.extend(path_violations)
        for v in path_violations:
            print(f"  {v}")
    else:
        print("  ✓ No repo paths leaked")

    # Summary
    print("\n" + "=" * 60)
    if all_violations:
        print(f"❌ FAILED: {len(all_violations)} violation(s) found")
        print("\nThese violations must be fixed before merging.")
        print("\nForbidden dependencies:", ", ".join(FORBIDDEN_DEPS))
        print("Forbidden strings:", ", ".join(FORBIDDEN_TEMPLATE_STRINGS[:5]), "...")
        sys.exit(1)
    else:
        print("✅ PASSED: All invariants satisfied")
        sys.exit(0)


if __name__ == '__main__':
    main()
