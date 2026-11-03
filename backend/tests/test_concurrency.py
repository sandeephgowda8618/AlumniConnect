import pytest
from datetime import datetime, timedelta, timezone
from app.services.booking_service import BookingService
from app.services.availability_service import AvailabilityService
from app.services.request_service import RequestService

def test_tx_01_idempotency_prevents_duplicate_booking(db_session):
    """TX-01: Same idempotency_key returns identical booking record without double insertion."""
    # Create slot 10 days out
    avail_svc = AvailabilityService(db_session)
    slot_start = (datetime.now(timezone.utc) + timedelta(days=10)).replace(minute=0, second=0, microsecond=0)
    slot_end = slot_start + timedelta(minutes=45)
    slot = avail_svc.create_slot(mentor_user_id=2, starts_at=slot_start, ends_at=slot_end)

    # Find or create active allocation for student 5 and mentor 2
    from app.models.entities import MentorshipRequest
    req = db_session.query(MentorshipRequest).filter_by(student_user_id=5, mentor_user_id=2, request_status="ACCEPTED").first()
    if req and req.allocation:
        alloc = req.allocation
    else:
        req_svc = RequestService(db_session)
        req = req_svc.submit_request(student_user_id=5, mentor_user_id=2, domain_id=1, request_message="Idemp test")
        alloc = req_svc.accept_request(request_id=req.request_id, actor_user_id=2)

    bkg_svc = BookingService(db_session)
    idem_key = f"idem-key-unique-{slot.availability_id}"
    
    b1 = bkg_svc.create_booking(actor_user_id=5, availability_id=slot.availability_id, allocation_id=alloc.allocation_id, idempotency_key=idem_key)
    b2 = bkg_svc.create_booking(actor_user_id=5, availability_id=slot.availability_id, allocation_id=alloc.allocation_id, idempotency_key=idem_key)

    assert b1.booking_id == b2.booking_id, "Idempotent call should return the exact same booking"
