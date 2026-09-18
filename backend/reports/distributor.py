"""Team Distributor — assigns reports to team members.

Strategy:
1. Filter by specialty (must match at least one)
2. Filter by shift (current shift preferred)
3. Filter by language (must speak the customer's language)
4. Filter by capacity (current_load < max_concurrent)
5. Sort by load (least loaded first)
6. Sort by shift priority (matching shift first)
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import structlog

from db.repositories import TeamRepository

logger = structlog.get_logger()


# ═══════════════════════════════════════════════════════
# Shift detection by hour (Egypt time)
# ═══════════════════════════════════════════════════════
def get_current_shift(hour: Optional[int] = None) -> str:
    """Detect current shift by hour.
    
    Morning:   06:00 - 14:00
    Evening:   14:00 - 22:00
    Night:     22:00 - 06:00
    """
    if hour is None:
        hour = datetime.now().hour
    
    if 6 <= hour < 14:
        return "morning"
    elif 14 <= hour < 22:
        return "evening"
    else:
        return "night"


@dataclass
class DistributionResult:
    """Result of distribution attempt."""
    member_id: Optional[str]
    member_name: Optional[str]
    strategy: str
    reason: str
    candidates_count: int
    success: bool


class TeamDistributor:
    """Assigns reports to team members."""
    
    def __init__(self):
        self._current_shift = None
    
    @property
    def current_shift(self) -> str:
        if self._current_shift is None:
            self._current_shift = get_current_shift()
        return self._current_shift
    
    def refresh_shift(self) -> str:
        """Refresh shift (call periodically)."""
        self._current_shift = get_current_shift()
        return self._current_shift
    
    def distribute(
        self,
        team_repo: TeamRepository,
        report_id: str,
        specialty_required: list[str],
        priority: str = "normal",
        language: str = "ar",
        preferred_shift: Optional[str] = None,
    ) -> DistributionResult:
        """Find best team member for a report.
        
        Returns DistributionResult with member_id if found.
        """
        shift = preferred_shift or self.current_shift
        
        # Get all available members
        all_members = team_repo.list_all(active_only=True)
        candidates_count = len(all_members)
        
        if not all_members:
            logger.warning("distributor.no_members")
            return DistributionResult(
                member_id=None,
                member_name=None,
                strategy="none",
                reason="no active team members",
                candidates_count=0,
                success=False,
            )
        
        # ─── Step 1: Filter by capacity ───
        members = [
            m for m in all_members
            if m.current_load < m.max_concurrent
        ]
        
        if not members:
            logger.warning("distributor.all_overloaded")
            return DistributionResult(
                member_id=None,
                member_name=None,
                strategy="overload",
                reason="all team members are at capacity",
                candidates_count=candidates_count,
                success=False,
            )
        
        # ─── Step 2: Filter by specialty ───
        specialty_matches = []
        for m in members:
            member_specs = m.specialties or []
            if any(s in member_specs for s in specialty_required):
                specialty_matches.append(m)
        
        if specialty_matches:
            members = specialty_matches
            strategy = "specialty"
        else:
            # Fallback: managers can handle anything
            managers = [m for m in members if m.role == "manager"]
            if managers:
                members = managers
                strategy = "fallback_manager"
            else:
                strategy = "fallback_any"
        
        # ─── Step 3: Filter by language ───
        language_matches = [
            m for m in members
            if not m.languages or language in m.languages
        ]
        if language_matches:
            members = language_matches
        
        # ─── Step 4: Prefer current shift ───
        shift_matches = [m for m in members if m.shift == shift]
        flexible = [m for m in members if m.shift == "flexible"]
        
        if shift_matches:
            members = shift_matches
            strategy = f"{strategy}+shift"
        elif flexible:
            members = flexible
            strategy = f"{strategy}+flexible"
        # else: keep all members (any shift)
        
        # ─── Step 5: Sort by load (least loaded first) ───
        members.sort(key=lambda m: (m.current_load, m.created_at))
        
        # ─── Best candidate ───
        best = members[0]
        
        logger.info(
            "distributor.assigned",
            report_id=report_id,
            member_id=best.id,
            member_name=best.name,
            strategy=strategy,
            current_load=best.current_load,
            max_concurrent=best.max_concurrent,
        )
        
        return DistributionResult(
            member_id=best.id,
            member_name=best.name,
            strategy=strategy,
            reason=f"matched {len(members)} candidates, chose least loaded",
            candidates_count=len(members),
            success=True,
        )
    
    def distribute_specific(
        self,
        team_repo: TeamRepository,
        member_id: str,
    ) -> DistributionResult:
        """Assign to a specific member."""
        member = team_repo.get_by_id(member_id)
        if not member or not member.is_active:
            return DistributionResult(
                member_id=None, member_name=None,
                strategy="manual", reason="member not found or inactive",
                candidates_count=0, success=False,
            )
        
        return DistributionResult(
            member_id=member.id,
            member_name=member.name,
            strategy="manual",
            reason="explicit assignment",
            candidates_count=1,
            success=True,
        )
    
    def find_escalation_target(
        self,
        team_repo: TeamRepository,
        current_member_id: str,
        specialty_required: list[str],
    ) -> DistributionResult:
        """Find escalation target (manager or supervisor)."""
        members = team_repo.list_all(active_only=True)
        
        # Exclude current member
        members = [m for m in members if m.id != current_member_id]
        
        # Prefer managers
        managers = [m for m in members if m.role == "manager"]
        if managers:
            managers.sort(key=lambda m: m.current_load)
            best = managers[0]
            return DistributionResult(
                member_id=best.id,
                member_name=best.name,
                strategy="escalation_manager",
                reason="escalated to manager",
                candidates_count=len(managers),
                success=True,
            )
        
        # Fallback: supervisors
        supervisors = [m for m in members if m.role == "supervisor"]
        if supervisors:
            supervisors.sort(key=lambda m: m.current_load)
            best = supervisors[0]
            return DistributionResult(
                member_id=best.id,
                member_name=best.name,
                strategy="escalation_supervisor",
                reason="escalated to supervisor",
                candidates_count=len(supervisors),
                success=True,
            )
        
        return DistributionResult(
            member_id=None,
            member_name=None,
            strategy="escalation_failed",
            reason="no escalation target available",
            candidates_count=0,
            success=False,
        )


# Singleton
team_distributor = TeamDistributor()
