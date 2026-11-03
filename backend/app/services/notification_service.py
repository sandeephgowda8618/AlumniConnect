"""AlumniConnect Notification Service
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.notification_repository import NotificationRepository
from app.models.entities import Notification


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def list_user_notifications(self, user_id: int) -> List[Notification]:
        return self.repo.list_user_notifications(user_id)

    def mark_read(self, notification_id: int, user_id: int) -> bool:
        res = self.repo.mark_as_read(notification_id, user_id)
        self.db.commit()
        return res

    def mark_all_read(self, user_id: int) -> int:
        count = self.repo.mark_all_as_read(user_id)
        self.db.commit()
        return count

