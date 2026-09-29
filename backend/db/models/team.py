"""Team Member — represents one of the 10 team members."""
from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON, Index
from sqlalchemy.sql import func
from db.base import Base


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(120), nullable=True, unique=True)
    
    # Role & expertise
    role = Column(String(30), nullable=False, default="pharmacist")
    # Roles: pharmacist, customer_service, manager, supervisor
    specialties = Column(JSON, default=list)
    # Specialties: prescriptions, interactions, inventory, complaints, general
    
    # Shift
    shift = Column(String(20), nullable=False, default="morning")
    # Shifts: morning, evening, night, flexible
    
    # Availability
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_available = Column(Boolean, default=True, nullable=False)
    max_concurrent = Column(Integer, default=10, nullable=False)
    current_load = Column(Integer, default=0, nullable=False)
    
    # Preferences
    languages = Column(JSON, default=lambda: ["ar"])
    whatsapp_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_team_role_active', 'role', 'is_active'),
        Index('idx_team_shift_active', 'shift', 'is_active'),
        Index('idx_team_load', 'current_load', 'is_available'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "name_ar": self.name_ar,
            "phone": self.phone,
            "email": self.email,
            "role": self.role,
            "specialties": self.specialties or [],
            "shift": self.shift,
            "is_active": self.is_active,
            "is_available": self.is_available,
            "max_concurrent": self.max_concurrent,
            "current_load": self.current_load,
            "languages": self.languages or ["ar"],
            "whatsapp_enabled": self.whatsapp_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }
