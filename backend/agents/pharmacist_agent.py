from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import (
    ToolMessage,
    BaseMessage, SystemMessage, AIMessage, HumanMessage,
)
from agents.tools import PHARMACIST_TOOLS, PHARMACIST_ALLOWED_TOOL_NAMES
from agents.guardrails import check_tool_calls_allowed, make_refusal_message
from models.schemas import AgentResponse
from llm.factory import create_llm
import structlog

logger = structlog.get_logger()

# ═══════════════════════════════════════════════════════════
# needs_human detection logic
# ═══════════════════════════════════════════════════════════
def should_need_human(text: str, original_message: str = "") -> bool:
    """تحديد إذا كان الرد يحتاج تدخل بشري."""
    if not text:
        return False
    
    # ═══ 1. ردود أسعار/منتجات → مش محتاج (حتى لو فيها "جرعة")
    price_indicators = ["السعر", "الكود", "ج.م", "جنيه", "الكمية المتوفرة", "كود الصنف"]
    if any(k in text for k in price_indicators):
        # إذا كان الرد فيه جدول أسعار → مش محتاج
        if "|" in text and ("السعر" in text or "الكود" in text):
            return False
    
    # ═══ 2. ردود غير طبية (greetings, thanks) → مش محتاج
    non_medical = [
        "كيف يمكنني مساعدتك", "كيف حالك", "أنا بخير", "مرحباً بك",
        "وعليكم السلام", "العفو", "أهلاً وسهلاً", "شكراً جزيلاً",
        "happy to help", "you're welcome",
    ]
    if any(phrase in text for phrase in non_medical):
        if len(text) < 200:
            return False
    
    # ═══ 3. ردود طبية/تحذيرية → محتاج
    medical_alerts = [
        "حساسية", "تداخل دوائي", "تحذير", "استشر طبيب", "استشارة",
        "الحمل", "الأطفال", "جرعة زائدة",
        "أعراض جانبية", "تفاعل دوائي", "منعت", "ممنوع",
    ]
    if any(k in text for k in medical_alerts):
        return True
    
    # ═══ 4. Emergency → محتاج (إلزامي)
    emergency = ["اتصل", "الطوارئ", "الإسعاف", "123", "فوراً"]
    if any(k in text for k in emergency):
        return True
    
    # ═══ 5. توصيات دوائية (بدون جدول) → محتاج
    medical_recs = ["يُنصح", "ينصح", "استخدم", "البديل", "تناول"]
    if any(k in text for k in medical_recs):
        # إذا كان الرد طبي (> 300 حرف) وبدون جدول أسعار
        if len(text) > 300 and "السعر" not in text:
            return True
    
    # ═══ 6. Default: مش محتاج
    return False
    
    text_lower = text.lower()
    
    # ═══ 1. ردود غير طبية (greetings, thanks) → مش محتاج
    non_medical = [
        "كيف يمكنني مساعدتك", "كيف حالك", "أنا بخير", "مرحباً بك",
        "وعليكم السلام", "العفو", "أهلاً وسهلاً", "شكراً جزيلاً",
        "happy to help", "you're welcome",
    ]
    if any(phrase in text for phrase in non_medical):
        # إذا كان الرد قصير (< 200 حرف) → مش محتاج
        if len(text) < 200:
            return False
    
    # ═══ 2. ردود طبية/تحذيرية → محتاج
    medical_alerts = [
        "حساسية", "تداخل دوائي", "تحذير", "استشر طبيب", "استشارة",
        "حامل", "الحمل", "طفل", "الأطفال", "جرعة زائدة",
        "أعراض جانبية", "تفاعل", "منعت", "ممنوع",
    ]
    if any(k in text for k in medical_alerts):
        return True
    
    # ═══ 3. Emergency → محتاج (بشكل إلزامي)
    emergency = ["اتصل", "الطوارئ", "الإسعاف", "123", "فوراً"]
    if any(k in text for k in emergency):
        return True
    
    # ═══ 4. توصيات دوائية → محتاج
    medical_recs = [
        "تناول", "الجرعة", "العلاج", "الدواء المناسب",
        "يُنصح", "ينصح", "استخدم", "البديل",
    ]
    if any(k in text for k in medical_recs):
        # فقط إذا كان الرد طبي (> 300 حرف)
        if len(text) > 300:
            return True
    
    # ═══ 5. Default: مش محتاج (للتقليل من false positives)
    return False



SYSTEM_PROMPT = (
    "أنت مساعد ذكي للصيادلة في H1-AI.\n\n"
    "مهامك:\n"
    "1. مراجعة التداخلات الدوائية.\n"
    "2. اقتراح بدائل من المخزون.\n"
    "3. تقارير المخزون والصلاحية.\n"
    "4. القرار النهائي للصيدلي البشري.\n\n"
    "أسلوبك: عربي مهني، موجز، منظّم."
)




# ═══════════════════════════════════════════════════════════
# MESSAGE SANITIZER — يضمن إن كل content string
# ═══════════════════════════════════════════════════════════
def _sanitize_messages(messages: list) -> list:
    """
    يضمن إن كل message عنده content من نوع string.
    ده يحل مشكلة Groq API:
    'messages.X.content' : value must be a string
    """
    sanitized = []
    for m in messages:
        # لو content مش string، نحوّله
        if hasattr(m, "content"):
            c = m.content
            if c is None:
                m.content = ""
            elif not isinstance(c, str):
                if isinstance(c, list):
                    # لو list من dicts/strings
                    parts = []
                    for item in c:
                        if isinstance(item, str):
                            parts.append(item)
                        elif isinstance(item, dict):
                            parts.append(item.get("text", str(item)))
                        else:
                            parts.append(str(item))
                    m.content = " ".join(parts) if parts else ""
                else:
                    m.content = str(c)
        sanitized.append(m)
    return sanitized


# ═══════════════════════════════════════════════════════════
# CUSTOM TOOL NODE — يضمن string content
# ═══════════════════════════════════════════════════════════

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
        wf.add_node("tools", self._call_tools_safe)  # ★ custom safe node
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
        # ★ إصلاح: sanitize قبل الإرسال للـ LLM
        sanitized_state = _sanitize_messages(list(state["messages"]))
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + sanitized_state
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

    def _call_tools_safe(self, state: AgentState):
        """
        ★ إصلاح: استدعاء الأدوات يدوياً مع ضمان string content.
        """
        last = state["messages"][-1]
        tool_calls = getattr(last, "tool_calls", []) or []

        tool_map = {t.name: t for t in PHARMACIST_TOOLS}
        tool_messages = []

        for tc in tool_calls:
            name = tc.get("name")
            args = tc.get("args", {})
            tc_id = tc.get("id", "")

            try:
                tool = tool_map.get(name)
                if tool:
                    result = tool.invoke(args)
                else:
                    result = f"أداة غير معروفة: {name}"
            except Exception as e:
                result = f"خطأ في تنفيذ {name}: {str(e)}"

            # ★ ضمان string
            if result is None:
                content = "لا توجد بيانات"
            elif isinstance(result, str):
                content = result
            elif isinstance(result, (list, dict)):
                import json as _json
                try:
                    content = _json.dumps(result, ensure_ascii=False)
                except Exception:
                    content = str(result)
            else:
                content = str(result)

            # لو فاضي، نحط رسالة افتراضية
            if not content or content.strip() == "":
                content = "لا توجد نتائج"

            tool_messages.append(ToolMessage(
                content=content,
                tool_call_id=tc_id,
                name=name,
            ))

        return {"messages": tool_messages}

    def _format_response(self, state: AgentState) -> dict:
        last = state["messages"][-1]
        # ★ ضمان string content
        if isinstance(last, AIMessage):
            c = last.content
            if c is None:
                last.content = ""
            elif not isinstance(c, str):
                if isinstance(c, list):
                    parts = []
                    for item in c:
                        if isinstance(item, str):
                            parts.append(item)
                        elif isinstance(item, dict):
                            parts.append(item.get("text", str(item)))
                        else:
                            parts.append(str(item))
                    last.content = " ".join(parts) if parts else ""
                else:
                    last.content = str(c)

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
            # ★ ضمان string
            c = last.content
            if c is None:
                text = ""
            elif isinstance(c, str):
                text = c
            elif isinstance(c, list):
                parts = []
                for item in c:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict):
                        parts.append(item.get("text", str(item)))
                    else:
                        parts.append(str(item))
                text = " ".join(parts) if parts else ""
            else:
                text = str(c)
            needs_human = should_need_human(text, message)
            return AgentResponse(
                text=text, action="answer",
                confidence=0.9, needs_human=needs_human,
            )
        except Exception as e:
            logger.error("pharmacist_agent.error", error=str(e))
            return AgentResponse(
                text="حدث خطأ مؤقت. حاول تاني.",
                action="answer", confidence=0.0,
            )
