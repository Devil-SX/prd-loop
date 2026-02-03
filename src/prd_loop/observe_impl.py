#!/usr/bin/env python3
"""
observe-impl: Analyze impl-prd session logs and report issues.

Usage:
    observe-impl --session <SESSION_DIR>
    observe-impl --latest           # Analyze the most recent session
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports when run directly
_SCRIPT_DIR = Path(__file__).parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from claude_cli import ClaudeCLI, check_claude_installed
from config import find_project_root


# Prompt template for analyzing session logs
OBSERVE_PROMPT = '''You are a log analyzer for impl-prd execution sessions.

## Task
Analyze the implementation session logs and:
1. Read all log files in the session directory
2. Identify errors, warnings, and failures
3. Summarize what went well and what went wrong
4. Generate a markdown report
5. Optionally create a GitHub Issue if significant issues were found

## Session Directory
{session_dir}

## Create GitHub Issue
{create_issue}

## Steps

### Step 1: Read summary.json
Read the summary.json file to understand:
- Overall session results (exit reason, duration, loop counts)
- Stories completed vs total
- Success/failure rates

### Step 2: Read session.log
Read the session.log file for the main execution flow and timeline.

### Step 3: Read loop log files
Read the loop_*.log files to understand:
- What Claude was asked to do in each loop
- What actions Claude took
- Any errors or failures that occurred
- Why stories passed or failed

### Step 4: Analyze patterns
Look for patterns such as:
- Repeated failures on the same story
- Common error types
- Timeout issues
- Circuit breaker triggers
- Quality check failures (lint, typecheck, test)

### Step 5: Write report
Write a markdown report to: {session_dir}/observation_report.md

Use this format:
```markdown
# Implementation Session Report

## Summary
- **Session ID**: ...
- **Duration**: ...
- **Stories Progress**: X/Y completed (Z this session)
- **Loop Results**: A successful, B failed
- **Exit Reason**: ...

## Session Timeline
Brief overview of what happened during the session.

## Issues Found

### Issue 1: [Short Title]
- **Loop(s)**: #N, #M
- **Story**: US-XXX (if applicable)
- **Problem**: Description of what went wrong
- **Root Cause**: Analysis of why it happened
- **Suggestion**: How to fix or avoid this issue

### Issue 2: ...

## What Went Well
- List of things that worked correctly
- Successful patterns observed

## Recommendations
Actionable suggestions for improving future runs or fixing issues.

## Technical Details
Any relevant technical information (error messages, stack traces, etc.)
```

### Step 6: Create GitHub Issue (if applicable)
If create_issue is "yes" AND significant issues were found (not just "all stories completed successfully"):
- Use `gh issue create -R Devil-SX/prd-loop` to create an issue in the prd-loop repository
- Title: "impl-prd Session Report: [brief summary]"
- Label: "impl-prd-observation" (create with `gh label create -R Devil-SX/prd-loop` if it doesn't exist)
- Include the key findings from the report

Do NOT create an issue if:
- The session completed successfully with no problems
- Only minor warnings were encountered
- create_issue is "no"

## Important Notes
- Be thorough but concise in your analysis
- Focus on actionable insights
- If a loop file is very long, focus on the error sections and key decision points
- Look for patterns across multiple loops, not just individual failures
'''


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze impl-prd session logs and report issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--session", "-s",
        type=str,
        help="Path to session directory",
    )
    parser.add_argument(
        "--latest", "-l",
        action="store_true",
        help="Analyze the most recent session",
    )
    parser.add_argument(
        "--no-issue",
        action="store_true",
        help="Don't create GitHub issue",
    )
    parser.add_argument(
        "--model", "-m",
        choices=["opus", "sonnet", "haiku"],
        default="haiku",
        help="Claude model to use (default: haiku)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Claude timeout in minutes (default: 10)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output",
    )
    return parser.parse_args()


def find_latest_session(logs_dir: Path) -> Path | None:
    """Find the most recent session directory (session_YYYYMMDD_HHMMSS format)."""
    if not logs_dir.exists():
        return None

    sessions = sorted(logs_dir.glob("session_*"), reverse=True)
    return sessions[0] if sessions else None


def run_observe(session_dir: Path, create_issue: bool = True, model: str = "haiku", timeout_minutes: int = 10) -> bool:
    """
    Run observation analysis on a session directory.

    Args:
        session_dir: Path to the session directory
        create_issue: Whether to create GitHub issue for issues found
        model: Claude model to use
        timeout_minutes: Timeout for Claude execution

    Returns:
        True if observation completed successfully, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"observe-impl: Analyzing session {session_dir.name}")
    print(f"{'=' * 60}")

    # Check for required files
    summary_file = session_dir / "summary.json"
    if not summary_file.exists():
        print(f"Warning: summary.json not found in {session_dir}")
        print("Session may be incomplete or still running")

    # Build prompt
    prompt = OBSERVE_PROMPT.format(
        session_dir=session_dir,
        create_issue="yes" if create_issue else "no"
    )

    # Configure allowed tools
    allowed_tools = [
        "Read",
        "Glob",
        "Write",
        "Bash(gh issue create *)",
        "Bash(gh label create *)",
    ]

    # Execute Claude
    cli = ClaudeCLI(
        output_timeout_minutes=timeout_minutes,
        allowed_tools=allowed_tools,
        model=model,
        dangerously_skip_permissions=True,
    )

    print(f"\nAnalyzing with Claude ({model})...\n")

    result = cli.execute(prompt)

    if result.timeout:
        print(f"\nError: Analysis timed out ({result.timeout_reason})")
        return False

    if not result.success:
        print(f"\nError: Analysis failed (exit code {result.exit_code})")
        return False

    # Check if report was created
    report_file = session_dir / "observation_report.md"
    if report_file.exists():
        print(f"\n{'=' * 60}")
        print(f"Observation complete!")
        print(f"Report saved to: {report_file}")
        print(f"{'=' * 60}")
    else:
        print(f"\nWarning: Report file not created at {report_file}")

    return True


def main():
    args = parse_args()

    # Determine session directory
    session_dir = None

    if args.session:
        session_dir = Path(args.session)
        if not session_dir.is_absolute():
            # Try relative to current directory first
            if not session_dir.exists():
                # Try relative to .prd/logs
                project_root = find_project_root()
                if project_root:
                    session_dir = project_root / ".prd" / "logs" / args.session

    elif args.latest:
        # Find latest session from .prd/logs
        project_root = find_project_root()
        if project_root:
            logs_dir = project_root / ".prd" / "logs"
            session_dir = find_latest_session(logs_dir)
            if not session_dir:
                print("Error: No session directories found in .prd/logs/")
                return 1
        else:
            print("Error: .prd directory not found")
            print("Run from a project directory with .prd/logs/")
            return 1
    else:
        print("Error: --session or --latest required")
        print("Usage:")
        print("  observe-impl --session <SESSION_DIR>")
        print("  observe-impl --latest")
        return 1

    # Validate session directory
    if not session_dir or not session_dir.exists():
        print(f"Error: Session directory not found: {session_dir}")
        return 1

    if not session_dir.is_dir():
        print(f"Error: Not a directory: {session_dir}")
        return 1

    # Check Claude CLI
    if not check_claude_installed():
        print("Error: Claude Code CLI not found")
        print("Install with: npm install -g @anthropic-ai/claude-code")
        return 1

    # Run observation
    success = run_observe(
        session_dir=session_dir,
        create_issue=not args.no_issue,
        model=args.model,
        timeout_minutes=args.timeout,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
