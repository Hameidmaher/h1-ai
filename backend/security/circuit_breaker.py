"""H1-AI Circuit Breaker for LLM calls."""
import time
import asyncio
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any
import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitStats:
    failures: int = 0
    successes: int = 0
    consecutive_failures: int = 0
    last_failure_time: float = 0.0
    total_calls: int = 0


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5,
                 recovery_timeout: int = 60, success_threshold: int = 2):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()

    def _should_reset(self) -> bool:
        return (self.state == CircuitState.OPEN and
                time.time() - self.stats.last_failure_time >= self.recovery_timeout)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if self._should_reset():
                logger.info(f"circuit.{self.name}.half_open")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(f"Circuit {self.name} is open")
        try:
            self.stats.total_calls += 1
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self.stats.successes += 1
            self.stats.consecutive_failures = 0
            if self.state == CircuitState.HALF_OPEN:
                if self.stats.successes >= self.success_threshold:
                    logger.info(f"circuit.{self.name}.closed")
                    self.state = CircuitState.CLOSED
                    self.stats.failures = 0
            return result
        except Exception as e:
            self.stats.failures += 1
            self.stats.consecutive_failures += 1
            self.stats.last_failure_time = time.time()
            logger.warning(f"circuit.{self.name}.failure",
                error=str(e)[:200],
                consecutive=self.stats.consecutive_failures)
            if self.stats.consecutive_failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(f"circuit.{self.name}.opened")
            raise

    def reset(self):
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        logger.info(f"circuit.{self.name}.manual_reset")


llm_breaker = CircuitBreaker("llm", 5, 60, 2)
advisory_breaker = CircuitBreaker("advisory", 3, 30, 1)
