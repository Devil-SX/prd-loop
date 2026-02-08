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
from prompt.observe import OBSERVE_PROMPT


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


def cleanup_previous_observation(session_dir: Path) -> None:
    """Remove previous observation files if they exist."""
    files_to_remove = [
        session_dir / "observation.log",
        session_dir / "observation_report.md",
        # Also clean up old naming convention
        session_dir / "observe.log",
    ]

    for file_path in files_to_remove:
        if file_path.exists():
            file_path.unlink()
            print(f"Removed previous: {file_path.name}")


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

    # Clean up previous observation files
    cleanup_previous_observation(session_dir)

    # Check for required files
    summary_file = session_dir / "summary.json"
    if not summary_file.exists():
        print(f"Warning: summary.json not found in {session_dir}")
        print("Session may be incomplete or still running")

    # Detect prd-loop framework
    project_root = session_dir.parent.parent.parent  # .prd/logs/session_xxx -> project_root
    uses_prd = (project_root / ".prd").exists()

    # Build prompt
    prompt = OBSERVE_PROMPT.format(
        session_dir=session_dir,
        project_root=project_root,
        uses_prd="yes" if uses_prd else "no",
        create_issue="yes" if create_issue else "no",
    )

    # Configure allowed tools
    allowed_tools = [
        "Read",
        "Glob",
        "Write",
        # GitHub CLI
        "Bash(gh api *)",           # Get user info
        "Bash(gh repo list *)",     # List user repos
        "Bash(gh repo create *)",   # Create private repo for target project
        "Bash(gh issue create *)",  # Create issues
        "Bash(gh issue close *)",   # Close auto-resolved issues
        "Bash(gh label create *)",  # Create labels
        # Git commands
        "Bash(git init *)",         # Initialize git
        "Bash(git remote *)",       # Check/add remote
        # Filesystem
        "Bash(mkdir *)",            # Create directories
    ]

    # Execute Claude
    cli = ClaudeCLI(
        output_timeout_minutes=timeout_minutes,
        allowed_tools=allowed_tools,
        model=model,
        dangerously_skip_permissions=True,
    )

    print(f"\nAnalyzing with Claude ({model})...\n")

    # Open log file for stream output
    observation_log_path = session_dir / "observation.log"
    with open(observation_log_path, "w", encoding="utf-8") as log_file:
        result = cli.execute(prompt, log_file=log_file)

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
        print(f"Log saved to: {observation_log_path}")
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
