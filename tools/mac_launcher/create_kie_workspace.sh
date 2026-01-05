#!/bin/zsh
# Create KIE Workspace Launcher for macOS
# Zero-terminal workspace creation for consultants
# Wraps: python3 -m kie.cli init

set -e

# ============================================================
# Configuration
# ============================================================

DRY_RUN="${DRY_RUN:-0}"
KIE_WORKSPACE_PARENT="${KIE_WORKSPACE_PARENT:-}"
KIE_PROJECT_NAME="${KIE_PROJECT_NAME:-}"
KIE_DATA_FILE="${KIE_DATA_FILE:-}"
KIE_OPEN_EDITOR="${KIE_OPEN_EDITOR:-none}"  # none, finder, vscode

# ============================================================
# Helper Functions
# ============================================================

log() {
    echo "[KIE Launcher] $*"
}

show_dialog() {
    local title="$1"
    local message="$2"
    local icon="${3:-note}"  # note, caution, stop

    if [[ "$DRY_RUN" == "1" ]]; then
        log "DIALOG: $title - $message"
        return
    fi

    # Skip dialogs in non-interactive mode
    if [[ -n "$KIE_WORKSPACE_PARENT" && -n "$KIE_PROJECT_NAME" ]]; then
        log "DIALOG: $title - $message"
        return
    fi

    osascript -e "display dialog \"$message\" with title \"$title\" with icon $icon buttons {\"OK\"} default button \"OK\""
}

show_error() {
    local title="$1"
    local message="$2"

    if [[ "$DRY_RUN" == "1" ]]; then
        log "ERROR: $title - $message"
        return
    fi

    # Skip dialogs in non-interactive mode
    if [[ -n "$KIE_WORKSPACE_PARENT" && -n "$KIE_PROJECT_NAME" ]]; then
        log "ERROR: $title - $message"
        return
    fi

    osascript -e "display dialog \"$message\" with title \"$title\" with icon stop buttons {\"OK\"} default button \"OK\""
}

choose_folder() {
    if [[ -n "$KIE_WORKSPACE_PARENT" ]]; then
        echo "$KIE_WORKSPACE_PARENT"
        return
    fi

    if [[ "$DRY_RUN" == "1" ]]; then
        echo "/tmp/dry_run_workspace_parent"
        return
    fi

    local result
    result=$(osascript -e 'tell application "Finder"
        set folderPath to choose folder with prompt "Choose parent folder for new workspace:"
        return POSIX path of folderPath
    end tell' 2>/dev/null)

    echo "$result"
}

prompt_text() {
    local prompt="$1"
    local default_value="${2:-}"

    if [[ -n "$KIE_PROJECT_NAME" ]]; then
        echo "$KIE_PROJECT_NAME"
        return
    fi

    if [[ "$DRY_RUN" == "1" ]]; then
        echo "dry_run_project"
        return
    fi

    local result
    result=$(osascript -e "display dialog \"$prompt\" default answer \"$default_value\" buttons {\"Cancel\", \"OK\"} default button \"OK\"" -e 'text returned of result' 2>/dev/null)

    echo "$result"
}

choose_file() {
    # Non-interactive mode: use env var if set
    if [[ -n "$KIE_DATA_FILE" ]]; then
        if [[ -f "$KIE_DATA_FILE" ]]; then
            echo "$KIE_DATA_FILE"
        else
            echo ""
        fi
        return
    fi

    # Non-interactive mode without file: skip
    if [[ -n "$KIE_WORKSPACE_PARENT" && -n "$KIE_PROJECT_NAME" ]]; then
        echo ""  # No file in non-interactive mode without KIE_DATA_FILE
        return
    fi

    if [[ "$DRY_RUN" == "1" ]]; then
        echo ""  # No file in dry run
        return
    fi

    # Ask if user wants to add a data file
    local add_data
    add_data=$(osascript -e 'display dialog "Add a data file to your workspace?" buttons {"Skip", "Choose File"} default button "Choose File"' -e 'button returned of result' 2>/dev/null || echo "Skip")

    if [[ "$add_data" == "Skip" ]]; then
        echo ""
        return
    fi

    # Choose CSV or Excel file
    local result
    result=$(osascript -e 'tell application "Finder"
        set dataFile to choose file with prompt "Choose data file (CSV or Excel):" of type {"public.comma-separated-values-text", "org.openxmlformats.spreadsheetml.sheet", "com.microsoft.excel.xls"}
        return POSIX path of dataFile
    end tell' 2>/dev/null || echo "")

    echo "$result"
}

# ============================================================
# Prerequisite Checks
# ============================================================

check_prerequisites() {
    log "Checking prerequisites..."

    # Check 1: python3 must exist
    if ! command -v python3 &>/dev/null; then
        show_error "Python Not Found" "Python 3 is not installed on this machine.\n\nPlease contact your tech lead or IT to install Python 3 before using this launcher."
        exit 1
    fi

    log "✓ Python 3 found: $(command -v python3)"

    # Check 2: KIE module must be importable
    local kie_check_output
    local kie_check_exit_code=0

    kie_check_output=$(python3 -c "import kie; print(kie.__file__)" 2>&1) || kie_check_exit_code=$?

    if [[ "$kie_check_exit_code" != "0" ]]; then
        show_error "KIE Not Installed" "KIE is not installed on this machine.\n\nPlease contact your tech lead or IT to install KIE before using this launcher.\n\nError: $kie_check_output"
        exit 1
    fi

    log "✓ KIE installed at: $kie_check_output"
}

# ============================================================
# Main Launcher Logic
# ============================================================

main() {
    log "Starting KIE Workspace Launcher..."

    # Run prerequisite checks first
    check_prerequisites

    # Step 1: Choose parent directory
    log "Step 1: Choose parent directory"
    PARENT_DIR=$(choose_folder)

    if [[ -z "$PARENT_DIR" ]]; then
        show_error "Error" "No parent directory selected. Exiting."
        exit 1
    fi

    # Remove trailing slash
    PARENT_DIR="${PARENT_DIR%/}"
    log "Parent directory: $PARENT_DIR"

    # Step 2: Get project name
    log "Step 2: Get project name"
    PROJECT_NAME=$(prompt_text "Enter project name:" "my_kie_project")

    if [[ -z "$PROJECT_NAME" ]]; then
        show_error "Error" "No project name provided. Exiting."
        exit 1
    fi

    log "Project name: $PROJECT_NAME"

    # Step 3: Construct workspace path
    WORKSPACE_PATH="$PARENT_DIR/$PROJECT_NAME"
    log "Workspace path: $WORKSPACE_PATH"

    # Step 4: Check if workspace already exists
    if [[ -d "$WORKSPACE_PATH" ]]; then
        show_error "Error" "Workspace already exists at:\n$WORKSPACE_PATH\n\nPlease choose a different name or location."
        exit 1
    fi

    # Step 5: Choose optional data file
    log "Step 3: Choose optional data file"
    DATA_FILE=$(choose_file)

    if [[ -n "$DATA_FILE" ]]; then
        log "Data file selected: $DATA_FILE"
    else
        log "No data file selected"
    fi

    # Step 6: Create workspace directory
    log "Creating workspace directory: $WORKSPACE_PATH"

    if [[ "$DRY_RUN" == "1" ]]; then
        log "DRY RUN: Would create directory: $WORKSPACE_PATH"
    else
        mkdir -p "$WORKSPACE_PATH"
    fi

    # Step 7: Run kie initialization via Python API
    log "Initializing KIE workspace..."

    if [[ "$DRY_RUN" == "1" ]]; then
        log "DRY RUN: Would execute Python initialization in: $WORKSPACE_PATH"
    else
        local init_output
        local init_exit_code=0

        init_output=$(cd "$WORKSPACE_PATH" && python3 -c "
from kie.commands.handler import CommandHandler
from pathlib import Path
import json

try:
    handler = CommandHandler(Path.cwd())
    result = handler.handle_startkie()
    print(json.dumps(result))
except Exception as e:
    print(f'ERROR: {str(e)}')
    exit(1)
" 2>&1) || init_exit_code=$?

        if [[ "$init_exit_code" != "0" ]] || [[ "$init_output" == *"ERROR:"* ]]; then
            show_error "Init Failed" "Failed to initialize workspace.\n\nError:\n$init_output\n\nPlease ensure KIE v3 is installed:\npip install -e /path/to/kie-v3"
            exit 1
        fi

        # Check if initialization was successful
        if [[ "$init_output" == *'"success": true'* ]] || [[ "$init_output" == *'"success":true'* ]]; then
            log "Init successful"
        else
            show_error "Init Failed" "Workspace initialization returned unexpected result:\n\n$init_output"
            exit 1
        fi
    fi

    # Step 8: Copy data file if provided
    if [[ -n "$DATA_FILE" ]]; then
        log "Copying data file to workspace/data/"

        local filename
        filename=$(basename "$DATA_FILE")

        if [[ "$DRY_RUN" == "1" ]]; then
            log "DRY RUN: Would copy: $DATA_FILE -> $WORKSPACE_PATH/data/$filename"
        else
            cp "$DATA_FILE" "$WORKSPACE_PATH/data/$filename"
            log "Data file copied: $filename"
        fi
    fi

    # Step 9: Run doctor to verify
    log "Running: python3 -m kie.cli doctor"

    if [[ "$DRY_RUN" == "1" ]]; then
        log "DRY RUN: Would execute: (cd \"$WORKSPACE_PATH\" && python3 -m kie.cli doctor)"
    else
        local doctor_output
        local doctor_exit_code

        doctor_output=$(cd "$WORKSPACE_PATH" && python3 -m kie.cli doctor 2>&1) || doctor_exit_code=$?

        if [[ -n "$doctor_exit_code" && "$doctor_exit_code" != "0" ]]; then
            show_error "Warning" "Workspace created but doctor check failed.\n\nOutput:\n$doctor_output\n\nYou can still use the workspace, but some features may not work correctly."
        else
            log "Doctor check passed"
        fi
    fi

    # Step 10: Open workspace based on KIE_OPEN_EDITOR setting
    log "Opening workspace (mode: $KIE_OPEN_EDITOR)"

    if [[ "$DRY_RUN" == "1" ]]; then
        log "DRY RUN: Would open with mode: $KIE_OPEN_EDITOR"
    elif [[ -n "$KIE_WORKSPACE_PARENT" && -n "$KIE_PROJECT_NAME" ]]; then
        log "Non-interactive mode: Skipping workspace open (use KIE_OPEN_EDITOR to override)"
    else
        case "$KIE_OPEN_EDITOR" in
            finder)
                log "Opening in Finder..."
                open "$WORKSPACE_PATH"
                ;;
            vscode)
                log "Opening in VS Code..."
                # Try code CLI first
                if command -v code &>/dev/null; then
                    if code "$WORKSPACE_PATH" 2>/dev/null; then
                        log "Opened in VS Code (via CLI)"
                    else
                        log "Warning: code CLI failed"
                    fi
                # Fallback to open -a
                elif open -a "Visual Studio Code" "$WORKSPACE_PATH" 2>/dev/null; then
                    log "Opened in VS Code (via app)"
                else
                    log "Error: VS Code not found. Install VS Code or use --open=none"
                    log "Workspace created successfully at: $WORKSPACE_PATH"
                fi
                ;;
            none)
                log "Not opening any editor (KIE_OPEN_EDITOR=none)"
                log "Workspace created at: $WORKSPACE_PATH"
                ;;
            *)
                log "Warning: Unknown KIE_OPEN_EDITOR value: $KIE_OPEN_EDITOR"
                log "Valid values: none, finder, vscode"
                log "Workspace created at: $WORKSPACE_PATH"
                ;;
        esac
    fi

    # Step 12: Show success message
    local success_msg="Workspace created successfully!\n\nLocation:\n$WORKSPACE_PATH"

    if [[ -n "$DATA_FILE" ]]; then
        success_msg="$success_msg\n\nData file: $(basename "$DATA_FILE")\n\nNext step: Open in Claude Code and run /eda"
    else
        success_msg="$success_msg\n\nNext steps:\n1. Add data files to data/\n2. Open in Claude Code\n3. Run /eda or /interview"
    fi

    show_dialog "Success" "$success_msg"

    log "Launcher completed successfully"
}

# ============================================================
# Entry Point
# ============================================================

main "$@"
