#!/usr/bin/env python3
"""
Verification script for Claude Code user-level commands.

Validates that all required command templates exist and have proper structure.
Runs in CI without requiring Claude Code installation.
"""

import re
import sys
from pathlib import Path


def verify_command_file(cmd_file: Path, cmd_name: str) -> list[str]:
    """
    Verify a single command file structure.

    Args:
        cmd_file: Path to command markdown file
        cmd_name: Expected command name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if not cmd_file.exists():
        return [f"Command file {cmd_name}.md does not exist"]

    content = cmd_file.read_text()

    # Check for frontmatter with name
    if not re.search(r"^---\s*\nname:\s*" + cmd_name, content, re.MULTILINE):
        errors.append(f"{cmd_name}.md: Missing or incorrect frontmatter name")

    # Check for bash fenced block
    if "```bash" not in content:
        errors.append(f"{cmd_name}.md: Missing bash fenced code block")

    # Check for workspace detection (.kie/src check)
    if '.kie/src' not in content:
        errors.append(f"{cmd_name}.md: Missing workspace detection (.kie/src check)")

    # Check for PYTHONPATH invocation
    if 'PYTHONPATH=".kie/src"' not in content:
        errors.append(f"{cmd_name}.md: Missing PYTHONPATH='.kie/src' setup")

    # Check for python -m kie.cli invocation
    if 'python3 -m kie.cli' not in content and 'python -m kie.cli' not in content:
        errors.append(f"{cmd_name}.md: Missing python -m kie.cli invocation")

    return errors


def verify_all_commands() -> int:
    """
    Verify all required command templates exist and are valid.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Find source directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    source_dir = repo_root / "tools" / "claude_user_commands"

    if not source_dir.exists():
        print(f"❌ Error: Command source directory not found: {source_dir}")
        return 1

    # Required commands (excluding startkie which is user-managed)
    required_commands = [
        "eda", "rails", "go", "spec", "status",
        "interview", "analyze", "build", "preview",
        "validate", "map", "doctor"
    ]

    print(f"Verifying {len(required_commands)} command templates...")
    print()

    all_errors = []
    for cmd_name in required_commands:
        cmd_file = source_dir / f"{cmd_name}.md"
        errors = verify_command_file(cmd_file, cmd_name)

        if errors:
            all_errors.extend(errors)
            print(f"❌ {cmd_name}.md: {len(errors)} error(s)")
            for error in errors:
                print(f"   - {error}")
        else:
            print(f"✓ {cmd_name}.md")

    print()

    if all_errors:
        print(f"❌ FAILED: {len(all_errors)} validation error(s)")
        return 1
    else:
        print(f"✅ PASSED: All {len(required_commands)} command templates are valid")
        return 0


def test_simulated_install() -> int:
    """
    Simulate installation to a temp directory and verify files are copied correctly.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import tempfile
    import shutil
    from datetime import datetime

    print()
    print("Testing simulated installation...")

    # Find source directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    source_dir = repo_root / "tools" / "claude_user_commands"

    if not source_dir.exists():
        print(f"❌ Error: Source directory not found: {source_dir}")
        return 1

    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        user_commands_dir = temp_path / ".claude" / "commands"
        user_commands_dir.mkdir(parents=True, exist_ok=True)

        # Simulate installation (copy with headers)
        installed_count = 0
        for cmd_file in source_dir.glob("*.md"):
            if cmd_file.name == "startkie.md":
                continue  # Skip startkie

            content = cmd_file.read_text()

            # Add header
            header = f"""<!--
installed_from_repo: preston-fay/kie-v3
installed_at: {datetime.now().isoformat()}
source_commit: test
-->

"""
            dest_file = user_commands_dir / cmd_file.name
            dest_file.write_text(header + content)
            installed_count += 1

        print(f"✓ Simulated installation of {installed_count} files to {user_commands_dir}")

        # Verify files exist and have headers
        for cmd_file in source_dir.glob("*.md"):
            if cmd_file.name == "startkie.md":
                continue

            dest_file = user_commands_dir / cmd_file.name
            if not dest_file.exists():
                print(f"❌ File not copied: {cmd_file.name}")
                return 1

            content = dest_file.read_text()
            if "installed_from_repo: preston-fay/kie-v3" not in content:
                print(f"❌ Missing header in {cmd_file.name}")
                return 1

        print(f"✓ All installed files have correct headers")

    print()
    print("✅ Simulated installation test passed")
    return 0


def main() -> int:
    """Main entry point."""
    print("=" * 70)
    print("KIE Claude User Commands Verification")
    print("=" * 70)
    print()

    # Run verification
    result = verify_all_commands()
    if result != 0:
        return result

    # Run simulated install test
    result = test_simulated_install()
    if result != 0:
        return result

    print()
    print("=" * 70)
    print("✅ ALL CHECKS PASSED")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
