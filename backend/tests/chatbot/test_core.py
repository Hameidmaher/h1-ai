"""Tests for ChatbotCore."""
import pytest
from chatbot.core import ChatbotCore, FAQ_KEYWORDS


PHARMACY_ID = "00000000-0000-0000-0000-000000000001"


def test_faq_keywords_loaded():
    assert len(FAQ_KEYWORDS) > 15


def test_should_presearch_true():
    core = ChatbotCore()
    assert core._should_presearch("بتفتحوا امتى؟") is True
    assert core._should_presearch("طرق الدفع") is True
    assert core._should_presearch("توصيل") is True


def test_should_presearch_false():
    core = ChatbotCore()
    assert core._should_presearch("بنادول بكام") is False
    assert core._should_presearch("مرحبا") is False


@pytest.mark.asyncio
async def test_chat_faq_fastpath():
    """سؤال FAQ يرد بسرعة من DB."""
    core = ChatbotCore()
    r = await core.chat(
        message="بتفتحوا امتى؟",
        channel="test",
        channel_user_id="test_faq_001",
        pharmacy_id=PHARMACY_ID,
    )
    assert r.text
    assert len(r.text) > 20
    assert r.is_error is False
    # لازم يستخدم search_knowledge
    tools = [t["name"] for t in r.tool_calls]
    assert "search_knowledge" in tools


@pytest.mark.asyncio
async def test_chat_drug_query():
    """سؤال عن دواء."""
    core = ChatbotCore()
    r = await core.chat(
        message="عندك بنادول؟",
        channel="test",
        channel_user_id="test_drug_001",
        pharmacy_id=PHARMACY_ID,
    )
    assert r.text
    assert r.is_error is False
