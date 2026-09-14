import time
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout: int = 60
    failure_count: int = 0
    broken_until: float = 0.0

    def is_available(self) -> bool:
        if self.broken_until == 0.0:
            return True
        if time.time() > self.broken_until:
            self.failure_count = 0
            self.broken_until = 0.0
            logger.info("circuit_breaker.recovered")
            return True
        return False

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.broken_until = time.time() + self.recovery_timeout
            logger.error("circuit_breaker.opened",
                         failures=self.failure_count)

    def record_success(self) -> None:
        self.failure_count = 0
