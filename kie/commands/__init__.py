"""
KIE v3 Command System

Slash command handlers for project management.

Commands:
- /startkie: Bootstrap new KIE project
- /status: Show project status
- /interview: Requirements gathering
- /validate: Quality control checks
- /build: Build deliverables
- /preview: Preview outputs

Usage:
    from kie.commands import CommandHandler

    handler = CommandHandler()

    # Handle commands
    result = handler.handle_startkie()
    status = handler.handle_status()
    interview = handler.handle_interview()
    validation = handler.handle_validate()
"""

from kie.commands.handler import CommandHandler

__all__ = ["CommandHandler"]
