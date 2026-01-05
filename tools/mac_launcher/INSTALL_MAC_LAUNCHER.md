# KIE Workspace Launcher - Mac Installation Guide

## Overview

The KIE Workspace Launcher is a zero-terminal, Mac-only tool that creates new KIE workspaces without requiring command-line usage or ZIP file extraction.

## What It Does

1. Prompts for workspace parent directory
2. Prompts for project name
3. Optionally prompts to select a data file (CSV/Excel)
4. Creates workspace at `<parent>/<project_name>`
5. Runs `python3 -m kie.cli init` to initialize workspace
6. Copies selected data file to `data/` (if provided)
7. Runs `python3 -m kie.cli doctor` to verify setup
8. Opens workspace in Finder
9. Attempts to open in Claude Code (or VS Code if available)

## Prerequisites

- macOS (tested on macOS 10.14+)
- Python 3.11+ installed
- KIE v3 installed: `pip install -e /path/to/kie-v3`

## Installation

### Option 1: Automator Application (Recommended)

1. Open **Automator** (Applications > Automator)
2. Create a new **Application**
3. Add action: **Run Shell Script**
4. Set shell to: `/bin/zsh`
5. Paste the contents of `create_kie_workspace.sh` into the script area
6. Save as: **Create KIE Workspace.app**
7. Move the app to your Applications folder or Desktop
8. (Optional) Add to Dock by dragging the app icon

### Option 2: Direct Script Execution

If you prefer to run the script directly from Terminal:

```bash
# Clone or navigate to KIE v3 repo
cd /path/to/kie-v3

# Run the launcher
zsh tools/mac_launcher/create_kie_workspace.sh
```

This will show GUI dialogs for all prompts.

## Usage

### Using the Automator App

1. Double-click **Create KIE Workspace.app**
2. Follow the prompts:
   - **Choose parent folder**: Select where to create workspace (e.g., `~/Documents`)
   - **Enter project name**: Type project name (e.g., `acme_q4_analysis`)
   - **Add data file?**: Choose "Choose File" to select CSV/Excel, or "Skip"
3. Wait for initialization (10-30 seconds)
4. Workspace opens in Finder and (if available) Claude Code

### First Run Permissions

On first use, macOS will prompt for permissions:

1. **"Create KIE Workspace" wants to access files**
   - Click **OK** to allow file system access
   - This is required to create workspace folders and copy data files

2. **Python execution**
   - If prompted about Python, click **Allow**
   - This is required to run `kie.cli init` and `kie.cli doctor`

## What Gets Created

After successful run, your workspace will contain:

```
<parent>/<project_name>/
├── .claude/
│   └── commands/         # Slash commands (interview, eda, build, etc.)
├── data/                 # Your data files (if provided)
│   └── <your_file.csv>
├── outputs/              # Generated charts, insights
├── exports/              # Final deliverables (dashboards, presentations)
└── project_state/        # Spec, interview state, profiles
    └── .kie_workspace    # Marker file
```

## Troubleshooting

### Error: "Failed to initialize workspace"

**Cause**: KIE v3 is not installed or Python cannot find it.

**Solution**:
```bash
# Verify KIE is installed
python3 -c "import kie; print(kie.__file__)"

# If not found, install KIE v3
cd /path/to/kie-v3
pip install -e .
```

### Error: "Workspace already exists"

**Cause**: A folder with the same project name already exists in the chosen location.

**Solution**:
- Choose a different project name, OR
- Choose a different parent folder, OR
- Delete/rename the existing folder

### Warning: "Doctor check failed"

**Cause**: Workspace was created but verification failed (missing dependencies, etc.)

**What to do**:
1. Open workspace in Claude Code manually
2. Run `python3 -m kie.cli doctor` in Terminal to see detailed errors
3. Fix any missing dependencies
4. Workspace should still be usable for most operations

### No GUI Dialogs Appear

**Cause**: Script is running in background or permissions issue.

**Solution**:
1. Check System Preferences > Security & Privacy > Automation
2. Ensure "Automator" or your app has permissions
3. Try running the script directly from Terminal to see error messages:
   ```bash
   zsh /path/to/create_kie_workspace.sh
   ```

### Claude Code Doesn't Open

**Cause**: Claude Code is not installed or not in Applications folder.

**What happens**:
- Script will silently fall back to VS Code (if available)
- If neither is available, only Finder opens
- This is expected behavior - not an error

**To enable Claude Code**:
- Install Claude Code
- Ensure it's named "Claude Code.app" in Applications folder

## Non-Interactive Mode (For Testing)

Developers and power users can run the launcher non-interactively:

```bash
# Set environment variables to skip dialogs
KIE_WORKSPACE_PARENT=/path/to/parent \
KIE_PROJECT_NAME=test_project \
KIE_DATA_FILE=/path/to/data.csv \
zsh tools/mac_launcher/create_kie_workspace.sh
```

Omit `KIE_DATA_FILE` to skip data file copying.

## Dry Run Mode (No Changes)

Test the launcher without creating anything:

```bash
DRY_RUN=1 zsh tools/mac_launcher/create_kie_workspace.sh
```

This will show all commands that would be executed without actually running them.

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Run `python3 -m kie.cli doctor` in Terminal from your workspace
3. Check KIE logs in `project_state/`
4. Contact KIE support with:
   - macOS version: `sw_vers`
   - Python version: `python3 --version`
   - KIE version: `python3 -c "import kie; print(kie.__version__)"`
   - Error messages from launcher or doctor

## Security Note

This launcher:
- Only accesses folders you explicitly choose
- Does NOT require `sudo` or admin privileges
- Does NOT modify your system or the KIE v3 product repo
- Only creates files in the workspace location you select
- Uses standard macOS APIs (osascript, Finder dialogs)

All operations are performed with your user account permissions.
