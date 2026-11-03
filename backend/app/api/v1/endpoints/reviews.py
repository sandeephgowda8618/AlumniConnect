"""AlumniConnect Feedback & Mentor Review Endpoints
Implements SP05 Student Mentor Reviews and Participant Feedback.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_student, get_current_user
from app.services.review_service import ReviewService
from app.schemas.review import (
    SessionFeedbackCreate, SessionFeedbackOut,
    MentorReviewCreate, MentorReviewOut
)
from app.models.entities import UserAccount

router = APIRouter()


@router.post("/feedback", response_model=SessionFeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_session_feedback(
    fb_data: SessionFeedbackCreate,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Participant (student or mentor) submits structured feedback for a completed session."""
    service = ReviewService(db)
    try:
        fb = service.submit_session_feedback(
            session_id=fb_data.session_id,
            actor_user_id=current_user.user_id,
            comm_rating=fb_data.communication_rating,
            help_rating=fb_data.helpfulness_rating,
            prep_rating=fb_data.technical_preparation_rating,
            comments=fb_data.comments
        )
        return {
            "feedback_id": fb.feedback_id,
            "session_id": fb.session_id,
            "submitted_by_user_id": fb.submitted_by_user_id,
            "submitted_by_name": current_user.display_name,
            "communication_rating": fb.communication_rating,
            "helpfulness_rating": fb.helpfulness_rating,
            "technical_preparation_rating": fb.technical_preparation_rating,
            "comments": fb.comments,
            "submitted_at": fb.submitted_at
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/mentor-review", response_model=MentorReviewOut, status_code=status.HTTP_201_CREATED)
def submit_mentor_review(
    review_data: MentorReviewCreate,
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Student submits a rating review for their mentor after an eligible completed session (SP05)."""
    service = ReviewService(db)
    try:
        rev = service.submit_mentor_review(
            session_id=review_data.session_id,
            actor_user_id=current_user.user_id,
            rating=review_data.rating,
            review_text=review_data.review_text
        )
        return {
            "review_id": rev.review_id,
            "session_id": rev.session_id,
            "rating": rev.rating,
            "rating_label": "EXCELLENT" if rev.rating >= 5 else "GOOD" if rev.rating >= 4 else "AVERAGE",
            "review_text": rev.review_text,
            "submitted_at": rev.submitted_at,
            "student_name": current_user.display_name
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/mentor/{mentor_id}", response_model=List[MentorReviewOut])
def list_mentor_reviews(
    mentor_id: int,
    db: Session = Depends(get_db)
):
    """Lists public reviews submitted for a mentor."""
    service = ReviewService(db)
    reviews = service.list_mentor_reviews(mentor_id)
    return [
        {
            "review_id": r.review_id,
            "session_id": r.session_id,
            "rating": r.rating,
            "rating_label": "EXCELLENT" if r.rating >= 5 else "GOOD" if r.rating >= 4 else "AVERAGE",
            "review_text": r.review_text,
            "submitted_at": r.submitted_at,
            "student_name": "Verified Student Mentee"
        } for r in reviews
    ]

