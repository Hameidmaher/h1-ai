def test_chatbot_greeting():
    from chatbot.chatbot import chatbot
    result = chatbot.try_quick_response("السلام عليكم")
    assert result is not None
    assert "وعليكم" in result.text


def test_chatbot_circuit_breaker():
    from chatbot.circuit_breaker import CircuitBreaker
    cb = CircuitBreaker(failure_threshold=2)
    assert cb.is_available()
    cb.record_failure()
    cb.record_failure()
    assert not cb.is_available()
