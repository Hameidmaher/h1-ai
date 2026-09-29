"""Tests for guardrails."""
import pytest
from security.guardrails import input_guard, output_guard


class TestInputGuardrails:
    def test_emergency_chest_pain(self):
        assert not input_guard.check("عندي ألم في الصدر").is_safe

    def test_emergency_breathing(self):
        assert not input_guard.check("صعوبة في التنفس").is_safe

    def test_self_harm(self):
        assert not input_guard.check("عايز أنهي حياتي").is_safe

    def test_forbidden_drugs(self):
        assert not input_guard.check("عايز أشتري مخدرات").is_safe

    def test_normal_question(self):
        assert input_guard.check("إيه استخدام الباراسيتامول؟").is_safe

    def test_empty_message(self):
        assert not input_guard.check("").is_safe


class TestOutputGuardrails:
    def test_safe_response(self):
        result = output_guard.check("أهلاً بك، كيف أساعدك؟")
        assert result.is_safe


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
