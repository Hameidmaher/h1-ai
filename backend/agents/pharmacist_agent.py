from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import (
    BaseMessage, SystemMessage, AIMessage, HumanMessage,
)
from agents.tools import PHARMACIST_TOOLS, PHARMACIST_ALLOWED_TOOL_NAMES
from agents.guardrails import check_tool_calls_allowed, make_refusal_message
from models.schemas import AgentResponse
from llm.factory import create_llm
import structlog

logger = structlog.get_logger()

SYSTEM_PROMPT = (
    "أنت مساعد ذكي للصيادلة في H1-AI.\n\n"
    "مهامك:\n"
    "1. مراجعة التداخلات الدوائية.\n"
    "2. اقتراح بدائل من المخزون.\n"
    "3. تقارير المخزون والصلاحية.\n"
    "4. القرار النهائي للصيدلي البشري.\n\n"
    "أسلوبك: عربي مهني، موجز، منظّم."
)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


class PharmacistAgent:
    MAX_ITERATIONS = 6

    def __init__(self):
        self.llm = create_llm(temperature=0.2)
        self.llm_with_tools = self.llm.bind_tools(PHARMACIST_TOOLS)
        self.graph = self._build_graph()

    def _build_graph(self):
        wf = StateGraph(AgentState)
        wf.add_node("agent", self._call_model)
        wf.add_node("tools", ToolNode(PHARMACIST_TOOLS))
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
                response.tool_calls, PHARMACIST_ALLOWED_TOOL_NAMES
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
                "مقدرتش أجمع بيانات كافية. "
                "ممكن توضح الاستفسار بشكل أدق؟"
            ))
            return {"messages": state["messages"] + [fallback]}
        return {"messages": state["messages"]}

    def process(self, message: str) -> AgentResponse:
        logger.info("pharmacist_agent.process", message=message[:80])
        try:
            result = self.graph.invoke(
                {"messages": [HumanMessage(content=message)]},
            )
            last = result["messages"][-1]
            text = last.content if isinstance(last.content, str) else str(last.content)
            return AgentResponse(
                text=text, action="answer",
                confidence=0.9, needs_human=True,
            )
        except Exception as e:
            logger.error("pharmacist_agent.error", error=str(e))
            return AgentResponse(
                text="حدث خطأ مؤقت. حاول تاني.",
                action="answer", confidence=0.0,
            )
