"""AlumniConnect Analytics Endpoints
Exposes the query catalogue Q01–Q32 and conversion funnel reports.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_admin
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    FunnelReportOut, MentorRatingReportItem,
    DomainDemandSupplyItem, MentorCapacityReportItem, PlatformOverviewStats
)
from app.models.entities import UserAccount

router = APIRouter()


@router.get("/overview", response_model=PlatformOverviewStats)
def get_overview_statistics(db: Session = Depends(get_db)):
    """Provides high-level platform health and engagement metrics."""
    repo = AnalyticsRepository(db)
    return repo.get_platform_overview()


@router.get("/funnel", response_model=FunnelReportOut)
def get_conversion_funnel(
    admin: UserAccount = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Request-to-Allocation-to-Session conversion funnel using SQL CTEs (Q29)."""
    repo = AnalyticsRepository(db)
    return repo.q29_conversion_funnel()


@router.get("/mentor-ratings", response_model=List[MentorRatingReportItem])
def get_top_rated_mentors(
    min_reviews: int = Query(1),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Mentors with highest average review rating (Q22)."""
    repo = AnalyticsRepository(db)
    res = repo.q22_mentors_highest_rated(min_reviews=min_reviews, limit=limit)
    return [
        {
            "mentor_user_id": r["user_id"],
            "full_name": r["display_name"],
            "job_title": r["job_title"],
            "company_name": r.get("company_name"),
            "review_count": r["review_count"],
            "average_rating": r["average_rating"],
            "rating_label": "EXCELLENT" if r["average_rating"] >= 4.5 else "VERY_GOOD" if r["average_rating"] >= 4.0 else "GOOD"
        } for r in res
    ]


@router.get("/demand-supply", response_model=List[DomainDemandSupplyItem])
def get_skill_demand_vs_supply(db: Session = Depends(get_db)):
    """Skill demand versus mentor supply analysis (Q28)."""
    repo = AnalyticsRepository(db)
    res = repo.q28_skill_demand_vs_supply()
    return [
        {
            "domain_id": r["skill_id"],
            "domain_name": r["skill_name"],
            "student_interest_count": r["student_demand_count"],
            "mentor_supply_count": r["mentor_supply_count"],
            "ratio": round(r["student_demand_count"] / max(1, r["mentor_supply_count"]), 2)
        } for r in res
    ]


@router.get("/capacity-utilization", response_model=List[MentorCapacityReportItem])
def get_mentor_capacity_report(db: Session = Depends(get_db)):
    """Mentor capacity utilization and saturation analysis (Q27)."""
    repo = AnalyticsRepository(db)
    res = repo.q27_mentor_capacity_utilisation()
    return [
        {
            "mentor_user_id": r["user_id"],
            "full_name": r["display_name"],
            "max_active_mentees": r["max_active_mentees"],
            "current_active_mentees": r["current_active_mentees"],
            "utilization_percent": r["utilization_percent"],
            "is_at_capacity": bool(r["is_at_capacity"])
        } for r in res
    ]


@router.get("/cancellation-rates")
def get_cancellation_and_noshow_rates(db: Session = Depends(get_db)):
    """Booking cancellation and no-show rates (Q26)."""
    repo = AnalyticsRepository(db)
    return repo.q26_cancellation_and_noshow_rates()


@router.get("/domain-requests")
def get_domain_requests(db: Session = Depends(get_db)):
    """Request distribution by department and domain (Q21)."""
    repo = AnalyticsRepository(db)
    return repo.q21_requests_by_department_and_domain()
