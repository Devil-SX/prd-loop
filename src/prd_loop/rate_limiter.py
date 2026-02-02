"""Rate limiter for API calls with file-based persistence."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class RateLimiter:
    """
    Rate limiter that persists state to disk.

    Tracks API calls per hour and provides wait functionality
    when the limit is reached.
    """

    def __init__(self, max_calls_per_hour: int, state_file: Path):
        """
        Initialize rate limiter.

        Args:
            max_calls_per_hour: Maximum allowed API calls per hour
            state_file: Path to the state file for persistence
        """
        self.max_calls = max_calls_per_hour
        self.state_file = state_file
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file or initialize new state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                self.call_count = data.get("call_count", 0)
                self.hour_start = data.get("hour_start", "")
            except (json.JSONDecodeError, KeyError):
                self._reset_state()
        else:
            self._reset_state()

        # Check if we need to reset for a new hour
        current_hour = datetime.now().strftime("%Y%m%d%H")
        if self.hour_start != current_hour:
            self._reset_state()

    def _reset_state(self) -> None:
        """Reset state for a new hour."""
        self.call_count = 0
        self.hour_start = datetime.now().strftime("%Y%m%d%H")
        self._save_state()

    def _save_state(self) -> None:
        """Save current state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump({
                "call_count": self.call_count,
                "hour_start": self.hour_start,
                "max_calls": self.max_calls
            }, f)

    def can_call(self) -> bool:
        """
        Check if we can make another API call.

        Returns:
            True if under the rate limit, False otherwise
        """
        # Check if hour has changed
        current_hour = datetime.now().strftime("%Y%m%d%H")
        if self.hour_start != current_hour:
            self._reset_state()

        return self.call_count < self.max_calls

    def record_call(self) -> int:
        """
        Record an API call.

        Returns:
            Updated call count for this hour
        """
        # Check if hour has changed
        current_hour = datetime.now().strftime("%Y%m%d%H")
        if self.hour_start != current_hour:
            self._reset_state()

        self.call_count += 1
        self._save_state()
        return self.call_count

    def get_remaining(self) -> int:
        """
        Get remaining calls for this hour.

        Returns:
            Number of remaining calls allowed
        """
        # Check if hour has changed
        current_hour = datetime.now().strftime("%Y%m%d%H")
        if self.hour_start != current_hour:
            self._reset_state()

        return max(0, self.max_calls - self.call_count)

    def get_wait_seconds(self) -> int:
        """
        Get seconds until the rate limit resets.

        Returns:
            Seconds until next hour
        """
        now = datetime.now()
        # Calculate seconds until next hour
        seconds_past = now.minute * 60 + now.second
        return 3600 - seconds_past

    def wait_for_reset(self, callback: Optional[callable] = None) -> None:
        """
        Wait until the rate limit resets.

        Args:
            callback: Optional callback called every second with remaining time
        """
        wait_time = self.get_wait_seconds()

        while wait_time > 0:
            if callback:
                callback(wait_time)
            time.sleep(1)
            wait_time -= 1

        # Reset state after waiting
        self._reset_state()

    def get_status(self) -> dict:
        """
        Get current rate limiter status.

        Returns:
            Dictionary with current status
        """
        return {
            "call_count": self.call_count,
            "max_calls": self.max_calls,
            "remaining": self.get_remaining(),
            "hour_start": self.hour_start,
            "wait_seconds": self.get_wait_seconds() if not self.can_call() else 0
        }
