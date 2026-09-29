"""Tests for symptom search."""
import pytest


@pytest.mark.asyncio
async def test_search_sadr():
    from chatbot.tools.symptom_search import search_by_symptom_handler
    result = await search_by_symptom_handler("صداع", limit=3)
    assert result.success
    # ممكن يكون فيه نتائج أو لأ، مش مهم — المهم إنه ميرجعش exception


@pytest.mark.asyncio
async def test_extract_symptom():
    from chatbot.tools.symptom_search import _extract_symptom
    assert _extract_symptom("عندي صداع") == "صداع"
    assert _extract_symptom("عايز حاجة للكحة") == "حاجة للكحة"
