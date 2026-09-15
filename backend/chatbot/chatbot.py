"""ChatBot — with corrected circuit breaker logic.

Circuit breaker only trips on EXCEPTIONS, not on "no match".
"""
from __future__ import annotations
from dataclasses import dataclass
from chatbot.rule_engine import rule_engine
from chatbot.circuit_breaker import CircuitBreaker
import structlog

logger = structlog.get_logger()


@dataclass
class ChatBotResponse:
    text: str
    method: str
    confidence: float


class ChatBot:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.breaker = CircuitBreaker()

    def is_available(self) -> bool:
        """Check if chatbot is enabled and breaker is closed."""
        return self.enabled and self.breaker.is_available()

    def try_quick_response(self, message: str) -> ChatBotResponse | None:
        """Try rule-based response.

        Circuit breaker semantics:
        - record_success: rule engine ran without exception
        - record_failure: rule engine raised an exception

        A "no match" is NOT a failure — it's just no matching rule.
        """
        if not self.is_available():
            logger.debug("chatbot.unavailable")
            return None

        try:
            match = rule_engine.match(message)
            # Rule engine ran fine (whether it matched or not)
            self.breaker.record_success()

            if match:
                return ChatBotResponse(
                    text=match.response,
                    method=f"rule:{match.rule_id}",
                    confidence=match.confidence,
                )
            # No match — that's fine, fall through to next handler
            return None

        except Exception as e:
            # Only actual exceptions trip the breaker
            logger.error("chatbot.rule_error", error=str(e)[:200])
            self.breaker.record_failure()
            return None

    def get_stats(self) -> dict:
        """Expose breaker stats for monitoring."""
        return {
            "enabled": self.enabled,
            "available": self.is_available(),
            "failure_count": self.breaker.failure_count,
            "is_broken": self.breaker.broken_until > 0,
        }


chatbot = ChatBot(enabled=True)
