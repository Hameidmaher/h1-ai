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
        return self.enabled and self.breaker.is_available()

    def try_quick_response(self, message: str) -> ChatBotResponse | None:
        if not self.is_available():
            return None
        try:
            match = rule_engine.match(message)
            if match:
                self.breaker.record_success()
                return ChatBotResponse(
                    text=match.response, method=f"rule:{match.rule_id}",
                    confidence=0.99,
                )
            self.breaker.record_success()
            return None
        except Exception as e:
            logger.error("chatbot.rule_error", error=str(e))
            self.breaker.record_failure()
            return None


chatbot = ChatBot(enabled=True)
