"""AlumniConnect SQL Analytics & Query Catalogue Repository
Implements the 32 queries from the authoritative AlumniConnect SQL Query Catalogue Final (Q01–Q32)
and administrative conversion funnel reports.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, func


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    # Q01: Student Profile with Department
    def q01_student_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT
            sp.user_id,
            sp.student_number,
            ua.display_name AS full_name,
            ua.email,
            d.department_name,
            sp.programme,
            sp.batch_year,
            sp.expected_graduation_year,
            sp.career_goal
        FROM student_profile AS sp
        JOIN user_account AS ua ON ua.user_id = sp.user_id
        JOIN department AS d ON d.department_id = sp.department_id
        WHERE sp.user_id = :user_id;
        """
        res = self.db.execute(text(sql), {"user_id": user_id}).mappings().first()
        return dict(res) if res else None

    # Q06: Incomplete Mentor Profiles (NULL handling)
    def q06_incomplete_mentor_profiles(self) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            mp.user_id,
            ua.display_name,
            mp.job_title,
            mp.current_company_id,
            mp.professional_summary
        FROM mentor_profile AS mp
        JOIN user_account AS ua ON ua.user_id = mp.user_id
        WHERE mp.current_company_id IS NULL
           OR mp.professional_summary IS NULL
           OR TRIM(mp.professional_summary) = '';
        """
        return [dict(r) for r in self.db.execute(text(sql)).mappings().all()]

    # Q10: Students without an active allocation (NOT EXISTS)
    def q10_students_without_active_allocation(self) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            sp.user_id,
            sp.student_number,
            ua.display_name,
            d.department_name
        FROM student_profile AS sp
        JOIN user_account AS ua ON ua.user_id = sp.user_id
        JOIN department AS d ON d.department_id = sp.department_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM mentor_allocation AS ma
            JOIN mentorship_request AS mr ON mr.request_id = ma.request_id
            WHERE mr.student_user_id = sp.user_id
              AND ma.allocation_status = 'ACTIVE'
        );
        """
        return [dict(r) for r in self.db.execute(text(sql)).mappings().all()]

    # Q13: Mentors currently mentoring the most students
    def q13_mentors_most_active_students(self, limit: int = 10) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            mp.user_id,
            ua.display_name,
            mp.job_title,
            mp.max_active_mentees,
            COUNT(ma.allocation_id) AS active_mentee_count
        FROM mentor_profile AS mp
        JOIN user_account AS ua ON ua.user_id = mp.user_id
        LEFT JOIN mentorship_request AS mr ON mr.mentor_user_id = mp.user_id
        LEFT JOIN mentor_allocation AS ma ON ma.request_id = mr.request_id AND ma.allocation_status = 'ACTIVE'
        GROUP BY mp.user_id, ua.display_name, mp.job_title, mp.max_active_mentees
        ORDER BY active_mentee_count DESC
        LIMIT :limit;
        """
        return [dict(r) for r in self.db.execute(text(sql), {"limit": limit}).mappings().all()]

    # Q14: Mentors with no reviews yet
    def q14_mentors_with_no_reviews(self) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            mp.user_id,
            ua.display_name,
            mp.job_title
        FROM mentor_profile AS mp
        JOIN user_account AS ua ON ua.user_id = mp.user_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM mentor_availability AS ma
            JOIN booking AS b ON b.availability_id = ma.availability_id
            JOIN mentorship_session AS ms ON ms.booking_id = b.booking_id
            JOIN mentor_review AS mr ON mr.session_id = ms.session_id
            WHERE ma.mentor_user_id = mp.user_id
        );
        """
        return [dict(r) for r in self.db.execute(text(sql)).mappings().all()]

    # Q21: Requests by Department and Domain
    def q21_requests_by_department_and_domain(self) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            d.department_name,
            dom.domain_name,
            COUNT(mr.request_id) AS request_count,
            SUM(CASE WHEN mr.request_status = 'ACCEPTED' THEN 1 ELSE 0 END) AS accepted_count
        FROM mentorship_request AS mr
        JOIN student_profile AS sp ON sp.user_id = mr.student_user_id
        JOIN department AS d ON d.department_id = sp.department_id
        JOIN mentorship_domain AS dom ON dom.domain_id = mr.domain_id
        GROUP BY d.department_name, dom.domain_name
        ORDER BY request_count DESC;
        """
        return [dict(r) for r in self.db.execute(text(sql)).mappings().all()]

    # Q22: Mentors with highest average review rating
    def q22_mentors_highest_rated(self, min_reviews: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            mp.user_id,
            ua.display_name,
            mp.job_title,
            c.company_name,
            COUNT(mr.review_id) AS review_count,
            ROUND(AVG(mr.rating), 2) AS average_rating
        FROM mentor_profile AS mp
        JOIN user_account AS ua ON ua.user_id = mp.user_id
        LEFT JOIN company AS c ON c.company_id = mp.current_company_id
        JOIN mentor_availability AS ma ON ma.mentor_user_id = mp.user_id
        JOIN booking AS b ON b.availability_id = ma.availability_id
        JOIN mentorship_session AS ms ON ms.booking_id = b.booking_id
        JOIN mentor_review AS mr ON mr.session_id = ms.session_id
        GROUP BY mp.user_id, ua.display_name, mp.job_title, c.company_name
        HAVING COUNT(mr.review_id) >= :min_reviews
        ORDER BY average_rating DESC, review_count DESC
        LIMIT :limit;
        """
        return [dict(r) for r in self.db.execute(text(sql), {"min_reviews": min_reviews, "limit": limit}).mappings().all()]

    # Q26: Booking cancellation and no-show rates
    def q26_cancellation_and_noshow_rates(self) -> Dict[str, Any]:
        sql = """
        SELECT
            COUNT(b.booking_id) AS total_bookings,
            SUM(CASE WHEN b.booking_status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_bookings,
            SUM(CASE WHEN ms.session_status = 'NO_SHOW' THEN 1 ELSE 0 END) AS no_show_sessions,
            SUM(CASE WHEN ms.session_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_sessions
        FROM booking AS b
        LEFT JOIN mentorship_session AS ms ON ms.booking_id = b.booking_id;
        """
        res = self.db.execute(text(sql)).mappings().first()
        if not res or res["total_bookings"] == 0:
            return {"total_bookings": 0, "cancellation_rate_pct": 0.0, "noshow_rate_pct": 0.0, "completion_rate_pct": 0.0}
        total = res["total_bookings"]
        return {
            "total_bookings": total,
            "cancelled_bookings": res["cancelled_bookings"] or 0,
            "no_show_sessions": res["no_show_sessions"] or 0,
            "completed_sessions": res["completed_sessions"] or 0,
            "cancellation_rate_pct": round(((res["cancelled_bookings"] or 0) / total) * 100, 2),
            "noshow_rate_pct": round(((res["no_show_sessions"] or 0) / total) * 100, 2),
            "completion_rate_pct": round(((res["completed_sessions"] or 0) / total) * 100, 2)
        }

    # Q27: Mentor capacity utilisation
    def q27_mentor_capacity_utilisation(self) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            mp.user_id,
            ua.display_name,
            mp.max_active_mentees,
            COALESCE(active_tbl.active_count, 0) AS current_active_mentees,
            ROUND((COALESCE(active_tbl.active_count, 0) * 100.0) / mp.max_active_mentees, 1) AS utilization_percent,
            (COALESCE(active_tbl.active_count, 0) >= mp.max_active_mentees) AS is_at_capacity
        FROM mentor_profile AS mp
        JOIN user_account AS ua ON ua.user_id = mp.user_id
        LEFT JOIN (
            SELECT mr.mentor_user_id, COUNT(*) AS active_count
            FROM mentor_allocation AS ma
            JOIN mentorship_request AS mr ON mr.request_id = ma.request_id
            WHERE ma.allocation_status = 'ACTIVE'
            GROUP BY mr.mentor_user_id
        ) AS active_tbl ON active_tbl.mentor_user_id = mp.user_id
        ORDER BY utilization_percent DESC;
        """
        return [dict(r) for r in self.db.execute(text(sql)).mappings().all()]

    # Q28: Skill demand vs mentor supply
    def q28_skill_demand_vs_supply(self) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            s.skill_id,
            s.skill_name,
            COALESCE(dem.demand_count, 0) AS student_demand_count,
            COALESCE(sup.supply_count, 0) AS mentor_supply_count
        FROM skill AS s
        LEFT JOIN (
            SELECT skill_id, COUNT(*) AS demand_count
            FROM student_skill
            GROUP BY skill_id
        ) AS dem ON dem.skill_id = s.skill_id
        LEFT JOIN (
            SELECT skill_id, COUNT(*) AS supply_count
            FROM mentor_skill
            GROUP BY skill_id
        ) AS sup ON sup.skill_id = s.skill_id
        ORDER BY student_demand_count DESC, mentor_supply_count DESC;
        """
        return [dict(r) for r in self.db.execute(text(sql)).mappings().all()]

    # Q29: Request-to-allocation-to-session funnel (CTEs)
    def q29_conversion_funnel(self) -> Dict[str, Any]:
        sql = """
        WITH FunnelData AS (
            SELECT
                COUNT(DISTINCT r.request_id) AS total_requests,
                COUNT(DISTINCT CASE WHEN r.request_status = 'ACCEPTED' THEN r.request_id END) AS accepted_requests,
                COUNT(DISTINCT b.booking_id) AS confirmed_bookings,
                COUNT(DISTINCT CASE WHEN s.session_status = 'COMPLETED' THEN s.session_id END) AS completed_sessions,
                COUNT(DISTINCT rev.review_id) AS reviewed_sessions
            FROM mentorship_request AS r
            LEFT JOIN mentor_allocation AS a ON a.request_id = r.request_id
            LEFT JOIN booking AS b ON b.allocation_id = a.allocation_id AND b.booking_status = 'CONFIRMED'
            LEFT JOIN mentorship_session AS s ON s.booking_id = b.booking_id
            LEFT JOIN mentor_review AS rev ON rev.session_id = s.session_id
        )
        SELECT * FROM FunnelData;
        """
        res = self.db.execute(text(sql)).mappings().first()
        if not res:
            return {"total_requests": 0, "accepted_requests": 0, "confirmed_bookings": 0, "completed_sessions": 0, "reviewed_sessions": 0, "steps": []}

        reqs = res["total_requests"] or 0
        accs = res["accepted_requests"] or 0
        bks = res["confirmed_bookings"] or 0
        comps = res["completed_sessions"] or 0
        revs = res["reviewed_sessions"] or 0

        steps = [
            {"step_name": "Submitted Requests", "count": reqs, "conversion_rate_percent": 100.0},
            {"step_name": "Accepted Allocations", "count": accs, "conversion_rate_percent": round((accs / reqs * 100), 1) if reqs else 0.0},
            {"step_name": "Confirmed Bookings", "count": bks, "conversion_rate_percent": round((bks / accs * 100), 1) if accs else 0.0},
            {"step_name": "Completed Sessions", "count": comps, "conversion_rate_percent": round((comps / bks * 100), 1) if bks else 0.0},
            {"step_name": "Mentor Reviews Submitted", "count": revs, "conversion_rate_percent": round((revs / comps * 100), 1) if comps else 0.0}
        ]
        return {
            "total_requests": reqs,
            "accepted_requests": accs,
            "confirmed_bookings": bks,
            "completed_sessions": comps,
            "reviewed_sessions": revs,
            "steps": steps
        }

    # Platform Overview
    def get_platform_overview(self) -> Dict[str, Any]:
        sql = """
        SELECT
            (SELECT COUNT(*) FROM student_profile) AS total_students,
            (SELECT COUNT(*) FROM mentor_profile) AS total_mentors,
            (SELECT COUNT(*) FROM mentorship_request) AS total_requests,
            (SELECT COUNT(*) FROM mentor_allocation WHERE allocation_status = 'ACTIVE') AS active_allocations,
            (SELECT COUNT(*) FROM mentorship_session WHERE session_status = 'COMPLETED') AS completed_sessions,
            COALESCE((SELECT ROUND(AVG(rating), 2) FROM mentor_review), 0.0) AS average_platform_rating;
        """
        res = self.db.execute(text(sql)).mappings().first()
        return dict(res) if res else {
            "total_students": 0, "total_mentors": 0, "total_requests": 0,
            "active_allocations": 0, "completed_sessions": 0, "average_platform_rating": 0.0
        }

