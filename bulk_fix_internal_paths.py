#!/usr/bin/env python3
"""Bulk fix test files to use internal/ paths for JSON/YAML artifacts."""

import re
from pathlib import Path

# Common artifacts that belong in internal/
INTERNAL_ARTIFACTS = [
    "eda_synthesis.json",
    "insight_triage.json",
    "visualization_plan.json",
    "visual_storyboard.json",
    "actionability_scores.json",
    "visual_qc.json",
    "story_manifest.json",
    "executive_summary.json",
    "executive_narrative.json",
]

def fix_file(file_path):
    """Fix a single test file."""
    content = file_path.read_text()
    modified = False

    for artifact in INTERNAL_ARTIFACTS:
        # Pattern 1: outputs_dir / "artifact.json"
        old_pattern = rf'\(outputs_dir / "{re.escape(artifact)}"\)'
        new_pattern = rf'(outputs_dir / "internal" / "{artifact}")'
        if old_pattern in content:
            content = re.sub(old_pattern, new_pattern, content)
            modified = True

        # Pattern 2: project_dir / "outputs" / "artifact.json"
        old_pattern = rf'\(project_dir / "outputs" / "{re.escape(artifact)}"\)'
        new_pattern = rf'(project_dir / "outputs" / "internal" / "{artifact}")'
        if old_pattern in content:
            content = re.sub(old_pattern, new_pattern, content)
            modified = True

        # Pattern 3: temp_project / "outputs" / "artifact.json"
        old_pattern = rf'\(temp_project / "outputs" / "{re.escape(artifact)}"\)'
        new_pattern = rf'(temp_project / "outputs" / "internal" / "{artifact}")'
        if old_pattern in content:
            content = re.sub(old_pattern, new_pattern, content)
            modified = True

    if modified:
        # Add mkdir calls where needed
        lines = content.split('\n')
        new_lines = []

        for i, line in enumerate(lines):
            new_lines.append(line)

            # If line writes to internal/ artifacts
            if ('/ "internal" /' in line or '/internal/' in line) and '.write_text' in line:
                # Check if previous line is NOT already a mkdir call
                if i > 0 and 'mkdir' not in lines[i - 1]:
                    if len(new_lines) > 1 and 'mkdir' not in new_lines[-2]:
                        # Add mkdir call before with same indentation
                        indent = len(line) - len(line.lstrip())

                        # Determine which dir variable to use
                        if 'outputs_dir' in line:
                            mkdir_line = ' ' * indent + '(outputs_dir / "internal").mkdir(parents=True, exist_ok=True)'
                        elif 'project_dir' in line:
                            mkdir_line = ' ' * indent + '(project_dir / "outputs" / "internal").mkdir(parents=True, exist_ok=True)'
                        elif 'temp_project' in line:
                            mkdir_line = ' ' * indent + '(temp_project / "outputs" / "internal").mkdir(parents=True, exist_ok=True)'
                        else:
                            continue

                        # Insert before current line
                        new_lines.insert(-1, mkdir_line)

        file_path.write_text('\n'.join(new_lines))
        return True

    return False

def main():
    """Fix all test files."""
    tests_dir = Path("/Users/pfay01/Projects/kie-v3/tests")
    fixed_count = 0

    for test_file in tests_dir.glob("test_*.py"):
        if fix_file(test_file):
            print(f"✅ Fixed {test_file.name}")
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} test files total")

if __name__ == "__main__":
    main()
