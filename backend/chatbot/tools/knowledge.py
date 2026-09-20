"""Knowledge Base Search Tool"""
from __future__ import annotations
from chatbot.tools.registry import Tool, ToolResult
from chatbot.rag.retriever import get_rag


async def search_knowledge_handler(query: str, limit: int = 3) -> ToolResult:
    rag = get_rag()
    results = await rag.search(query, limit=limit)

    if not results:
        return ToolResult.ok(data={"results": [], "count": 0},
                             message="مفيش نتائج")

    return ToolResult.ok(
        data={"results": results, "count": len(results)},
        message=f"لقيت {len(results)} نتيجة",
    )


KNOWLEDGE_TOOLS = [
    Tool(
        name="search_knowledge",
        description=(
            "ابحث في قاعدة المعرفة (FAQs، سياسات الصيدلية، معلومات عامة). "
            "استخدمها لما العميل يسأل عن حاجة مش متعلقة بدواء معين."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 3},
            },
            "required": ["query"],
        },
        handler=search_knowledge_handler,
    ),
]
