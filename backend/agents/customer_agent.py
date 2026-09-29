from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import (
    BaseMessage, SystemMessage, AIMessage, HumanMessage,
)
from agents.tools import CUSTOMER_TOOLS, CUSTOMER_ALLOWED_TOOL_NAMES
from agents.guardrails import check_tool_calls_allowed, make_refusal_message
from models.schemas import AgentResponse
from llm.factory import create_llm
import structlog

logger = structlog.get_logger()

SYSTEM_PROMPT = (
    "أنت مساعد ذكي لصيدلية H1-AI.\n\n"
    "مهامك:\n"
    "1. ساعد العملاء في البحث عن منتجات OTC والفيتامينات.\n"
    "2. استخدم الأدوات المتاحة للحصول على معلومات دقيقة.\n"
    "3. لا تختلق معلومات أبداً.\n\n"
    "محظور:\n"
    "- تشخيص الأمراض\n"
    "- اقتراح أدوية بوصفة\n"
    "- نصائح طبية\n\n"
    "عند أي سؤال طبي: وجّه العميل لرفع صورة الوصفة.\n"
    "أسلوبك: عربي فصيح، ودود، مختصر."
)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


class CustomerAgent:
    MAX_ITERATIONS = 5

    def __init__(self):
        self.llm = create_llm(temperature=0.3)
        self.llm_with_tools = self.llm.bind_tools(CUSTOMER_TOOLS)
        self.graph = self._build_graph()

    def _build_graph(self):
        wf = StateGraph(AgentState)
        wf.add_node("agent", self._call_model)
        wf.add_node("tools", ToolNode(CUSTOMER_TOOLS))
        wf.add_node("format", self._format_response)
        wf.set_entry_point("agent")
        wf.add_conditional_edges(
            "agent", self._should_continue,
            {"tools": "tools", "format": "format"},
        )
        wf.add_edge("tools", "agent")
        wf.add_edge("format", END)
        return wf.compile()

    def _call_model(self, state: AgentState):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = self.llm_with_tools.invoke(messages)
        if getattr(response, "tool_calls", None):
            allowed, reason = check_tool_calls_allowed(
                response.tool_calls, CUSTOMER_ALLOWED_TOOL_NAMES
            )
            if not allowed:
                return {"messages": [make_refusal_message(reason or "")]}
        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> str:
        last = state["messages"][-1]
        if not getattr(last, "tool_calls", None):
            return "format"
        count = sum(1 for m in state["messages"]
                    if isinstance(m, AIMessage) and m.tool_calls)
        if count >= self.MAX_ITERATIONS:
            return "format"
        return "tools"

    def _format_response(self, state: AgentState) -> dict:
        last = state["messages"][-1]
        if not isinstance(last, AIMessage) or not last.content:
            fallback = AIMessage(content=(
                "معلش، مقدرتش أفهم طلبك كويس. "
                "ممكن توضح أكتر؟"
            ))
            return {"messages": state["messages"] + [fallback]}
        return {"messages": state["messages"]}

    def process(self, message: str) -> AgentResponse:
        logger.info("customer_agent.process", message=message[:80])
        try:
            result = self.graph.invoke(
                {"messages": [HumanMessage(content=message)]},
            )
            last = result["messages"][-1]
            text = last.content if isinstance(last.content, str) else str(last.content)
            return AgentResponse(
                text=text, action="answer",
                confidence=0.85, needs_human=False,
            )
        except Exception as e:
            logger.error("customer_agent.error", error=str(e))
            return AgentResponse(
                text="عذراً، حدث خطأ مؤقت. حاول تاني.",
                action="answer", confidence=0.0,
            )
