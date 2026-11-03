"""AlumniConnect Booking Service
Implements SP02 Atomic Booking Creation (concurrency row-locks, overlap guards, idempotency)
and SP03 Booking Cancellation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.repositories.booking_repository import BookingRepository
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.allocation_repository import AllocationRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.audit_repository import AuditRepository
from app.core.config import settings
from app.models.entities import Booking, MentorAvailability, MentorshipSession, UserAccount, StudentProfile


class BookingService:
    def __init__(self, db: Session):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.avail_repo = AvailabilityRepository(db)
        self.alloc_repo = AllocationRepository(db)
        self.profile_repo = ProfileRepository(db)
        self.session_repo = SessionRepository(db)
        self.notif_repo = NotificationRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_booking(self, actor_user_id: int, availability_id: int,
                       allocation_id: int, booking_type: str = "MENTORSHIP",
                       idempotency_key: Optional[str] = None) -> Booking:
        """Executes the SP02 Atomic Booking Transaction with row locks and overlap checks."""
        if not idempotency_key:
            idempotency_key = f"idem:{actor_user_id}:{availability_id}:{int(datetime.utcnow().timestamp())}"

        # 1. Idempotency Check (BR-T14)
        existing = self.booking_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return existing

        # 2. Lock and verify the student actor (row-level lock on student profile prevents concurrent overlap races)
        student = self.db.query(StudentProfile).filter(StudentProfile.user_id == actor_user_id).with_for_update().first()
        if not student or not student.user or student.user.account_status != "ACTIVE":
            raise ValueError("Caller is not an active student mentee")

        # 3. Lock and verify availability slot
        slot = self.avail_repo.get_by_id(availability_id, lock=True)
        if not slot:
            raise ValueError("Availability slot not found")

        if slot.slot_status != "OPEN":
            raise ValueError(f"Availability slot is already {slot.slot_status}")

        if slot.starts_at <= datetime.utcnow():
            raise ValueError("Cannot reserve a slot in the past")

        # Check existing confirmed booking for this slot (double-booking defense)
        existing_slot_booking = self.db.query(Booking).filter(
            Booking.availability_id == availability_id,
            Booking.booking_status == "CONFIRMED"
        ).with_for_update().first()
        if existing_slot_booking:
            raise ValueError("Availability slot has already been confirmed for another booking")

        # 4. Lock and verify mentor profile
        mentor = self.profile_repo.get_mentor_profile(slot.mentor_user_id)
        if not mentor or mentor.user.account_status != "ACTIVE":
            raise ValueError("Mentor account is not active")

        # 5. Lock and verify allocation
        alloc = self.alloc_repo.get_by_id(allocation_id, lock=True)
        if not alloc or alloc.allocation_status != "ACTIVE":
            raise ValueError("Active allocation is required for booking")

        req = alloc.request
        if req.student_user_id != actor_user_id or req.mentor_user_id != slot.mentor_user_id:
            raise ValueError("Allocation does not match student and mentor participants")

        # 6. Check student schedule conflict (overlapping confirmed booking)
        if self.booking_repo.check_student_conflict(actor_user_id, slot.starts_at, slot.ends_at):
            raise ValueError("Student has an overlapping confirmed booking during this time slot")

        # 7. Check mentor schedule conflict
        if self.booking_repo.check_mentor_conflict(slot.mentor_user_id, slot.starts_at, slot.ends_at):
            raise ValueError("Mentor has an overlapping confirmed booking during this time slot")

        # 8. Insert Booking
        booking = self.booking_repo.create_booking(
            allocation_id=allocation_id,
            availability_id=availability_id,
            booking_type=booking_type,
            idempotency_key=idempotency_key
        )

        # 9. Update Slot Status to BOOKED
        slot.slot_status = "BOOKED"

        # 10. Insert Planned Mentorship Session (SCHEDULED)
        session = self.session_repo.create_session(booking.booking_id)

        # 11. Transactional Outbox Event
        dedupe = f"outbox:booking_created:{booking.booking_id}:{int(datetime.utcnow().timestamp())}"
        self.notif_repo.create_outbox_event(
            aggregate_type="BOOKING",
            aggregate_id=booking.booking_id,
            event_type="BOOKING_CONFIRMED",
            payload={
                "booking_id": booking.booking_id,
                "session_id": session.session_id,
                "student_user_id": actor_user_id,
                "mentor_user_id": slot.mentor_user_id,
                "starts_at": slot.starts_at.isoformat(),
                "ends_at": slot.ends_at.isoformat()
            },
            dedupe_key=dedupe
        )

        self.db.commit()
        return booking

    def cancel_booking(self, booking_id: int, actor_user_id: int, reason: str) -> Booking:
        """Executes the SP03 Booking Cancellation Transaction."""
        booking = self.booking_repo.get_by_id(booking_id, lock=True)
        if not booking:
            raise ValueError("Booking not found")

        if booking.booking_status != "CONFIRMED":
            raise ValueError(f"Booking is already in {booking.booking_status} status")

        req = booking.allocation.request
        is_student = req.student_user_id == actor_user_id
        is_mentor = req.mentor_user_id == actor_user_id

        if not is_student and not is_mentor:
            # Check admin role
            user = self.db.query(UserAccount).filter(UserAccount.user_id == actor_user_id).first()
            if not user or not user.role or user.role.role_code != "ADMINISTRATOR":
                raise ValueError("Not authorized to cancel this booking")

        # Check Cancellation Cutoff (Business Rules BR-T16, BR-T17)
        slot = booking.availability
        cutoff_hours = settings.BOOKING_CANCELLATION_CUTOFF_HOURS
        time_to_slot = slot.starts_at - datetime.utcnow()
        if time_to_slot < timedelta(hours=cutoff_hours):
            raise ValueError(f"Cancellation window closed. Bookings must be cancelled at least {cutoff_hours} hours prior to start time.")

        # Update booking
        booking.booking_status = "CANCELLED"
        booking.cancelled_at = datetime.utcnow()
        booking.cancelled_by_user_id = actor_user_id
        booking.cancellation_reason = reason

        # Update scheduled session
        if booking.session and booking.session.session_status == "SCHEDULED":
            booking.session.session_status = "CANCELLED"

        # Reopen slot if in future and policy allows
        if settings.REOPEN_SLOT_ON_CANCELLATION and slot.starts_at > datetime.utcnow():
            slot.slot_status = "OPEN"

        # Outbox event
        dedupe = f"outbox:booking_cancelled:{booking_id}:{int(datetime.utcnow().timestamp())}"
        self.notif_repo.create_outbox_event(
            aggregate_type="BOOKING",
            aggregate_id=booking_id,
            event_type="BOOKING_CANCELLED",
            payload={
                "booking_id": booking_id,
                "cancelled_by_user_id": actor_user_id,
                "student_user_id": req.student_user_id,
                "mentor_user_id": req.mentor_user_id,
                "reason": reason
            },
            dedupe_key=dedupe
        )

        self.db.commit()
        return booking

    def list_student_bookings(self, student_user_id: int) -> List[Booking]:
        return self.booking_repo.list_student_bookings(student_user_id)

    def list_mentor_bookings(self, mentor_user_id: int) -> List[Booking]:
        return self.booking_repo.list_mentor_bookings(mentor_user_id)

