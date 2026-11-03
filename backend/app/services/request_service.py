"""AlumniConnect Mentorship Request Service
Implements SP01 atomic acceptance transaction, lifecycle state transitions,
and transactional outbox event creation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.request_repository import RequestRepository
from app.repositories.allocation_repository import AllocationRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.audit_repository import AuditRepository
from app.core.graph_client import graph_client
from app.models.entities import MentorshipRequest, MentorAllocation


class RequestService:
    def __init__(self, db: Session):
        self.db = db
        self.req_repo = RequestRepository(db)
        self.alloc_repo = AllocationRepository(db)
        self.profile_repo = ProfileRepository(db)
        self.notif_repo = NotificationRepository(db)
        self.audit_repo = AuditRepository(db)

    def submit_request(self, student_user_id: int, mentor_user_id: int, domain_id: int,
                       request_message: str, career_goal: Optional[str] = None,
                       idempotency_key: Optional[str] = None) -> MentorshipRequest:
        # Check student account status
        student = self.profile_repo.get_student_profile(student_user_id)
        if not student or student.user.account_status != "ACTIVE":
            raise ValueError("Student account is not active")

        # Check mentor account status & acceptance
        mentor = self.profile_repo.get_mentor_profile(mentor_user_id)
        if not mentor or mentor.user.account_status != "ACTIVE":
            raise ValueError("Target mentor is not active")
        if not mentor.accepting_requests:
            raise ValueError("Mentor is not currently accepting new requests")

        # Check duplicate pending request (BR-T02)
        existing = self.req_repo.find_pending_request(student_user_id, mentor_user_id, domain_id)
        if existing:
            raise ValueError("You already have a pending request with this mentor in this domain")

        # Insert request
        req = self.req_repo.create_request(
            student_user_id=student_user_id,
            mentor_user_id=mentor_user_id,
            domain_id=domain_id,
            request_message=request_message,
            career_goal_snapshot=career_goal or student.career_goal,
            idempotency_key=idempotency_key
        )

        # Transactional outbox event
        dedupe = f"outbox:req_created:{req.request_id}:{int(datetime.utcnow().timestamp())}"
        self.notif_repo.create_outbox_event(
            aggregate_type="MENTORSHIP_REQUEST",
            aggregate_id=req.request_id,
            event_type="MENTORSHIP_REQUEST_SUBMITTED",
            payload={
                "request_id": req.request_id,
                "student_user_id": student_user_id,
                "mentor_user_id": mentor_user_id,
                "domain_id": domain_id,
                "student_name": student.user.display_name
            },
            dedupe_key=dedupe
        )

        self.db.commit()
        return req

    def accept_request(self, request_id: int, actor_user_id: int) -> MentorAllocation:
        """Executes the SP01 atomic acceptance transaction."""
        # 1. Lock and inspect request
        req = self.req_repo.get_by_id(request_id, lock=True)
        if not req:
            raise ValueError("Mentorship request not found")

        if req.request_status != "PENDING":
            raise ValueError(f"Request is already in {req.request_status} status")

        if req.mentor_user_id != actor_user_id:
            raise ValueError("Only the addressed mentor may accept this request")

        # 2. Lock and inspect mentor
        mentor = self.profile_repo.get_mentor_profile(actor_user_id)
        if not mentor or mentor.user.account_status != "ACTIVE":
            raise ValueError("Mentor account is not active")

        # 3. Check capacity
        active_count = self.profile_repo.get_mentor_active_mentees_count(actor_user_id)
        if active_count >= mentor.max_active_mentees:
            raise ValueError("You have reached your maximum active mentee capacity")

        # 4. Check duplicate active allocation
        existing_alloc = self.alloc_repo.find_active_allocation(req.student_user_id, req.mentor_user_id)
        if existing_alloc:
            raise ValueError("An active allocation already exists for this student and mentor")

        # 5. Create Allocation
        alloc = self.alloc_repo.create_allocation(request_id=request_id)

        # 6. Update Request Status to ACCEPTED
        req.request_status = "ACCEPTED"
        req.decision_at = datetime.utcnow()
        req.decided_by_user_id = actor_user_id
        req.decision_reason = "Accepted by mentor"

        # 7. Audit log
        self.audit_repo.log_event(
            entity_type="MENTORSHIP_REQUEST",
            entity_id=request_id,
            action="ACCEPTED",
            actor_user_id=actor_user_id,
            old_values={"request_status": "PENDING"},
            new_values={"request_status": "ACCEPTED", "allocation_id": alloc.allocation_id}
        )

        # 8. Transactional outbox event
        dedupe = f"outbox:req_accepted:{request_id}:{int(datetime.utcnow().timestamp())}"
        self.notif_repo.create_outbox_event(
            aggregate_type="MENTORSHIP_REQUEST",
            aggregate_id=request_id,
            event_type="MENTORSHIP_REQUEST_ACCEPTED",
            payload={
                "request_id": request_id,
                "allocation_id": alloc.allocation_id,
                "student_user_id": req.student_user_id,
                "mentor_user_id": req.mentor_user_id,
                "actor_user_id": actor_user_id
            },
            dedupe_key=dedupe
        )

        self.db.commit()

        # Update in-memory graph
        graph_client.engine.record_mentored_by(req.student_user_id, req.mentor_user_id, alloc.allocation_id)

        return alloc

    def reject_request(self, request_id: int, actor_user_id: int, reason: Optional[str] = None) -> MentorshipRequest:
        req = self.req_repo.get_by_id(request_id, lock=True)
        if not req:
            raise ValueError("Mentorship request not found")

        if req.request_status != "PENDING":
            raise ValueError(f"Request is already in {req.request_status} status")

        if req.mentor_user_id != actor_user_id:
            raise ValueError("Only the addressed mentor may reject this request")

        req.request_status = "REJECTED"
        req.decision_at = datetime.utcnow()
        req.decided_by_user_id = actor_user_id
        req.decision_reason = reason or "Declined by mentor"

        self.audit_repo.log_event(
            entity_type="MENTORSHIP_REQUEST",
            entity_id=request_id,
            action="REJECTED",
            actor_user_id=actor_user_id,
            old_values={"request_status": "PENDING"},
            new_values={"request_status": "REJECTED", "reason": reason}
        )

        dedupe = f"outbox:req_rejected:{request_id}:{int(datetime.utcnow().timestamp())}"
        self.notif_repo.create_outbox_event(
            aggregate_type="MENTORSHIP_REQUEST",
            aggregate_id=request_id,
            event_type="MENTORSHIP_REQUEST_REJECTED",
            payload={
                "request_id": request_id,
                "student_user_id": req.student_user_id,
                "mentor_user_id": req.mentor_user_id,
                "reason": reason
            },
            dedupe_key=dedupe
        )

        self.db.commit()
        return req

    def cancel_request(self, request_id: int, actor_user_id: int) -> MentorshipRequest:
        req = self.req_repo.get_by_id(request_id, lock=True)
        if not req:
            raise ValueError("Mentorship request not found")

        if req.student_user_id != actor_user_id:
            raise ValueError("Only the student who submitted this request may cancel it")

        if req.request_status != "PENDING":
            raise ValueError("Only PENDING requests can be cancelled")

        req.request_status = "CANCELLED"
        req.decision_at = datetime.utcnow()
        req.decided_by_user_id = actor_user_id
        req.decision_reason = "Cancelled by student"

        self.db.commit()
        return req

    def list_student_requests(self, student_user_id: int) -> List[MentorshipRequest]:
        return self.req_repo.list_student_requests(student_user_id)

    def list_mentor_inbox(self, mentor_user_id: int) -> List[MentorshipRequest]:
        return self.req_repo.list_mentor_pending_inbox(mentor_user_id)

    def list_mentor_history(self, mentor_user_id: int) -> List[MentorshipRequest]:
        return self.req_repo.list_mentor_request_history(mentor_user_id)

