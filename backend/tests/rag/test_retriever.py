"""Tests for RAG retriever."""
import pytest
from chatbot.rag.retriever import get_rag, detect_category


def test_detect_category_mo3id():
    assert detect_category("بتفتحوا امتى؟") == "مواعيد العمل"
    assert detect_category("مواعيد العمل ايه؟") == "مواعيد العمل"


def test_detect_category_delivery():
    assert detect_category("بتوصلوا للبيت؟") == "التوصيل للمنزل"
    assert detect_category("فيه دليفري؟") == "التوصيل للمنزل"


def test_detect_category_payment():
    assert detect_category("طرق الدفع ايه؟") == "طرق الدفع"
    assert detect_category("بتقبلوا فيزا؟") == "طرق الدفع"


def test_detect_category_none():
    assert detect_category("عايز حاجة للصداع") is None


@pytest.mark.asyncio
async def test_rag_search_mo3id():
    rag = get_rag()
    results = await rag.search("بتفتحوا امتى؟", limit=3)
    assert len(results) >= 1
    assert results[0]["match_type"] == "category"
    assert "مواعيد" in results[0]["title"]
    assert "9" in results[0]["content"] or "٩" in results[0]["content"]


@pytest.mark.asyncio
async def test_rag_search_delivery():
    rag = get_rag()
    results = await rag.search("بتوصلوا للبيت؟", limit=3)
    assert len(results) >= 1
    assert "15" in results[0]["content"]


@pytest.mark.asyncio
async def test_rag_search_no_match():
    rag = get_rag()
    results = await rag.search("asdfghjklzxcvbnm123", limit=3)
    assert len(results) == 0 or results[0].get("match_type") == "vector"
