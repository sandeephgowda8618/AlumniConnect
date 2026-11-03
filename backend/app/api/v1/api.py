"""AlumniConnect API v1 Router Aggregator
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, students, mentors, catalogues, requests, allocations,
    availability, bookings, sessions, reviews, recommendations,
    notifications, admin, analytics
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Identity"])
api_router.include_router(students.router, prefix="/students", tags=["Student Portal"])
api_router.include_router(mentors.router, prefix="/mentors", tags=["Mentor Portal & Directory"])
api_router.include_router(catalogues.router, prefix="/catalogues", tags=["Catalogues"])
api_router.include_router(requests.router, prefix="/requests", tags=["Mentorship Requests"])
api_router.include_router(allocations.router, prefix="/allocations", tags=["Mentor Allocations"])
api_router.include_router(availability.router, prefix="/availability", tags=["Availability"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Mentorship Sessions"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Feedback & Reviews"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendation Engine"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["In-App Notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administration"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["DBMS Query Catalogue & Analytics"])

