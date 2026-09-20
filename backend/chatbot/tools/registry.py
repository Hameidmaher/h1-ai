"""
Tool Registry — سجل أدوات الشات بوت
كل tool عبارة عن function + metadata
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
import structlog

logger = structlog.get_logger()


@dataclass
class ToolResult:
    """نتيجة تشغيل أداة."""
    success: bool
    data: Any = None
    message: str = ""
    error: str | None = None

    @classmethod
    def ok(cls, data: Any, message: str = ""):
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, error: str):
        return cls(success=False, error=error)


@dataclass
class Tool:
    """تعريف أداة واحدة."""
    name: str
    description: str
    parameters: dict                    # JSON schema للمعاملات
    handler: Callable[..., Awaitable[ToolResult]]
    requires_context: bool = False      # محتاجة pharmacy_id/customer_id؟

    def to_openai_schema(self) -> dict:
        """تحويل لـ OpenAI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """سجل مركزي للأدوات."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.warning("tool.duplicate", name=tool.name)
        self._tools[tool.name] = tool
        logger.info("tool.registered", name=tool.name)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def openai_schemas(self) -> list[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]

    async def execute(
        self,
        name: str,
        arguments: dict,
        context: dict | None = None,
    ) -> ToolResult:
        """تنفيذ أداة بالاسم مع المعاملات."""
        tool = self.get(name)
        if not tool:
            return ToolResult.fail(f"Tool '{name}' not found")

        try:
            if tool.requires_context and context:
                return await tool.handler(context=context, **arguments)
            return await tool.handler(**arguments)
        except Exception as e:
            logger.error("tool.exec_failed", name=name, error=str(e)[:200])
            return ToolResult.fail(f"{name}: {str(e)[:150]}")


# ═══════════════════════════════════════════════════════════
#  Global Registry
# ═══════════════════════════════════════════════════════════
_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """الحصول على السجل (singleton)."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_all(_registry)
    return _registry


def _register_all(registry: ToolRegistry) -> None:
    """تسجيل كل الأدوات المتاحة."""
    from chatbot.tools.drug_search import DRUG_SEARCH_TOOLS
    from chatbot.tools.inventory import INVENTORY_TOOLS
    from chatbot.tools.alternatives import ALTERNATIVE_TOOLS

    for tool in DRUG_SEARCH_TOOLS + INVENTORY_TOOLS + ALTERNATIVE_TOOLS:
        registry.register(tool)
