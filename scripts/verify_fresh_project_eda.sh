#!/bin/bash
# Verification script: Fresh project EDA workflow
# This script verifies that a freshly created KIE workspace can run /eda successfully

set -e  # Exit on error

echo "====================================="
echo "Fresh Project EDA Verification Script"
echo "====================================="
echo ""

# Create temp workspace
TEMP_DIR=$(mktemp -d)
WORKSPACE="$TEMP_DIR/test_kie_eda"

echo "1. Creating fresh workspace at: $WORKSPACE"
KIE_WORKSPACE_PARENT="$TEMP_DIR" KIE_PROJECT_NAME="test_kie_eda" \
  zsh tools/mac_launcher/create_kie_workspace.sh > /dev/null 2>&1

if [ ! -d "$WORKSPACE" ]; then
    echo "❌ FAIL: Workspace not created"
    exit 1
fi
echo "✓ Workspace created"
echo ""

echo "2. Checking fixture dataset..."
if [ ! -f "$WORKSPACE/data/sample_data.csv" ]; then
    echo "❌ FAIL: Fixture dataset missing at $WORKSPACE/data/sample_data.csv"
    exit 1
fi
LINES=$(wc -l < "$WORKSPACE/data/sample_data.csv" | tr -d ' ')
echo "✓ Fixture dataset exists ($LINES lines)"
echo ""

echo "3. Running EDA command..."
cd "$WORKSPACE"
set +e
python3 -m kie.cli eda > /tmp/eda_run.log 2>&1
EXIT_CODE=$?
set -e
if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ FAIL: EDA command failed"
    tail -n 50 /tmp/eda_run.log || true
    exit 1
fi
echo "✓ EDA command succeeded"
echo ""

echo "4. Verifying log file..."
LOG_FILE="$WORKSPACE/outputs/_logs/eda.log"
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ FAIL: Log file missing: $LOG_FILE"
    exit 1
fi
LOG_BYTES=$(wc -c < "$LOG_FILE" | tr -d ' ')
if [ "$LOG_BYTES" -le 0 ]; then
    echo "❌ FAIL: Log file empty"
    exit 1
fi
echo "✓ Log file exists and non-empty ($LOG_BYTES bytes)"
echo ""

echo "5. Verifying EDA output artifact..."
PROFILE_FILE="$WORKSPACE/outputs/eda_profile.yaml"
if [ ! -f "$PROFILE_FILE" ]; then
    echo "❌ FAIL: EDA profile missing: $PROFILE_FILE"
    exit 1
fi
PROFILE_BYTES=$(wc -c < "$PROFILE_FILE" | tr -d ' ')
if [ "$PROFILE_BYTES" -le 0 ]; then
    echo "❌ FAIL: EDA profile empty"
    exit 1
fi
echo "✓ EDA profile exists and non-empty ($PROFILE_BYTES bytes)"
echo ""

echo "6. Testing idempotency (running EDA again)..."
set +e
python3 -m kie.cli eda > /tmp/eda_run2.log 2>&1
EXIT_CODE2=$?
set -e
if [ $EXIT_CODE2 -ne 0 ]; then
    echo "❌ FAIL: Second EDA run failed"
    tail -n 50 /tmp/eda_run2.log || true
    exit 1
fi
NEW_LOG_BYTES=$(wc -c < "$LOG_FILE" | tr -d ' ')
if [ "$NEW_LOG_BYTES" -le "$LOG_BYTES" ]; then
    echo "❌ FAIL: Log file did not grow on second run"
    exit 1
fi
echo "✓ Second run succeeded and logs appended"
echo ""

echo "7. Testing failure behavior (no data)..."
EMPTY_WORKSPACE="$TEMP_DIR/empty_kie_eda"
mkdir -p "$EMPTY_WORKSPACE/data"
cd "$EMPTY_WORKSPACE"

set +e
python3 -m kie.cli eda > /tmp/eda_fail.log 2>&1
FAIL_EXIT=$?
set -e

if [ $FAIL_EXIT -eq 0 ]; then
    echo "❌ FAIL: EDA succeeded with no data"
    exit 1
fi
echo "✓ Failure behavior correct (EDA fails with no data)"
echo ""

echo "====================================="
echo "✅ ALL VERIFICATION CHECKS PASSED"
echo "====================================="
