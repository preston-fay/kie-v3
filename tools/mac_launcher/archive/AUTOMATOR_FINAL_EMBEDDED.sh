#!/bin/zsh
# Create KIE Workspace Launcher for macOS
# Embedded version for Automator (no external dependencies)

set -e

DRY_RUN="${DRY_RUN:-0}"
KIE_WORKSPACE_PARENT="${KIE_WORKSPACE_PARENT:-}"
KIE_PROJECT_NAME="${KIE_PROJECT_NAME:-}"
KIE_DATA_FILE="${KIE_DATA_FILE:-}"
KIE_OPEN_EDITOR="${KIE_OPEN_EDITOR:-none}"

log() {
    echo "[KIE Launcher] $*"
}

show_dialog() {
    local title="$1"
    local message="$2"
    local icon="${3:-note}"
    if [[ "$DRY_RUN" == "1" ]]; then
        log "DIALOG: $title - $message"
        return
    fi
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
    if [[ -n "$KIE_DATA_FILE" ]]; then
        if [[ -f "$KIE_DATA_FILE" ]]; then
            echo "$KIE_DATA_FILE"
        else
            echo ""
        fi
        return
    fi
    if [[ -n "$KIE_WORKSPACE_PARENT" && -n "$KIE_PROJECT_NAME" ]]; then
        echo ""
        return
    fi
    if [[ "$DRY_RUN" == "1" ]]; then
        echo ""
        return
    fi
    local add_data
    add_data=$(osascript -e 'display dialog "Add a data file to your workspace?" buttons {"Skip", "Choose File"} default button "Choose File"' -e 'button returned of result' 2>/dev/null || echo "Skip")
    if [[ "$add_data" == "Skip" ]]; then
        echo ""
        return
    fi
    local result
    result=$(osascript -e 'tell application "Finder"
        set dataFile to choose file with prompt "Choose data file (CSV or Excel):" of type {"public.comma-separated-values-text", "org.openxmlformats.spreadsheetml.sheet", "com.microsoft.excel.xls"}
        return POSIX path of dataFile
    end tell' 2>/dev/null || echo "")
    echo "$result"
}

check_prerequisites() {
    log "Checking prerequisites..."
    if ! command -v python3 &>/dev/null; then
        show_error "Python Not Found" "Python 3 is not installed on this machine."
        exit 1
    fi
    log "✓ Python 3 found: $(command -v python3)"
    local kie_check_output
    local kie_check_exit_code=0
    kie_check_output=$(python3 -c "import kie; print(kie.__file__)" 2>&1) || kie_check_exit_code=$?
    if [[ "$kie_check_exit_code" != "0" ]]; then
        show_error "KIE Not Installed" "KIE is not installed on this machine."
        exit 1
    fi
    log "✓ KIE installed at: $kie_check_output"
}

main() {
    log "Starting KIE Workspace Launcher..."
    check_prerequisites
    log "Step 1: Choose parent directory"
    PARENT_DIR=$(choose_folder)
    if [[ -z "$PARENT_DIR" ]]; then
        show_error "Error" "No parent directory selected. Exiting."
        exit 1
    fi
    PARENT_DIR="${PARENT_DIR%/}"
    log "Parent directory: $PARENT_DIR"
    log "Step 2: Get project name"
    PROJECT_NAME=$(prompt_text "Enter project name:" "my_kie_project")
    if [[ -z "$PROJECT_NAME" ]]; then
        show_error "Error" "No project name provided. Exiting."
        exit 1
    fi
    log "Project name: $PROJECT_NAME"
    WORKSPACE_PATH="$PARENT_DIR/$PROJECT_NAME"
    log "Workspace path: $WORKSPACE_PATH"
    if [[ -d "$WORKSPACE_PATH" ]]; then
        show_error "Error" "Workspace already exists at:\n$WORKSPACE_PATH"
        exit 1
    fi
    log "Step 3: Choose optional data file"
    DATA_FILE=$(choose_file)
    if [[ -n "$DATA_FILE" ]]; then
        log "Data file selected: $DATA_FILE"
    else
        log "No data file selected"
    fi
    log "Creating workspace directory: $WORKSPACE_PATH"
    if [[ "$DRY_RUN" == "1" ]]; then
        log "DRY RUN: Would create directory: $WORKSPACE_PATH"
    else
        mkdir -p "$WORKSPACE_PATH"
    fi
    log "Initializing KIE workspace..."
    if [[ "$DRY_RUN" == "1" ]]; then
        log "DRY RUN: Would execute Python initialization"
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
            show_error "Init Failed" "Failed to initialize workspace."
            exit 1
        fi
        if [[ "$init_output" == *'"success": true'* ]] || [[ "$init_output" == *'"success":true'* ]]; then
            log "Init successful"
        else
            show_error "Init Failed" "Workspace initialization returned unexpected result"
            exit 1
        fi
    fi
    if [[ -n "$DATA_FILE" ]]; then
        log "Copying data file to workspace/data/"
        local filename
        filename=$(basename "$DATA_FILE")
        if [[ "$DRY_RUN" == "1" ]]; then
            log "DRY RUN: Would copy: $DATA_FILE"
        else
            cp "$DATA_FILE" "$WORKSPACE_PATH/data/$filename"
            log "Data file copied: $filename"
        fi
    fi
    log "Running: python3 -m kie.cli doctor"
    if [[ "$DRY_RUN" == "1" ]]; then
        log "DRY RUN: Would execute doctor"
    else
        local doctor_output
        local doctor_exit_code
        doctor_output=$(cd "$WORKSPACE_PATH" && python3 -m kie.cli doctor 2>&1) || doctor_exit_code=$?
        if [[ -n "$doctor_exit_code" && "$doctor_exit_code" != "0" ]]; then
            show_error "Warning" "Workspace created but doctor check failed."
        else
            log "Doctor check passed"
        fi
    fi
    log "Opening workspace (mode: $KIE_OPEN_EDITOR)"
    if [[ "$DRY_RUN" == "1" ]]; then
        log "DRY RUN: Would open with mode: $KIE_OPEN_EDITOR"
    elif [[ -n "$KIE_WORKSPACE_PARENT" && -n "$KIE_PROJECT_NAME" ]]; then
        log "Non-interactive mode: Skipping workspace open"
    else
        case "$KIE_OPEN_EDITOR" in
            finder)
                log "Opening in Finder..."
                open "$WORKSPACE_PATH"
                ;;
            vscode)
                log "Opening in VS Code..."
                if command -v code &>/dev/null; then
                    if code "$WORKSPACE_PATH" 2>/dev/null; then
                        log "Opened in VS Code"
                    fi
                elif open -a "Visual Studio Code" "$WORKSPACE_PATH" 2>/dev/null; then
                    log "Opened in VS Code"
                fi
                ;;
            none)
                log "Not opening editor"
                ;;
        esac
    fi
    local success_msg="Workspace created successfully!\n\nLocation:\n$WORKSPACE_PATH"
    if [[ -n "$DATA_FILE" ]]; then
        success_msg="$success_msg\n\nData file: $(basename "$DATA_FILE")\n\nNext: Open in Claude Code and run /eda"
    else
        success_msg="$success_msg\n\nNext:\n1. Add data files\n2. Open in Claude Code\n3. Run /eda"
    fi
    show_dialog "Success" "$success_msg"
    log "Launcher completed successfully"
}

main "$@"
