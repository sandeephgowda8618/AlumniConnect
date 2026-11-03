"""AlumniConnect Mentor Allocation Repository
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.models.entities import MentorAllocation, MentorshipRequest, StudentProfile, MentorProfile, MentorshipDomain


class AllocationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, allocation_id: int, lock: bool = False) -> Optional[MentorAllocation]:
        query = (
            self.db.query(MentorAllocation)
            .options(
                joinedload(MentorAllocation.request).joinedload(MentorshipRequest.student).joinedload(StudentProfile.user),
                joinedload(MentorAllocation.request).joinedload(MentorshipRequest.mentor).joinedload(MentorProfile.user),
                joinedload(MentorAllocation.request).joinedload(MentorshipRequest.domain)
            )
            .filter(MentorAllocation.allocation_id == allocation_id)
        )
        if lock:
            query = query.with_for_update()
        return query.first()

    def get_by_request_id(self, request_id: int) -> Optional[MentorAllocation]:
        return (
            self.db.query(MentorAllocation)
            .filter(MentorAllocation.request_id == request_id)
            .first()
        )

    def find_active_allocation(self, student_user_id: int, mentor_user_id: int) -> Optional[MentorAllocation]:
        return (
            self.db.query(MentorAllocation)
            .join(MentorAllocation.request)
            .filter(
                MentorshipRequest.student_user_id == student_user_id,
                MentorshipRequest.mentor_user_id == mentor_user_id,
                MentorAllocation.allocation_status == "ACTIVE"
            )
            .first()
        )

    def list_student_allocations(self, student_user_id: int) -> List[MentorAllocation]:
        return (
            self.db.query(MentorAllocation)
            .join(MentorAllocation.request)
            .options(
                joinedload(MentorAllocation.request).joinedload(MentorshipRequest.mentor).joinedload(MentorProfile.user),
                joinedload(MentorAllocation.request).joinedload(MentorshipRequest.domain)
            )
            .filter(MentorshipRequest.student_user_id == student_user_id)
            .order_by(MentorAllocation.allocated_at.desc())
            .all()
        )

    def list_mentor_allocations(self, mentor_user_id: int) -> List[MentorAllocation]:
        return (
            self.db.query(MentorAllocation)
            .join(MentorAllocation.request)
            .options(
                joinedload(MentorAllocation.request).joinedload(MentorshipRequest.student).joinedload(StudentProfile.user),
                joinedload(MentorAllocation.request).joinedload(MentorshipRequest.domain)
            )
            .filter(MentorshipRequest.mentor_user_id == mentor_user_id)
            .order_by(MentorAllocation.allocated_at.desc())
            .all()
        )

    def create_allocation(self, request_id: int) -> MentorAllocation:
        alloc = MentorAllocation(
            request_id=request_id,
            allocation_status="ACTIVE",
            allocated_at=datetime.utcnow()
        )
        self.db.add(alloc)
        self.db.flush()
        return alloc

    def end_allocation(self, allocation_id: int, ended_by_user_id: int, reason: str) -> Optional[MentorAllocation]:
        alloc = self.get_by_id(allocation_id)
        if alloc and alloc.allocation_status == "ACTIVE":
            alloc.allocation_status = "ENDED"
            alloc.ended_at = datetime.utcnow()
            alloc.ended_by_user_id = ended_by_user_id
            alloc.termination_reason = reason
            self.db.flush()
        return alloc

