"""Order Flow — إدارة دورة حياة الطلب عبر WhatsApp."""
import structlog
from services.whatsapp_sender import whatsapp_sender

logger = structlog.get_logger()


class OrderFlow:
    """تدفق الطلب الكامل."""

    @staticmethod
    def format_order_message(
        customer_name: str,
        order_number: str,
        items: list,
        total: float,
        address: str,
        notes: str = "",
    ) -> str:
        """تنسيق رسالة تأكيد الطلب."""
        items_text = ""
        for item in items:
            name = item.get("name", "")
            qty = item.get("quantity", 1)
            items_text += f"🔹 {name} × {qty}\n"

        message = f"""مرحباً {customer_name} 👋

✅ تم استلام طلبك رقم *{order_number}* بنجاح

📋 *تفاصيل الطلب:*
{items_text}
💰 *إجمالي المبلغ:* {total} ج.م

📍 *عنوان التوصيل:*
{address}
"""

        if notes:
            message += f"\n📝 *ملاحظات:*\n{notes}\n"

        message += "\n━━━━━━━━━━━━━━━━\n"
        message += "يرجى تأكيد الطلب للبدء في التجهيز ⬇️"

        return message

    @staticmethod
    async def send_order_confirmation(
        phone: str,
        customer_name: str,
        order_number: str,
        items: list,
        total: float,
        address: str,
        notes: str = "",
    ) -> dict:
        """إرسال رسالة تأكيد الطلب مع أزرار."""
        message = OrderFlow.format_order_message(
            customer_name=customer_name,
            order_number=order_number,
            items=items,
            total=total,
            address=address,
            notes=notes,
        )

        buttons = [
            {"id": f"confirm_{order_number}", "title": "✅ تأكيد الطلب"},
            {"id": f"delay_{order_number}", "title": "🕐 تأجيل الطلب"},
            {"id": f"cancel_{order_number}", "title": "❌ إلغاء الطلب"},
        ]

        result = await whatsapp_sender.send_buttons(
            phone=phone,
            text=message,
            buttons=buttons,
            footer="H1-AI • صيدليتك الموثوقة",
        )

        logger.info(
            "order.confirmation_sent",
            phone=phone,
            order_number=order_number,
            success=result.get("success"),
        )

        return result

    @staticmethod
    async def handle_button_reply(phone: str, button_id: str) -> dict:
        """معالجة ضغط الزر."""
        if button_id.startswith("confirm_"):
            order_number = button_id.replace("confirm_", "")
            return await OrderFlow._confirm_order(phone, order_number)
        elif button_id.startswith("delay_"):
            order_number = button_id.replace("delay_", "")
            return await OrderFlow._delay_order(phone, order_number)
        elif button_id.startswith("cancel_"):
            order_number = button_id.replace("cancel_", "")
            return await OrderFlow._cancel_order(phone, order_number)
        else:
            return {"success": False, "error": "Unknown button"}

    @staticmethod
    async def _confirm_order(phone: str, order_number: str) -> dict:
        message = f"""✅ *تم تأكيد طلبك #{order_number}*

📦 جاري تجهيز الطلب
🚚 سيتم التواصل معك عند التوصيل

شكراً لثقتك بنا 🌿"""
        await whatsapp_sender.send_text(phone, message)
        return {"success": True, "action": "confirmed"}

    @staticmethod
    async def _delay_order(phone: str, order_number: str) -> dict:
        message = f"""🕐 *تم تأجيل الطلب #{order_number}*

سنتواصل معك قريباً لمعرفة الموعد المناسب.

إذا احتجت أي مساعدة، فقط اكتب لنا ✍️"""
        await whatsapp_sender.send_text(phone, message)
        return {"success": True, "action": "delayed"}

    @staticmethod
    async def _cancel_order(phone: str, order_number: str) -> dict:
        message = f"""❌ *تم إلغاء الطلب #{order_number}*

إذا كان هناك خطأ، تواصل معنا لإعادة الطلب.

نحن في خدمتك دائماً 💚"""
        await whatsapp_sender.send_text(phone, message)
        return {"success": True, "action": "cancelled"}


order_flow = OrderFlow()
