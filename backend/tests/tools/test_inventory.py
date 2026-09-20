"""Tests for inventory tools."""
import pytest
from chatbot.tools.registry import get_registry


PHARMACY_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_check_availability_panadol():
    r = await get_registry().execute(
        name="check_availability",
        arguments={"drug_name": "بنادول"},
        context={"pharmacy_id": PHARMACY_ID},
    )
    assert r.success is True
    assert r.data["available"] is True
    assert len(r.data["matches"]) >= 1


@pytest.mark.asyncio
async def test_check_availability_no_pharmacy():
    r = await get_registry().execute(
        name="check_availability",
        arguments={"drug_name": "بنادول"},
        context={},
    )
    assert r.success is False


@pytest.mark.asyncio
async def test_check_price():
    r = await get_registry().execute(
        name="check_price",
        arguments={"drug_name": "بنادول"},
        context={"pharmacy_id": PHARMACY_ID},
    )
    assert r.success is True
    assert r.data["found"] is True
    assert r.data["prices"][0]["price"] > 0


@pytest.mark.asyncio
async def test_find_alternatives():
    r = await get_registry().execute(
        name="find_alternatives",
        arguments={"drug_name": "بنادول"},
        context={"pharmacy_id": PHARMACY_ID},
    )
    assert r.success is True
