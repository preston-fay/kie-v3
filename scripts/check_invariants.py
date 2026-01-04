#!/usr/bin/env python3
"""
CI Invariant Checker for KIE v3

Enforces architectural rules:
- No forbidden dependencies (matplotlib, streamlit, etc.)
- No forbidden strings in templates/code
- No absolute paths leaked into workspace templates
"""

import sys
from pathlib import Path

# Forbidden dependencies in pyproject.toml
FORBIDDEN_DEPS = [
    'matplotlib',
    'seaborn',
    'plotly',
    'altair',
    'bokeh',
    'streamlit',
    'dash',
]

# Forbidden strings in templates and code (case-insensitive)
FORBIDDEN_TEMPLATE_STRINGS = [
    'import matplotlib',
    'from matplotlib',
    'import streamlit as st',
    'import streamlit',
    'from streamlit',
    'pyplot',
]

# Forbidden path patterns (workspace paths must not leak into templates)
FORBIDDEN_PATH_PATTERNS = [
    '/Users/',
    'OneDrive-Kearney',
    'kie-v3-v11',
    '/Projects/kie-v3',
]

# No exceptions - matplotlib completely removed
ALLOWED_MATPLOTLIB_LOCATIONS = []


def check_dependencies():
    """Check pyproject.toml for forbidden dependencies."""
    pyproject = Path('pyproject.toml')
    if not pyproject.exists():
        print("❌ pyproject.toml not found")
        return False

    content = pyproject.read_text().lower()
    violations = []

    for dep in FORBIDDEN_DEPS:
        # Check if dependency appears (not in a comment)
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            # Skip comment-only lines
            if line.strip().startswith('#'):
                continue
            if dep in line and not line.strip().startswith('#'):
                violations.append(f"Line {i}: forbidden dependency '{dep}'")

    if violations:
        print(f"❌ pyproject.toml violations:")
        for v in violations:
            print(f"   {v}")
        return False

    print("✅ pyproject.toml: no forbidden dependencies")
    return True


def check_template_content():
    """Check templates for forbidden strings."""
    violations = []

    # Check kie/templates/ and kie/ directories
    check_dirs = [
        Path('kie/templates'),
        Path('kie'),
    ]

    for check_dir in check_dirs:
        if not check_dir.exists():
            continue

        for file_path in check_dir.rglob('*.py'):
            # Read file and filter out comments
            lines = file_path.read_text().lower().splitlines()
            # Remove lines that are pure comments (start with #)
            content_lines = [line for line in lines if not line.strip().startswith('#')]
            content = '\n'.join(content_lines)

            for forbidden in FORBIDDEN_TEMPLATE_STRINGS:
                if forbidden.lower() in content:
                    # Check if this is an allowed exception
                    is_allowed = False
                    for allowed_loc in ALLOWED_MATPLOTLIB_LOCATIONS:
                        if str(file_path) in allowed_loc:
                            is_allowed = True
                            break

                    if not is_allowed:
                        violations.append(f"{file_path}: contains '{forbidden}'")

        for file_path in check_dir.rglob('*.md'):
            content = file_path.read_text().lower()
            for forbidden in FORBIDDEN_TEMPLATE_STRINGS:
                if forbidden.lower() in content:
                    violations.append(f"{file_path}: contains '{forbidden}'")

    if violations:
        print(f"❌ Template content violations:")
        for v in violations:
            print(f"   {v}")
        return False

    print("✅ Templates: no forbidden strings")
    return True


def check_leaked_paths():
    """Check for absolute paths in workspace templates."""
    violations = []

    template_dirs = [
        Path('kie/templates'),
    ]

    for template_dir in template_dirs:
        if not template_dir.exists():
            continue

        for file_path in template_dir.rglob('*'):
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text()
                for pattern in FORBIDDEN_PATH_PATTERNS:
                    if pattern in content:
                        violations.append(f"{file_path}: contains path '{pattern}'")
            except UnicodeDecodeError:
                # Skip binary files
                pass

    if violations:
        print(f"❌ Leaked path violations:")
        for v in violations:
            print(f"   {v}")
        return False

    print("✅ Templates: no leaked absolute paths")
    return True


def main():
    print("=== KIE v3 Invariant Checker ===\n")

    checks = [
        ("Dependencies", check_dependencies),
        ("Template Content", check_template_content),
        ("Leaked Paths", check_leaked_paths),
    ]

    all_passed = True
    for name, check_func in checks:
        try:
            passed = check_func()
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            all_passed = False
        print()

    if all_passed:
        print("✅ All invariant checks passed")
        return 0
    else:
        print("❌ Invariant checks failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
