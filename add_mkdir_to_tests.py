#!/usr/bin/env python3
"""
Add internal_dir.mkdir() calls after internal_dir definitions in tests.
"""
from pathlib import Path
import re

def fix_file(filepath: Path):
    """Add mkdir calls after internal_dir definitions."""
    lines = filepath.read_text().splitlines(keepends=True)
    modified = False
    new_lines = []

    for i, line in enumerate(lines):
        new_lines.append(line)

        # If this line defines internal_dir
        if 'internal_dir = outputs_dir / "internal"' in line or 'internal_dir = ' in line and '/ "internal"' in line:
            # Check if the next line already has mkdir
            if i + 1 < len(lines) and 'internal_dir.mkdir' not in lines[i + 1]:
                # Get indentation
                indent = len(line) - len(line.lstrip())
                mkdir_line = ' ' * indent + 'internal_dir.mkdir(parents=True, exist_ok=True)\n'
                new_lines.append(mkdir_line)
                modified = True

    if modified:
        filepath.write_text(''.join(new_lines))
        return True
    return False

# Find all test files
test_dir = Path("tests")
fixed_count = 0

for test_file in test_dir.rglob("*.py"):
    if fix_file(test_file):
        fixed_count += 1
        print(f"Fixed: {test_file}")

print(f"\nTotal files fixed: {fixed_count}")
