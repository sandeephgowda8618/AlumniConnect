"""AlumniConnect Mentorship Session Repository
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.models.entities import (
    MentorshipSession, SessionSkillAssessment, Booking, MentorAvailability,
    MentorAllocation, MentorshipRequest, Skill, StudentProfile, MentorProfile
)


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, session_id: int, lock: bool = False) -> Optional[MentorshipSession]:
        query = (
            self.db.query(MentorshipSession)
            .options(
                joinedload(MentorshipSession.booking).joinedload(Booking.availability),
                joinedload(MentorshipSession.booking).joinedload(Booking.allocation).joinedload(MentorAllocation.request).joinedload(MentorshipRequest.student).joinedload(StudentProfile.user),
                joinedload(MentorshipSession.booking).joinedload(Booking.allocation).joinedload(MentorAllocation.request).joinedload(MentorshipRequest.mentor).joinedload(MentorProfile.user),
                joinedload(MentorshipSession.skill_assessments).joinedload(SessionSkillAssessment.skill),
                joinedload(MentorshipSession.feedback),
                joinedload(MentorshipSession.review)
            )
            .filter(MentorshipSession.session_id == session_id)
        )
        if lock:
            query = query.with_for_update()
        return query.first()

    def get_by_booking_id(self, booking_id: int) -> Optional[MentorshipSession]:
        return (
            self.db.query(MentorshipSession)
            .options(
                joinedload(MentorshipSession.skill_assessments).joinedload(SessionSkillAssessment.skill),
                joinedload(MentorshipSession.feedback),
                joinedload(MentorshipSession.review)
            )
            .filter(MentorshipSession.booking_id == booking_id)
            .first()
        )

    def create_session(self, booking_id: int) -> MentorshipSession:
        sess = MentorshipSession(
            booking_id=booking_id,
            session_status="SCHEDULED"
        )
        self.db.add(sess)
        self.db.flush()
        return sess

    def record_outcome(self, session_id: int, new_status: str, recorded_by_user_id: int,
                       actual_start: Optional[datetime] = None, actual_end: Optional[datetime] = None,
                       discussion: Optional[str] = None, observations: Optional[str] = None,
                       improvement_areas: Optional[str] = None, next_steps: Optional[str] = None,
                       preparation_rec: Optional[str] = None) -> Optional[MentorshipSession]:
        sess = self.get_by_id(session_id, lock=True)
        if not sess:
            return None
        sess.session_status = new_status
        sess.actual_start_at = actual_start
        sess.actual_end_at = actual_end
        sess.discussion_summary = discussion
        sess.performance_observations = observations
        sess.improvement_areas = improvement_areas
        sess.next_steps = next_steps
        sess.preparation_recommendation = preparation_rec
        sess.recorded_at = datetime.utcnow()
        sess.recorded_by_user_id = recorded_by_user_id
        self.db.flush()
        return sess

    def add_skill_assessment(self, session_id: int, skill_id: int, result: str, notes: Optional[str] = None) -> SessionSkillAssessment:
        existing = (
            self.db.query(SessionSkillAssessment)
            .filter(SessionSkillAssessment.session_id == session_id, SessionSkillAssessment.skill_id == skill_id)
            .first()
        )
        if existing:
            existing.assessment_result = result
            existing.assessment_notes = notes
            self.db.flush()
            return existing
        item = SessionSkillAssessment(session_id=session_id, skill_id=skill_id, assessment_result=result, assessment_notes=notes)
        self.db.add(item)
        self.db.flush()
        return item

    def list_student_sessions(self, student_user_id: int) -> List[MentorshipSession]:
        """Implements Q17: Student mentorship history with sessions."""
        return (
            self.db.query(MentorshipSession)
            .join(MentorshipSession.booking)
            .join(Booking.allocation)
            .join(MentorAllocation.request)
            .options(
                joinedload(MentorshipSession.booking).joinedload(Booking.availability),
                joinedload(MentorshipSession.booking).joinedload(Booking.allocation).joinedload(MentorAllocation.request).joinedload(MentorshipRequest.mentor).joinedload(MentorProfile.user),
                joinedload(MentorshipSession.skill_assessments).joinedload(SessionSkillAssessment.skill),
                joinedload(MentorshipSession.review),
                joinedload(MentorshipSession.feedback)
            )
            .filter(MentorshipRequest.student_user_id == student_user_id)
            .order_by(Booking.booked_at.desc())
            .all()
        )

    def list_mentor_sessions(self, mentor_user_id: int) -> List[MentorshipSession]:
        """Implements Q18: Completed mentorship sessions per mentor."""
        return (
            self.db.query(MentorshipSession)
            .join(MentorshipSession.booking)
            .join(Booking.availability)
            .options(
                joinedload(MentorshipSession.booking).joinedload(Booking.availability),
                joinedload(MentorshipSession.booking).joinedload(Booking.allocation).joinedload(MentorAllocation.request).joinedload(MentorshipRequest.student).joinedload(StudentProfile.user),
                joinedload(MentorshipSession.skill_assessments).joinedload(SessionSkillAssessment.skill),
                joinedload(MentorshipSession.review),
                joinedload(MentorshipSession.feedback)
            )
            .filter(MentorAvailability.mentor_user_id == mentor_user_id)
            .order_by(Booking.booked_at.desc())
            .all()
        )

