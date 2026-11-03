"""AlumniConnect Mentor Availability Service
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.availability_repository import AvailabilityRepository
from app.models.entities import MentorAvailability


class AvailabilityService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AvailabilityRepository(db)

    def create_slot(self, mentor_user_id: int, starts_at: datetime, ends_at: datetime) -> MentorAvailability:
        if starts_at.tzinfo is not None:
            starts_at = starts_at.astimezone(timezone.utc).replace(tzinfo=None)
        if ends_at.tzinfo is not None:
            ends_at = ends_at.astimezone(timezone.utc).replace(tzinfo=None)

        if ends_at <= starts_at:
            raise ValueError("Slot end time must be strictly after start time")

        if starts_at <= datetime.utcnow():
            raise ValueError("Availability slots must be scheduled in the future")

        # Overlap check
        overlap = self.repo.find_overlapping_slot(mentor_user_id, starts_at, ends_at)
        if overlap:
            raise ValueError(f"Slot overlaps with an existing slot from {overlap.starts_at} to {overlap.ends_at}")

        slot = self.repo.create_slot(mentor_user_id, starts_at, ends_at)
        self.db.commit()
        return slot

    def list_mentor_slots(self, mentor_user_id: int, include_past: bool = False) -> List[MentorAvailability]:
        return self.repo.list_mentor_slots(mentor_user_id, include_past=include_past)

    def list_open_slots_for_mentor(self, mentor_user_id: int) -> List[MentorAvailability]:
        return self.repo.list_open_slots_for_mentor(mentor_user_id)

    def withdraw_slot(self, availability_id: int, mentor_user_id: int) -> bool:
        slot = self.repo.get_by_id(availability_id)
        if not slot:
            raise ValueError("Availability slot not found")
        if slot.mentor_user_id != mentor_user_id:
            raise ValueError("Not authorized to withdraw this slot")
        if slot.slot_status != "OPEN":
            raise ValueError("Only OPEN slots can be withdrawn")

        res = self.repo.delete_slot(availability_id)
        self.db.commit()
        return res
