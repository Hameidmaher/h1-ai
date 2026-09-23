"""Tests for drug search."""
import pytest
import asyncio


@pytest.mark.asyncio
async def test_search_paracetamol_arabic():
    from chatbot.tools.drug_search import search_drug_handler
    result = await search_drug_handler("الباراسيتامول", limit=3)
    assert result.success
    assert result.data["count"] > 0


@pytest.mark.asyncio
async def test_search_paracetamol_english():
    from chatbot.tools.drug_search import search_drug_handler
    result = await search_drug_handler("paracetamol", limit=3)
    assert result.success
    assert result.data["count"] > 0


@pytest.mark.asyncio
async def test_search_typo():
    from chatbot.tools.drug_search import search_drug_handler
    result = await search_drug_handler("باراسيتاموول", limit=3)
    assert result.success
    assert result.data["count"] > 0


@pytest.mark.asyncio
async def test_search_empty():
    from chatbot.tools.drug_search import search_drug_handler
    result = await search_drug_handler("", limit=3)
    assert result.success
    assert result.data["count"] == 0
