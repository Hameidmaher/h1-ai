from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import (
    BaseMessage, SystemMessage, AIMessage, HumanMessage,
)
from agents.tools import PHARMACIST_TOOLS, PHARMACIST_ALLOWED_TOOL_NAMES
from agents.safety_guardrails import check_safety
from agents.guardrails import check_tool_calls_allowed, make_refusal_message
from models.schemas import AgentResponse
from llm.factory import create_llm
import structlog
from core.text_utils import normalize_message, should_use_normalized

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





# ═══════════════════════════════════════════════════════════
# SIMPLE SYNC CACHE
# ═══════════════════════════════════════════════════════════
import threading
import time

class SimpleCache:
    """Cache بسيط بيعمل في sync mode"""
    def __init__(self, ttl=300, max_size=500):
        self._cache = {}
        self._ttl = ttl
        self._max_size = max_size
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            if key not in self._cache:
                return None
            value, ts = self._cache[key]
            if time.time() - ts > self._ttl:
                del self._cache[key]
                return None
            return value

    def set(self, key: str, value):
        with self._lock:
            self._cache[key] = (value, time.time())
            if len(self._cache) > self._max_size:
                # نشيل الأقدم
                oldest = min(self._cache.items(), key=lambda x: x[1][1])
                del self._cache[oldest[0]]


_simple_cache = SimpleCache()




# ═══════════════════════════════════════════════════════════
# OUT-OF-SCOPE DETECTOR — Fallback ذكي
# ═══════════════════════════════════════════════════════════

# كلمات مفتاحية للنطاقات خارج التخصص
OUT_OF_SCOPE_KEYWORDS = {
    "طبخ": [
        "طبخ", "أطبخ", "اطبخ", "طبيخ", "وصفة", "كشري", "محشي",
        "مكرونة", "بامية", "ملوخية", "فتة", "شاورما", "بيتزا",
        "حلويات", "كيكة", "مقادير", "مكونات الطبق",
        "recipe", "cook", "bake",
    ],
    "سياسة": [
        "رئيس", "حكومة", "انتخابات", "وزير", "برلمان",
        "مرشح", "سياسي", "دولة", "سفير",
        "president", "election", "government",
    ],
    "ترفيه": [
        "فيلم", "مسلسل", "أغنية", "مغني", "ممثل", "ممثلة",
        "سينما", "نتفليكس", "يوتيوب", "دراما",
        "movie", "series", "song", "actor",
    ],
    "رياضة": [
        "ماتش", "مباراة", "كورة", "فريق", "لاعب", "دوري",
        "الأهلي", "الزمالك", "ريال", "برشلونة",
        "football", "match", "player",
    ],
    "برمجة_عام": [
        "بايثون", "جافا", "كود", "برمجة", "html", "css",
        "جافاسكريبت", "sql", "react", "node",
        "python", "javascript", "programming", "code",
    ],
    "دين": [
        "فتوى", "حلال", "حرام", "صلاة", "زكاة", "حج",
        "عمرة", "قرآن", "تفسير", "حديث",
        "religion", "prayer",
    ],
    "أخبار": [
        "خبر", "أخبار", "حدث", "كارثة", "زلزال",
        "حرب", "انفجار", "news",
    ],
    "تعليم_عام": [
        "مدرسة", "جامعة", "امتحان", "دراسة", "بحث",
        "رياضيات", "فيزياء", "كيمياء", "أحياء",
        "school", "university", "math", "physics",
    ],
}

# كلمات طبية/صحية — لو موجودة، نسامح الكلمات التانية
MEDICAL_OVERRIDE = [
    "دوا", "دواء", "أدوية", "حبوب", "حقنة", "شراب", "مرهم",
    "قطرة", "لبوس", "وصفة", "روشتة", "جرعة",
    "ألم", "وجع", "صداع", "حرارة", "سخونة", "كحة", "برد",
    "إسهال", "إمساك", "قيء", "غثيان", "دوخة", "دوار",
    "ضغط", "سكر", "قلب", "كبد", "كلى", "معدة", "قولون",
    "حساسية", "حامل", "مرضع", "طفل", "رضيع", "سن",
    "علاج", "مرض", "عرض", "أعراض", "تشخيص",
    "medicine", "drug", "symptom", "treatment", "dose",
    "medication", "pill", "pain", "fever", "cough",
]


def detect_out_of_scope(message: str) -> str | None:
    """
    يكتشف إذا كانت الرسالة خارج التخصص.
    يرجّع اسم النطاق أو None لو الرسالة طبية.
    """
    if not message:
        return None
    
    msg_lower = message.lower()
    
    # ★ أول حاجة: لو فيه كلمة طبية → مش خارج النطاق
    for kw in MEDICAL_OVERRIDE:
        if kw in msg_lower:
            return None
    
    # ★ تاني حاجة: نفحص النطاقات الخارجية
    for scope, keywords in OUT_OF_SCOPE_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                return scope.replace("_", " ")
    
    return None


def make_scope_response(scope: str) -> str:
    """رد مهني وودود للأسئلة خارج النطاق"""
    return (
        f"أنا مساعد صيدلي متخصص في **الأدوية والصحة** فقط. 💊\n\n"
        f"للأسف، **{scope}** خارج نطاق تخصصي، ومش هقدر أساعدك فيه.\n\n"
        "**لكن أنا هنا لو احتجت:**\n"
        "- استشارة عن دواء أو جرعة\n"
        "- فحص تفاعلات دوائية\n"
        "- اقتراح علاج لأعراض معينة\n"
        "- بدائل من المخزون\n\n"
        "قولّي، فيه حاجة صحية أقدر أساعدك فيها؟"
    )


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
# EMOTIONAL SUPPORT — ردود عاطفية
# ═══════════════════════════════════════════════════════════

EMOTIONAL_KEYWORDS = {
    "زهقان": "معلش، حسّ إنك مش لوحدك. 💙 خد نفس عميق، وحاول تتكلم مع حد قريب منك. أنا هنا لو عاوز تحكي.",
    "تعبان": "ربنا يعينك، تعبك ده محتاج راحة. لو التعب مستمر، يفضل تروح لدكتور.",
    "زعلان": "معلش، كلنا بنعدي بأوقات صعبة. 💙 خد وقتك، وافتكر إن كل حاجة بتعدي.",
    "مكتئب": "أنا آسف إنك حاسس كده. 💙 الاكتئاب مرض حقيقي وليه علاج. يفضل تتكلم مع طبيب نفسي متخصص.",
    "خايف": "طبيعي تخاف، بس متقلقش. لو الخوف مستمر، يفضل تتكلم مع حد متخصص.",
    "قلقان": "القلق حاجة طبيعية، بس لو بيأثر على حياتك، يفضل تروح لدكتور نفسي.",
    "وحيد": "مش لوحدك أبداً. 💙 حاول تتواصل مع أصحابك أو عيلتك، أو اتصل بخط دعم نفسي.",
    "محتار": "الحيرة طبيعية. خد وقتك وفكر بهدوء. لو محتاج مساعدة، أنا هنا.",
    "مش عارف": "مفيش مشكلة، ممكن نساعدك. قولّي بالظبط إيه اللي محتاجه.",
}

def check_emotional(message: str) -> str | None:
    """يفحص لو الرسالة عاطفية ويرجع رد مناسب"""
    for keyword, response in EMOTIONAL_KEYWORDS.items():
        if keyword in message:
            return response
    return None


MAX_HISTORY = 3  # آخر 3 رسائل فقط


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
        
        # ★ Cache lookup
        cached = _simple_cache.get(message)
        if cached is not None:
            logger.info("pharmacist_agent.cache_hit", message=message[:40])
            return cached
        
        # ★ ضمان string
        safe_message = str(message) if message else ""
        if not safe_message.strip():
            safe_message = "مرحبا"
        
        # ★★ Safety Check (قبل أي حاجة) ★★
        is_safe, safety_response = check_safety(safe_message)
        if not is_safe and safety_response:
            logger.warning("pharmacist_agent.safety_blocked",
                          message=safe_message[:50])
            return AgentResponse(
                text=safety_response,
                action="answer",
                confidence=1.0,
                needs_human=False,
            )
        
        # ★★ Emotional Support ★★
        emotional = check_emotional(safe_message)
        if emotional:
            logger.info("pharmacist_agent.emotional", message=safe_message[:50])
            return AgentResponse(
                text=emotional,
                action="answer",
                confidence=0.9,
                needs_human=False,
            )
        
        # ★★ Fuzzy Matching ★★
        normalized = normalize_message(safe_message)
        if should_use_normalized(safe_message, normalized):
            logger.info("pharmacist_agent.fuzzy",
                       original=safe_message[:50],
                       normalized=normalized[:50])
            safe_message = normalized
        
        # ★★ Out-of-Scope Detection (Fallback ذكي) ★★
        scope = detect_out_of_scope(safe_message)
        if scope:
            logger.info("pharmacist_agent.out_of_scope",
                       scope=scope, message=safe_message[:50])
            # ★ نستخدم LLM مباشرة لتوليد الرد
            try:
                from langchain_core.messages import SystemMessage as _SM
                scope_prompt = (
                    "أنت مساعد صيدلي في H1-AI. مهمتك الوحيدة: "
                    "الرد على الاستفسارات الطبية والصحية والدوائية.\n\n"
                    "المستخدم سأل سؤال خارج تخصصك الطبي.\n"
                    "رد عليه بلطف ومهنية، وضّح إن السؤال خارج نطاق تخصصك "
                    "الطبي، واقترح عليه يسأل عن أي شيء يتعلق بالصحة أو الأدوية.\n\n"
                    "اجعل الرد قصير (2-3 جمل) وودود ومهني. "
                    "لا تكرر السؤال ولا تذكر اسم النطاق بشكل سلبي."
                )
                resp = self.llm.invoke([
                    _SM(content=scope_prompt),
                    HumanMessage(content=safe_message),
                ])
                text = self._extract_text(resp)
                if text and len(text) >= 10:
                    response = AgentResponse(
                        text=text,
                        action="answer",  # ★ نستخدم "answer" بدل "redirect"
                        confidence=0.9,
                        needs_human=False,
                    )
                    _simple_cache.set(safe_message, response)
                    return response
            except Exception as e:
                logger.warning("pharmacist_agent.scope_llm_error", 
                              error=str(e)[:100])
            
            # ★ fallback: الرد الثابت
            response = AgentResponse(
                text=make_scope_response(scope),
                action="answer",  # ★ "answer"
                confidence=0.9,
                needs_human=False,
            )
            return response
        
        # ═══ محاولة 1: graph.invoke مع tools ═══
        try:
            # ★ تحديد آخر 3 رسائل فقط
            recent_history = []
            try:
                # نحاول نقرأ الـ history من الـ session
                from chatbot.memory.session import get_session_history
                recent_history = get_session_history(max_messages=MAX_HISTORY)
            except Exception:
                recent_history = []
            
            result = self.graph.invoke(
                {"messages": recent_history + [HumanMessage(content=safe_message)]},
            )
            last = result["messages"][-1]
            text = self._extract_text(last)
            
            if text and len(text) >= 5:
                needs_human = should_need_human(text, safe_message)
                response = AgentResponse(
                    text=text, action="answer",
                    confidence=0.9, needs_human=needs_human,
                )
                if len(text) >= 100:
                    _simple_cache.set(safe_message, response)
                return response
            else:
                logger.warning("pharmacist_agent.empty_response")
        except Exception as e:
            logger.error("pharmacist_agent.error", 
                        error=str(e)[:200],
                        message=safe_message[:50])
        
        # ═══ محاولة 2: LLM بدون tools (fallback) ═══
        try:
            logger.info("pharmacist_agent.fallback_no_tools", 
                       message=safe_message[:50])
            fallback_prompt = (
                SYSTEM_PROMPT + 
                "\n\nملاحظة: أجب بشكل مباشر ومختصر. "
                "لا تستخدم أدوات. إذا السؤال غير واضح، "
                "اسأل للتوضيح بشكل مهني."
            )
            from langchain_core.messages import SystemMessage as _SM
            resp = self.llm.invoke([
                _SM(content=fallback_prompt),
                HumanMessage(content=safe_message),
            ])
            text = self._extract_text(resp)
            if text and len(text) >= 5:
                response = AgentResponse(
                    text=text, action="answer",
                    confidence=0.7, needs_human=False,
                )
                if len(text) >= 100:
                    _simple_cache.set(safe_message, response)
                return response
        except Exception as e2:
            logger.error("pharmacist_agent.fallback_error", 
                        error=str(e2)[:200])
        
        # ═══ محاولة 3: رد افتراضي ═══
        return AgentResponse(
            text=(
                "عذراً، مش قادر أفهم استفسارك بشكل كامل. "
                "ممكن توضح أكتر؟ مثلاً:\n"
                "• بتشتكي من إيه بالظبط؟\n"
                "• من امتى؟\n"
                "• فيه أعراض تانية؟"
            ),
            action="ask",
            confidence=0.3,
            needs_human=False,
        )
    
    def _extract_text(self, msg) -> str:
        """يستخرج نص من أي message"""
        if msg is None:
            return ""
        c = getattr(msg, "content", None)
        if c is None:
            return ""
        if isinstance(c, str):
            return c.strip()
        if isinstance(c, list):
            parts = []
            for item in c:
                if isinstance(item, str):
                    if item.strip():
                        parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text") or item.get("content") or ""
                    if text:
                        parts.append(str(text))
            return " ".join(parts).strip()
        if isinstance(c, dict):
            text = c.get("text") or c.get("content") or ""
            return str(text).strip()
        return str(c).strip()