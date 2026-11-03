"""AlumniConnect Pydantic Schemas for Bookings
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BookingCreate(BaseModel):
    availability_id: int
    allocation_id: int
    booking_type: str = "MENTORSHIP"  # 'MENTORSHIP' or 'MOCK_INTERVIEW'
    idempotency_key: str


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = "Cancelled by user"


class BookingOut(BaseModel):
    booking_id: int
    allocation_id: int
    availability_id: int
    booking_type: str
    booking_status: str
    booked_at: datetime
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    idempotency_key: str
    
    # Joined contextual attributes
    student_user_id: Optional[int] = None
    student_name: Optional[str] = None
    mentor_user_id: Optional[int] = None
    mentor_name: Optional[str] = None
    slot_starts_at: Optional[datetime] = None
    slot_ends_at: Optional[datetime] = None
    session_id: Optional[int] = None
    session_status: Optional[str] = None

    class Config:
        from_attributes = True

