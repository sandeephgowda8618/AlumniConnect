"""AlumniConnect Background Outbox Worker
Polls and claims pending transactional events from `notification_outbox`,
fans out user inbox notifications, synchronizes graph projections into Neo4j,
invalidates Redis caches, and handles safe retries.
"""

import time
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.repositories.notification_repository import NotificationRepository
from app.services.cache_service import CacheService
from app.core.graph_client import graph_client
from app.models.entities import NotificationOutbox

logger = logging.getLogger("alumniconnect.worker")


class OutboxWorker:
    def __init__(self, poll_interval: float = 2.0):
        self.poll_interval = poll_interval
        self._running = False

    def process_pending_events(self, batch_size: int = 20) -> int:
        """Processes a batch of pending outbox events."""
        db: Session = SessionLocal()
        processed_count = 0
        try:
            repo = NotificationRepository(db)
            events = repo.get_pending_outbox_events(limit=batch_size)

            for event in events:
                try:
                    self._dispatch_event(db, repo, event)
                    repo.mark_outbox_delivered(event.outbox_id)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process outbox event {event.outbox_id} ({e})")
                    repo.mark_outbox_failed(event.outbox_id, str(e))
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Outbox worker batch error: {e}")
        finally:
            db.close()

        return processed_count

    def _dispatch_event(self, db: Session, repo: NotificationRepository, event: NotificationOutbox):
        payload: Dict[str, Any] = event.payload_json or {}
        event_type = event.event_type

        if event_type == "MENTORSHIP_REQUEST_SUBMITTED":
            mentor_id = payload.get("mentor_user_id")
            student_name = payload.get("student_name", "A student")
            if mentor_id:
                repo.create_notification(
                    recipient_user_id=mentor_id,
                    outbox_id=event.outbox_id,
                    title="New Mentorship Request",
                    body=f"{student_name} has submitted a mentorship request to you."
                )

        elif event_type == "MENTORSHIP_REQUEST_ACCEPTED":
            student_id = payload.get("student_user_id")
            mentor_id = payload.get("mentor_user_id")
            alloc_id = payload.get("allocation_id", 0)
            if student_id:
                repo.create_notification(
                    recipient_user_id=student_id,
                    outbox_id=event.outbox_id,
                    title="Mentorship Request Accepted!",
                    body="Your mentorship request has been accepted. You may now view open slots and book appointments."
                )
            # Sync graph projection
            if student_id and mentor_id:
                graph_client.engine.record_mentored_by(student_id, mentor_id, alloc_id)

        elif event_type == "MENTORSHIP_REQUEST_REJECTED":
            student_id = payload.get("student_user_id")
            reason = payload.get("reason", "Declined by mentor")
            if student_id:
                repo.create_notification(
                    recipient_user_id=student_id,
                    outbox_id=event.outbox_id,
                    title="Mentorship Request Update",
                    body=f"Your mentorship request was declined: {reason}"
                )

        elif event_type == "BOOKING_CONFIRMED":
            student_id = payload.get("student_user_id")
            mentor_id = payload.get("mentor_user_id")
            starts_at = payload.get("starts_at", "")
            if student_id:
                repo.create_notification(
                    recipient_user_id=student_id,
                    outbox_id=event.outbox_id,
                    title="Booking Confirmed",
                    body=f"Your mentorship appointment is confirmed for {starts_at}."
                )
            if mentor_id:
                repo.create_notification(
                    recipient_user_id=mentor_id,
                    outbox_id=event.outbox_id,
                    title="New Appointment Booked",
                    body=f"A mentee has booked your availability slot on {starts_at}."
                )

        elif event_type == "BOOKING_CANCELLED":
            student_id = payload.get("student_user_id")
            mentor_id = payload.get("mentor_user_id")
            reason = payload.get("reason", "")
            msg = f"Mentorship appointment cancelled. Reason: {reason}"
            if student_id:
                repo.create_notification(
                    recipient_user_id=student_id,
                    outbox_id=event.outbox_id,
                    title="Booking Cancelled",
                    body=msg
                )
            if mentor_id:
                repo.create_notification(
                    recipient_user_id=mentor_id,
                    outbox_id=event.outbox_id,
                    title="Booking Cancelled",
                    body=msg
                )

        elif event_type == "SESSION_OUTCOME_RECORDED":
            student_id = payload.get("student_user_id")
            status = payload.get("status", "COMPLETED")
            if student_id:
                repo.create_notification(
                    recipient_user_id=student_id,
                    outbox_id=event.outbox_id,
                    title=f"Session Marked {status}",
                    body="Your mentor has recorded the discussion outcomes and skill evaluation. Please submit your feedback."
                )

        elif event_type == "MENTOR_REVIEW_SUBMITTED":
            mentor_id = payload.get("mentor_user_id")
            rating = payload.get("rating", 5)
            if mentor_id:
                repo.create_notification(
                    recipient_user_id=mentor_id,
                    outbox_id=event.outbox_id,
                    title="New Review Received",
                    body=f"A mentee submitted a {rating}-star review for your mentorship session."
                )
                # Invalidate cached mentor profile to reflect updated score
                CacheService.invalidate_mentor_profile(mentor_id)

    def run_once(self) -> int:
        return self.process_pending_events()

    def run_forever(self):
        self._running = True
        print(f"[*] AlumniConnect Outbox Worker active. Polling notification_outbox every {self.poll_interval}s...")
        try:
            while self._running:
                dispatched = self.process_pending_events()
                if dispatched > 0:
                    print(f"[{time.strftime('%X')}] [Outbox Worker] Processed & dispatched {dispatched} event(s)")
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n[*] Outbox Worker shutting down...")


outbox_worker = OutboxWorker()

if __name__ == "__main__":
    outbox_worker.run_forever()

