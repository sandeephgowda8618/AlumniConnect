"""AlumniConnect Mentorship Session Service
Implements SP04 Session Outcome Recording and Skill Assessments.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.session_repository import SessionRepository
from app.repositories.notification_repository import NotificationRepository
from app.models.entities import MentorshipSession


class SessionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SessionRepository(db)
        self.notif_repo = NotificationRepository(db)

    def record_outcome(self, session_id: int, actor_user_id: int, new_status: str,
                       actual_start: Optional[datetime] = None, actual_end: Optional[datetime] = None,
                       discussion: Optional[str] = None, observations: Optional[str] = None,
                       improvement_areas: Optional[str] = None, next_steps: Optional[str] = None,
                       preparation_rec: Optional[str] = None,
                       skill_assessments: Optional[List[Dict[str, Any]]] = None) -> MentorshipSession:
        """Executes SP04 logic: updates session record and skill assessments atomically."""
        sess = self.repo.get_by_id(session_id, lock=True)
        if not sess:
            raise ValueError("Mentorship session not found")

        if sess.session_status != "SCHEDULED":
            raise ValueError(f"Outcome can only be recorded for SCHEDULED sessions, currently {sess.session_status}")

        req = sess.booking.allocation.request
        if req.mentor_user_id != actor_user_id:
            raise ValueError("Only the assigned mentor may record this session outcome")

        if new_status not in ["COMPLETED", "CANCELLED", "NO_SHOW"]:
            raise ValueError("Status must be COMPLETED, CANCELLED, or NO_SHOW")

        updated_sess = self.repo.record_outcome(
            session_id=session_id,
            new_status=new_status,
            recorded_by_user_id=actor_user_id,
            actual_start=actual_start or datetime.utcnow(),
            actual_end=actual_end,
            discussion=discussion,
            observations=observations,
            improvement_areas=improvement_areas,
            next_steps=next_steps,
            preparation_rec=preparation_rec
        )

        # Record skill assessments if provided
        if skill_assessments and new_status == "COMPLETED":
            for sa in skill_assessments:
                self.repo.add_skill_assessment(
                    session_id=session_id,
                    skill_id=sa["skill_id"],
                    result=sa["assessment_result"],
                    notes=sa.get("assessment_notes")
                )

        # Outbox event
        dedupe = f"outbox:session_outcome:{session_id}:{int(datetime.utcnow().timestamp())}"
        self.notif_repo.create_outbox_event(
            aggregate_type="MENTORSHIP_SESSION",
            aggregate_id=session_id,
            event_type="SESSION_OUTCOME_RECORDED",
            payload={
                "session_id": session_id,
                "booking_id": sess.booking_id,
                "status": new_status,
                "student_user_id": req.student_user_id,
                "mentor_user_id": req.mentor_user_id
            },
            dedupe_key=dedupe
        )

        self.db.commit()
        return updated_sess

    def get_session(self, session_id: int) -> Optional[MentorshipSession]:
        return self.repo.get_by_id(session_id)

    def list_student_sessions(self, student_user_id: int) -> List[MentorshipSession]:
        return self.repo.list_student_sessions(student_user_id)

    def list_mentor_sessions(self, mentor_user_id: int) -> List[MentorshipSession]:
        return self.repo.list_mentor_sessions(mentor_user_id)

