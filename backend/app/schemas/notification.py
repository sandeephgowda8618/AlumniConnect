"""AlumniConnect Pydantic Schemas for In-App Notifications
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationOut(BaseModel):
    notification_id: int
    recipient_user_id: int
    title: str
    body: str
    created_at: datetime
    read_at: Optional[datetime] = None
    is_read: bool = False

    class Config:
        from_attributes = True

