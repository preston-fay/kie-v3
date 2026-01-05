# KIE Workspace Launcher - Mac Installation Guide

## Overview

The KIE Workspace Launcher is a zero-terminal, Mac-only tool that creates new KIE workspaces without requiring command-line usage or ZIP file extraction.

## Prerequisites (Required)

**IMPORTANT**: Before using the launcher, you must have:

1. **macOS** (tested on macOS 10.14+)
2. **Python 3.11+** installed
3. **KIE v3 installed** by your tech lead or IT

If KIE is not installed, the launcher will show an error dialog and prompt you to contact your tech lead.

**To verify KIE is installed**, open Terminal and run:
```bash
python3 -c "import kie; print(kie.__file__)"
```

If this prints a file path, KIE is installed correctly.

## Installation

### Step 1: Get the Launcher App

**The `Create KIE Workspace.app` file should be provided to you by your tech lead or IT department.**

Do NOT attempt to build the app yourself unless you are a developer.

### Step 2: Install the App

1. Download or copy **Create KIE Workspace.app** to your Mac
2. Move it to your **Applications** folder or **Desktop**
3. (Optional) Drag the app icon to your **Dock** for quick access

### Step 3: First Run Permissions

On first use, macOS will prompt for permissions:

1. **"Create KIE Workspace" wants to access files**
   - Click **OK** to allow file system access
   - This is required to create workspace folders and copy data files

2. **Python execution**
   - If prompted about Python, click **Allow**
   - This is required to run KIE initialization and validation

## Usage

### Creating a Workspace

1. **Double-click** `Create KIE Workspace.app`
2. Follow the prompts:
   - **Choose parent folder**: Select where to create workspace (e.g., `~/Documents`)
   - **Enter project name**: Type your project name (e.g., `acme_q4_analysis`)
   - **Add data file?**: Choose "Choose File" to select CSV/Excel, or "Skip"
3. Wait 10-30 seconds for initialization
4. Your workspace opens in Finder and (if available) Claude Code

### What You'll See

The launcher will:
1. Check that KIE is installed (fail fast if not)
2. Create your workspace folder
3. Initialize workspace structure (data/, outputs/, exports/, project_state/)
4. Copy slash commands to `.claude/commands/`
5. Copy your data file (if you selected one)
6. Validate the workspace setup
7. Open the folder in Finder
8. Try to open Claude Code (falls back to VS Code if unavailable)

### What Gets Created

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
```

## Troubleshooting

### Error: "KIE Not Installed"

**Cause**: KIE is not installed on your machine.

**Solution**: Contact your tech lead or IT department to install KIE before using this launcher.

### Error: "Python Not Found"

**Cause**: Python 3 is not installed on your machine.

**Solution**: Contact your tech lead or IT department to install Python 3.

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
2. Run `/doctor` in Claude Code to see detailed diagnostics
3. Contact your tech lead if issues persist

### No GUI Dialogs Appear

**Cause**: Script is running in background or permissions issue.

**Solution**:
1. Check **System Preferences** > **Security & Privacy** > **Automation**
2. Ensure "Create KIE Workspace" has permissions
3. Try running the app again

### Claude Code Doesn't Open

**Cause**: Claude Code is not installed or not in Applications folder.

**What happens**:
- Launcher will try VS Code as fallback
- If neither is available, only Finder opens
- This is expected behavior - not an error

**To enable Claude Code**:
- Install Claude Code
- Ensure it's named "Claude Code.app" in Applications folder

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Contact your tech lead or KIE support with:
   - macOS version: run `sw_vers` in Terminal
   - Python version: run `python3 --version` in Terminal
   - Error messages from the launcher
   - Screenshot of any error dialogs

## Security Note

This launcher:
- Only accesses folders you explicitly choose
- Does NOT require `sudo` or admin privileges
- Does NOT modify your system or the KIE installation
- Only creates files in the workspace location you select
- Uses standard macOS APIs (osascript, Finder dialogs)

All operations are performed with your user account permissions.

---

## Developer Appendix: Building the Automator App

**This section is for developers and tech leads only. Consultants should use the pre-built .app file.**

### Building from Source

1. Open **Automator** (Applications > Automator)
2. Create a new **Application**
3. Add action: **Run Shell Script**
4. Set shell to: `/bin/zsh`
5. Copy the entire contents of `create_kie_workspace.sh` into the script area
6. Save as: **Create KIE Workspace.app**
7. Distribute the .app file to consultants

### Testing the Script Directly

Developers can test the script without building an app:

```bash
# Navigate to KIE v3 repo
cd /path/to/kie-v3

# Run the launcher script directly
zsh tools/mac_launcher/create_kie_workspace.sh
```

This will show GUI dialogs for all prompts.

### Non-Interactive Mode (For Automated Testing)

```bash
# Set environment variables to skip dialogs
KIE_WORKSPACE_PARENT=/path/to/parent \
KIE_PROJECT_NAME=test_project \
KIE_DATA_FILE=/path/to/data.csv \
zsh tools/mac_launcher/create_kie_workspace.sh
```

Omit `KIE_DATA_FILE` to skip data file copying.

### Dry Run Mode (No Changes)

Test the launcher without creating anything:

```bash
DRY_RUN=1 zsh tools/mac_launcher/create_kie_workspace.sh
```

This will show all commands that would be executed without actually running them.
