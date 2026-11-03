"""AlumniConnect Mentorship Requests Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_student, require_mentor, get_current_user
from app.services.request_service import RequestService
from app.schemas.request import (
    MentorshipRequestCreate, MentorshipRequestOut,
    MentorshipRequestDecision, MentorAllocationOut
)
from app.models.entities import UserAccount

router = APIRouter()


@router.post("", response_model=MentorshipRequestOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=MentorshipRequestOut, status_code=status.HTTP_201_CREATED)
def submit_request(
    request_data: MentorshipRequestCreate,
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Student submits a targeted mentorship request to an alumni mentor."""
    service = RequestService(db)
    try:
        req = service.submit_request(
            student_user_id=current_user.user_id,
            mentor_user_id=request_data.mentor_user_id,
            domain_id=request_data.domain_id,
            request_message=request_data.request_message,
            career_goal=request_data.career_goal_snapshot,
            idempotency_key=request_data.idempotency_key
        )
        return _format_request_out(req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/student", response_model=List[MentorshipRequestOut])
def list_student_requests(
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Student views their own request and decision history (Q16)."""
    service = RequestService(db)
    requests = service.list_student_requests(current_user.user_id)
    return [_format_request_out(r) for r in requests]


@router.get("/mentor/inbox", response_model=List[MentorshipRequestOut])
def list_mentor_inbox(
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Mentor views their pending mentorship request inbox (Q15)."""
    service = RequestService(db)
    requests = service.list_mentor_inbox(current_user.user_id)
    return [_format_request_out(r) for r in requests]


@router.get("/mentor/history", response_model=List[MentorshipRequestOut])
def list_mentor_history(
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Mentor views all historic requests decided by them."""
    service = RequestService(db)
    requests = service.list_mentor_history(current_user.user_id)
    return [_format_request_out(r) for r in requests]


@router.post("/{request_id}/accept", response_model=MentorAllocationOut)
def accept_request(
    request_id: int,
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Mentor accepts a PENDING request, atomically creating an active allocation (SP01)."""
    service = RequestService(db)
    try:
        alloc = service.accept_request(request_id=request_id, actor_user_id=current_user.user_id)
        req = alloc.request
        return {
            "allocation_id": alloc.allocation_id,
            "request_id": alloc.request_id,
            "student_user_id": req.student_user_id,
            "student_name": req.student.user.display_name if req.student and req.student.user else "",
            "mentor_user_id": req.mentor_user_id,
            "mentor_name": req.mentor.user.display_name if req.mentor and req.mentor.user else "",
            "domain_name": req.domain.domain_name if req.domain else "",
            "allocation_status": alloc.allocation_status,
            "allocated_at": alloc.allocated_at,
            "ended_at": alloc.ended_at,
            "termination_reason": alloc.termination_reason
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{request_id}/reject", response_model=MentorshipRequestOut)
def reject_request(
    request_id: int,
    decision: MentorshipRequestDecision,
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Mentor declines a pending request and records an optional decision reason."""
    service = RequestService(db)
    try:
        req = service.reject_request(
            request_id=request_id,
            actor_user_id=current_user.user_id,
            reason=decision.decision_reason
        )
        return _format_request_out(req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{request_id}/cancel", response_model=MentorshipRequestOut)
def cancel_request(
    request_id: int,
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Student cancels their pending mentorship request."""
    service = RequestService(db)
    try:
        req = service.cancel_request(request_id=request_id, actor_user_id=current_user.user_id)
        return _format_request_out(req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def _format_request_out(r) -> dict:
    return {
        "request_id": r.request_id,
        "student_user_id": r.student_user_id,
        "student_name": r.student.user.display_name if r.student and r.student.user else None,
        "student_programme": r.student.programme if r.student else None,
        "mentor_user_id": r.mentor_user_id,
        "mentor_name": r.mentor.user.display_name if r.mentor and r.mentor.user else None,
        "mentor_job_title": r.mentor.job_title if r.mentor else None,
        "domain_id": r.domain_id,
        "domain_name": r.domain.domain_name if r.domain else None,
        "request_message": r.request_message,
        "career_goal_snapshot": r.career_goal_snapshot,
        "request_status": r.request_status,
        "submitted_at": r.submitted_at,
        "decision_at": r.decision_at,
        "decision_reason": r.decision_reason,
        "response_note": r.response_note,
        "allocation_id": r.allocation.allocation_id if r.allocation else None
    }

