# KIE Workspace Launcher for macOS

Zero-terminal workspace creation for consultants. Replaces the ZIP workflow with a native Mac app experience.

## For Consultants

**You should receive a pre-built `Create KIE Workspace.app` from your tech lead.**

See [INSTALL_MAC_LAUNCHER.md](INSTALL_MAC_LAUNCHER.md) for complete installation and usage instructions.

### Quick Start

1. Get `Create KIE Workspace.app` from your tech lead
2. Move it to Applications or Desktop
3. Double-click to create a new workspace
4. Follow the GUI prompts

**Prerequisites**: KIE must be installed by your tech lead before using the launcher.

## For Developers and Tech Leads

### Quick Test

```bash
# Test the script (shows GUI dialogs)
cd /path/to/kie-v3
zsh tools/mac_launcher/create_kie_workspace.sh

# Non-interactive test (no GUI)
KIE_WORKSPACE_PARENT=/tmp \
KIE_PROJECT_NAME=test_workspace \
zsh tools/mac_launcher/create_kie_workspace.sh

# Dry run (no changes)
DRY_RUN=1 zsh tools/mac_launcher/create_kie_workspace.sh
```

### Building the Automator App

1. Open **Automator** (Applications > Automator)
2. Create new **Application**
3. Add "Run Shell Script" action (shell: `/bin/zsh`)
4. Paste entire contents of `create_kie_workspace.sh`
5. Save as **Create KIE Workspace.app**
6. Distribute the .app to consultants

### Files

- `create_kie_workspace.sh` - Main launcher script (executable)
- `INSTALL_MAC_LAUNCHER.md` - Complete consultant guide
- `README.md` - This file (developer/overview)

## Architecture

The launcher is a thin wrapper that:

1. **Checks prerequisites** (Python 3, KIE installed) - fails fast if missing
2. Uses macOS `osascript` for native GUI dialogs
3. Calls `handle_startkie()` via Python API (single source of truth)
4. Validates with `python3 -m kie.cli doctor`
5. Opens workspace in Finder + Claude Code

**Zero new dependencies** - Uses only macOS built-ins and existing KIE CLI.

## Design Principles

- **Mac-only** (uses osascript, Finder, open commands)
- **Thin wrapper** (calls existing KIE logic, no duplication)
- **Fail fast** (checks prerequisites before any folder creation)
- **Graceful degradation** (skips editor open if unavailable)
- **Consultant-friendly** (.app distribution, no terminal usage)

## Distribution Model

1. **Developer/Tech Lead**: Builds .app from script using Automator
2. **Consultant**: Receives pre-built .app, double-clicks to use
3. **No self-service building** - consultants should NOT build their own apps

This ensures consistent behavior and reduces support burden.
