"""AlumniConnect Pydantic Schemas for Session Feedback & Student Mentor Reviews
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SessionFeedbackCreate(BaseModel):
    session_id: int
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    helpfulness_rating: Optional[int] = Field(None, ge=1, le=5)
    technical_preparation_rating: Optional[int] = Field(None, ge=1, le=5)
    comments: Optional[str] = None


class SessionFeedbackOut(BaseModel):
    feedback_id: int
    session_id: int
    submitted_by_user_id: int
    submitted_by_name: Optional[str] = None
    communication_rating: Optional[int] = None
    helpfulness_rating: Optional[int] = None
    technical_preparation_rating: Optional[int] = None
    comments: Optional[str] = None
    submitted_at: datetime

    class Config:
        from_attributes = True


class MentorReviewCreate(BaseModel):
    session_id: int
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None


class MentorReviewOut(BaseModel):
    review_id: int
    session_id: int
    rating: int
    rating_label: Optional[str] = None
    review_text: Optional[str] = None
    submitted_at: datetime
    student_name: Optional[str] = None

    class Config:
        from_attributes = True

