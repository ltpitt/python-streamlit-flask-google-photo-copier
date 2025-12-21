#!/usr/bin/env python3
"""
Script to create GitHub issues from GITHUB_ISSUES.md

This script parses the GITHUB_ISSUES.md file and creates GitHub issues
for issues #2 through #16 using the GitHub CLI (gh).

Prerequisites:
- GitHub CLI (gh) must be installed and authenticated
- Run: gh auth login

Usage:
    python create_github_issues.py           # Create all issues
    python create_github_issues.py --dry-run # Preview without creating
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def parse_issues_from_markdown(md_file: Path) -> List[Tuple[int, str, str]]:
    """Parse issues from GITHUB_ISSUES.md file.
    
    Args:
        md_file: Path to GITHUB_ISSUES.md
        
    Returns:
        List of tuples (issue_number, title, body)
    """
    content = md_file.read_text()
    
    # Split content by issue headers
    # Pattern matches: ## Issue #N: Title
    issue_sections = re.split(r'\n(?=## Issue #\d+:)', content)
    
    issues = []
    for section in issue_sections:
        # Extract issue number and title
        header_match = re.match(r'## Issue #(\d+): (.+?)\n', section)
        if not header_match:
            continue
        
        issue_num = int(header_match.group(1))
        title = header_match.group(2).strip()
        
        # Extract everything after the header until the next issue or special sections
        # Stop at: next issue, "---", "# Implementation Order", or "# Notes for AI Agent"
        body_match = re.search(
            r'## Issue #\d+: .+?\n\n(.+?)(?=\n---\n|\n## Issue #|\n# Implementation Order|\n# Notes for AI Agent|\Z)',
            section,
            re.DOTALL
        )
        
        if body_match:
            body = body_match.group(1).strip()
            issues.append((issue_num, title, body))
    
    return issues


def create_github_issue(issue_num: int, title: str, body: str, repo: str, dry_run: bool = False) -> bool:
    """Create a GitHub issue using gh CLI.
    
    Args:
        issue_num: Issue number
        title: Issue title
        body: Issue body (markdown)
        repo: Repository in format owner/repo
        dry_run: If True, only preview without creating
        
    Returns:
        True if successful, False otherwise
    """
    full_title = f"Issue #{issue_num}: {title}"
    
    if dry_run:
        print(f"\n{'='*60}")
        print(f"Issue #{issue_num}: {title}")
        print(f"{'='*60}")
        print(f"Title: {full_title}")
        print(f"Body preview (first 500 chars):")
        print(body[:500] + ("..." if len(body) > 500 else ""))
        print(f"{'='*60}")
        return True
    
    try:
        # Create issue using gh CLI
        cmd = [
            "gh", "issue", "create",
            "--repo", repo,
            "--title", full_title,
            "--body", body
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✓ Created Issue #{issue_num}: {title}")
        print(f"  URL: {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create Issue #{issue_num}: {title}")
        print(f"  Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error creating Issue #{issue_num}: {title}")
        print(f"  Error: {e}")
        return False


def main():
    """Main function to create all GitHub issues."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create GitHub issues from GITHUB_ISSUES.md")
    parser.add_argument("--dry-run", action="store_true", help="Preview issues without creating them")
    args = parser.parse_args()
    
    dry_run = args.dry_run
    
    if dry_run:
        print("🔍 DRY RUN MODE - No issues will be created\n")
    else:
        # Check if gh is installed and authenticated
        try:
            subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            print("❌ GitHub CLI (gh) is not authenticated.")
            print("   Please run: gh auth login")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ GitHub CLI (gh) is not installed.")
            print("   Please install from: https://cli.github.com/")
            sys.exit(1)
    
    # Parse GITHUB_ISSUES.md
    md_file = Path(__file__).parent / "GITHUB_ISSUES.md"
    if not md_file.exists():
        print(f"❌ GITHUB_ISSUES.md not found at {md_file}")
        sys.exit(1)
    
    print(f"📄 Parsing issues from {md_file}")
    issues = parse_issues_from_markdown(md_file)
    
    if not issues:
        print("❌ No issues found in GITHUB_ISSUES.md")
        sys.exit(1)
    
    print(f"📋 Found {len(issues)} issues")
    
    # Filter issues #2 through #16 (skip #1 as it's already created)
    issues_to_create = [(num, title, body) for num, title, body in issues if num >= 2]
    
    if not issues_to_create:
        print("⚠️  No issues found to create (looking for issues #2 and above)")
        sys.exit(0)
    
    print(f"\n🚀 {'Previewing' if dry_run else 'Creating'} {len(issues_to_create)} issues (#2-#16)...")
    print(f"   Repository: ltpitt/python-streamlit-flask-google-photo-copier\n")
    
    # Create each issue
    success_count = 0
    fail_count = 0
    
    for issue_num, title, body in issues_to_create:
        success = create_github_issue(
            issue_num,
            title,
            body,
            "ltpitt/python-streamlit-flask-google-photo-copier",
            dry_run=dry_run
        )
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    if dry_run:
        print(f"  📋 Previewed: {success_count} issues")
        print(f"\n  To create these issues, run without --dry-run:")
        print(f"  python3 create_github_issues.py")
    else:
        print(f"  ✓ Successfully created: {success_count} issues")
        if fail_count > 0:
            print(f"  ✗ Failed: {fail_count} issues")
            sys.exit(1)
        else:
            print(f"\n🎉 All issues created successfully!")


if __name__ == "__main__":
    main()
