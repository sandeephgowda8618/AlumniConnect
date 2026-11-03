"""AlumniConnect Notification & Transactional Outbox Repository
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.entities import NotificationOutbox, Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Outbox Operations ---

    def create_outbox_event(self, aggregate_type: str, aggregate_id: int, event_type: str,
                            payload: Dict[str, Any], dedupe_key: str) -> NotificationOutbox:
        # Avoid duplicate outbox entries with same dedupe_key
        existing = (
            self.db.query(NotificationOutbox)
            .filter(NotificationOutbox.dedupe_key == dedupe_key)
            .first()
        )
        if existing:
            return existing

        event = NotificationOutbox(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload_json=payload,
            delivery_status="PENDING",
            dedupe_key=dedupe_key,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.flush()
        return event

    def get_pending_outbox_events(self, limit: int = 20) -> List[NotificationOutbox]:
        return (
            self.db.query(NotificationOutbox)
            .filter(NotificationOutbox.delivery_status == "PENDING")
            .order_by(NotificationOutbox.created_at.asc())
            .limit(limit)
            .all()
        )

    def mark_outbox_delivered(self, outbox_id: int) -> Optional[NotificationOutbox]:
        event = self.db.query(NotificationOutbox).filter(NotificationOutbox.outbox_id == outbox_id).first()
        if event:
            event.delivery_status = "SENT"
            event.processed_at = datetime.utcnow()
            self.db.flush()
        return event

    def mark_outbox_failed(self, outbox_id: int, error_msg: str) -> Optional[NotificationOutbox]:
        event = self.db.query(NotificationOutbox).filter(NotificationOutbox.outbox_id == outbox_id).first()
        if event:
            event.attempt_count += 1
            event.last_error = error_msg
            if event.attempt_count >= 5:
                event.delivery_status = "FAILED"
            self.db.flush()
        return event

    # --- In-App Notifications Fan-Out ---

    def create_notification(self, recipient_user_id: int, outbox_id: int,
                            title: str, body: str) -> Optional[Notification]:
        existing = (
            self.db.query(Notification)
            .filter(Notification.outbox_id == outbox_id, Notification.recipient_user_id == recipient_user_id)
            .first()
        )
        if existing:
            return existing

        notif = Notification(
            recipient_user_id=recipient_user_id,
            outbox_id=outbox_id,
            title=title,
            body=body,
            created_at=datetime.utcnow()
        )
        self.db.add(notif)
        self.db.flush()
        return notif

    def list_user_notifications(self, user_id: int, limit: int = 50) -> List[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.recipient_user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        notif = (
            self.db.query(Notification)
            .filter(Notification.notification_id == notification_id, Notification.recipient_user_id == user_id)
            .first()
        )
        if notif:
            notif.read_at = datetime.utcnow()
            self.db.flush()
            return True
        return False

    def mark_all_as_read(self, user_id: int) -> int:
        count = (
            self.db.query(Notification)
            .filter(Notification.recipient_user_id == user_id, Notification.read_at.is_(None))
            .update({"read_at": datetime.utcnow()})
        )
        self.db.flush()
        return count

