"""Session-based logging system for PRD Loop.

Creates a session directory structure:
    .prd/logs/session_YYYYMMDD_HHMMSS/
        ├── config.json          # All configuration options
        ├── prd_snapshot.json    # PRD state at start
        ├── loop_001.jsonl       # Raw stream-json output for loop 1
        ├── loop_002.jsonl       # Raw stream-json output for loop 2
        ├── ...
        └── summary.json         # Final summary report
"""

import json
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, TextIO


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
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = ''
        cls.PURPLE = cls.CYAN = cls.NC = ''


@dataclass
class LoopRecord:
    """Record for a single loop iteration."""
    loop_num: int
    story_id: str
    story_title: str
    start_time: str
    end_time: str = ""
    duration_seconds: float = 0.0
    api_duration_seconds: float = 0.0
    success: bool = False
    story_passed: bool = False
    timeout: bool = False
    error: str = ""
    log_file: str = ""


@dataclass
class SessionSummary:
    """Summary report for the session."""
    session_id: str
    start_time: str
    end_time: str = ""
    total_duration_seconds: float = 0.0
    exit_reason: str = ""

    # PRD info
    project: str = ""
    prd_file: str = ""
    total_stories: int = 0
    stories_completed: int = 0
    stories_completed_this_session: int = 0

    # Loop stats
    total_loops: int = 0
    successful_loops: int = 0
    failed_loops: int = 0
    total_api_calls: int = 0

    # Timing
    total_api_time_seconds: float = 0.0
    avg_loop_duration_seconds: float = 0.0

    # Configuration used
    config: Dict[str, Any] = field(default_factory=dict)

    # Individual loop records
    loops: List[Dict] = field(default_factory=list)


class SessionLogger:
    """
    Session-based logger that saves all run information.

    Creates a session directory with:
    - config.json: All configuration options
    - prd_snapshot.json: PRD state at start
    - loop_NNN.log: Stream output for each loop
    - summary.json: Final summary report
    """

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
        logs_dir: Path,
        enable_colors: bool = True
    ):
        """
        Initialize session logger.

        Args:
            logs_dir: Base logs directory (.prd/logs/)
            enable_colors: Whether to use colors in console output
        """
        # Create session directory
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = logs_dir / f"session_{self.session_id}"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.config_file = self.session_dir / "config.json"
        self.prd_snapshot_file = self.session_dir / "prd_snapshot.json"
        self.summary_file = self.session_dir / "summary.json"

        # State
        self.start_time = datetime.now()
        self.loop_records: List[LoopRecord] = []
        self.current_loop: Optional[LoopRecord] = None
        self.current_loop_file: Optional[TextIO] = None
        self.timers: Dict[str, float] = {}

        # Summary tracking
        self.summary = SessionSummary(
            session_id=self.session_id,
            start_time=self.start_time.isoformat()
        )

        # Colors
        if not enable_colors or not sys.stdout.isatty():
            Colors.disable()

        # Main log file for overall session
        self.main_log_file = self.session_dir / "session.log"
        self.main_log_handle = open(self.main_log_file, "w", encoding="utf-8")

    def save_config(self, config: Any) -> None:
        """Save configuration at session start."""
        if hasattr(config, 'to_dict'):
            config_data = config.to_dict()
        elif hasattr(config, '__dict__'):
            config_data = {k: v for k, v in config.__dict__.items()
                         if not k.startswith('_')}
        else:
            config_data = dict(config)

        self.summary.config = config_data

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, default=str)

        self.info(f"Config saved to {self.config_file.name}")

    def save_prd_snapshot(self, prd: Any) -> None:
        """Save PRD snapshot at session start."""
        if hasattr(prd, 'to_dict'):
            prd_data = prd.to_dict()
        else:
            prd_data = dict(prd)

        with open(self.prd_snapshot_file, "w", encoding="utf-8") as f:
            json.dump(prd_data, f, indent=2, default=str)

        # Update summary
        self.summary.project = prd_data.get("project", "")
        self.summary.total_stories = len(prd_data.get("userStories", []))
        self.summary.stories_completed = sum(
            1 for s in prd_data.get("userStories", []) if s.get("passes", False)
        )

        self.info(f"PRD snapshot saved to {self.prd_snapshot_file.name}")

    def save_run_args(self, args: Any) -> None:
        """Save command-line arguments."""
        args_file = self.session_dir / "args.json"

        if hasattr(args, '__dict__'):
            args_data = vars(args)
        else:
            args_data = dict(args)

        # Convert Path objects to strings
        args_data = {k: str(v) if isinstance(v, Path) else v
                    for k, v in args_data.items()}

        with open(args_file, "w", encoding="utf-8") as f:
            json.dump(args_data, f, indent=2, default=str)

        self.info(f"Arguments saved to {args_file.name}")

    def start_loop(self, loop_num: int, story_id: str, story_title: str) -> Path:
        """
        Start a new loop iteration.

        Args:
            loop_num: Loop iteration number
            story_id: Current story ID
            story_title: Current story title

        Returns:
            Path to the loop log file for stream output
        """
        # Close previous loop file if open
        if self.current_loop_file:
            self.current_loop_file.close()
            self.current_loop_file = None

        # Create loop record
        log_filename = f"loop_{loop_num:03d}.jsonl"
        log_path = self.session_dir / log_filename

        self.current_loop = LoopRecord(
            loop_num=loop_num,
            story_id=story_id,
            story_title=story_title,
            start_time=datetime.now().isoformat(),
            log_file=log_filename
        )

        # Open log file for this loop (raw JSONL from Claude stream-json)
        self.current_loop_file = open(log_path, "w", encoding="utf-8")

        # Start timer
        self.timers[f"loop_{loop_num}"] = time.time()

        self.separator()
        self.loop(f"Loop #{loop_num} started: {story_id} - {story_title}")

        return log_path

    def get_loop_log_file(self) -> Optional[TextIO]:
        """Get the current loop's log file handle for stream output."""
        return self.current_loop_file

    def end_loop(
        self,
        success: bool,
        story_passed: bool = False,
        timeout: bool = False,
        error: str = "",
        api_duration: float = 0.0
    ) -> float:
        """
        End the current loop iteration.

        Returns:
            Total loop duration in seconds
        """
        if not self.current_loop:
            return 0.0

        # Calculate duration
        timer_key = f"loop_{self.current_loop.loop_num}"
        duration = time.time() - self.timers.get(timer_key, time.time())
        if timer_key in self.timers:
            del self.timers[timer_key]

        # Update loop record
        self.current_loop.end_time = datetime.now().isoformat()
        self.current_loop.duration_seconds = duration
        self.current_loop.api_duration_seconds = api_duration
        self.current_loop.success = success
        self.current_loop.story_passed = story_passed
        self.current_loop.timeout = timeout
        self.current_loop.error = error

        # Close loop log file (raw JSONL, no footer needed — metadata is in summary.json)
        if self.current_loop_file:
            self.current_loop_file.close()
            self.current_loop_file = None

        # Save to records
        self.loop_records.append(self.current_loop)

        # Update summary stats
        self.summary.total_loops += 1
        if success:
            self.summary.successful_loops += 1
        else:
            self.summary.failed_loops += 1
        if story_passed:
            self.summary.stories_completed_this_session += 1
        self.summary.total_api_time_seconds += api_duration

        # Log completion
        status = "SUCCESS" if success else "FAILED"
        self.log(
            status if success else "ERROR",
            f"Loop #{self.current_loop.loop_num} completed in {self.format_duration(duration)} "
            f"(API: {self.format_duration(api_duration)})"
        )

        self.current_loop = None
        return duration

    def finalize(
        self,
        exit_reason: str,
        total_api_calls: int,
        stories_completed: int,
        total_stories: int,
        prd_file: str = ""
    ) -> None:
        """
        Finalize the session and write summary.

        Args:
            exit_reason: Why the session ended
            total_api_calls: Total API calls made
            stories_completed: Stories completed (overall)
            total_stories: Total stories in PRD
            prd_file: Path to PRD file
        """
        # Close any open loop file
        if self.current_loop_file:
            self.current_loop_file.close()
            self.current_loop_file = None

        # Calculate final stats
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        # Update summary
        self.summary.end_time = end_time.isoformat()
        self.summary.total_duration_seconds = total_duration
        self.summary.exit_reason = exit_reason
        self.summary.prd_file = prd_file
        self.summary.total_api_calls = total_api_calls
        self.summary.stories_completed = stories_completed
        self.summary.total_stories = total_stories

        if self.summary.total_loops > 0:
            self.summary.avg_loop_duration_seconds = (
                total_duration / self.summary.total_loops
            )

        # Add loop records
        self.summary.loops = [asdict(r) for r in self.loop_records]

        # Write summary
        with open(self.summary_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self.summary), f, indent=2, default=str)

        # Log final summary
        self.separator()
        self.stats("=" * 40)
        self.stats("SESSION SUMMARY")
        self.stats("=" * 40)
        self.stats(f"Session ID: {self.session_id}")
        self.stats(f"Exit Reason: {exit_reason}")
        self.stats(f"Total Duration: {self.format_duration(total_duration)}")
        self.stats(f"Total Loops: {self.summary.total_loops}")
        self.stats(f"Successful Loops: {self.summary.successful_loops}")
        self.stats(f"Failed Loops: {self.summary.failed_loops}")
        self.stats(f"Stories Completed This Session: {self.summary.stories_completed_this_session}")
        self.stats(f"Overall Progress: {stories_completed}/{total_stories}")
        self.stats(f"Total API Calls: {total_api_calls}")
        self.stats(f"Total API Time: {self.format_duration(self.summary.total_api_time_seconds)}")
        self.stats("=" * 40)
        self.info(f"Session logs saved to: {self.session_dir}")
        self.info(f"Summary: {self.summary_file}")

        # Close main log
        if self.main_log_handle:
            self.main_log_handle.close()

    # Logging methods
    def _format_message(self, level: str, message: str) -> tuple:
        """Format log message for console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = self.LEVEL_COLORS.get(level, Colors.NC)
        console_msg = f"{color}[{timestamp}] [{level}] {message}{Colors.NC}"
        file_msg = f"[{timestamp}] [{level}] {message}"
        return console_msg, file_msg

    def log(self, level: str, message: str) -> None:
        """Log a message to console and file."""
        console_msg, file_msg = self._format_message(level, message)
        print(console_msg)
        if self.main_log_handle:
            self.main_log_handle.write(file_msg + "\n")
            self.main_log_handle.flush()

    def info(self, message: str) -> None:
        self.log("INFO", message)

    def warn(self, message: str) -> None:
        self.log("WARN", message)

    def error(self, message: str) -> None:
        self.log("ERROR", message)

    def success(self, message: str) -> None:
        self.log("SUCCESS", message)

    def loop(self, message: str) -> None:
        self.log("LOOP", message)

    def stats(self, message: str) -> None:
        self.log("STATS", message)

    def separator(self, char: str = "=", width: int = 60) -> None:
        """Log a visual separator line."""
        line = char * width
        print(f"{Colors.PURPLE}{line}{Colors.NC}")
        if self.main_log_handle:
            self.main_log_handle.write(line + "\n")
            self.main_log_handle.flush()

    def log_stats(
        self,
        api_calls: int,
        max_calls: int,
        stories_done: int,
        total_stories: int
    ) -> None:
        """Log progress statistics."""
        runtime = self.format_duration(
            (datetime.now() - self.start_time).total_seconds()
        )
        self.stats(
            f"Runtime: {runtime} | "
            f"API calls: {api_calls}/{max_calls} | "
            f"Stories: {stories_done}/{total_stories}"
        )

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

    # Timer methods for backwards compatibility
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
