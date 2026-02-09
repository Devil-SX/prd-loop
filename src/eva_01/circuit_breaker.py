"""Simple circuit breaker for detecting stuck loops."""

from dataclasses import dataclass


@dataclass
class CircuitBreakerStatus:
    """Status of the circuit breaker."""
    consecutive_failures: int
    max_failures: int
    should_stop: bool
    reason: str = ""


class SimpleCircuitBreaker:
    """
    Simple circuit breaker that stops execution after consecutive failures.

    This is a simplified version that only tracks consecutive failures,
    without the full OPEN/HALF_OPEN/CLOSED state machine.
    """

    def __init__(self, max_failures: int = 3):
        """
        Initialize circuit breaker.

        Args:
            max_failures: Number of consecutive failures before stopping
        """
        self.max_failures = max_failures
        self.consecutive_failures = 0
        self.last_failure_reason = ""

    def record_success(self) -> None:
        """Record a successful iteration, resetting the failure count."""
        self.consecutive_failures = 0
        self.last_failure_reason = ""

    def record_failure(self, reason: str = "") -> None:
        """
        Record a failed iteration.

        Args:
            reason: Optional reason for the failure
        """
        self.consecutive_failures += 1
        self.last_failure_reason = reason

    def should_stop(self) -> bool:
        """
        Check if the circuit breaker has tripped.

        Returns:
            True if we should stop execution
        """
        return self.consecutive_failures >= self.max_failures

    def get_status(self) -> CircuitBreakerStatus:
        """
        Get current circuit breaker status.

        Returns:
            CircuitBreakerStatus with current state
        """
        should_stop = self.should_stop()
        reason = ""
        if should_stop:
            reason = f"Circuit breaker tripped after {self.consecutive_failures} consecutive failures"
            if self.last_failure_reason:
                reason += f": {self.last_failure_reason}"

        return CircuitBreakerStatus(
            consecutive_failures=self.consecutive_failures,
            max_failures=self.max_failures,
            should_stop=should_stop,
            reason=reason
        )

    def reset(self) -> None:
        """Reset the circuit breaker."""
        self.consecutive_failures = 0
        self.last_failure_reason = ""
