"""AlumniConnect Feedback & Mentor Review Repository
"""

from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.entities import SessionFeedback, MentorReview, MentorshipSession, Booking, MentorAvailability, UserAccount


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Session Feedback ---

    def get_feedback(self, session_id: int, user_id: int) -> Optional[SessionFeedback]:
        return (
            self.db.query(SessionFeedback)
            .filter(SessionFeedback.session_id == session_id, SessionFeedback.submitted_by_user_id == user_id)
            .first()
        )

    def create_feedback(self, session_id: int, user_id: int,
                        comm_rating: Optional[int] = None, help_rating: Optional[int] = None,
                        prep_rating: Optional[int] = None, comments: Optional[str] = None) -> SessionFeedback:
        fb = SessionFeedback(
            session_id=session_id,
            submitted_by_user_id=user_id,
            communication_rating=comm_rating,
            helpfulness_rating=help_rating,
            technical_preparation_rating=prep_rating,
            comments=comments,
            submitted_at=datetime.utcnow()
        )
        self.db.add(fb)
        self.db.flush()
        return fb

    def list_session_feedback(self, session_id: int) -> List[SessionFeedback]:
        return (
            self.db.query(SessionFeedback)
            .options(joinedload(SessionFeedback.submitted_by))
            .filter(SessionFeedback.session_id == session_id)
            .all()
        )

    # --- Mentor Review ---

    def get_review_by_session(self, session_id: int) -> Optional[MentorReview]:
        return self.db.query(MentorReview).filter(MentorReview.session_id == session_id).first()

    def create_mentor_review(self, session_id: int, rating: int, review_text: Optional[str] = None) -> MentorReview:
        rev = MentorReview(
            session_id=session_id,
            rating=rating,
            review_text=review_text,
            submitted_at=datetime.utcnow()
        )
        self.db.add(rev)
        self.db.flush()
        return rev

    def list_mentor_reviews(self, mentor_user_id: int) -> List[MentorReview]:
        return (
            self.db.query(MentorReview)
            .join(MentorReview.session)
            .join(MentorshipSession.booking)
            .join(Booking.availability)
            .filter(MentorAvailability.mentor_user_id == mentor_user_id)
            .order_by(MentorReview.submitted_at.desc())
            .all()
        )

    def get_mentor_rating_stats(self, mentor_user_id: int) -> Tuple[int, float]:
        """Calculates review count and average rating for a mentor."""
        result = (
            self.db.query(
                func.count(MentorReview.review_id),
                func.avg(MentorReview.rating)
            )
            .join(MentorReview.session)
            .join(MentorshipSession.booking)
            .join(Booking.availability)
            .filter(MentorAvailability.mentor_user_id == mentor_user_id)
            .first()
        )
        count = result[0] if result and result[0] is not None else 0
        avg = float(result[1]) if result and result[1] is not None else 0.0
        return count, round(avg, 2)

