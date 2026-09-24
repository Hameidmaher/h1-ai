"""TeamMember Repository."""
from typing import Optional
from sqlalchemy.orm import Session
from db.models.team import TeamMember


class TeamRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> TeamMember:
        member = TeamMember(**kwargs)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_by_id(self, member_id: str) -> Optional[TeamMember]:
        return self.db.query(TeamMember).filter(TeamMember.id == member_id).first()

    def get_by_phone(self, phone: str) -> Optional[TeamMember]:
        return self.db.query(TeamMember).filter(TeamMember.phone == phone).first()

    def list_all(self, active_only: bool = True) -> list[TeamMember]:
        q = self.db.query(TeamMember)
        if active_only:
            q = q.filter(TeamMember.is_active == True)
        return q.all()

    def find_available(
        self,
        role: Optional[str] = None,
        specialty: Optional[str] = None,
        shift: Optional[str] = None,
        language: str = "ar",
    ) -> list[TeamMember]:
        """Find available team members matching criteria."""
        q = self.db.query(TeamMember).filter(
            TeamMember.is_active == True,
            TeamMember.is_available == True,
        )
        
        if role:
            q = q.filter(TeamMember.role == role)
        if shift:
            q = q.filter(TeamMember.shift == shift)
        
        members = q.all()
        
        # Filter by specialty (in JSON array)
        if specialty:
            members = [
                m for m in members
                if m.specialties and specialty in m.specialties
            ]
        
        # Filter by language
        members = [
            m for m in members
            if not m.languages or language in m.languages
        ]
        
        return members

    def find_least_loaded(self, **criteria) -> Optional[TeamMember]:
        """Find least loaded member matching criteria."""
        members = self.find_available(**criteria)
        if not members:
            return None
        
        # Filter by capacity
        members = [m for m in members if m.current_load < m.max_concurrent]
        if not members:
            return None
        
        # Sort by load
        members.sort(key=lambda m: m.current_load)
        return members[0]

    def increment_load(self, member_id: str) -> bool:
        member = self.get_by_id(member_id)
        if not member:
            return False
        member.current_load += 1
        if member.current_load >= member.max_concurrent:
            member.is_available = False
        self.db.commit()
        return True

    def decrement_load(self, member_id: str) -> bool:
        member = self.get_by_id(member_id)
        if not member:
            return False
        member.current_load = max(0, member.current_load - 1)
        if member.current_load < member.max_concurrent:
            member.is_available = True
        self.db.commit()
        return True

    def update(self, member_id: str, **fields) -> Optional[TeamMember]:
        member = self.get_by_id(member_id)
        if not member:
            return None
        for key, value in fields.items():
            if hasattr(member, key):
                setattr(member, key, value)
        self.db.commit()
        self.db.refresh(member)
        return member

    def delete(self, member_id: str) -> bool:
        member = self.get_by_id(member_id)
        if not member:
            return False
        self.db.delete(member)
        self.db.commit()
        return True

    def count(self) -> int:
        return self.db.query(TeamMember).count()

    def stats(self) -> dict:
        total = self.count()
        active = self.db.query(TeamMember).filter(TeamMember.is_active == True).count()
        available = self.db.query(TeamMember).filter(
            TeamMember.is_active == True,
            TeamMember.is_available == True,
        ).count()
        total_load = self.db.query(TeamMember).with_entities(
            __import__('sqlalchemy').func.sum(TeamMember.current_load)
        ).scalar() or 0
        return {
            "total": total,
            "active": active,
            "available": available,
            "total_load": total_load,
        }
