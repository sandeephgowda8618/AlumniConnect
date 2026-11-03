import pytest
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_sec_01_student_cannot_access_mentor_inbox():
    """SEC-01: RBAC enforcement - Student gets 403 trying to access mentor endpoints."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Student login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "aarav.sharma@alumniconnect.edu", "password": "Password123!"}
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access mentor inbox
        res = await client.get("/api/v1/requests/mentor/inbox", headers=headers)
        assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}"

@pytest.mark.asyncio
async def test_sec_02_mentor_cannot_access_admin_funnel():
    """SEC-02: RBAC enforcement - Mentor gets 403 trying to access admin analytics."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Mentor login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "rohit.verma@alumniconnect.edu", "password": "Password123!"}
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access admin funnel analytics
        res = await client.get("/api/v1/analytics/funnel", headers=headers)
        assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}"

