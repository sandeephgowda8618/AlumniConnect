"""AlumniConnect Pydantic Schemas for Mentorship Sessions & Outcomes
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class SkillAssessmentItem(BaseModel):
    skill_id: int
    assessment_result: str  # 'PROFICIENT', 'DEVELOPING', 'NEEDS_IMPROVEMENT', 'NOT_EVALUATED'
    assessment_notes: Optional[str] = None


class SessionOutcomeRecordRequest(BaseModel):
    new_status: str  # 'COMPLETED', 'CANCELLED', 'NO_SHOW'
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    discussion_summary: Optional[str] = None
    performance_observations: Optional[str] = None
    improvement_areas: Optional[str] = None
    next_steps: Optional[str] = None
    preparation_recommendation: Optional[str] = None
    skill_assessments: List[SkillAssessmentItem] = []


class SessionSkillAssessmentOut(BaseModel):
    skill_id: int
    skill_name: str
    assessment_result: str
    assessment_notes: Optional[str] = None

    class Config:
        from_attributes = True


class SessionOut(BaseModel):
    session_id: int
    booking_id: int
    session_status: str
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    discussion_summary: Optional[str] = None
    performance_observations: Optional[str] = None
    improvement_areas: Optional[str] = None
    next_steps: Optional[str] = None
    preparation_recommendation: Optional[str] = None
    recorded_at: Optional[datetime] = None
    
    # Contextual fields
    student_user_id: Optional[int] = None
    student_name: Optional[str] = None
    mentor_user_id: Optional[int] = None
    mentor_name: Optional[str] = None
    slot_starts_at: Optional[datetime] = None
    slot_ends_at: Optional[datetime] = None
    skill_assessments: List[SessionSkillAssessmentOut] = []
    has_review: bool = False
    has_feedback: bool = False

    class Config:
        from_attributes = True

