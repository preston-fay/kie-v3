#!/usr/bin/env python3
"""
Remove redundant outputs_dir.mkdir() calls after internal_dir.mkdir(parents=True).
"""
from pathlib import Path

def fix_file(filepath: Path):
    """Remove redundant mkdir calls."""
    lines = filepath.read_text().splitlines(keepends=True)
    modified = False
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line has internal_dir.mkdir with parents=True
        if 'internal_dir.mkdir(parents=True' in line:
            new_lines.append(line)
            # Check if next line is outputs_dir.mkdir()
            if i + 1 < len(lines) and 'outputs_dir.mkdir()' in lines[i + 1]:
                # Skip the redundant line
                i += 2
                modified = True
                continue

        new_lines.append(line)
        i += 1

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
