#!/usr/bin/env bash
#
# Clean untracked generated artifacts from working tree
#
# Usage: ./scripts/clean_junk.sh
#
# Removes:
# - __pycache__/ directories
# - .DS_Store files
# - *.egg-info directories
# - build/ and dist/ directories
#
# Does NOT remove git-tracked files (safe to run)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "Cleaning untracked generated artifacts..."
echo

# Remove __pycache__ directories
echo "Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Remove .DS_Store files
echo "Removing .DS_Store files..."
find . -type f -name ".DS_Store" -delete 2>/dev/null || true

# Remove .egg-info directories
echo "Removing *.egg-info directories..."
find . -maxdepth 1 -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Remove build/dist directories
echo "Removing build/ and dist/ directories..."
rm -rf build/ dist/ 2>/dev/null || true

echo
echo "✅ Cleanup complete!"
echo
echo "Run 'python3 scripts/check_invariants.py' to verify."
