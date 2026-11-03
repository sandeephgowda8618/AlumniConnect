"""AlumniConnect Mentorship Sessions Endpoints
Implements session outcome recording and skill evaluations (SP04).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_student, require_mentor, get_current_user
from app.services.session_service import SessionService
from app.schemas.session import SessionOutcomeRecordRequest, SessionOut
from app.models.entities import UserAccount

router = APIRouter()


@router.get("/student", response_model=List[SessionOut])
def list_student_sessions(
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Student views their completed and upcoming session records (Q17)."""
    service = SessionService(db)
    sessions = service.list_student_sessions(current_user.user_id)
    return [_format_session_out(s, current_user.user_id) for s in sessions]


@router.get("/mentor", response_model=List[SessionOut])
def list_mentor_sessions(
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Mentor views their conducted session history (Q18)."""
    service = SessionService(db)
    sessions = service.list_mentor_sessions(current_user.user_id)
    return [_format_session_out(s, current_user.user_id) for s in sessions]


@router.get("/{session_id}", response_model=SessionOut)
def get_session_details(
    session_id: int,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves session evaluation notes and skill assessment rubrics."""
    service = SessionService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # IDOR Protection: only participating student, assigned mentor, or administrator may inspect session details
    req = session.booking.allocation.request if (session.booking and session.booking.allocation) else None
    is_student = req and req.student_user_id == current_user.user_id
    is_mentor = req and req.mentor_user_id == current_user.user_id
    is_admin = current_user.role and current_user.role.role_code == "ADMINISTRATOR"
    if not (is_student or is_mentor or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have authorization to view this mentorship session"
        )

    return _format_session_out(session, current_user.user_id)


@router.post("/{session_id}/outcome", response_model=SessionOut)
def record_session_outcome(
    session_id: int,
    outcome_data: SessionOutcomeRecordRequest,
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Mentor records the offline mentorship session outcome and skill assessments (SP04)."""
    service = SessionService(db)
    try:
        session = service.record_outcome(
            session_id=session_id,
            actor_user_id=current_user.user_id,
            new_status=outcome_data.new_status,
            actual_start=outcome_data.actual_start_at,
            actual_end=outcome_data.actual_end_at,
            discussion=outcome_data.discussion_summary,
            observations=outcome_data.performance_observations,
            improvement_areas=outcome_data.improvement_areas,
            next_steps=outcome_data.next_steps,
            preparation_rec=outcome_data.preparation_recommendation,
            skill_assessments=[sa.dict() for sa in outcome_data.skill_assessments]
        )
        return _format_session_out(session, current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def _format_session_out(s, viewer_user_id: int) -> dict:
    req = s.booking.allocation.request if (s.booking and s.booking.allocation) else None
    has_feedback = any(fb.submitted_by_user_id == viewer_user_id for fb in s.feedback) if s.feedback else False
    has_review = bool(s.review)

    assessments = [
        {
            "skill_id": sa.skill_id,
            "skill_name": sa.skill.skill_name if sa.skill else "",
            "assessment_result": sa.assessment_result,
            "assessment_notes": sa.assessment_notes
        } for sa in (s.skill_assessments or [])
    ]

    return {
        "session_id": s.session_id,
        "booking_id": s.booking_id,
        "session_status": s.session_status,
        "actual_start_at": s.actual_start_at,
        "actual_end_at": s.actual_end_at,
        "discussion_summary": s.discussion_summary,
        "performance_observations": s.performance_observations,
        "improvement_areas": s.improvement_areas,
        "next_steps": s.next_steps,
        "preparation_recommendation": s.preparation_recommendation,
        "recorded_at": s.recorded_at,
        "student_user_id": req.student_user_id if req else None,
        "student_name": req.student.user.display_name if req and req.student and req.student.user else None,
        "mentor_user_id": req.mentor_user_id if req else None,
        "mentor_name": req.mentor.user.display_name if req and req.mentor and req.mentor.user else None,
        "slot_starts_at": s.booking.availability.starts_at if (s.booking and s.booking.availability) else None,
        "slot_ends_at": s.booking.availability.ends_at if (s.booking and s.booking.availability) else None,
        "skill_assessments": assessments,
        "has_review": has_review,
        "has_feedback": has_feedback
    }

