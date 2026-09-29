"""Tests for drug_search tool."""
import pytest
from chatbot.tools.registry import get_registry


@pytest.mark.asyncio
async def test_search_drug_by_trade_name_arabic():
    """البحث بالاسم العربي."""
    r = await get_registry().execute(
        name="search_drug",
        arguments={"query": "بنادول", "limit": 5},
    )
    assert r.success is True
    assert r.data["count"] >= 1
    names = [d.get("name_ar") or d.get("name_en", "") for d in r.data["drugs"]]
    assert any("بنادول" in n for n in names)


@pytest.mark.asyncio
async def test_search_drug_by_english_name():
    """البحث بالاسم الإنجليزي."""
    r = await get_registry().execute(
        name="search_drug",
        arguments={"query": "Panadol", "limit": 5},
    )
    assert r.success is True
    assert r.data["count"] >= 1


@pytest.mark.asyncio
async def test_search_drug_by_scientific_name():
    """البحث بالاسم العلمي."""
    r = await get_registry().execute(
        name="search_drug",
        arguments={"query": "Paracetamol", "limit": 5},
    )
    assert r.success is True
    assert r.data["count"] >= 1


@pytest.mark.asyncio
async def test_search_drug_not_found():
    """دواء مش موجود."""
    r = await get_registry().execute(
        name="search_drug",
        arguments={"query": "Zzzzzzzz9999", "limit": 5},
    )
    assert r.success is True
    assert r.data["count"] == 0
