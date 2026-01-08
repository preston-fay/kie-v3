#!/bin/bash
set -e

# KIE Zero-Install Bootstrap Script
# Vendors the KIE runtime and creates a ready-to-use workspace

echo "🚀 Bootstrapping KIE workspace..."

# Check 1: Already a KIE project?
if [ -f "CLAUDE.md" ]; then
    if grep -q "KIE Project" "CLAUDE.md"; then
        echo "✓ This is already a KIE project. Ready to start working!"
        exit 0
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
            sed -i.bak 's/python3 -m kie\.cli/PYTHONPATH=".kie\/src" python3 -m kie.cli/g' "$cmd_file"
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
