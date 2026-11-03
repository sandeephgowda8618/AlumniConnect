"""AlumniConnect Mentorship Request Repository
Implements query catalogue Q15 (mentor inbox), Q16 (student request history),
and request persistence with pending request uniqueness guard.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.models.entities import MentorshipRequest, MentorAllocation, StudentProfile, MentorProfile, MentorshipDomain


class RequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, request_id: int, lock: bool = False) -> Optional[MentorshipRequest]:
        query = (
            self.db.query(MentorshipRequest)
            .options(
                joinedload(MentorshipRequest.student).joinedload(StudentProfile.user),
                joinedload(MentorshipRequest.mentor).joinedload(MentorProfile.user),
                joinedload(MentorshipRequest.domain),
                joinedload(MentorshipRequest.allocation)
            )
            .filter(MentorshipRequest.request_id == request_id)
        )
        if lock:
            query = query.with_for_update()
        return query.first()

    def find_pending_request(self, student_user_id: int, mentor_user_id: int, domain_id: int) -> Optional[MentorshipRequest]:
        return (
            self.db.query(MentorshipRequest)
            .filter(
                MentorshipRequest.student_user_id == student_user_id,
                MentorshipRequest.mentor_user_id == mentor_user_id,
                MentorshipRequest.domain_id == domain_id,
                MentorshipRequest.request_status == "PENDING"
            )
            .first()
        )

    def create_request(self, student_user_id: int, mentor_user_id: int, domain_id: int,
                       request_message: str, career_goal_snapshot: Optional[str] = None,
                       idempotency_key: Optional[str] = None) -> MentorshipRequest:
        req = MentorshipRequest(
            student_user_id=student_user_id,
            mentor_user_id=mentor_user_id,
            domain_id=domain_id,
            request_message=request_message,
            career_goal_snapshot=career_goal_snapshot,
            request_status="PENDING",
            idempotency_key=idempotency_key,
            submitted_at=datetime.utcnow()
        )
        self.db.add(req)
        self.db.flush()
        return req

    def list_student_requests(self, student_user_id: int) -> List[MentorshipRequest]:
        """Implements Q16: Student request and decision history."""
        return (
            self.db.query(MentorshipRequest)
            .options(
                joinedload(MentorshipRequest.mentor).joinedload(MentorProfile.user),
                joinedload(MentorshipRequest.domain),
                joinedload(MentorshipRequest.allocation)
            )
            .filter(MentorshipRequest.student_user_id == student_user_id)
            .order_by(MentorshipRequest.submitted_at.desc())
            .all()
        )

    def list_mentor_pending_inbox(self, mentor_user_id: int) -> List[MentorshipRequest]:
        """Implements Q15: Mentor pending-request inbox."""
        return (
            self.db.query(MentorshipRequest)
            .options(
                joinedload(MentorshipRequest.student).joinedload(StudentProfile.user),
                joinedload(MentorshipRequest.domain)
            )
            .filter(
                MentorshipRequest.mentor_user_id == mentor_user_id,
                MentorshipRequest.request_status == "PENDING"
            )
            .order_by(MentorshipRequest.submitted_at.asc())
            .all()
        )

    def list_mentor_request_history(self, mentor_user_id: int) -> List[MentorshipRequest]:
        return (
            self.db.query(MentorshipRequest)
            .options(
                joinedload(MentorshipRequest.student).joinedload(StudentProfile.user),
                joinedload(MentorshipRequest.domain),
                joinedload(MentorshipRequest.allocation)
            )
            .filter(MentorshipRequest.mentor_user_id == mentor_user_id)
            .order_by(MentorshipRequest.submitted_at.desc())
            .all()
        )

