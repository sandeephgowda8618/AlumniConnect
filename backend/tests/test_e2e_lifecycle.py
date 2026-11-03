import pytest
import httpx
from datetime import datetime, timedelta, timezone
from app.main import app

@pytest.mark.asyncio
async def test_complete_10_step_lifecycle():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Step 1: Student Login (Aarav Sharma)
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "aarav.sharma@alumniconnect.edu", "password": "Password123!"}
        )
        assert login_res.status_code == 200, f"Student login failed: {login_res.text}"
        student_auth = login_res.json()
        student_token = student_auth["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}
        assert student_auth["role"] == "STUDENT"

        # Fetch student profile
        stud_prof_res = await client.get("/api/v1/students/profile", headers=student_headers)
        assert stud_prof_res.status_code == 200, f"Get student profile failed: {stud_prof_res.text}"
        student_profile = stud_prof_res.json()
        student_user_id = student_profile["user_id"]
        print(f"Step 1 OK: Student logged in (user_id={student_user_id})")

        # Step 2: Recommendations Discovery (Neo4j graph candidate generation + 5-factor scoring)
        rec_res = await client.post("/api/v1/recommendations/discover", json={}, headers=student_headers)
        assert rec_res.status_code == 200, f"Rec failed: {rec_res.text}"
        rec_run = rec_res.json()
        recs = rec_run["results"]
        assert len(recs) > 0, "No recommendations returned"
        top_rec = recs[0]
        target_mentor_id = top_rec["mentor_user_id"]
        print(f"Step 2 OK: Top recommended mentor is {top_rec['full_name']} (score={top_rec['overall_score']})")

        # Step 3: Student submits mentorship request
        req_res = await client.post(
            "/api/v1/requests/",
            json={
                "mentor_user_id": target_mentor_id,
                "domain_id": 1,
                "request_message": "E2E lifecycle test request: Guidance on Python and Machine Learning systems.",
                "career_goal_snapshot": "Machine Learning Engineer"
            },
            headers=student_headers
        )
        assert req_res.status_code == 201, f"Submit request failed: {req_res.text}"
        req_data = req_res.json()
        request_id = req_data["request_id"]
        assert req_data["request_status"] == "PENDING"
        print(f"Step 3 OK: Mentorship request submitted (request_id={request_id})")

        # Step 4: Mentor Login (Rohit Verma) & Accept Request (SP01)
        mentor_login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "rohit.verma@alumniconnect.edu", "password": "Password123!"}
        )
        assert mentor_login_res.status_code == 200, f"Mentor login failed: {mentor_login_res.text}"
        mentor_auth = mentor_login_res.json()
        mentor_token = mentor_auth["access_token"]
        mentor_headers = {"Authorization": f"Bearer {mentor_token}"}
        assert mentor_auth["role"] == "MENTOR"

        mentor_prof_res = await client.get("/api/v1/mentors/profile", headers=mentor_headers)
        assert mentor_prof_res.status_code == 200, f"Get mentor profile failed: {mentor_prof_res.text}"
        mentor_profile = mentor_prof_res.json()
        mentor_user_id = mentor_profile["user_id"]

        # Accept the request
        accept_res = await client.post(
            f"/api/v1/requests/{request_id}/accept",
            headers=mentor_headers
        )
        assert accept_res.status_code == 200, f"Accept request failed: {accept_res.text}"
        alloc_data = accept_res.json()
        allocation_id = alloc_data["allocation_id"]
        assert alloc_data["allocation_status"] == "ACTIVE"
        print(f"Step 4 OK: Mentor accepted request {request_id}, allocation active (id={allocation_id})")

        # Step 5: Mentor publishes availability slot (WF-05, BR-AVL-01)
        slot_start = (datetime.now(timezone.utc) + timedelta(days=5)).replace(minute=0, second=0, microsecond=0)
        slot_end = slot_start + timedelta(hours=1)
        slot_res = await client.post(
            "/api/v1/availability/",
            json={
                "starts_at": slot_start.isoformat(),
                "ends_at": slot_end.isoformat()
            },
            headers=mentor_headers
        )
        assert slot_res.status_code == 201, f"Create slot failed: {slot_res.text}"
        slot_data = slot_res.json()
        availability_id = slot_data["availability_id"]
        assert slot_data["slot_status"] == "OPEN"
        print(f"Step 5 OK: Availability slot created (availability_id={availability_id})")

        # Step 6: Student books the slot (SP02, BR-BKG-01..04)
        book_res = await client.post(
            "/api/v1/bookings/",
            json={
                "availability_id": availability_id,
                "allocation_id": allocation_id,
                "booking_type": "MENTORSHIP",
                "idempotency_key": f"test-idemp-{availability_id}"
            },
            headers=student_headers
        )
        assert book_res.status_code == 201, f"Booking failed: {book_res.text}"
        booking_data = book_res.json()
        booking_id = booking_data["booking_id"]
        assert booking_data["booking_status"] == "CONFIRMED"
        print(f"Step 6 OK: Booking confirmed (booking_id={booking_id})")

        # Step 7: Race Condition Guard Test (TX-01) - Attempting double booking should fail
        double_book_res = await client.post(
            "/api/v1/bookings/",
            json={
                "availability_id": availability_id,
                "allocation_id": allocation_id,
                "booking_type": "MENTORSHIP",
                "idempotency_key": f"test-idemp-duplicate-{availability_id}"
            },
            headers=student_headers
        )
        assert double_book_res.status_code in [400, 409], f"Double booking succeeded unexpectedly: {double_book_res.text}"
        print("Step 7 OK: Concurrency guard correctly rejected double-booking")

        # Step 8: Get session and Mentor records session outcome (SP04)
        sessions_res = await client.get("/api/v1/sessions/mentor", headers=mentor_headers)
        assert sessions_res.status_code == 200, f"Get sessions failed: {sessions_res.text}"
        sessions = sessions_res.json()
        session = next(s for s in sessions if s["booking_id"] == booking_id)
        session_id = session["session_id"]

        outcome_res = await client.post(
            f"/api/v1/sessions/{session_id}/outcome",
            json={
                "new_status": "COMPLETED",
                "discussion_summary": "Excellent session on Python backend architecture and graph modeling.",
                "performance_observations": "Strong problem solving skills and architectural intuition.",
                "improvement_areas": "Deep dive into distributed cache invalidation.",
                "next_steps": "1. Build async pipeline. 2. Implement Redis caching.",
                "preparation_recommendation": "Review ACID isolation levels.",
                "skill_assessments": [
                    {"skill_id": 1, "assessment_result": "PROFICIENT", "assessment_notes": "Strong understanding"}
                ]
            },
            headers=mentor_headers
        )
        assert outcome_res.status_code == 200, f"Record outcome failed: {outcome_res.text}"
        completed_session = outcome_res.json()
        assert completed_session["session_status"] == "COMPLETED"
        print(f"Step 8 OK: Session outcome recorded (session_id={session_id})")

        # Step 9: Student submits review & rating (SP05)
        review_res = await client.post(
            "/api/v1/reviews/mentor-review",
            json={
                "session_id": session_id,
                "rating": 5,
                "review_text": "Incredible mentorship session! Rohit provided clear, actionable architectural guidance."
            },
            headers=student_headers
        )
        assert review_res.status_code == 201, f"Submit review failed: {review_res.text}"
        review_data = review_res.json()
        assert review_data["rating"] == 5
        print(f"Step 9 OK: Mentor review submitted (review_id={review_data['review_id']})")

        # Step 10: Run outbox worker to deliver notifications & verify funnel analytics
        from app.workers.outbox_worker import OutboxWorker
        worker = OutboxWorker()
        dispatched = worker.process_pending_events(batch_size=20)
        print(f"Step 10a OK: Outbox worker dispatched {dispatched} pending notifications")

        # Admin checks funnel analytics
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@alumniconnect.edu", "password": "Password123!"}
        )
        admin_token = admin_login.json()["access_token"]
        funnel_res = await client.get("/api/v1/analytics/funnel", headers={"Authorization": f"Bearer {admin_token}"})
        assert funnel_res.status_code == 200, f"Funnel analytics failed: {funnel_res.text}"
        funnel = funnel_res.json()
        assert funnel["total_requests"] >= 1
        assert funnel["completed_sessions"] >= 1
        print(f"Step 10b OK: Admin verified platform funnel: {funnel}")
