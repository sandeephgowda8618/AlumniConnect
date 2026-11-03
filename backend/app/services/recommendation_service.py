"""AlumniConnect Multi-Factor Recommendation Service
Implements the recommendation pipeline strictly following the Recommendation Design Specification:
1. Neo4j graph-based candidate discovery
2. Authoritative MySQL capacity and eligibility gating
3. Five-factor transparent weighted scoring (Skills 30%, Domains 20%, Experience 15%, Career 20%, Quality 15%)
4. Structured human-readable match explanations
5. Redis caching (300s TTL)
6. Decision run & candidate snapshot persistence in MySQL
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.graph_client import graph_client
from app.repositories.profile_repository import ProfileRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.services.cache_service import CacheService
from app.models.entities import StudentProfile, MentorProfile, UserAccount


PROFICIENCY_WEIGHTS = {
    "BEGINNER": 0.35,
    "INTERMEDIATE": 0.65,
    "ADVANCED": 0.85,
    "EXPERT": 1.00
}


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.review_repo = ReviewRepository(db)
        self.rec_repo = RecommendationRepository(db)

    def get_recommendations_for_student(self, student_user_id: int, filters: Optional[Dict[str, Any]] = None,
                                        limit: int = 10, skip_cache: bool = False) -> Dict[str, Any]:
        filters = filters or {}

        # 1. Check Redis Cache
        if not skip_cache:
            cached = CacheService.get_cached_recommendations(student_user_id, filters)
            if cached is not None:
                return {
                    "run_id": None,
                    "student_user_id": student_user_id,
                    "algorithm_version": "v1.0-graph-weighted",
                    "executed_at": datetime.utcnow(),
                    "results": cached,
                    "from_cache": True
                }

        # 2. Retrieve Student Profile from MySQL
        student = self.profile_repo.get_student_profile(student_user_id)
        if not student:
            return {
                "run_id": None,
                "student_user_id": student_user_id,
                "algorithm_version": "v1.0-graph-weighted",
                "executed_at": datetime.utcnow(),
                "results": [],
                "from_cache": False
            }

        student_skills = {sk.skill_id: (sk.skill.skill_name, PROFICIENCY_WEIGHTS.get(sk.proficiency_level, 0.5)) for sk in student.skills}
        student_domains = {di.domain_id: (di.domain.domain_name, max(1, 4 - di.priority_order)) for di in student.domain_interests}

        # 3. Neo4j Graph Candidate Discovery (shared skills, domains, alumni links)
        skill_cand_graph = graph_client.engine.find_shared_skill_candidates(student_user_id)
        domain_cand_graph = graph_client.engine.find_domain_aligned_candidates(student_user_id)
        alumni_mentors = set(graph_client.engine.find_alumni_from_same_department(student_user_id))

        # Union candidate mentor IDs
        candidate_ids = set()
        skill_evidence: Dict[int, List[Dict[str, Any]]] = {}
        for c in skill_cand_graph:
            mid = c["mentor_id"]
            candidate_ids.add(mid)
            skill_evidence[mid] = c["shared_skills"]

        domain_evidence: Dict[int, List[Dict[str, Any]]] = {}
        for c in domain_cand_graph:
            mid = c["mentor_id"]
            candidate_ids.add(mid)
            domain_evidence[mid] = c["matched_domains"]

        # Also pull all public mentors if candidate pool is small
        all_mentors = self.profile_repo.list_public_mentors()
        for m in all_mentors:
            candidate_ids.add(m.user_id)

        # 4. Authoritative MySQL Hard Gating & Capacity Check (§7.1)
        eligible_candidates: List[Dict[str, Any]] = []

        for mid in candidate_ids:
            mentor = self.profile_repo.get_mentor_profile(mid)
            if not mentor or not mentor.user:
                continue

            # Hard gate: Account must be ACTIVE and accepting requests
            if mentor.user.account_status != "ACTIVE" or not mentor.accepting_requests:
                continue

            # Hard gate: Capacity check
            active_mentees = self.profile_repo.get_mentor_active_mentees_count(mid)
            if settings.GATE_CAPACITY and active_mentees >= mentor.max_active_mentees:
                continue

            # User filters
            if filters.get("min_years_experience") and float(mentor.years_experience or 0) < filters["min_years_experience"]:
                continue
            if filters.get("company_ids") and mentor.current_company_id not in filters["company_ids"]:
                continue
            if filters.get("domain_ids"):
                m_doms = {de.domain_id for de in mentor.domain_expertises}
                if not m_doms.intersection(set(filters["domain_ids"])):
                    continue

            # 5. Multi-Factor Scoring Framework (§7 & §8)
            # Factor 1: Skill similarity (wS = 30%)
            m_skills = {sk.skill_id: (sk.skill.skill_name, PROFICIENCY_WEIGHTS.get(sk.proficiency_level, 0.5)) for sk in mentor.skills}
            matched_skill_names = []
            if student_skills:
                total_student_weight = sum(w for _, w in student_skills.values())
                matched_weight = 0.0
                for sk_id, (sk_name, s_w) in student_skills.items():
                    if sk_id in m_skills:
                        matched_skill_names.append(sk_name)
                        m_w = m_skills[sk_id][1]
                        matched_weight += s_w * m_w
                skill_score = (matched_weight / total_student_weight) * 100.0 if total_student_weight > 0 else 50.0
            else:
                skill_score = 50.0

            # Factor 2: Domain relevance (wD = 20%)
            m_doms = {de.domain_id: (de.domain.domain_name, PROFICIENCY_WEIGHTS.get(de.expertise_level, 0.7), de.is_primary) for de in mentor.domain_expertises}
            matched_domain_names = []
            if student_domains:
                total_domain_prio = sum(p for _, p in student_domains.values())
                matched_domain_score = 0.0
                for d_id, (d_name, p) in student_domains.items():
                    if d_id in m_doms:
                        matched_domain_names.append(d_name)
                        d_strength = m_doms[d_id][1]
                        matched_domain_score += p * d_strength
                domain_score = (matched_domain_score / total_domain_prio) * 100.0 if total_domain_prio > 0 else 50.0
            else:
                domain_score = 50.0

            # Factor 3: Relevant experience (wE = 15%)
            years = float(mentor.years_experience or 0)
            exp_score = min(100.0, (years / settings.TARGET_EXPERIENCE_YEARS) * 100.0)

            # Factor 4: Career relevance (wC = 20%)
            is_alumni = mid in alumni_mentors
            career_score = 50.0
            if matched_domain_names and is_alumni:
                career_score = 100.0
            elif matched_domain_names or is_alumni:
                career_score = 80.0

            # Factor 5: Mentor quality (wQ = 15%, Bayesian smoothed)
            v, mentor_avg = self.review_repo.get_mentor_rating_stats(mid)
            m = settings.BAYESIAN_PRIOR_M
            c = settings.PLATFORM_AVERAGE_RATING
            adj_rating = (v / (v + m)) * mentor_avg + (m / (v + m)) * c
            quality_score = max(0.0, min(100.0, 100.0 * (adj_rating - 1.0) / 4.0))

            # Overall Weighted Score
            overall = (
                settings.WEIGHT_SKILL * skill_score +
                settings.WEIGHT_DOMAIN * domain_score +
                settings.WEIGHT_EXPERIENCE * exp_score +
                settings.WEIGHT_CAREER * career_score +
                settings.WEIGHT_QUALITY * quality_score
            )
            overall = round(overall, 2)

            # 6. Generate Structured Explanation (§10)
            explanation_parts = []
            if matched_skill_names:
                explanation_parts.append(f"Shares skills in {', '.join(matched_skill_names[:3])}")
            if matched_domain_names:
                explanation_parts.append(f"Specializes in {', '.join(matched_domain_names[:2])}")
            if mentor.company:
                explanation_parts.append(f"{years} yrs exp at {mentor.company.company_name}")
            else:
                explanation_parts.append(f"{years} yrs industry experience")
            if is_alumni and mentor.department:
                explanation_parts.append(f"Alumnus from {mentor.department.department_code}")

            explanation_text = ". ".join(explanation_parts) + "."

            candidate_dict = {
                "mentor_user_id": mid,
                "full_name": mentor.user.display_name,
                "job_title": mentor.job_title,
                "company_name": mentor.company.company_name if mentor.company else None,
                "industry": mentor.company.industry if mentor.company else None,
                "years_experience": years,
                "overall_score": overall,
                "skill_score": round(skill_score, 1),
                "domain_score": round(domain_score, 1),
                "experience_score": round(exp_score, 1),
                "career_score": round(career_score, 1),
                "quality_score": round(quality_score, 1),
                "eligibility_status": "ELIGIBLE",
                "explanation_text": explanation_text,
                "matched_skills": matched_skill_names,
                "matched_domains": matched_domain_names,
                "shared_alumni": is_alumni,
                "average_rating": mentor_avg if v > 0 else None,
                "review_count": v,
                "accepting_requests": mentor.accepting_requests
            }
            eligible_candidates.append(candidate_dict)

        # 7. Sort by Overall Score descending
        eligible_candidates.sort(key=lambda x: x["overall_score"], reverse=True)

        # Assign rank positions
        for idx, cand in enumerate(eligible_candidates, 1):
            cand["rank_position"] = idx

        top_candidates = eligible_candidates[:limit]

        # 8. Persist Run History to MySQL
        try:
            run = self.rec_repo.save_run(
                student_user_id=student_user_id,
                algorithm_version="v1.0-graph-weighted",
                input_goal=student.career_goal,
                filter_snapshot=filters
            )
            self.rec_repo.save_candidates(run.run_id, top_candidates)
            self.db.commit()
            run_id = run.run_id
        except Exception:
            self.db.rollback()
            run_id = 0

        # 9. Cache in Redis
        CacheService.set_cached_recommendations(student_user_id, filters, top_candidates, ttl=300)

        return {
            "run_id": run_id,
            "student_user_id": student_user_id,
            "algorithm_version": "v1.0-graph-weighted",
            "executed_at": datetime.utcnow(),
            "results": top_candidates,
            "from_cache": False
        }

