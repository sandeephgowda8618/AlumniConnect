"""AlumniConnect Booking Endpoints
Implements atomic booking creation (SP02) and cancellation (SP03).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_student, require_mentor, get_current_user
from app.services.booking_service import BookingService
from app.schemas.booking import BookingCreate, BookingCancelRequest, BookingOut
from app.models.entities import UserAccount

router = APIRouter()


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Student creates an atomic booking against an active allocation and open slot (SP02)."""
    service = BookingService(db)
    try:
        booking = service.create_booking(
            actor_user_id=current_user.user_id,
            availability_id=booking_data.availability_id,
            allocation_id=booking_data.allocation_id,
            booking_type=booking_data.booking_type,
            idempotency_key=booking_data.idempotency_key
        )
        return _format_booking_out(booking)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/student", response_model=List[BookingOut])
def list_student_bookings(
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Student views all their upcoming and past bookings."""
    service = BookingService(db)
    bookings = service.list_student_bookings(current_user.user_id)
    return [_format_booking_out(b) for b in bookings]


@router.get("/mentor", response_model=List[BookingOut])
def list_mentor_bookings(
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Mentor views their appointment calendar (Q20)."""
    service = BookingService(db)
    bookings = service.list_mentor_bookings(current_user.user_id)
    return [_format_booking_out(b) for b in bookings]


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: int,
    cancel_data: BookingCancelRequest,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Participant cancels an upcoming booking with cutoff validation (SP03)."""
    service = BookingService(db)
    try:
        booking = service.cancel_booking(
            booking_id=booking_id,
            actor_user_id=current_user.user_id,
            reason=cancel_data.reason
        )
        return _format_booking_out(booking)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def _format_booking_out(b) -> dict:
    req = b.allocation.request if b.allocation else None
    return {
        "booking_id": b.booking_id,
        "allocation_id": b.allocation_id,
        "availability_id": b.availability_id,
        "booking_type": b.booking_type,
        "booking_status": b.booking_status,
        "booked_at": b.booked_at,
        "cancelled_at": b.cancelled_at,
        "cancellation_reason": b.cancellation_reason,
        "idempotency_key": b.idempotency_key,
        "student_user_id": req.student_user_id if req else None,
        "student_name": req.student.user.display_name if req and req.student and req.student.user else None,
        "mentor_user_id": req.mentor_user_id if req else None,
        "mentor_name": req.mentor.user.display_name if req and req.mentor and req.mentor.user else None,
        "slot_starts_at": b.availability.starts_at if b.availability else None,
        "slot_ends_at": b.availability.ends_at if b.availability else None,
        "session_id": b.session.session_id if b.session else None,
        "session_status": b.session.session_status if b.session else None
    }

