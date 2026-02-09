"""Response analyzer for Claude output - detects completion signals and status."""

import json
import re
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class AnalysisResult:
    """Result of analyzing Claude's response."""
    is_complete: bool = False          # All stories complete (<promise>COMPLETE</promise>)
    exit_signal: bool = False          # EXIT_SIGNAL: true in status block
    story_passed: bool = False         # Current story passed
    story_id: Optional[str] = None     # Story ID from status block
    status: str = "UNKNOWN"            # STATUS field value
    has_error: bool = False            # Detected errors in output
    files_modified: List[str] = None   # List of modified files
    summary: str = ""                  # Work summary

    def __post_init__(self):
        if self.files_modified is None:
            self.files_modified = []


class ResponseAnalyzer:
    """Analyzes Claude Code responses for completion signals and status."""

    # Pattern for the RALPH_STATUS block
    STATUS_BLOCK_PATTERN = re.compile(
        r"---RALPH_STATUS---\s*(.*?)\s*---END_RALPH_STATUS---",
        re.DOTALL | re.IGNORECASE
    )

    # Pattern for completion signal
    COMPLETE_PATTERN = re.compile(r"<promise>COMPLETE</promise>", re.IGNORECASE)

    # Patterns for errors
    ERROR_PATTERNS = [
        re.compile(r"^Error:", re.MULTILINE | re.IGNORECASE),
        re.compile(r"^ERROR:", re.MULTILINE),
        re.compile(r"Exception:", re.IGNORECASE),
        re.compile(r"Fatal:", re.IGNORECASE),
        re.compile(r"failed with error", re.IGNORECASE),
    ]

    def analyze(self, output: str) -> AnalysisResult:
        """
        Analyze Claude's output for completion signals and status.

        Args:
            output: Raw output from Claude CLI

        Returns:
            AnalysisResult with detected signals and status
        """
        result = AnalysisResult()

        # Check for <promise>COMPLETE</promise>
        result.is_complete = self.detect_completion(output)

        # Parse RALPH_STATUS block if present
        status_data = self.parse_status_block(output)
        if status_data:
            result.status = status_data.get("STATUS", "UNKNOWN")
            result.exit_signal = status_data.get("EXIT_SIGNAL", "").lower() == "true"
            result.story_passed = status_data.get("STORY_PASSED", "").lower() == "true"
            result.story_id = status_data.get("STORY_ID")

            files_str = status_data.get("FILES_MODIFIED", "")
            if files_str:
                result.files_modified = self._parse_file_list(files_str)

        # Check for errors
        result.has_error = self.detect_errors(output)

        # Generate summary
        result.summary = self._generate_summary(result, output)

        return result

    def detect_completion(self, output: str) -> bool:
        """Check if output contains the completion signal."""
        return bool(self.COMPLETE_PATTERN.search(output))

    def parse_status_block(self, output: str) -> Optional[dict]:
        """
        Parse the RALPH_STATUS block from output.

        Returns:
            Dictionary of status fields, or None if not found
        """
        match = self.STATUS_BLOCK_PATTERN.search(output)
        if not match:
            return None

        block_content = match.group(1)
        result = {}

        for line in block_content.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()

        return result

    def detect_errors(self, output: str) -> bool:
        """Check if output contains error patterns."""
        for pattern in self.ERROR_PATTERNS:
            if pattern.search(output):
                return True
        return False

    def _parse_file_list(self, files_str: str) -> List[str]:
        """Parse a file list from string (comma-separated or JSON array)."""
        files_str = files_str.strip()

        # Try JSON array first
        if files_str.startswith("["):
            try:
                return json.loads(files_str)
            except json.JSONDecodeError:
                pass

        # Comma-separated
        return [f.strip() for f in files_str.split(",") if f.strip()]

    def _generate_summary(self, result: AnalysisResult, output: str) -> str:
        """Generate a brief summary of the analysis."""
        parts = []

        if result.is_complete:
            parts.append("All stories complete")
        elif result.story_passed:
            parts.append(f"Story {result.story_id} passed")
        elif result.story_id:
            parts.append(f"Working on {result.story_id}")

        if result.files_modified:
            parts.append(f"{len(result.files_modified)} files modified")

        if result.has_error:
            parts.append("Errors detected")

        return "; ".join(parts) if parts else "No status information"

    def extract_json_from_output(self, output: str) -> Optional[dict]:
        """
        Try to extract JSON data from Claude's output.

        Looks for the last valid JSON object in the output.
        """
        # Look for result type JSON (from stream-json format)
        for line in reversed(output.split("\n")):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue
        return None


def detect_story_completion(output: str, story_id: str) -> bool:
    """
    Detect if a specific story was completed in the output.

    This is a convenience function that checks for various completion signals
    for a specific story ID.

    Args:
        output: Raw output from Claude CLI
        story_id: The story ID to check for (e.g., "US-001")

    Returns:
        True if the story appears to be completed
    """
    # Check for STORY_PASSED: true in status block
    analyzer = ResponseAnalyzer()
    status_data = analyzer.parse_status_block(output)

    if status_data:
        # Check if this specific story passed
        if status_data.get("STORY_ID") == story_id:
            if status_data.get("STORY_PASSED", "").lower() == "true":
                return True
            if status_data.get("STATUS", "").upper() == "COMPLETE":
                return True

    # Check for git commit message pattern
    commit_pattern = re.compile(
        rf"feat:\s*{re.escape(story_id)}\s*-",
        re.IGNORECASE
    )
    if commit_pattern.search(output):
        return True

    # Check for common completion phrases
    completion_patterns = [
        rf"{re.escape(story_id)}.*completed",
        rf"{re.escape(story_id)}.*done",
        rf"completed.*{re.escape(story_id)}",
        rf"finished.*{re.escape(story_id)}",
    ]

    for pattern in completion_patterns:
        if re.search(pattern, output, re.IGNORECASE):
            return True

    return False
