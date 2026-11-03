"""AlumniConnect Mentor Availability Repository
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.entities import MentorAvailability


class AvailabilityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, availability_id: int, lock: bool = False) -> Optional[MentorAvailability]:
        query = self.db.query(MentorAvailability).filter(MentorAvailability.availability_id == availability_id)
        if lock:
            query = query.with_for_update()
        return query.first()

    def find_overlapping_slot(self, mentor_user_id: int, starts_at: datetime, ends_at: datetime,
                               exclude_id: Optional[int] = None) -> Optional[MentorAvailability]:
        """Finds any slot owned by the mentor that overlaps with the proposed [starts_at, ends_at) interval."""
        query = self.db.query(MentorAvailability).filter(
            MentorAvailability.mentor_user_id == mentor_user_id,
            MentorAvailability.slot_status.in_(["OPEN", "BOOKED"]),
            MentorAvailability.starts_at < ends_at,
            MentorAvailability.ends_at > starts_at
        )
        if exclude_id:
            query = query.filter(MentorAvailability.availability_id != exclude_id)
        return query.first()

    def create_slot(self, mentor_user_id: int, starts_at: datetime, ends_at: datetime) -> MentorAvailability:
        slot = MentorAvailability(
            mentor_user_id=mentor_user_id,
            starts_at=starts_at,
            ends_at=ends_at,
            slot_status="OPEN",
            created_at=datetime.utcnow()
        )
        self.db.add(slot)
        self.db.flush()
        return slot

    def list_mentor_slots(self, mentor_user_id: int, include_past: bool = False) -> List[MentorAvailability]:
        query = self.db.query(MentorAvailability).filter(MentorAvailability.mentor_user_id == mentor_user_id)
        if not include_past:
            query = query.filter(MentorAvailability.ends_at >= datetime.utcnow())
        return query.order_by(MentorAvailability.starts_at.asc()).all()

    def list_open_slots_for_mentor(self, mentor_user_id: int) -> List[MentorAvailability]:
        return (
            self.db.query(MentorAvailability)
            .filter(
                MentorAvailability.mentor_user_id == mentor_user_id,
                MentorAvailability.slot_status == "OPEN",
                MentorAvailability.starts_at > datetime.utcnow()
            )
            .order_by(MentorAvailability.starts_at.asc())
            .all()
        )

    def update_slot_status(self, availability_id: int, new_status: str) -> Optional[MentorAvailability]:
        slot = self.get_by_id(availability_id)
        if slot:
            slot.slot_status = new_status
            self.db.flush()
        return slot

    def delete_slot(self, availability_id: int) -> bool:
        slot = self.get_by_id(availability_id)
        if slot and slot.slot_status == "OPEN":
            self.db.delete(slot)
            self.db.flush()
            return True
        return False

