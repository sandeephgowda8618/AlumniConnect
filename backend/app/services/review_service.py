"""AlumniConnect Feedback & Mentor Review Service
Implements SP05 Student Mentor Review and Two-Way Session Feedback.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.review_repository import ReviewRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.cache_service import CacheService
from app.models.entities import SessionFeedback, MentorReview


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.review_repo = ReviewRepository(db)
        self.session_repo = SessionRepository(db)
        self.notif_repo = NotificationRepository(db)

    def submit_session_feedback(self, session_id: int, actor_user_id: int,
                                comm_rating: Optional[int] = None, help_rating: Optional[int] = None,
                                prep_rating: Optional[int] = None, comments: Optional[str] = None) -> SessionFeedback:
        sess = self.session_repo.get_by_id(session_id)
        if not sess:
            raise ValueError("Mentorship session not found")

        if sess.session_status != "COMPLETED":
            raise ValueError("Feedback can only be submitted for COMPLETED sessions")

        req = sess.booking.allocation.request
        if actor_user_id != req.student_user_id and actor_user_id != req.mentor_user_id:
            raise ValueError("Only participants in this session may submit feedback")

        existing = self.review_repo.get_feedback(session_id, actor_user_id)
        if existing:
            raise ValueError("You have already submitted feedback for this session")

        fb = self.review_repo.create_feedback(
            session_id=session_id,
            user_id=actor_user_id,
            comm_rating=comm_rating,
            help_rating=help_rating,
            prep_rating=prep_rating,
            comments=comments
        )
        self.db.commit()
        return fb

    def submit_mentor_review(self, session_id: int, actor_user_id: int,
                             rating: int, review_text: Optional[str] = None) -> MentorReview:
        """Executes SP05 Student Mentor Review submission."""
        sess = self.session_repo.get_by_id(session_id, lock=True)
        if not sess:
            raise ValueError("Mentorship session not found")

        if sess.session_status != "COMPLETED":
            raise ValueError("Reviews can only be submitted for COMPLETED sessions")

        req = sess.booking.allocation.request
        if actor_user_id != req.student_user_id:
            raise ValueError("Only the participating student may review the mentor for this session")

        if rating < 1 or rating > 5:
            raise ValueError("Rating must be an integer between 1 and 5")

        existing = self.review_repo.get_review_by_session(session_id)
        if existing:
            raise ValueError("A review has already been submitted for this session")

        rev = self.review_repo.create_mentor_review(
            session_id=session_id,
            rating=rating,
            review_text=review_text
        )

        # Invalidate mentor cache so updated review count & average rating refresh
        CacheService.invalidate_mentor_profile(req.mentor_user_id)

        # Transactional outbox event
        dedupe = f"outbox:review_submitted:{rev.review_id}:{int(datetime.utcnow().timestamp())}"
        self.notif_repo.create_outbox_event(
            aggregate_type="MENTOR_REVIEW",
            aggregate_id=rev.review_id,
            event_type="MENTOR_REVIEW_SUBMITTED",
            payload={
                "review_id": rev.review_id,
                "session_id": session_id,
                "student_user_id": actor_user_id,
                "mentor_user_id": req.mentor_user_id,
                "rating": rating
            },
            dedupe_key=dedupe
        )

        self.db.commit()
        return rev

    def list_mentor_reviews(self, mentor_user_id: int) -> List[MentorReview]:
        return self.review_repo.list_mentor_reviews(mentor_user_id)

