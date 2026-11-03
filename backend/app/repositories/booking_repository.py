"""AlumniConnect Booking Repository
Implements query catalogue Q20 (booking calendar) and booking queries.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.models.entities import (
    Booking, MentorAvailability, MentorAllocation, MentorshipRequest,
    MentorshipSession, UserAccount, StudentProfile, MentorProfile
)


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, booking_id: int, lock: bool = False) -> Optional[Booking]:
        query = (
            self.db.query(Booking)
            .options(
                joinedload(Booking.availability),
                joinedload(Booking.allocation).joinedload(MentorAllocation.request).joinedload(MentorshipRequest.student).joinedload(StudentProfile.user),
                joinedload(Booking.allocation).joinedload(MentorAllocation.request).joinedload(MentorshipRequest.mentor).joinedload(MentorProfile.user),
                joinedload(Booking.session)
            )
            .filter(Booking.booking_id == booking_id)
        )
        if lock:
            query = query.with_for_update()
        return query.first()

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[Booking]:
        return (
            self.db.query(Booking)
            .options(
                joinedload(Booking.availability),
                joinedload(Booking.allocation).joinedload(MentorAllocation.request).joinedload(MentorshipRequest.student).joinedload(StudentProfile.user),
                joinedload(Booking.allocation).joinedload(MentorAllocation.request).joinedload(MentorshipRequest.mentor).joinedload(MentorProfile.user),
                joinedload(Booking.session)
            )
            .filter(Booking.idempotency_key == idempotency_key)
            .first()
        )

    def check_student_conflict(self, student_user_id: int, starts_at: datetime, ends_at: datetime) -> bool:
        """Checks if student already has a CONFIRMED booking overlapping [starts_at, ends_at)."""
        count = (
            self.db.query(Booking)
            .join(Booking.availability)
            .join(Booking.allocation)
            .join(MentorAllocation.request)
            .filter(
                MentorshipRequest.student_user_id == student_user_id,
                Booking.booking_status == "CONFIRMED",
                MentorAvailability.starts_at < ends_at,
                MentorAvailability.ends_at > starts_at
            )
            .count()
        )
        return count > 0

    def check_mentor_conflict(self, mentor_user_id: int, starts_at: datetime, ends_at: datetime) -> bool:
        """Checks if mentor already has another CONFIRMED booking overlapping [starts_at, ends_at)."""
        count = (
            self.db.query(Booking)
            .join(Booking.availability)
            .filter(
                MentorAvailability.mentor_user_id == mentor_user_id,
                Booking.booking_status == "CONFIRMED",
                MentorAvailability.starts_at < ends_at,
                MentorAvailability.ends_at > starts_at
            )
            .count()
        )
        return count > 0

    def create_booking(self, allocation_id: int, availability_id: int,
                       booking_type: str, idempotency_key: str) -> Booking:
        booking = Booking(
            allocation_id=allocation_id,
            availability_id=availability_id,
            booking_type=booking_type,
            booking_status="CONFIRMED",
            idempotency_key=idempotency_key,
            booked_at=datetime.utcnow()
        )
        self.db.add(booking)
        self.db.flush()
        return booking

    def list_student_bookings(self, student_user_id: int) -> List[Booking]:
        return (
            self.db.query(Booking)
            .join(Booking.allocation)
            .join(MentorAllocation.request)
            .options(
                joinedload(Booking.availability),
                joinedload(Booking.allocation).joinedload(MentorAllocation.request).joinedload(MentorshipRequest.mentor).joinedload(MentorProfile.user),
                joinedload(Booking.session)
            )
            .filter(MentorshipRequest.student_user_id == student_user_id)
            .order_by(Booking.booked_at.desc())
            .all()
        )

    def list_mentor_bookings(self, mentor_user_id: int) -> List[Booking]:
        """Implements Q20: Booking calendar for a mentor."""
        return (
            self.db.query(Booking)
            .join(Booking.availability)
            .options(
                joinedload(Booking.availability),
                joinedload(Booking.allocation).joinedload(MentorAllocation.request).joinedload(MentorshipRequest.student).joinedload(StudentProfile.user),
                joinedload(Booking.session)
            )
            .filter(MentorAvailability.mentor_user_id == mentor_user_id)
            .order_by(MentorAvailability.starts_at.asc())
            .all()
        )

