"""Knowledge Base Search Tool"""
from __future__ import annotations
from chatbot.tools.registry import Tool, ToolResult
from chatbot.rag.retriever import get_rag


async def search_knowledge_handler(query: str, limit: int = 3) -> ToolResult:
    """ابحث في knowledge_base بالـ embeddings."""
    rag = get_rag()

    # ⚠️ مهم: search بيرجع dict بـ id, category, title, content
    results = await rag.search(query, limit=limit)

    if not results:
        return ToolResult.ok(
            data={"found": False, "results": []},
            message="مفيش نتائج مطابقة في قاعدة المعرفة",
        )

    # رتّب النتائج — الأفضل similarity الأول
    results = sorted(results, key=lambda x: x.get("similarity", 0), reverse=True)

    return ToolResult.ok(
        data={
            "found": True,
            "count": len(results),
            "results": [
                {
                    "category": r["category"],
                    "title": r["title"],
                    "content": r["content"],  # ← النص الكامل
                    "similarity": round(r.get("similarity", 0), 3),
                }
                for r in results
            ],
        },
        message=f"لقيت {len(results)} معلومة",
    )


KNOWLEDGE_TOOLS = [
    Tool(
        name="search_knowledge",
        description=(
            "ابحث في قاعدة المعرفة الرسمية للصيدلية. "
            "**لازم تستخدمها لكل سؤال عن:** "
            "1) مواعيد العمل، "
            "2) التوصيل والدليفري، "
            "3) طرق الدفع، "
            "4) سياسة الاسترجاع، "
            "5) الروشتة الطبية، "
            "6) الخصوصية، "
            "7) أي نصيحة صحية عامة، "
            "8) أي سياسة أو معلومة عن الصيدلية. "
            "🔴 مهم: لو العميل سأل سؤال عام (مش عن دواء معين)، "
            "استدعي الأداة دي دايماً قبل الرد — "
            "لأن سياساتنا وقوانيننا قد تختلف عن المعلومات العامة. "
            "ممنوع تختلق معلومات!"
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "الموضوع اللي بيدور عليه (مثلاً: 'مواعيد', 'دليفري', 'دفع', 'روشتة')",
                },
                "limit": {
                    "type": "integer",
                    "default": 3,
                    "description": "أقصى عدد نتائج (افتراضي 3)",
                },
            },
            "required": ["query"],
        },
        handler=search_knowledge_handler,
    ),
]
