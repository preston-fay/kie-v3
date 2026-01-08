"""
Enumerate slash commands by scanning .claude/commands/*.md files.

This is the single source of truth for command enumeration used by:
- Bootstrap script (tools/bootstrap/startkie.sh)
- railscheck command
- Any other tool that needs to list available commands
"""

import re
from pathlib import Path
from typing import List, Dict, Optional


def parse_command_frontmatter(md_path: Path) -> Optional[Dict[str, str]]:
    """Parse YAML frontmatter from a markdown file.

    Returns dict with 'name' and 'description' if valid, else None.
    """
    try:
        content = md_path.read_text()
    except Exception:
        return None

    # Match frontmatter block
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None

    frontmatter = match.group(1)

    # Extract name and description
    name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
    desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)

    if not name_match:
        return None

    return {
        'name': name_match.group(1).strip(),
        'description': desc_match.group(1).strip() if desc_match else ''
    }


def enumerate_commands(commands_dir: Path) -> List[Dict[str, str]]:
    """Scan .claude/commands/*.md and return list of command metadata.

    Returns list of dicts with 'name' and 'description' keys, sorted by name.
    """
    if not commands_dir.exists():
        return []

    commands = []
    for md_file in commands_dir.glob('*.md'):
        cmd_data = parse_command_frontmatter(md_file)
        if cmd_data:
            commands.append(cmd_data)

    return sorted(commands, key=lambda x: x['name'])


def format_commands_table(commands: List[Dict[str, str]]) -> str:
    """Format commands as a table for display.

    Returns multi-line string with header and commands.
    """
    if not commands:
        return "No slash commands found."

    lines = ["AVAILABLE SLASH COMMANDS (case-sensitive, lowercase):", ""]

    for cmd in commands:
        name = f"/{cmd['name']}"
        desc = cmd['description']
        if desc:
            lines.append(f"  {name:15} - {desc}")
        else:
            lines.append(f"  {name}")

    return "\n".join(lines)


if __name__ == "__main__":
    # CLI usage: python3 -m kie.commands.enumerate [commands_dir]
    import sys

    if len(sys.argv) > 1:
        commands_dir = Path(sys.argv[1])
    else:
        commands_dir = Path.cwd() / ".claude" / "commands"

    commands = enumerate_commands(commands_dir)
    print(format_commands_table(commands))
