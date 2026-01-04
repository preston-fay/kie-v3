#!/usr/bin/env bash
set -euo pipefail

# whereami.sh - Verifies CC is operating in the correct directory
# Used by slash commands to prevent product/workspace confusion

echo "=== Location Check ==="
echo "PWD: $(pwd)"
echo "Git root: $(git rev-parse --show-toplevel 2>/dev/null || echo 'NOT A GIT REPO')"
echo "Remote: $(git remote get-url origin 2>/dev/null || echo 'NO REMOTE')"
echo "Branch: $(git branch --show-current 2>/dev/null || echo 'NO BRANCH')"
echo ""

# Expected product repo path
EXPECTED_REPO_ROOT="/Users/pfay01/Projects/kie-v3"
ACTUAL_REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo '')"

# Check 1: Must be in the product repo
if [[ "$ACTUAL_REPO_ROOT" != "$EXPECTED_REPO_ROOT" ]]; then
    echo "❌ ERROR: Not in product repo!"
    echo "   Expected: $EXPECTED_REPO_ROOT"
    echo "   Actual:   $ACTUAL_REPO_ROOT"
    exit 1
fi

# Check 2: Must NOT be inside a workspace (has workspace marker)
if [[ -f "project_state/.kie_workspace" ]]; then
    echo "❌ ERROR: Inside a workspace directory!"
    echo "   Product code must not be edited from within workspaces."
    echo "   Switch to: $EXPECTED_REPO_ROOT"
    exit 1
fi

# Check 3: Must have product repo marker
if [[ ! -f ".kie_product_repo" ]]; then
    echo "⚠️  WARNING: Missing .kie_product_repo marker"
    echo "   This should exist in the product repo root."
    exit 1
fi

echo "✅ Location verified: product repo"
exit 0
