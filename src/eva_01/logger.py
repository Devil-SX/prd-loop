"""Logging system with runtime statistics for PRD Loop."""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, TextIO


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)."""
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.PURPLE = cls.CYAN = cls.NC = ''


class PrdLogger:
    """Logger with runtime statistics support."""

    LEVEL_COLORS = {
        "INFO": Colors.BLUE,
        "WARN": Colors.YELLOW,
        "ERROR": Colors.RED,
        "SUCCESS": Colors.GREEN,
        "LOOP": Colors.PURPLE,
        "STATS": Colors.CYAN,
    }

    def __init__(
        self,
        log_file: Optional[Path] = None,
        log_dir: Optional[Path] = None,
        prefix: str = "",
        enable_colors: bool = True
    ):
        self.log_file = log_file
        self.file_handle: Optional[TextIO] = None
        self.timers: Dict[str, float] = {}
        self.total_start_time: Optional[float] = None

        if not enable_colors or not sys.stdout.isatty():
            Colors.disable()

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self.file_handle = open(log_file, "a", encoding="utf-8")

    def __del__(self):
        if self.file_handle:
            self.file_handle.close()

    def _format_message(self, level: str, message: str, loop_num: Optional[int] = None) -> tuple:
        """Format log message for console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        loop_str = f"[Loop #{loop_num}] " if loop_num is not None else ""

        color = self.LEVEL_COLORS.get(level, Colors.NC)
        console_msg = f"{color}[{timestamp}] [{level}] {loop_str}{message}{Colors.NC}"
        file_msg = f"[{timestamp}] [{level}] {loop_str}{message}"

        return console_msg, file_msg

    def log(self, level: str, message: str, loop_num: Optional[int] = None) -> None:
        """Log a message to console and file."""
        console_msg, file_msg = self._format_message(level, message, loop_num)

        print(console_msg)

        if self.file_handle:
            self.file_handle.write(file_msg + "\n")
            self.file_handle.flush()

    def info(self, message: str, loop_num: Optional[int] = None) -> None:
        self.log("INFO", message, loop_num)

    def warn(self, message: str, loop_num: Optional[int] = None) -> None:
        self.log("WARN", message, loop_num)

    def error(self, message: str, loop_num: Optional[int] = None) -> None:
        self.log("ERROR", message, loop_num)

    def success(self, message: str, loop_num: Optional[int] = None) -> None:
        self.log("SUCCESS", message, loop_num)

    def loop(self, message: str, loop_num: Optional[int] = None) -> None:
        self.log("LOOP", message, loop_num)

    def stats(self, message: str) -> None:
        self.log("STATS", message)

    # Timer functions
    def start_timer(self, name: str) -> None:
        """Start a named timer."""
        self.timers[name] = time.time()

    def stop_timer(self, name: str) -> float:
        """Stop a timer and return elapsed seconds."""
        if name not in self.timers:
            return 0.0
        elapsed = time.time() - self.timers[name]
        del self.timers[name]
        return elapsed

    def get_elapsed(self, name: str) -> float:
        """Get elapsed time without stopping timer."""
        if name not in self.timers:
            return 0.0
        return time.time() - self.timers[name]

    def start_total_timer(self) -> None:
        """Start the total runtime timer."""
        self.total_start_time = time.time()

    def get_total_runtime(self) -> float:
        """Get total runtime in seconds."""
        if self.total_start_time is None:
            return 0.0
        return time.time() - self.total_start_time

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format seconds as human-readable duration."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def log_iteration_complete(
        self,
        loop_num: int,
        api_duration: float,
        total_duration: float,
        success: bool
    ) -> None:
        """Log iteration completion with timing stats."""
        processing_time = total_duration - api_duration
        status = "SUCCESS" if success else "WARN"
        self.log(
            status,
            f"Completed in {self.format_duration(total_duration)} "
            f"(API: {self.format_duration(api_duration)}, "
            f"Processing: {self.format_duration(processing_time)})",
            loop_num
        )

    def log_progress_stats(
        self,
        loop_num: int,
        api_calls: int,
        max_calls: int,
        stories_done: int,
        stories_total: int
    ) -> None:
        """Log progress statistics."""
        runtime = self.format_duration(self.get_total_runtime())
        self.stats(
            f"Total runtime: {runtime} | "
            f"API calls: {api_calls}/{max_calls} | "
            f"Stories: {stories_done}/{stories_total} done"
        )

    def log_separator(self, char: str = "=", width: int = 60) -> None:
        """Log a visual separator line."""
        line = char * width
        print(f"{Colors.PURPLE}{line}{Colors.NC}")
        if self.file_handle:
            self.file_handle.write(line + "\n")
            self.file_handle.flush()

    def separator(self, char: str = "=", width: int = 60) -> None:
        """Alias for log_separator."""
        self.log_separator(char, width)
