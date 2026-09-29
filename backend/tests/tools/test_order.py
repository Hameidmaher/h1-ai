"""Tests for order creation tool."""
import pytest
from chatbot.tools.registry import get_registry


PHARMACY_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_create_order_simple():
    """طلب بدون روشتة."""
    r = await get_registry().execute(
        name="create_order",
        arguments={"drug_name": "بنادول", "quantity": 1},
        context={"pharmacy_id": PHARMACY_ID, "customer_id": None},
    )
    assert r.success is True
    assert r.data["created"] is True
    assert r.data["order_no"].startswith("ORD-")
    assert r.data["total"] > 0


@pytest.mark.asyncio
async def test_create_order_requires_prescription():
    """دواء محتاج روشتة — الأداة ترفض."""
    r = await get_registry().execute(
        name="create_order",
        arguments={"drug_name": "أوجمنتين", "quantity": 1},
        context={"pharmacy_id": PHARMACY_ID, "customer_id": None},
    )
    assert r.success is True
    assert r.data["created"] is False
    assert r.data.get("requires_prescription") is True
