"""Multi-pharmacy service."""
from __future__ import annotations

from typing import Optional, List
from uuid import uuid4

import structlog
from sqlalchemy import text

from db import SessionLocal

logger = structlog.get_logger()


class PharmacyService:
    def list_pharmacies(self) -> List[dict]:
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT p.id::text, p.name, p.name_ar, p.phone, p.email,
                       p.city, p.subscription_plan, p.is_active, p.created_at,
                       (SELECT COUNT(*) FROM whatsapp_numbers WHERE pharmacy_id = p.id) AS numbers_count,
                       (SELECT COUNT(*) FROM products WHERE pharmacy_id = p.id) AS products_count,
                       (SELECT COUNT(*) FROM messages WHERE pharmacy_id = p.id) AS messages_count
                FROM pharmacies p
                ORDER BY p.created_at DESC
            """))
            return [dict(row._mapping) for row in result]
        finally:
            db.close()

    def get_pharmacy(self, pharmacy_id: str) -> Optional[dict]:
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT p.id::text, p.name, p.name_ar, p.phone, p.email,
                       p.address, p.city, p.subscription_plan,
                       p.subscription_expires_at, p.is_active, p.settings,
                       p.created_at, p.updated_at
                FROM pharmacies p WHERE p.id = :pid
            """), {"pid": pharmacy_id})
            row = result.first()
            return dict(row._mapping) if row else None
        finally:
            db.close()

    def create_pharmacy(self, data: dict) -> dict:
        db = SessionLocal()
        try:
            pid = str(uuid4())
            db.execute(text("""
                INSERT INTO pharmacies (id, name, name_ar, phone, email, address, city)
                VALUES (:id, :name, :name_ar, :phone, :email, :address, :city)
            """), {
                "id": pid,
                "name": data.get("name", ""),
                "name_ar": data.get("name_ar", ""),
                "phone": data.get("phone", ""),
                "email": data.get("email", ""),
                "address": data.get("address", ""),
                "city": data.get("city", ""),
            })
            db.commit()
            return self.get_pharmacy(pid)
        except Exception as e:
            db.rollback()
            logger.error("pharmacy.create_failed", error=str(e)[:200])
            raise
        finally:
            db.close()

    def update_pharmacy(self, pid: str, data: dict) -> Optional[dict]:
        db = SessionLocal()
        try:
            allowed = ["name", "name_ar", "phone", "email", "address", "city", "is_active"]
            updates = {k: v for k, v in data.items() if k in allowed}
            if not updates:
                return self.get_pharmacy(pid)
            
            set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
            updates["pid"] = pid
            db.execute(text(f"""
                UPDATE pharmacies SET {set_clause}, updated_at = NOW() WHERE id = :pid
            """), updates)
            db.commit()
            return self.get_pharmacy(pid)
        finally:
            db.close()

    def delete_pharmacy(self, pid: str) -> bool:
        db = SessionLocal()
        try:
            db.execute(text("""
                UPDATE pharmacies SET is_active = FALSE, updated_at = NOW() WHERE id = :pid
            """), {"pid": pid})
            db.commit()
            return True
        finally:
            db.close()

    def list_whatsapp_numbers(self, pharmacy_id: str = None) -> List[dict]:
        db = SessionLocal()
        try:
            if pharmacy_id:
                sql = """
                    SELECT w.id::text, w.pharmacy_id::text, p.name_ar AS pharmacy_name,
                           w.phone_number, w.display_name, w.mode,
                           w.is_active, w.is_primary, w.last_connected_at, w.created_at,
                           w.status, w.disconnected_at,
                           (SELECT COUNT(*) FROM messages WHERE pharmacy_id = w.pharmacy_id) AS messages_count
                    FROM whatsapp_numbers w
                    LEFT JOIN pharmacies p ON p.id = w.pharmacy_id
                    WHERE w.pharmacy_id = :pid
                    ORDER BY w.is_primary DESC, w.created_at ASC
                """
                params = {"pid": pharmacy_id}
            else:
                sql = """
                    SELECT w.id::text, w.pharmacy_id::text, p.name_ar AS pharmacy_name,
                           w.phone_number, w.display_name, w.mode,
                           w.is_active, w.is_primary, w.last_connected_at, w.created_at,
                           w.status, w.disconnected_at,
                           (SELECT COUNT(*) FROM messages WHERE pharmacy_id = w.pharmacy_id) AS messages_count
                    FROM whatsapp_numbers w
                    LEFT JOIN pharmacies p ON p.id = w.pharmacy_id
                    ORDER BY p.name_ar, w.is_primary DESC, w.created_at ASC
                """
                params = {}
            
            result = db.execute(text(sql), params)
            return [dict(row._mapping) for row in result]
        finally:
            db.close()

    def add_whatsapp_number(self, pharmacy_id: str, data: dict) -> dict:
        db = SessionLocal()
        try:
            nid = str(uuid4())
            count = db.execute(text("""
                SELECT COUNT(*) FROM whatsapp_numbers WHERE pharmacy_id = :pid
            """), {"pid": pharmacy_id}).scalar()
            
            is_primary = data.get("is_primary", count == 0)
            
            if is_primary:
                db.execute(text("""
                    UPDATE whatsapp_numbers SET is_primary = FALSE WHERE pharmacy_id = :pid
                """), {"pid": pharmacy_id})
            
            db.execute(text("""
                INSERT INTO whatsapp_numbers 
                    (id, pharmacy_id, phone_number, display_name, mode, is_active, is_primary)
                VALUES (:id, :pid, :phone, :name, :mode, TRUE, :primary)
            """), {
                "id": nid,
                "pid": pharmacy_id,
                "phone": data.get("phone_number", ""),
                "name": data.get("display_name", ""),
                "mode": data.get("mode", "link"),
                "primary": is_primary,
            })
            db.commit()
            return self._get_number(nid)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _get_number(self, nid: str) -> Optional[dict]:
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT w.id::text, w.pharmacy_id::text, w.phone_number,
                       w.display_name, w.mode, w.is_active, w.is_primary,
                       w.last_connected_at, w.created_at
                FROM whatsapp_numbers w WHERE w.id = :id
            """), {"id": nid})
            row = result.first()
            return dict(row._mapping) if row else None
        finally:
            db.close()

    def update_whatsapp_number(self, nid: str, data: dict) -> Optional[dict]:
        db = SessionLocal()
        try:
            allowed = ["phone_number", "display_name", "mode", "is_active", "is_primary"]
            updates = {k: v for k, v in data.items() if k in allowed}
            if not updates:
                return self._get_number(nid)
            
            if updates.get("is_primary"):
                pid = db.execute(text("""
                    SELECT pharmacy_id FROM whatsapp_numbers WHERE id = :id
                """), {"id": nid}).scalar()
                db.execute(text("""
                    UPDATE whatsapp_numbers SET is_primary = FALSE WHERE pharmacy_id = :pid
                """), {"pid": pid})
            
            set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
            updates["id"] = nid
            db.execute(text(f"""
                UPDATE whatsapp_numbers SET {set_clause}, updated_at = NOW()
                WHERE id = :id
            """), updates)
            db.commit()
            return self._get_number(nid)
        finally:
            db.close()

    def delete_whatsapp_number(self, nid: str) -> bool:
        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM whatsapp_numbers WHERE id = :id"), {"id": nid})
            db.commit()
            return True
        finally:
            db.close()



    def hard_delete(self, pharmacy_id: str) -> bool:
        """Hard delete pharmacy and all related data (CASCADE)."""
        db = SessionLocal()
        try:
            # Get WhatsApp numbers first for disconnection
            db.execute(text("""
                SELECT phone_number FROM whatsapp_numbers WHERE pharmacy_id = :pid
            """), {"pid": pharmacy_id}).fetchall()
            
            # Delete pharmacy (CASCADE will handle related data)
            result = db.execute(text("""
                DELETE FROM pharmacies WHERE id = :pid
            """), {"pid": pharmacy_id})
            db.commit()
            
            return result.rowcount > 0
        except Exception as e:
            db.rollback()
            logger.error("pharmacy.hard_delete_failed", error=str(e)[:200])
            raise
        finally:
            db.close()
    
    def full_update(self, pharmacy_id: str, data: dict) -> Optional[dict]:
        """Full update of pharmacy data."""
        db = SessionLocal()
        try:
            allowed = ["name", "name_ar", "phone", "email", "address", "city", "subscription_plan"]
            updates = {k: v for k, v in data.items() if k in allowed}
            
            if not updates:
                return self.get_pharmacy(pharmacy_id)
            
            set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
            updates["pid"] = pharmacy_id
            
            db.execute(text(f"""
                UPDATE pharmacies 
                SET {set_clause}, updated_at = NOW()
                WHERE id = :pid
            """), updates)
            db.commit()
            
            return self.get_pharmacy(pharmacy_id)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


pharmacy_service = PharmacyService()
