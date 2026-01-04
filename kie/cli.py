"""
KIE v3 Command Line Interface

Interactive REPL for KIE commands.
"""

import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from kie.commands.handler import CommandHandler


class KIEClient:
    """Interactive KIE command-line client."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize KIE client.

        Args:
            project_root: Project root directory (default: current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.handler = CommandHandler(project_root=self.project_root)

        if HAS_RICH:
            self.console = Console()
        else:
            self.console = None

    def print_welcome(self):
        """Print welcome message."""
        # Try to read from CLAUDE.md if available
        claude_md = self.project_root / "CLAUDE.md"

        if HAS_RICH and self.console:
            welcome_text = """# Welcome to KIE v3

**Kearney Insight Engine** - AI-powered consulting delivery platform

## Available Commands:
- `/startkie` - Bootstrap new KIE project
- `/status` - Show project status
- `/spec` - View current specification
- `/interview` - Start requirements gathering
- `/eda` - Run exploratory data analysis
- `/analyze` - Extract insights from data
- `/map` - Create geographic visualizations
- `/validate` - Run quality checks
- `/build [target]` - Build deliverables (all, presentation, dashboard)
- `/preview` - Preview outputs
- `/doctor` - Check workspace health and detect package collisions
- `/help` - Show this help
- `/quit` or `/exit` - Exit KIE

Type a command to get started!
"""
            self.console.print(Panel(Markdown(welcome_text), title="KIE v3", border_style="purple"))
        else:
            print("=" * 60)
            print("Welcome to KIE v3")
            print("Kearney Insight Engine - AI-powered consulting delivery")
            print("=" * 60)
            print("\nAvailable Commands:")
            print("  /startkie      - Bootstrap new KIE project")
            print("  /status        - Show project status")
            print("  /spec          - View current specification")
            print("  /interview     - Start requirements gathering")
            print("  /eda           - Run exploratory data analysis")
            print("  /analyze       - Extract insights from data")
            print("  /map           - Create geographic visualizations")
            print("  /validate      - Run quality checks")
            print("  /build [target]- Build deliverables")
            print("  /preview       - Preview outputs")
            print("  /doctor        - Check workspace health")
            print("  /help          - Show this help")
            print("  /quit or /exit - Exit KIE")
            print()

    def print_result(self, result: dict):
        """
        Print command result with rich formatting if available.

        Args:
            result: Result dictionary from handler
        """
        if not HAS_RICH or not self.console:
            # Fallback to standard print
            import json
            from datetime import datetime, date

            # Custom JSON encoder for datetime objects
            def datetime_handler(obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            print(json.dumps(result, indent=2, default=datetime_handler))
            return

        # Rich formatting
        if isinstance(result, dict):
            # Check for success/failure
            if result.get("success") is False:
                self.console.print(f"[red]✗ {result.get('message', 'Command failed')}[/red]")
                if result.get("hint"):
                    self.console.print(f"[yellow]Hint: {result['hint']}[/yellow]")
                return
            elif result.get("success") is True:
                self.console.print(f"[green]✓ {result.get('message', 'Success')}[/green]")

            # Print structured data
            table = Table(show_header=True, header_style="bold purple")
            table.add_column("Key", style="cyan")
            table.add_column("Value")

            for key, value in result.items():
                if key not in ["success", "message"]:
                    if isinstance(value, (list, dict)):
                        import json
                        from datetime import datetime, date

                        # Custom JSON encoder for datetime objects
                        def datetime_handler(obj):
                            if isinstance(obj, (datetime, date)):
                                return obj.isoformat()
                            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

                        value_str = json.dumps(value, indent=2, default=datetime_handler)
                    else:
                        value_str = str(value)
                    table.add_row(key, value_str)

            if table.row_count > 0:
                self.console.print(table)

    def process_command(self, command: str) -> bool:
        """
        Process a command.

        Args:
            command: Command string

        Returns:
            True to continue, False to exit
        """
        command = command.strip()

        if not command:
            return True

        # Parse command and arguments
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else None

        # Handle exit commands
        if cmd in ["/quit", "/exit", "quit", "exit"]:
            if HAS_RICH and self.console:
                self.console.print("[purple]Goodbye![/purple]")
            else:
                print("Goodbye!")
            return False

        # Handle help
        if cmd in ["/help", "help"]:
            self.print_welcome()
            return True

        # Dispatch to handler
        try:
            if cmd == "/startkie":
                result = self.handler.handle_startkie()
            elif cmd == "/status":
                result = self.handler.handle_status()
            elif cmd == "/spec":
                result = self.handler.handle_spec()
            elif cmd == "/interview":
                result = self.handler.handle_interview()
            elif cmd == "/eda":
                result = self.handler.handle_eda()
            elif cmd == "/analyze":
                result = self.handler.handle_analyze()
            elif cmd == "/map":
                result = self.handler.handle_map()
            elif cmd == "/validate":
                result = self.handler.handle_validate()
            elif cmd == "/build":
                target = args or "all"
                result = self.handler.handle_build(target=target)
            elif cmd == "/preview":
                result = self.handler.handle_preview()
            elif cmd == "/doctor":
                result = self.handler.handle_doctor()
            elif cmd == "/template":
                result = self.handler.handle_template()
            else:
                result = {
                    "success": False,
                    "message": f"Unknown command: {cmd}",
                    "hint": "Type /help to see available commands"
                }

            self.print_result(result)

        except KeyboardInterrupt:
            if HAS_RICH and self.console:
                self.console.print("\n[yellow]Command interrupted[/yellow]")
            else:
                print("\nCommand interrupted")
        except Exception as e:
            if HAS_RICH and self.console:
                self.console.print(f"[red]Error: {str(e)}[/red]")
            else:
                print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

        return True

    def start(self):
        """Start the interactive REPL."""
        self.print_welcome()

        try:
            while True:
                try:
                    # Read input
                    if HAS_RICH and self.console:
                        command = self.console.input("[purple](kie)[/purple] > ")
                    else:
                        command = input("(kie) > ")

                    # Process command
                    should_continue = self.process_command(command)
                    if not should_continue:
                        break

                except KeyboardInterrupt:
                    if HAS_RICH and self.console:
                        self.console.print("\n[yellow]Use /quit to exit[/yellow]")
                    else:
                        print("\nUse /quit to exit")
                    continue
                except EOFError:
                    # Handle Ctrl+D
                    break

        except Exception as e:
            print(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point for kie CLI."""
    # Check for command-line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        # Handle help/version flags
        if arg in ["-h", "--help"]:
            print("Usage: kie [command | project_directory]")
            print("\nOne-shot command execution:")
            print("  kie status       - Show project status and exit")
            print("  kie eda          - Run EDA and exit")
            print("  kie analyze      - Run analysis and exit")
            print("  kie doctor       - Check workspace health and exit")
            print("  ... (any KIE command)")
            print("\nInteractive mode:")
            print("  kie              - Start REPL in current directory")
            print("  kie <directory>  - Start REPL in specified directory")
            sys.exit(0)
        elif arg in ["-v", "--version"]:
            from kie import __version__
            print(f"KIE v{__version__}")
            sys.exit(0)

        # Check if it's a known command (without slash prefix for CLI)
        known_commands = ["startkie", "status", "spec", "interview", "eda",
                        "analyze", "map", "validate", "build", "preview", "doctor", "template", "help"]

        if arg in known_commands:
            # It's a command - execute and exit
            client = KIEClient(project_root=Path.cwd())

            # Special handling for template command with --out flag
            if arg == "template" and len(sys.argv) > 2:
                if sys.argv[2] == "--out" and len(sys.argv) > 3:
                    output_path = Path(sys.argv[3])
                    result = client.handler.handle_template(output_path=output_path)
                    client.print_result(result)
                    sys.exit(0 if result["success"] else 1)

            # Add slash prefix for internal process_command (REPL compatibility)
            client.process_command(f"/{arg}")
            sys.exit(0)
        elif arg.startswith("/"):
            # Reject slash-prefixed commands in CLI
            print(f"Error: Invalid command format '{arg}'")
            print(f"Use 'kie {arg[1:]}' instead (without the slash)")
            print("Slash commands (/command) are only for Claude Code slash commands,")
            print("not terminal CLI usage.")
            sys.exit(1)
        else:
            # Treat as directory path for interactive mode
            project_root = Path(arg).resolve()
            if not project_root.exists():
                print(f"Error: Directory does not exist: {project_root}")
                sys.exit(1)
            client = KIEClient(project_root=project_root)
    else:
        # Use current directory for interactive mode
        client = KIEClient()

    # Start REPL
    client.start()


if __name__ == "__main__":
    main()
