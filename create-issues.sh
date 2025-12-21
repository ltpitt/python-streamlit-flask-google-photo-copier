#!/bin/bash
# Wrapper script to create GitHub issues from GITHUB_ISSUES.md
# This script checks prerequisites and runs the Python script

set -e  # Exit on error

echo "🔍 GitHub Issues Creator"
echo "========================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "   Please install Python 3.10 or later"
    exit 1
fi

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo "   Please install from: https://cli.github.com/"
    echo ""
    echo "   Quick install:"
    echo "   - macOS: brew install gh"
    echo "   - Ubuntu/Debian: sudo apt install gh"
    echo "   - Windows: winget install GitHub.cli"
    exit 1
fi

# Check if gh is authenticated (only if not dry-run)
if [[ "$1" != "--dry-run" ]]; then
    if ! gh auth status &> /dev/null; then
        echo "❌ GitHub CLI is not authenticated"
        echo "   Please run: gh auth login"
        exit 1
    fi
    echo "✅ GitHub CLI is authenticated"
fi

# Run the Python script
echo ""
python3 create_github_issues.py "$@"
