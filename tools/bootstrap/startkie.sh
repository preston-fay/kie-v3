#!/bin/bash
set -e

# KIE Zero-Install Bootstrap Script
# Vendors the KIE runtime and creates a ready-to-use workspace

echo "🚀 Bootstrapping KIE workspace..."

# Check 1: Already a KIE project?
if [ -f "CLAUDE.md" ]; then
    if grep -q "KIE Project" "CLAUDE.md"; then
        # REFRESH MODE: Upgrade existing workspace if requested
        if [ "$KIE_BOOTSTRAP_REFRESH" = "1" ]; then
            echo "🔄 REFRESH MODE: Upgrading existing KIE workspace..."

            # Ensure vendored runtime exists
            if [ ! -d ".kie/src" ]; then
                echo "📦 Downloading KIE runtime from GitHub..."
                mkdir -p .kie/tmp

                if [ -n "$KIE_BOOTSTRAP_SRC_DIR" ]; then
                    echo "Using local source: $KIE_BOOTSTRAP_SRC_DIR"
                    cp -r "$KIE_BOOTSTRAP_SRC_DIR" .kie/src
                else
                    curl -L https://github.com/preston-fay/kie-v3/archive/refs/heads/main.zip -o .kie/tmp/kie-v3.zip
                    cd .kie/tmp
                    unzip -q kie-v3.zip
                    cd ../..
                    mv .kie/tmp/kie-v3-main .kie/src
                fi

                rm -rf .kie/tmp
                echo "✓ KIE runtime vendored to .kie/src/"
            else
                echo "✓ Using existing vendored runtime at .kie/src/"
            fi

            # Verify critical paths
            if [ ! -d ".kie/src/project_template" ]; then
                echo "❌ ERROR: .kie/src/project_template not found"
                exit 1
            fi

            # Update command pack from vendored template
            echo "📝 Updating command pack..."
            TEMPLATE_CMD_DIR=".kie/src/project_template/.claude/commands"
            WORKSPACE_CMD_DIR=".claude/commands"

            if [ -d "$TEMPLATE_CMD_DIR" ]; then
                mkdir -p "$WORKSPACE_CMD_DIR"

                # Copy all commands from template (overwrite existing)
                cp "$TEMPLATE_CMD_DIR"/*.md "$WORKSPACE_CMD_DIR"/
                echo "✓ Copied latest command pack"

                # Remove legacy command files
                LEGACY_FILES=("interview_v3.md" "status_v3.md" "validate_v3.md" "help.md" "start.md")
                for legacy_file in "${LEGACY_FILES[@]}"; do
                    if [ -f "$WORKSPACE_CMD_DIR/$legacy_file" ]; then
                        rm "$WORKSPACE_CMD_DIR/$legacy_file"
                        echo "✓ Removed legacy file: $legacy_file"
                    fi
                done

                # Fix command wrappers to use vendored runtime
                for cmd_file in "$WORKSPACE_CMD_DIR"/*.md; do
                    if [ -f "$cmd_file" ]; then
                        sed -i.bak '/PYTHONPATH="\.kie\/src"/! s/python3 -m kie\.cli/PYTHONPATH=".kie\/src" python3 -m kie.cli/g' "$cmd_file"
                        rm -f "${cmd_file}.bak"
                    fi
                done
                echo "✓ Fixed command wrappers for vendored runtime"
            fi

            # Ensure rails_state.json exists
            if [ ! -f "project_state/rails_state.json" ]; then
                mkdir -p project_state
                if [ -f ".kie/src/project_template/project_state/rails_state.json" ]; then
                    cp ".kie/src/project_template/project_state/rails_state.json" "project_state/"
                    echo "✓ Added rails_state.json"
                fi
            else
                echo "✓ rails_state.json already exists"
            fi

            echo ""
            echo "✅ Workspace upgraded successfully!"
            echo ""
            echo "CHANGES MADE:"
            echo "  - Updated command pack from latest template"
            echo "  - Removed legacy *_v3.md commands"
            echo "  - Added/verified rails_state.json"
            echo "  - Configured commands for vendored runtime"
            echo ""
            exit 0
        else
            echo "✓ This is already a KIE project. Ready to start working!"
            echo "   (Use KIE_BOOTSTRAP_REFRESH=1 to upgrade command pack)"
            exit 0
        fi
    fi
fi

# Check 2: In the kie-v3 repo itself?
if [ -d "kie" ] && [ -d "web" ]; then
    echo "⚠️  You're in the KIE repo. Use this folder for client projects instead."
    exit 1
fi

# Check 3: Folder not empty check
# Allow .claude/ (created by Claude Code) and .DS_Store (macOS artifact)
# Block if any other files/dirs exist
EXISTING_ITEMS=()
for item in * .[^.]*; do
    # Skip if glob didn't match anything
    [ -e "$item" ] || continue
    # Skip allowed items
    if [ "$item" = ".claude" ] || [ "$item" = ".DS_Store" ]; then
        continue
    fi
    EXISTING_ITEMS+=("$item")
done

if [ ${#EXISTING_ITEMS[@]} -gt 0 ]; then
    echo "❌ This folder is not empty. Found existing: ${EXISTING_ITEMS[*]}"
    echo "   Hint: Create a new empty folder and run this script there."
    exit 1
fi

# Step 1: Download and vendor KIE runtime
echo "📦 Downloading KIE runtime from GitHub..."
mkdir -p .kie/tmp

# Allow override for testing (no network)
if [ -n "$KIE_BOOTSTRAP_SRC_DIR" ]; then
    echo "Using local source: $KIE_BOOTSTRAP_SRC_DIR"
    cp -r "$KIE_BOOTSTRAP_SRC_DIR" .kie/src
else
    curl -L https://github.com/preston-fay/kie-v3/archive/refs/heads/main.zip -o .kie/tmp/kie-v3.zip
    cd .kie/tmp
    unzip -q kie-v3.zip
    cd ../..
    mv .kie/tmp/kie-v3-main .kie/src
fi

rm -rf .kie/tmp

# Verify critical paths
if [ ! -d ".kie/src/kie" ]; then
    echo "❌ ERROR: .kie/src/kie directory not found after extraction"
    exit 1
fi

if [ ! -d ".kie/src/project_template" ]; then
    echo "❌ ERROR: .kie/src/project_template not found after extraction"
    exit 1
fi

echo "✓ KIE runtime vendored to .kie/src/"

# Step 2: Copy workspace skeleton from project_template
echo "📁 Creating workspace structure..."
TEMPLATE_DIR=".kie/src/project_template"

# Use rsync if available (most reliable), otherwise fall back to tar
if command -v rsync >/dev/null 2>&1; then
    echo "Using rsync to copy template..."
    rsync -a --exclude '.DS_Store' --exclude '__MACOSX' "$TEMPLATE_DIR"/ ./
else
    echo "Using tar to copy template..."
    (cd "$TEMPLATE_DIR" && tar cf - .) | tar xf -
fi

echo "✓ Copied workspace skeleton"

# Hard assertion: verify critical directories exist
echo "Verifying workspace structure..."
CRITICAL_DIRS=("data" "outputs" "exports" "project_state" ".claude/commands")
MISSING_DIRS=()

for dir in "${CRITICAL_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        MISSING_DIRS+=("$dir")
    fi
done

if [ ${#MISSING_DIRS[@]} -ne 0 ]; then
    echo ""
    echo "❌ ERROR: Template copy failed - missing directories:"
    for dir in "${MISSING_DIRS[@]}"; do
        echo "   - $dir"
    done
    echo ""
    echo "This is a critical failure. Workspace structure is incomplete."
    exit 1
fi

echo "✓ All critical directories present"

# Step 3: Rewrite command wrappers to use vendored runtime
echo "🔧 Configuring command wrappers for vendored runtime..."
if [ -d ".claude/commands" ]; then
    for cmd_file in .claude/commands/*.md; do
        if [ -f "$cmd_file" ]; then
            sed -i.bak '/PYTHONPATH="\.kie\/src"/! s/python3 -m kie\.cli/PYTHONPATH=".kie\/src" python3 -m kie.cli/g' "$cmd_file"
            rm -f "${cmd_file}.bak"
            echo "✓ Fixed $(basename "$cmd_file")"
        fi
    done
fi

# Step 4: Enumerate all available commands
echo ""
echo "============================================================"
echo "KIE WORKSPACE INITIALIZED"
echo "============================================================"
echo ""

# Use Python to enumerate commands dynamically
if [ -d ".claude/commands" ]; then
    PYTHONPATH=".kie/src" python3 -m kie.commands.enumerate .claude/commands
fi

echo ""
echo "⚠️ NOTE: Commands are case-sensitive. Use /eda not /EDA"
echo ""

# Step 5: Show recommended workflows
echo "RECOMMENDED WORKFLOWS:"
echo ""
echo "  Option 1: I Have Data, Need Quick Analysis"
echo "    1. Drop your data file (CSV/Excel/Parquet/JSON) in data/ folder"
echo "    2. Run /eda to profile your data"
echo "    3. Run /analyze to extract insights"
echo ""
echo "  Option 2: Need Formal Deliverable (Presentation/Dashboard)"
echo "    1. Run /interview to gather requirements"
echo "    2. Choose express (6 questions) or full (11 questions)"
echo "    3. I'll guide you through the rest"
echo ""
echo "  Option 3: Just Exploring KIE"
echo "    1. Sample data is in data/sample_data.csv"
echo "    2. Run /eda to see how analysis works"
echo "    3. Run /analyze to see insight extraction"
echo ""
echo "============================================================"
echo ""

# Step 6: Verify with railscheck
echo "Running railscheck to verify setup..."
PYTHONPATH=".kie/src" python3 -m kie.cli railscheck

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo ""
    echo "❌ WARNING: Rails configuration check failed"
    echo "   This workspace may not be fully configured"
    exit $exit_code
fi

echo ""
echo "✅ KIE workspace bootstrapped successfully!"
