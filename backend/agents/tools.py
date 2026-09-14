"""Agent tools — يستخدمها Agent للوصول لبيانات المعرفة."""
from langchain_core.tools import tool
from knowledge.loader import knowledge_loader
from knowledge.engine import advisory_engine
import structlog

logger = structlog.get_logger()


@tool
def search_products(query: str, top_k: int = 5) -> list[dict]:
    """ابحث عن منتجات بالاسم أو الوصف."""
    logger.info("tool.search_products", query=query)
    results = advisory_engine.search(query, top_k=top_k)
    return [
        {
            "item_code": p.get("ItemCode", ""),
            "name": p.get("ItemName", ""),
            "category": p.get("Category", ""),
            "price": float(p.get("Price", 0)),
            "stock_qty": int(p.get("StockQty", 0)),
            "expiry_date": p.get("ExpiryDate", ""),
        }
        for p in results
    ]


@tool
def check_stock(item_code: str, qty: int = 1) -> dict:
    """تحقق من توفر منتج."""
    for p in knowledge_loader.products:
        if str(p.get("ItemCode", "")) == str(item_code):
            stock = int(p.get("StockQty", 0))
            return {
                "available": stock >= qty,
                "available_qty": stock,
                "name": p.get("ItemName", ""),
                "price": float(p.get("Price", 0)),
            }
    return {"available": False, "reason": "not_found"}


@tool
def get_low_stock_report(threshold: int = 5) -> list[dict]:
    """تقرير بالمنتجات اللي كميتها أقل من الحد. [صيدلي فقط]"""
    rows = [p for p in knowledge_loader.products
            if int(p.get("StockQty", 0)) < threshold]
    return [
        {
            "item_code": str(p.get("ItemCode", "")),
            "name": p.get("ItemName", ""),
            "stock_qty": int(p.get("StockQty", 0)),
        }
        for p in rows
    ]


@tool
def get_expiry_alerts(days: int = 90) -> list[dict]:
    """تقرير بالمنتجات اللي صلاحيتها قاربة. [صيدلي فقط]"""
    from datetime import datetime, timedelta
    cutoff = datetime.now() + timedelta(days=days)
    rows = []
    for p in knowledge_loader.products:
        try:
            exp = datetime.strptime(p.get("ExpiryDate", ""), "%Y-%m-%d")
            if exp <= cutoff:
                rows.append(p)
        except Exception:
            continue
    return [
        {
            "item_code": str(p.get("ItemCode", "")),
            "name": p.get("ItemName", ""),
            "expiry_date": p.get("ExpiryDate", ""),
        }
        for p in rows
    ]


@tool
def knowledge_search(query: str) -> dict:
    """بحث طبي موثوق. يستخدمها للحصول على معلومات دقيقة."""
    result = advisory_engine.analyze(query)
    return result.to_dict()


CUSTOMER_TOOLS = [search_products, check_stock, knowledge_search]
PHARMACIST_TOOLS = [
    search_products, check_stock, knowledge_search,
    get_low_stock_report, get_expiry_alerts,
]
CUSTOMER_ALLOWED_TOOL_NAMES = {t.name for t in CUSTOMER_TOOLS}
PHARMACIST_ALLOWED_TOOL_NAMES = {t.name for t in PHARMACIST_TOOLS}
