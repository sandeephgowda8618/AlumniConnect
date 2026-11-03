"""AlumniConnect Pydantic Schemas for Mentorship Requests and Allocations
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class MentorshipRequestCreate(BaseModel):
    mentor_user_id: int
    domain_id: int
    request_message: str
    career_goal_snapshot: Optional[str] = None
    idempotency_key: Optional[str] = None


class MentorshipRequestDecision(BaseModel):
    decision: str  # 'ACCEPT' or 'REJECT'
    decision_reason: Optional[str] = None
    response_note: Optional[str] = None


class MentorshipRequestOut(BaseModel):
    request_id: int
    student_user_id: int
    student_name: Optional[str] = None
    student_programme: Optional[str] = None
    mentor_user_id: int
    mentor_name: Optional[str] = None
    mentor_job_title: Optional[str] = None
    domain_id: int
    domain_name: Optional[str] = None
    request_message: str
    career_goal_snapshot: Optional[str] = None
    request_status: str
    submitted_at: datetime
    decision_at: Optional[datetime] = None
    decision_reason: Optional[str] = None
    response_note: Optional[str] = None
    allocation_id: Optional[int] = None

    class Config:
        from_attributes = True


class MentorAllocationOut(BaseModel):
    allocation_id: int
    request_id: int
    student_user_id: int
    student_name: str
    mentor_user_id: int
    mentor_name: str
    domain_name: str
    allocation_status: str
    allocated_at: datetime
    ended_at: Optional[datetime] = None
    termination_reason: Optional[str] = None

    class Config:
        from_attributes = True

