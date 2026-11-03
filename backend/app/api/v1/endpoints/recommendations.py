"""AlumniConnect Recommendation Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_student
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import RecommendationFilter, RecommendationRunOut
from app.models.entities import UserAccount

router = APIRouter()


@router.post("/discover", response_model=RecommendationRunOut)
def discover_mentors(
    filters: Optional[RecommendationFilter] = None,
    limit: int = Query(10, ge=1, le=50),
    skip_cache: bool = Query(False),
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Executes the Neo4j graph traversal and multi-factor ranking recommendation pipeline."""
    service = RecommendationService(db)
    filter_dict = filters.dict(exclude_none=True) if filters else {}
    results = service.get_recommendations_for_student(
        student_user_id=current_user.user_id,
        filters=filter_dict,
        limit=limit,
        skip_cache=skip_cache
    )
    return results

