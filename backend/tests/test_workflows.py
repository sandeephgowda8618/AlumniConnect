import pytest
from datetime import datetime, timedelta, timezone
from app.services.request_service import RequestService
from app.services.booking_service import BookingService
from app.services.session_service import SessionService
from app.services.availability_service import AvailabilityService

def test_wf_01_request_submission_and_rejection(db_session):
    """WF-01: Mentorship request submission -> PENDING -> REJECTED."""
    req_svc = RequestService(db_session)
    # Student 6 (Priya Patel) submits request to Mentor 3 (Sneha Rao)
    req = req_svc.submit_request(
        student_user_id=6,
        mentor_user_id=3,
        domain_id=1,
        request_message="Test rejection workflow"
    )
    assert req.request_status == "PENDING"
    
    # Mentor 3 rejects with reason
    rejected = req_svc.reject_request(
        request_id=req.request_id,
        actor_user_id=3,
        reason="Current mentee quota full for this semester"
    )
    assert rejected.request_status == "REJECTED"
    assert rejected.decision_reason == "Current mentee quota full for this semester"

def test_wf_02_invalid_request_transition(db_session):
    """WF-02: Disallow accepting an already rejected request."""
    req_svc = RequestService(db_session)
    req = req_svc.submit_request(
        student_user_id=6,
        mentor_user_id=4,
        domain_id=2,
        request_message="Test invalid transition"
    )
    req_svc.reject_request(request_id=req.request_id, actor_user_id=4, reason="Not matching domain")
    
    # Trying to accept now should raise ValueError
    with pytest.raises(ValueError, match="is already in REJECTED status"):
        req_svc.accept_request(request_id=req.request_id, actor_user_id=4)
