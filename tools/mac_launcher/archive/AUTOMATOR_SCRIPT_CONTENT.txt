#!/bin/zsh
# Automator Wrapper for KIE Workspace Launcher
# This wrapper finds the bundled script inside the .app and executes it

# Find the app bundle's Resources directory
# When run from Automator, we need to locate the .app bundle
APP_BUNDLE_RESOURCES=""

# Method 1: Check if we're being run from within an app bundle
if [[ "$0" == *"/Contents/MacOS/"* ]] || [[ "$0" == *"/Contents/Resources/"* ]]; then
    # Extract the .app path
    APP_PATH="${0%%/Contents/*}"
    APP_BUNDLE_RESOURCES="$APP_PATH/Contents/Resources"
elif [[ -n "$BASH_SOURCE" ]] && [[ "$BASH_SOURCE" == *"/Contents/"* ]]; then
    APP_PATH="${BASH_SOURCE%%/Contents/*}"
    APP_BUNDLE_RESOURCES="$APP_PATH/Contents/Resources"
fi

# If we couldn't determine the app bundle location, try relative to script location
if [[ -z "$APP_BUNDLE_RESOURCES" ]] || [[ ! -d "$APP_BUNDLE_RESOURCES" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    # Check if we're in a typical Automator app structure
    if [[ -d "$SCRIPT_DIR/../../Resources" ]]; then
        APP_BUNDLE_RESOURCES="$SCRIPT_DIR/../../Resources"
    elif [[ -d "$SCRIPT_DIR/../Resources" ]]; then
        APP_BUNDLE_RESOURCES="$SCRIPT_DIR/../Resources"
    else
        APP_BUNDLE_RESOURCES="$SCRIPT_DIR"
    fi
fi

# Path to the bundled launcher script
LAUNCHER_SCRIPT="$APP_BUNDLE_RESOURCES/create_kie_workspace.sh"

# Verify the script exists
if [[ ! -f "$LAUNCHER_SCRIPT" ]]; then
    osascript -e 'display dialog "ERROR: Launcher script not found.\n\nThe app bundle is incomplete. Please ensure create_kie_workspace.sh is copied to:\n\nCreate KIE Workspace.app/Contents/Resources/\n\nContact your tech lead for a properly built version." with title "Missing Script" with icon stop buttons {"OK"} default button "OK"'
    exit 1
fi

# Verify the script is executable
if [[ ! -x "$LAUNCHER_SCRIPT" ]]; then
    chmod +x "$LAUNCHER_SCRIPT"
fi

# Execute the bundled launcher script
exec "$LAUNCHER_SCRIPT" "$@"
