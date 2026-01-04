"""
KIE workspace initialization and management.
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files  # Python < 3.9 fallback


def initialize_workspace(target_dir: Path) -> Tuple[bool, str]:
    """
    Initialize a KIE workspace in the target directory.

    Creates:
    - Workspace folders (data/, outputs/, exports/, project_state/)
    - Project files (README.md, CLAUDE.md, .gitignore)
    - Slash commands (.claude/commands/*.md)

    Args:
        target_dir: Directory to initialize as a KIE workspace

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        target_dir = target_dir.resolve()

        # Check if this is the product repo (FORBIDDEN)
        if (target_dir / '.kie_product_repo').exists():
            return False, """
❌ CANNOT INITIALIZE: This is the KIE v3 product repository.

Do NOT run client work or workspace commands here.

To start a client project:
1. Create a new folder: mkdir ~/my-project
2. Open it in Claude Code
3. Run /startkie

The product repo is for KIE development only.
"""

        # Check for other product repo indicators
        if ((target_dir / 'pyproject.toml').exists() and
            (target_dir / 'kie' / '__init__.py').exists() and
            not (target_dir / 'project_state').exists()):
            return False, """
❌ CANNOT INITIALIZE: This appears to be the KIE v3 product repository.

Workspace initialization is not allowed in the product codebase.

Create a separate folder for client projects and run /startkie there.
"""

        # Create workspace folders
        folders = ['data', 'outputs', 'exports', 'project_state']
        for folder in folders:
            folder_path = target_dir / folder
            folder_path.mkdir(exist_ok=True)
            # Create .gitkeep to preserve empty folders in git
            (folder_path / '.gitkeep').touch(exist_ok=True)

        # Copy project template files
        template_source = files('kie.templates.project_template')

        # Copy README.md
        readme_content = template_source.joinpath('README.md').read_text()
        (target_dir / 'README.md').write_text(readme_content)

        # Copy CLAUDE.md
        claude_content = template_source.joinpath('CLAUDE.md').read_text()
        (target_dir / 'CLAUDE.md').write_text(claude_content)

        # Copy .gitignore (stored as gitignore.txt to avoid git issues)
        gitignore_content = template_source.joinpath('gitignore.txt').read_text()
        (target_dir / '.gitignore').write_text(gitignore_content)

        # Create .claude/commands directory
        commands_dir = target_dir / '.claude' / 'commands'
        commands_dir.mkdir(parents=True, exist_ok=True)

        # Copy all slash commands
        commands_source = files('kie.templates.commands')
        command_files = ['interview.md', 'build.md', 'review.md', 'startkie.md']

        for cmd_file in command_files:
            cmd_content = commands_source.joinpath(cmd_file).read_text()
            (commands_dir / cmd_file).write_text(cmd_content)

        # Write workspace marker
        import kie
        workspace_marker = {
            "workspace_version": 1,
            "kie_version": kie.__version__,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "workspace_type": "kie_project"
        }
        marker_path = target_dir / 'project_state' / '.kie_workspace'
        with open(marker_path, 'w') as f:
            json.dump(workspace_marker, f, indent=2)

        # Verify critical files exist
        verification_failures = []

        critical_files = [
            commands_dir / 'interview.md',
            commands_dir / 'build.md',
            target_dir / 'CLAUDE.md',
            target_dir / 'README.md',
        ]

        for critical_file in critical_files:
            if not critical_file.exists():
                verification_failures.append(str(critical_file.relative_to(target_dir)))

        if verification_failures:
            return False, f"Verification failed - missing files: {', '.join(verification_failures)}"

        # Verify importability
        try:
            import kie
            _ = kie.__version__
        except ImportError as e:
            return False, f"Verification failed - cannot import kie: {e}"

        success_msg = f"""
KIE workspace initialized successfully in {target_dir}

Created:
  ✓ Workspace folders (data/, outputs/, exports/, project_state/)
  ✓ Project files (README.md, CLAUDE.md, .gitignore)
  ✓ Slash commands (.claude/commands/*.md)

Verified:
  ✓ All critical files present
  ✓ Python package importable

Next steps:
  1. Drop your data file into data/
  2. Run /interview to start a project
  3. Run /build to create deliverables
"""

        return True, success_msg

    except Exception as e:
        return False, f"Initialization failed: {e}"


def diagnose_workspace(target_dir: Path) -> Tuple[bool, str]:
    """
    Diagnose a KIE workspace and report issues.

    Args:
        target_dir: Directory to diagnose

    Returns:
        Tuple of (all_passed: bool, report: str)
    """
    target_dir = target_dir.resolve()

    checks = []
    all_passed = True

    # CRITICAL: Check if this is the product repo
    if (target_dir / '.kie_product_repo').exists():
        return False, """
❌ PRODUCT REPO DETECTED

You are in the KIE v3 product repository.
Do NOT run workspace commands or client work here.

This is for KIE development only.

To work on a client project:
1. Create a new folder outside this repo
2. Open it in Claude Code
3. Run /startkie

Current directory: {target_dir}
""".format(target_dir=target_dir)

    # Check for workspace marker
    workspace_marker = target_dir / 'project_state' / '.kie_workspace'
    if not workspace_marker.exists():
        checks.append("✗ Workspace marker missing (not initialized)")
        all_passed = False
    else:
        checks.append("✓ Workspace marker present")
        try:
            with open(workspace_marker) as f:
                marker_data = json.load(f)
                checks.append(f"  Version: {marker_data.get('workspace_version', 'unknown')}")
                checks.append(f"  KIE version: {marker_data.get('kie_version', 'unknown')}")
        except Exception:
            checks.append("  ⚠ Warning: Could not read marker file")

    # Check required folders
    required_folders = ['data', 'outputs', 'exports', 'project_state']
    for folder in required_folders:
        folder_path = target_dir / folder
        if folder_path.exists() and folder_path.is_dir():
            checks.append(f"✓ Folder {folder}/ exists")
        else:
            checks.append(f"✗ Folder {folder}/ missing")
            all_passed = False

    # Check .claude/commands
    commands_dir = target_dir / '.claude' / 'commands'
    if commands_dir.exists() and commands_dir.is_dir():
        checks.append("✓ .claude/commands/ exists")

        # Check for command files
        command_files = list(commands_dir.glob('*.md'))
        if len(command_files) >= 2:
            checks.append(f"✓ Found {len(command_files)} command files")
        else:
            checks.append(f"✗ Only {len(command_files)} command files found (need at least 2)")
            all_passed = False

        # Check critical commands
        critical_commands = ['interview.md', 'build.md']
        for cmd in critical_commands:
            if (commands_dir / cmd).exists():
                checks.append(f"  ✓ {cmd}")
            else:
                checks.append(f"  ✗ {cmd} missing")
                all_passed = False
    else:
        checks.append("✗ .claude/commands/ missing")
        all_passed = False

    # Check project files
    if (target_dir / 'CLAUDE.md').exists():
        checks.append("✓ CLAUDE.md exists")
    else:
        checks.append("✗ CLAUDE.md missing")
        all_passed = False

    if (target_dir / 'README.md').exists():
        checks.append("✓ README.md exists")
    else:
        checks.append("✗ README.md missing")
        all_passed = False

    # Check spec.yaml (warning only)
    if (target_dir / 'project_state' / 'spec.yaml').exists():
        checks.append("✓ project_state/spec.yaml exists")
    else:
        checks.append("⚠ project_state/spec.yaml not found (run /interview to create)")

    # Check Python package
    try:
        import kie
        version = kie.__version__
        checks.append(f"✓ KIE package importable (v{version})")
    except ImportError as e:
        checks.append(f"✗ Cannot import kie: {e}")
        all_passed = False

    # Build report
    status = "PASS" if all_passed else "FAIL"
    report = f"""
KIE Workspace Diagnostic - {status}

Checks:
{chr(10).join(checks)}
"""

    if not all_passed:
        report += """
Remediation:
  Run: python -m kie.cli init
  Or reinstall KIE: pip install -e /path/to/kie-v3
"""

    return all_passed, report


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m kie.cli <command>")
        print("\nCommands:")
        print("  init    - Initialize a KIE workspace")
        print("  doctor  - Diagnose workspace issues")
        sys.exit(1)

    command = sys.argv[1]
    target_dir = Path.cwd()

    if command == 'init':
        success, message = initialize_workspace(target_dir)
        print(message)
        sys.exit(0 if success else 1)

    elif command == 'doctor':
        all_passed, report = diagnose_workspace(target_dir)
        print(report)
        sys.exit(0 if all_passed else 1)

    else:
        print(f"Unknown command: {command}")
        print("\nAvailable commands: init, doctor")
        sys.exit(1)


if __name__ == '__main__':
    main()
