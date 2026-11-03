"""AlumniConnect Notification Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationOut
from app.models.entities import UserAccount

router = APIRouter()


@router.get("", response_model=List[NotificationOut], include_in_schema=False)
@router.get("/", response_model=List[NotificationOut])
def list_notifications(
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists in-app notifications for the authenticated user."""
    service = NotificationService(db)
    notifs = service.list_user_notifications(current_user.user_id)
    return [
        {
            "notification_id": n.notification_id,
            "recipient_user_id": n.recipient_user_id,
            "title": n.title,
            "body": n.body,
            "created_at": n.created_at,
            "read_at": n.read_at,
            "is_read": n.read_at is not None
        } for n in notifs
    ]


@router.post("/{notification_id}/read", status_code=status.HTTP_200_OK)
def mark_notification_read(
    notification_id: int,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks a single notification as read."""
    service = NotificationService(db)
    success = service.mark_read(notification_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"status": "success"}


@router.post("/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_read(
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks all notifications as read for current user."""
    service = NotificationService(db)
    count = service.mark_all_read(current_user.user_id)
    return {"marked_read": count}

