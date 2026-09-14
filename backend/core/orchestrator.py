"""Orchestrator — يقرر من يرد: ChatBot / Advisory / Agent."""
from __future__ import annotations
from dataclasses import dataclass
from knowledge.engine import advisory_engine
from chatbot.chatbot import chatbot
from agents.customer_agent import CustomerAgent
from agents.pharmacist_agent import PharmacistAgent
from models.schemas import AgentResponse
import structlog

logger = structlog.get_logger()


@dataclass
class OrchestratorResponse:
    response: AgentResponse
    handler: str
    route_method: str
    user_type: str


class Orchestrator:
    def __init__(self):
        self.customer_agent = CustomerAgent()
        self.pharmacist_agent = PharmacistAgent()

    def handle(self, message: str, user_role: str = "customer") -> OrchestratorResponse:
        user_type = "pharmacist" if user_role in ("pharmacist", "admin") else "customer"

        # 1) ChatBot rule (سريع جداً — للحيات والوداع)
        if user_type == "customer":
            quick = chatbot.try_quick_response(message)
            if quick:
                return OrchestratorResponse(
                    response=AgentResponse(
                        text=quick.text, action="answer",
                        confidence=quick.confidence,
                    ),
                    handler="chatbot",
                    route_method=quick.method,
                    user_type=user_type,
                )

        # 2) Advisory Engine (سريع — للاستعلامات)
        try:
            adv = advisory_engine.analyze(message)
            if adv.is_emergency:
                return OrchestratorResponse(
                    response=AgentResponse(
                        text=adv.emergency.message,
                        action="redirect_to_pharmacist",
                        confidence=1.0, needs_human=True,
                        advisory=adv.to_dict(),
                    ),
                    handler="advisory_emergency",
                    route_method="advisory",
                    user_type=user_type,
                )
            # ENHANCED-ADVISORY-FIRST
            # Strategy: إذا Advisory عندها نتيجة → استخدمها مباشرة
            # هذا يوفر 70% من LLM calls ويجعل الردود أسرع 50x
            if (adv.products or adv.advice or adv.conditions) and user_type == "customer":
                # ابنِ الرد النصي
                reply_text = adv.advice or ""
                if adv.products:
                    products_list = "\n".join([
                        f"• {p.name} — {p.price} EGP"
                        for p in adv.products[:3]
                    ])
                    if reply_text:
                        reply_text = f"{reply_text}\n\n{products_list}"
                    else:
                        reply_text = f"لقيت لك {len(adv.products)} منتجات:\n{products_list}"

                # أضف التحذيرات
                if adv.warnings:
                    warnings_text = "\n".join([
                        f"⚠️ {w.message}" for w in adv.warnings[:2]
                    ])
                    reply_text += f"\n\n{warnings_text}"

                return OrchestratorResponse(
                    response=AgentResponse(
                        text=reply_text,
                        action="answer",
                        confidence=adv.confidence,
                        products_referenced=[p.item_code for p in adv.products],
                        advisory=adv.to_dict(),
                    ),
                    handler="advisory",
                    route_method="advisory",
                    user_type=user_type,
                )

            # Fallback: Advisory بثقة عالية
            if adv.confidence > 0.85 and adv.has_direct_answer and user_type == "customer":
                return OrchestratorResponse(
                    response=AgentResponse(
                        text=adv.advice or "لقيت لك النتيجة",
                        action="answer",
                        confidence=adv.confidence,
                        advisory=adv.to_dict(),
                    ),
                    handler="advisory",
                    route_method=adv.method,
                    user_type=user_type,
                )
        except Exception as e:
            logger.warning("orchestrator.advisory_failed", error=str(e))

        # 3) Agent (للمعقّد)
        if user_type == "customer":
            resp = self.customer_agent.process(message)
        else:
            resp = self.pharmacist_agent.process(message)

        return OrchestratorResponse(
            response=resp,
            handler="agent",
            route_method="agent",
            user_type=user_type,
        )


orchestrator = Orchestrator()
