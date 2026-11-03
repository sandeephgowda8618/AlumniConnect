"""AlumniConnect Pydantic Schemas for Multi-Factor Recommendations & Explanations
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class RecommendationFilter(BaseModel):
    domain_ids: Optional[List[int]] = None
    skill_ids: Optional[List[int]] = None
    min_years_experience: Optional[float] = None
    company_ids: Optional[List[int]] = None


class RecommendedMentorOut(BaseModel):
    mentor_user_id: int
    full_name: str
    job_title: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    years_experience: float
    rank_position: int
    overall_score: float
    skill_score: float
    domain_score: float
    experience_score: float
    career_score: float
    quality_score: float
    eligibility_status: str = "ELIGIBLE"
    explanation_text: str
    matched_skills: List[str] = []
    matched_domains: List[str] = []
    shared_alumni: bool = False
    average_rating: Optional[float] = None
    review_count: int = 0
    accepting_requests: bool = True

    class Config:
        from_attributes = True


class RecommendationRunOut(BaseModel):
    run_id: Optional[int] = None
    student_user_id: int
    algorithm_version: str = "v1.0-graph-weighted"
    executed_at: Optional[datetime] = None
    results: List[RecommendedMentorOut] = []
    from_cache: Optional[bool] = False

    class Config:
        from_attributes = True

