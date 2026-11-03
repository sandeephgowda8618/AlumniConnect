"""AlumniConnect Pydantic Schemas for Availability Slots
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class AvailabilitySlotCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime

    @field_validator("ends_at")
    @classmethod
    def validate_interval(cls, ends_at: datetime, info):
        starts_at = info.data.get("starts_at")
        if starts_at and ends_at <= starts_at:
            raise ValueError("ends_at must be strictly greater than starts_at")
        return ends_at


class AvailabilitySlotOut(BaseModel):
    availability_id: int
    mentor_user_id: int
    starts_at: datetime
    ends_at: datetime
    slot_status: str
    created_at: datetime

    class Config:
        from_attributes = True

