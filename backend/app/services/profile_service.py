"""AlumniConnect Profile Service
Handles student and mentor profiles, associative relationships,
Redis cache invalidation, and graph synchronization.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.profile_repository import ProfileRepository
from app.repositories.review_repository import ReviewRepository
from app.services.cache_service import CacheService
from app.core.graph_client import graph_client


class ProfileService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProfileRepository(db)
        self.review_repo = ReviewRepository(db)

    # --- Student Profile ---

    def get_student_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        student = self.repo.get_student_profile(user_id)
        if not student:
            return None
        return self._format_student(student)

    def update_student_profile(self, user_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        student = self.repo.update_student_profile(user_id, **kwargs)
        if not student:
            return None
        # Graph update
        graph_client.engine.upsert_student(
            student.user_id, student.user_id, student.department_id,
            student.programme, student.expected_graduation_year or 0
        )
        CacheService.invalidate_student_recommendations(user_id)
        self.db.commit()
        return self._format_student(student)

    def add_student_skill(self, student_id: int, skill_id: int, proficiency: str, years: float = 0.0) -> Dict[str, Any]:
        item = self.repo.add_student_skill(student_id, skill_id, proficiency, years)
        graph_client.engine.set_student_skill(student_id, skill_id, proficiency, years)
        CacheService.invalidate_student_recommendations(student_id)
        self.db.commit()
        return {"student_user_id": student_id, "skill_id": skill_id, "proficiency_level": proficiency, "years_experience": years}

    def remove_student_skill(self, student_id: int, skill_id: int) -> bool:
        res = self.repo.remove_student_skill(student_id, skill_id)
        s_node = f"Student:{student_id}"
        sk_node = f"Skill:{skill_id}"
        if graph_client.engine.g.has_edge(s_node, sk_node):
            graph_client.engine.g.remove_edge(s_node, sk_node)
        CacheService.invalidate_student_recommendations(student_id)
        self.db.commit()
        return res

    def add_student_domain(self, student_id: int, domain_id: int, priority: int, notes: Optional[str] = None) -> Dict[str, Any]:
        item = self.repo.add_student_domain(student_id, domain_id, priority, notes)
        graph_client.engine.set_student_domain_interest(student_id, domain_id, priority)
        CacheService.invalidate_student_recommendations(student_id)
        self.db.commit()
        return {"student_user_id": student_id, "domain_id": domain_id, "priority_order": priority, "interest_notes": notes}

    def remove_student_domain(self, student_id: int, domain_id: int) -> bool:
        res = self.repo.remove_student_domain(student_id, domain_id)
        s_node = f"Student:{student_id}"
        d_node = f"Domain:{domain_id}"
        if graph_client.engine.g.has_edge(s_node, d_node):
            graph_client.engine.g.remove_edge(s_node, d_node)
        CacheService.invalidate_student_recommendations(student_id)
        self.db.commit()
        return res

    def sync_student_skills_and_domains(self, student_id: int, skills: List[Dict[str, Any]], domains: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        self.repo.sync_student_skills(student_id, skills)
        self.repo.sync_student_domains(student_id, domains)

        # Update in-memory graph edges
        s_node = f"Student:{student_id}"
        if graph_client.engine.g.has_node(s_node):
            edges_to_remove = []
            for u, v, data in graph_client.engine.g.out_edges(s_node, data=True):
                if data.get("type") in ("HAS_SKILL", "INTERESTED_IN"):
                    edges_to_remove.append((u, v))
            for u, v in edges_to_remove:
                graph_client.engine.g.remove_edge(u, v)

            for sk in skills:
                graph_client.engine.set_student_skill(
                    student_id,
                    sk["skill_id"],
                    sk.get("proficiency_level", "INTERMEDIATE"),
                    float(sk.get("years_experience", 0.0) or 0.0)
                )
            for idx, dom in enumerate(domains):
                graph_client.engine.set_student_domain_interest(
                    student_id,
                    dom["domain_id"],
                    dom.get("priority_order", idx + 1)
                )

        CacheService.invalidate_student_recommendations(student_id)
        self.db.commit()
        self.db.expire_all()
        return self.get_student_profile(student_id)

    # --- Mentor Profile ---

    def get_mentor_profile(self, user_id: int, is_owner: bool = False) -> Optional[Dict[str, Any]]:
        # Check cache if public read
        if not is_owner:
            cached = CacheService.get_public_mentor_profile(user_id)
            if cached:
                return cached

        mentor = self.repo.get_mentor_profile(user_id)
        if not mentor:
            return None
        formatted = self._format_mentor(mentor, is_owner=is_owner)
        if not is_owner:
            CacheService.set_public_mentor_profile(user_id, formatted)
        return formatted

    def update_mentor_profile(self, user_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        mentor = self.repo.update_mentor_profile(user_id, **kwargs)
        if not mentor:
            return None
        # Invalidate public cache
        CacheService.invalidate_mentor_profile(user_id)
        # Update graph projection
        graph_client.engine.upsert_mentor(
            mentor.user_id, mentor.user_id, mentor.alumni_department_id,
            mentor.current_company_id, mentor.job_title, float(mentor.years_experience or 0)
        )
        self.db.commit()
        return self._format_mentor(mentor, is_owner=True)

    def add_mentor_skill(self, mentor_id: int, skill_id: int, proficiency: str, years: float = 0.0) -> Dict[str, Any]:
        item = self.repo.add_mentor_skill(mentor_id, skill_id, proficiency, years)
        CacheService.invalidate_mentor_profile(mentor_id)
        graph_client.engine.set_mentor_skill(mentor_id, skill_id, proficiency, years)
        self.db.commit()
        return {"mentor_user_id": mentor_id, "skill_id": skill_id, "proficiency_level": proficiency, "years_experience": years}

    def remove_mentor_skill(self, mentor_id: int, skill_id: int) -> bool:
        res = self.repo.remove_mentor_skill(mentor_id, skill_id)
        CacheService.invalidate_mentor_profile(mentor_id)
        m_node = f"Mentor:{mentor_id}"
        sk_node = f"Skill:{skill_id}"
        if graph_client.engine.g.has_edge(m_node, sk_node):
            graph_client.engine.g.remove_edge(m_node, sk_node)
        self.db.commit()
        return res

    def add_mentor_domain(self, mentor_id: int, domain_id: int, level: str, years: float = 0.0, is_primary: bool = False) -> Dict[str, Any]:
        item = self.repo.add_mentor_domain(mentor_id, domain_id, level, years, is_primary)
        CacheService.invalidate_mentor_profile(mentor_id)
        graph_client.engine.set_mentor_domain_expertise(mentor_id, domain_id, level, is_primary)
        self.db.commit()
        return {"mentor_user_id": mentor_id, "domain_id": domain_id, "expertise_level": level, "years_experience": years, "is_primary": is_primary}

    def remove_mentor_domain(self, mentor_id: int, domain_id: int) -> bool:
        res = self.repo.remove_mentor_domain(mentor_id, domain_id)
        CacheService.invalidate_mentor_profile(mentor_id)
        m_node = f"Mentor:{mentor_id}"
        d_node = f"Domain:{domain_id}"
        if graph_client.engine.g.has_edge(m_node, d_node):
            graph_client.engine.g.remove_edge(m_node, d_node)
        self.db.commit()
        return res

    def list_public_mentors(self, domain_id: Optional[int] = None, skill_id: Optional[int] = None,
                            company_id: Optional[int] = None, min_years: Optional[float] = None) -> List[Dict[str, Any]]:
        mentors = self.repo.list_public_mentors(domain_id=domain_id, skill_id=skill_id, company_id=company_id, min_years=min_years)
        return [self._format_mentor(m, is_owner=False) for m in mentors]

    # --- Formatting helpers ensuring privacy rules ---

    def _format_student(self, s) -> Dict[str, Any]:
        return {
            "user_id": s.user_id,
            "display_name": s.user.display_name if s.user else "",
            "email": s.user.email if s.user else "",
            "student_number": s.student_number,
            "department_id": s.department_id,
            "department_name": s.department.department_name if s.department else None,
            "programme": s.programme,
            "batch_year": s.batch_year,
            "expected_graduation_year": s.expected_graduation_year,
            "career_goal": s.career_goal,
            "bio": s.bio,
            "skills": [
                {
                    "skill_id": sk.skill_id,
                    "skill_name": sk.skill.skill_name if sk.skill else "",
                    "proficiency_level": sk.proficiency_level,
                    "years_experience": float(sk.years_experience or 0)
                } for sk in s.skills
            ],
            "domain_interests": [
                {
                    "domain_id": di.domain_id,
                    "domain_name": di.domain.domain_name if di.domain else "",
                    "priority_order": di.priority_order,
                    "interest_notes": di.interest_notes
                } for di in s.domain_interests
            ]
        }

    def _format_mentor(self, m, is_owner: bool = False) -> Dict[str, Any]:
        count, avg = self.review_repo.get_mentor_rating_stats(m.user_id)
        active_mentees = self.repo.get_mentor_active_mentees_count(m.user_id)

        data = {
            "user_id": m.user_id,
            "display_name": m.user.display_name if m.user else "",
            "email": m.user.email if (is_owner and m.user) else None,  # Excluded for public viewers
            "job_title": m.job_title,
            "years_experience": float(m.years_experience or 0),
            "max_active_mentees": m.max_active_mentees,
            "accepting_requests": m.accepting_requests,
            "professional_summary": m.professional_summary,
            "company_id": m.current_company_id,
            "company_name": m.company.company_name if m.company else None,
            "industry": m.company.industry if m.company else None,
            "department_id": m.alumni_department_id,
            "department_name": m.department.department_name if m.department else None,
            "skills": [
                {
                    "skill_id": sk.skill_id,
                    "skill_name": sk.skill.skill_name if sk.skill else "",
                    "proficiency_level": sk.proficiency_level,
                    "years_experience": float(sk.years_experience or 0)
                } for sk in m.skills
            ],
            "domain_expertises": [
                {
                    "domain_id": de.domain_id,
                    "domain_name": de.domain.domain_name if de.domain else "",
                    "expertise_level": de.expertise_level,
                    "years_experience": float(de.years_experience or 0),
                    "is_primary": de.is_primary
                } for de in m.domain_expertises
            ],
            "active_mentees_count": active_mentees,
            "average_rating": avg if count > 0 else None,
            "review_count": count
        }
        return data

