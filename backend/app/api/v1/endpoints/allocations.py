"""AlumniConnect Mentor Allocation Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_student, require_mentor
from app.repositories.allocation_repository import AllocationRepository
from app.schemas.request import MentorAllocationOut
from app.models.entities import UserAccount

router = APIRouter()


@router.get("/student", response_model=List[MentorAllocationOut])
def list_student_allocations(
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Lists all active and historical mentor allocations for the student."""
    repo = AllocationRepository(db)
    allocations = repo.list_student_allocations(current_user.user_id)
    return [_format_alloc_out(a) for a in allocations]


@router.get("/mentor", response_model=List[MentorAllocationOut])
def list_mentor_allocations(
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Lists all active and historical student allocations for the mentor."""
    repo = AllocationRepository(db)
    allocations = repo.list_mentor_allocations(current_user.user_id)
    return [_format_alloc_out(a) for a in allocations]


def _format_alloc_out(a) -> dict:
    req = a.request
    return {
        "allocation_id": a.allocation_id,
        "request_id": a.request_id,
        "student_user_id": req.student_user_id,
        "student_name": req.student.user.display_name if req.student and req.student.user else "",
        "mentor_user_id": req.mentor_user_id,
        "mentor_name": req.mentor.user.display_name if req.mentor and req.mentor.user else "",
        "domain_name": req.domain.domain_name if req.domain else "",
        "allocation_status": a.allocation_status,
        "allocated_at": a.allocated_at,
        "ended_at": a.ended_at,
        "termination_reason": a.termination_reason
    }

