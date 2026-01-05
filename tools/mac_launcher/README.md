# KIE Workspace Launcher for macOS

Zero-terminal workspace creation for consultants. Replaces the ZIP workflow with a native Mac app experience.

## Quick Start

**For Consultants:**
1. See [INSTALL_MAC_LAUNCHER.md](INSTALL_MAC_LAUNCHER.md) for setup instructions
2. Double-click "Create KIE Workspace.app"
3. Follow prompts to create workspace

**For Developers:**
```bash
# Test the script
DRY_RUN=1 zsh create_kie_workspace.sh

# Non-interactive test
KIE_WORKSPACE_PARENT=/tmp \
KIE_PROJECT_NAME=test_workspace \
zsh create_kie_workspace.sh
```

## Files

- `create_kie_workspace.sh` - Main launcher script
- `INSTALL_MAC_LAUNCHER.md` - Consultant installation guide
- `Create KIE Workspace.app` - Automator application (build from script)

## Architecture

The launcher is a thin wrapper that:
1. Uses macOS `osascript` for native GUI dialogs
2. Calls `python3 -m kie.cli init` (single source of truth)
3. Validates with `python3 -m kie.cli doctor`
4. Opens workspace in Finder + Claude Code

**Zero new dependencies** - Uses only macOS built-ins and existing KIE CLI.

## Building the Automator App

1. Open Automator
2. New > Application
3. Add "Run Shell Script" action
4. Set shell: `/bin/zsh`
5. Paste contents of `create_kie_workspace.sh`
6. Save as "Create KIE Workspace.app"

Distribute the `.app` to consultants.
