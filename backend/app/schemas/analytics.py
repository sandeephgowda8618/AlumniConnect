"""AlumniConnect Pydantic Schemas for Platform Analytics & Administrative Reports
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class FunnelStepOut(BaseModel):
    step_name: str
    count: int
    conversion_rate_percent: float


class FunnelReportOut(BaseModel):
    total_requests: int
    accepted_requests: int
    confirmed_bookings: int
    completed_sessions: int
    reviewed_sessions: int
    steps: List[FunnelStepOut]


class MentorRatingReportItem(BaseModel):
    mentor_user_id: int
    full_name: str
    job_title: str
    company_name: Optional[str] = None
    review_count: int
    average_rating: float
    rating_label: str


class DomainDemandSupplyItem(BaseModel):
    domain_id: int
    domain_name: str
    student_interest_count: int
    mentor_supply_count: int
    ratio: float


class MentorCapacityReportItem(BaseModel):
    mentor_user_id: int
    full_name: str
    max_active_mentees: int
    current_active_mentees: int
    utilization_percent: float
    is_at_capacity: bool


class PlatformOverviewStats(BaseModel):
    total_students: int
    total_mentors: int
    total_requests: int
    active_allocations: int
    completed_sessions: int
    average_platform_rating: float

