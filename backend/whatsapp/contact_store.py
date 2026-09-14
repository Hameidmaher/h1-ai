"""
تخزين تصنيفات الأرقام (JSON-based)
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional
import structlog

logger = structlog.get_logger()


ContactType = Literal["customer", "supplier", "blacklist", "unknown"]


class ContactStore:
    """يدير contacts.json"""

    def __init__(self, path: str = "../data/contacts.json"):
        self.path = Path(path)
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._write({
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "contacts": {},
                "stats": {
                    "customer": 0,
                    "supplier": 0,
                    "blacklist": 0,
                },
            })
            logger.info("contact_store.created", path=str(self.path))

    def _read(self) -> dict:
        try:
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("contact_store.read_error", error=str(e))
            return {"contacts": {}, "stats": {}}

    def _write(self, data: dict) -> None:
        try:
            data["last_updated"] = datetime.now().isoformat()
            # احسب stats
            contacts = data.get("contacts", {})
            data["stats"] = {
                "customer": sum(1 for c in contacts.values() if c.get("type") == "customer"),
                "supplier": sum(1 for c in contacts.values() if c.get("type") == "supplier"),
                "blacklist": sum(1 for c in contacts.values() if c.get("type") == "blacklist"),
                "total": len(contacts),
            }
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("contact_store.write_error", error=str(e))

    def get(self, phone: str) -> Optional[dict]:
        """يعيد تصنيف الرقم."""
        data = self._read()
        return data.get("contacts", {}).get(phone)

    def get_type(self, phone: str) -> Optional[ContactType]:
        """يعيد نوع الرقم."""
        contact = self.get(phone)
        return contact.get("type") if contact else None

    def set(
        self,
        phone: str,
        contact_type: ContactType,
        name: str = "",
        note: str = "",
    ) -> None:
        """يعيّن تصنيف رقم."""
        data = self._read()
        data.setdefault("contacts", {})
        data["contacts"][phone] = {
            "type": contact_type,
            "name": name or data["contacts"].get(phone, {}).get("name", ""),
            "note": note,
            "added_at": datetime.now().isoformat(),
            "learned": False,
        }
        self._write(data)
        logger.info(
            "contact_store.set",
            phone=phone,
            type=contact_type,
            name=name,
        )

    def add_customer(self, phone: str, name: str = "") -> None:
        self.set(phone, "customer", name=name)

    def add_supplier(self, phone: str, name: str = "") -> None:
        self.set(phone, "supplier", name=name)

    def add_blacklist(self, phone: str, note: str = "") -> None:
        self.set(phone, "blacklist", note=note)

    def remove(self, phone: str) -> bool:
        """يحذف رقم."""
        data = self._read()
        if phone in data.get("contacts", {}):
            del data["contacts"][phone]
            self._write(data)
            return True
        return False

    def list_all(self, contact_type: Optional[ContactType] = None) -> list[dict]:
        """يعيد كل الأرقام (مفلترة حسب النوع)."""
        data = self._read()
        contacts = data.get("contacts", {})
        result = []
        for phone, info in contacts.items():
            if contact_type and info.get("type") != contact_type:
                continue
            result.append({"phone": phone, **info})
        return sorted(result, key=lambda x: x.get("added_at", ""), reverse=True)

    def get_stats(self) -> dict:
        """يعيد الإحصائيات."""
        data = self._read()
        return data.get("stats", {})


# Singleton
contact_store = ContactStore()
