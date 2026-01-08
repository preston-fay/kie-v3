"""
railscheck command - verify KIE workspace Rails configuration.

This command checks that the workspace is properly configured for the "Rails" workflow
where slash commands deterministically execute CLI commands.
"""

from pathlib import Path
from typing import Any
import shutil
from .enumerate import enumerate_commands, format_commands_table


class RailsChecker:
    """Check and optionally fix KIE workspace Rails configuration."""

    # No longer hardcode required commands - scan dynamically

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.claude_md = project_root / "CLAUDE.md"
        self.commands_dir = project_root / ".claude" / "commands"
        self.data_dir = project_root / "data"
        self.checks = []
        self.failed = []

    def check(self, fix: bool = False) -> dict[str, Any]:
        """
        Run all Rails checks.

        Args:
            fix: If True, attempt to repair failures

        Returns:
            Results dictionary
        """
        self.checks = []
        self.failed = []

        # Check 1: Is this a KIE workspace?
        self._check_kie_workspace()

        # Check 2: Does .claude/commands/ exist?
        self._check_commands_dir(fix)

        # Check 3: Do required command wrappers exist?
        self._check_command_wrappers(fix)

        # Check 4: Does CLAUDE.md contain Rails mapping table?
        self._check_claude_md()

        # Check 5: Is there data available?
        self._check_data_available()

        passed = len(self.failed) == 0

        return {
            "passed": passed,
            "checks": self.checks,
            "failed": self.failed,
            "fix_applied": fix,
        }

    def _check_kie_workspace(self):
        """Check if this is a KIE workspace."""
        if self.claude_md.exists():
            content = self.claude_md.read_text()
            if "KIE Project" in content or "Kearney Insight Engine" in content:
                self.checks.append(("KIE workspace", "PASS", None))
                return

        self.checks.append(("KIE workspace", "FAIL", "CLAUDE.md missing or invalid"))
        self.failed.append("Not a KIE workspace (CLAUDE.md missing or invalid)")

    def _check_commands_dir(self, fix: bool):
        """Check if .claude/commands/ directory exists."""
        if self.commands_dir.exists():
            self.checks.append((".claude/commands/ exists", "PASS", None))
            return

        if fix:
            self.commands_dir.mkdir(parents=True, exist_ok=True)
            self.checks.append((".claude/commands/ exists", "FIXED", "Created directory"))
        else:
            self.checks.append(
                (
                    ".claude/commands/ exists",
                    "FAIL",
                    "Run with --fix or manually create .claude/commands/",
                )
            )
            self.failed.append(".claude/commands/ directory missing")

    def _check_command_wrappers(self, fix: bool):
        """Check if command wrapper files exist and are valid."""
        if not self.commands_dir.exists():
            self.checks.append(("Command wrappers", "SKIP", ".claude/commands/ missing"))
            return

        # Enumerate all commands
        commands = enumerate_commands(self.commands_dir)

        if not commands:
            self.checks.append(
                (
                    "Command wrappers",
                    "FAIL",
                    "No valid command files found in .claude/commands/",
                )
            )
            self.failed.append("No command wrappers found")
            return

        # Check that wrappers contain CLI invocation
        invalid = []
        for cmd_file in self.commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            if "python3 -m kie.cli" not in content and "PYTHONPATH" not in content:
                invalid.append(cmd_file.name)

        if invalid:
            self.checks.append(
                (
                    f"Command wrappers ({len(commands)} found)",
                    "WARN",
                    f"{len(invalid)} wrappers don't contain CLI invocation: {', '.join(invalid)}",
                )
            )
        else:
            self.checks.append((f"All {len(commands)} command wrappers present", "PASS", None))

    def _fix_missing_commands(self, missing: list[str]) -> list[str]:
        """Copy missing command files from canonical source."""
        # Try to find kie package
        try:
            import kie
            kie_package_dir = Path(kie.__file__).parent
            source_commands = kie_package_dir / "commands" / "slash_commands"

            if source_commands.exists():
                fixed = []
                for cmd_file in missing:
                    source_file = source_commands / cmd_file
                    if source_file.exists():
                        target_file = self.commands_dir / cmd_file
                        shutil.copy(source_file, target_file)
                        fixed.append(cmd_file)
                return fixed
        except (ImportError, AttributeError):
            pass

        return []

    def _check_claude_md(self):
        """Check if CLAUDE.md contains Rails command mapping table."""
        if not self.claude_md.exists():
            self.checks.append(("CLAUDE.md Rails table", "SKIP", "CLAUDE.md not found"))
            return

        content = self.claude_md.read_text()
        if "Rule 4: Execute KIE Commands Correctly" in content and "python3 -m kie.cli" in content:
            self.checks.append(("CLAUDE.md Rails table", "PASS", None))
        else:
            self.checks.append(
                (
                    "CLAUDE.md Rails table",
                    "WARN",
                    "CLAUDE.md may not have Rails command mapping (Rule 4)",
                )
            )
            # This is a warning, not a hard failure

    def _check_data_available(self):
        """Check if there's data available in data/ folder."""
        if not self.data_dir.exists():
            self.checks.append(("Data available", "FAIL", "data/ directory missing"))
            self.failed.append("data/ directory missing")
            return

        csv_files = list(self.data_dir.glob("*.csv"))
        if csv_files:
            self.checks.append(
                (
                    "Data available",
                    "PASS",
                    f"{len(csv_files)} CSV file(s) found",
                )
            )
        else:
            self.checks.append(
                (
                    "Data available",
                    "WARN",
                    "No CSV files in data/ - upload data or use sample_data.csv",
                )
            )


def format_report(result: dict[str, Any]) -> str:
    """Format railscheck results as human-readable report."""
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("KIE RAILS CHECK")
    lines.append("=" * 60)

    for check_name, status, detail in result["checks"]:
        symbol = {
            "PASS": "✓",
            "FAIL": "✗",
            "WARN": "⚠",
            "FIXED": "🔧",
            "SKIP": "○",
        }.get(status, "?")

        line = f"{symbol} {check_name:<40} {status:>6}"
        if detail:
            line += f"\n  └─ {detail}"
        lines.append(line)

    lines.append("=" * 60)

    if result["passed"]:
        lines.append("✓ PASS - Rails configuration is correct")
    else:
        lines.append("✗ FAIL - Rails configuration has issues")
        lines.append("\nFailed checks:")
        for failure in result["failed"]:
            lines.append(f"  • {failure}")

        if not result["fix_applied"]:
            lines.append("\nTo attempt automatic repair, run:")
            lines.append("  python3 -m kie.cli railscheck --fix")

    lines.append("=" * 60)

    # Always show available commands (dynamically enumerated)
    project_root = Path.cwd()  # Assume we're in project root
    commands_dir = project_root / ".claude" / "commands"
    if commands_dir.exists():
        commands = enumerate_commands(commands_dir)
        if commands:
            lines.append("")
            lines.append(format_commands_table(commands))

    lines.append("")

    return "\n".join(lines)


def railscheck_cli(project_root: Path, fix: bool = False) -> int:
    """
    CLI entrypoint for railscheck command.

    Args:
        project_root: Path to project root
        fix: If True, attempt to repair failures

    Returns:
        Exit code (0 = pass, 1 = fail)
    """
    checker = RailsChecker(project_root)
    result = checker.check(fix=fix)
    report = format_report(result)
    print(report)

    return 0 if result["passed"] else 1
