"""AlumniConnect Availability Slot Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_mentor, get_current_user
from app.services.availability_service import AvailabilityService
from app.schemas.availability import AvailabilitySlotCreate, AvailabilitySlotOut
from app.models.entities import UserAccount

router = APIRouter()


@router.post("", response_model=AvailabilitySlotOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=AvailabilitySlotOut, status_code=status.HTTP_201_CREATED)
def publish_slot(
    slot_data: AvailabilitySlotCreate,
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Mentor publishes a new availability time slot for bookings."""
    service = AvailabilityService(db)
    try:
        slot = service.create_slot(
            mentor_user_id=current_user.user_id,
            starts_at=slot_data.starts_at,
            ends_at=slot_data.ends_at
        )
        return slot
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/mentor", response_model=List[AvailabilitySlotOut])
def list_own_slots(
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Mentor views their own published availability calendar."""
    service = AvailabilityService(db)
    return service.list_mentor_slots(current_user.user_id)


@router.get("/mentor/{mentor_id}/open", response_model=List[AvailabilitySlotOut])
def list_open_slots_for_mentor(
    mentor_id: int,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Discovers available OPEN time slots for a specific mentor."""
    service = AvailabilityService(db)
    return service.list_open_slots_for_mentor(mentor_id)


@router.delete("/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_slot(
    availability_id: int,
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Mentor withdraws an unbooked OPEN availability slot."""
    service = AvailabilityService(db)
    try:
        service.withdraw_slot(availability_id, current_user.user_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

