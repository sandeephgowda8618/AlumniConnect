"""AlumniConnect Profile & Catalogue Repository
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.entities import (
    StudentProfile, MentorProfile, UserAccount, Department, Company,
    Skill, MentorshipDomain, StudentSkill, MentorSkill,
    StudentDomainInterest, MentorDomainExpertise, MentorAllocation, MentorReview
)


class ProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Student Profile ---

    def get_student_profile(self, user_id: int) -> Optional[StudentProfile]:
        return (
            self.db.query(StudentProfile)
            .options(
                joinedload(StudentProfile.user),
                joinedload(StudentProfile.department),
                joinedload(StudentProfile.skills).joinedload(StudentSkill.skill),
                joinedload(StudentProfile.domain_interests).joinedload(StudentDomainInterest.domain)
            )
            .filter(StudentProfile.user_id == user_id)
            .first()
        )

    def create_student_profile(self, user_id: int, student_number: str, department_id: int,
                              programme: str, batch_year: int, expected_grad_year: Optional[int] = None,
                              career_goal: Optional[str] = None, bio: Optional[str] = None) -> StudentProfile:
        profile = StudentProfile(
            user_id=user_id,
            student_number=student_number,
            department_id=department_id,
            programme=programme,
            batch_year=batch_year,
            expected_graduation_year=expected_grad_year,
            career_goal=career_goal,
            bio=bio
        )
        self.db.add(profile)
        self.db.flush()
        return profile

    def update_student_profile(self, user_id: int, programme: Optional[str] = None,
                               expected_grad_year: Optional[int] = None, career_goal: Optional[str] = None,
                               bio: Optional[str] = None) -> Optional[StudentProfile]:
        profile = self.get_student_profile(user_id)
        if not profile:
            return None
        if programme is not None:
            profile.programme = programme
        if expected_grad_year is not None:
            profile.expected_graduation_year = expected_grad_year
        if career_goal is not None:
            profile.career_goal = career_goal
        if bio is not None:
            profile.bio = bio
        self.db.flush()
        return profile

    def add_student_skill(self, student_id: int, skill_id: int, proficiency: str, years: float = 0.0) -> StudentSkill:
        existing = (
            self.db.query(StudentSkill)
            .filter(StudentSkill.student_user_id == student_id, StudentSkill.skill_id == skill_id)
            .first()
        )
        if existing:
            existing.proficiency_level = proficiency
            existing.years_experience = years
            self.db.flush()
            return existing
        item = StudentSkill(student_user_id=student_id, skill_id=skill_id, proficiency_level=proficiency, years_experience=years)
        self.db.add(item)
        self.db.flush()
        return item

    def remove_student_skill(self, student_id: int, skill_id: int) -> bool:
        deleted = (
            self.db.query(StudentSkill)
            .filter(StudentSkill.student_user_id == student_id, StudentSkill.skill_id == skill_id)
            .delete()
        )
        self.db.flush()
        return deleted > 0

    def add_student_domain(self, student_id: int, domain_id: int, priority: int, notes: Optional[str] = None) -> StudentDomainInterest:
        existing = (
            self.db.query(StudentDomainInterest)
            .filter(StudentDomainInterest.student_user_id == student_id, StudentDomainInterest.domain_id == domain_id)
            .first()
        )
        if existing:
            existing.priority_order = priority
            existing.interest_notes = notes
            self.db.flush()
            return existing
        item = StudentDomainInterest(student_user_id=student_id, domain_id=domain_id, priority_order=priority, interest_notes=notes)
        self.db.add(item)
        self.db.flush()
        return item

    def remove_student_domain(self, student_id: int, domain_id: int) -> bool:
        deleted = (
            self.db.query(StudentDomainInterest)
            .filter(StudentDomainInterest.student_user_id == student_id, StudentDomainInterest.domain_id == domain_id)
            .delete()
        )
        self.db.flush()
        return deleted > 0

    def sync_student_skills(self, student_id: int, skills: List[Dict[str, Any]]) -> List[StudentSkill]:
        self.db.query(StudentSkill).filter(StudentSkill.student_user_id == student_id).delete()
        items = []
        for sk in skills:
            item = StudentSkill(
                student_user_id=student_id,
                skill_id=sk["skill_id"],
                proficiency_level=sk.get("proficiency_level", "INTERMEDIATE"),
                years_experience=float(sk.get("years_experience", 0.0) or 0.0)
            )
            self.db.add(item)
            items.append(item)
        self.db.flush()
        return items

    def sync_student_domains(self, student_id: int, domains: List[Dict[str, Any]]) -> List[StudentDomainInterest]:
        self.db.query(StudentDomainInterest).filter(StudentDomainInterest.student_user_id == student_id).delete()
        items = []
        for idx, dom in enumerate(domains):
            item = StudentDomainInterest(
                student_user_id=student_id,
                domain_id=dom["domain_id"],
                priority_order=dom.get("priority_order", idx + 1),
                interest_notes=dom.get("interest_notes")
            )
            self.db.add(item)
            items.append(item)
        self.db.flush()
        return items

    # --- Mentor Profile ---

    def get_mentor_profile(self, user_id: int) -> Optional[MentorProfile]:
        return (
            self.db.query(MentorProfile)
            .options(
                joinedload(MentorProfile.user),
                joinedload(MentorProfile.department),
                joinedload(MentorProfile.company),
                joinedload(MentorProfile.skills).joinedload(MentorSkill.skill),
                joinedload(MentorProfile.domain_expertises).joinedload(MentorDomainExpertise.domain)
            )
            .filter(MentorProfile.user_id == user_id)
            .first()
        )

    def create_mentor_profile(self, user_id: int, alumni_department_id: int,
                              job_title: str, years_experience: float,
                              current_company_id: Optional[int] = None,
                              alumni_identifier: Optional[str] = None,
                              max_active_mentees: int = 2,
                              professional_summary: Optional[str] = None) -> MentorProfile:
        profile = MentorProfile(
            user_id=user_id,
            alumni_identifier=alumni_identifier,
            alumni_department_id=alumni_department_id,
            current_company_id=current_company_id,
            job_title=job_title,
            years_experience=years_experience,
            max_active_mentees=max_active_mentees,
            accepting_requests=True,
            professional_summary=professional_summary
        )
        self.db.add(profile)
        self.db.flush()
        return profile

    def update_mentor_profile(self, user_id: int, job_title: Optional[str] = None,
                              company_id: Optional[int] = None, years_exp: Optional[float] = None,
                              max_mentees: Optional[int] = None, accepting_req: Optional[bool] = None,
                              summary: Optional[str] = None) -> Optional[MentorProfile]:
        profile = self.get_mentor_profile(user_id)
        if not profile:
            return None
        if job_title is not None:
            profile.job_title = job_title
        if company_id is not None:
            profile.current_company_id = company_id
        if years_exp is not None:
            profile.years_experience = years_exp
        if max_mentees is not None:
            profile.max_active_mentees = max_mentees
        if accepting_req is not None:
            profile.accepting_requests = accepting_req
        if summary is not None:
            profile.professional_summary = summary
        self.db.flush()
        return profile

    def add_mentor_skill(self, mentor_id: int, skill_id: int, proficiency: str, years: float = 0.0) -> MentorSkill:
        existing = (
            self.db.query(MentorSkill)
            .filter(MentorSkill.mentor_user_id == mentor_id, MentorSkill.skill_id == skill_id)
            .first()
        )
        if existing:
            existing.proficiency_level = proficiency
            existing.years_experience = years
            self.db.flush()
            return existing
        item = MentorSkill(mentor_user_id=mentor_id, skill_id=skill_id, proficiency_level=proficiency, years_experience=years)
        self.db.add(item)
        self.db.flush()
        return item

    def remove_mentor_skill(self, mentor_id: int, skill_id: int) -> bool:
        deleted = (
            self.db.query(MentorSkill)
            .filter(MentorSkill.mentor_user_id == mentor_id, MentorSkill.skill_id == skill_id)
            .delete()
        )
        self.db.flush()
        return deleted > 0

    def add_mentor_domain(self, mentor_id: int, domain_id: int, level: str, years: float = 0.0, is_primary: bool = False) -> MentorDomainExpertise:
        existing = (
            self.db.query(MentorDomainExpertise)
            .filter(MentorDomainExpertise.mentor_user_id == mentor_id, MentorDomainExpertise.domain_id == domain_id)
            .first()
        )
        if existing:
            existing.expertise_level = level
            existing.years_experience = years
            existing.is_primary = is_primary
            self.db.flush()
            return existing
        item = MentorDomainExpertise(mentor_user_id=mentor_id, domain_id=domain_id, expertise_level=level, years_experience=years, is_primary=is_primary)
        self.db.add(item)
        self.db.flush()
        return item

    def remove_mentor_domain(self, mentor_id: int, domain_id: int) -> bool:
        deleted = (
            self.db.query(MentorDomainExpertise)
            .filter(MentorDomainExpertise.mentor_user_id == mentor_id, MentorDomainExpertise.domain_id == domain_id)
            .delete()
        )
        self.db.flush()
        return deleted > 0

    def get_mentor_active_mentees_count(self, mentor_id: int) -> int:
        return (
            self.db.query(MentorAllocation)
            .join(MentorAllocation.request)
            .filter(
                MentorAllocation.request.has(mentor_user_id=mentor_id),
                MentorAllocation.allocation_status == "ACTIVE"
            )
            .count()
        )

    def list_public_mentors(self, domain_id: Optional[int] = None, skill_id: Optional[int] = None,
                            company_id: Optional[int] = None, min_years: Optional[float] = None) -> List[MentorProfile]:
        """Implements Q02 / V01 public mentor directory with filters."""
        query = (
            self.db.query(MentorProfile)
            .join(MentorProfile.user)
            .options(
                joinedload(MentorProfile.user),
                joinedload(MentorProfile.department),
                joinedload(MentorProfile.company),
                joinedload(MentorProfile.skills).joinedload(MentorSkill.skill),
                joinedload(MentorProfile.domain_expertises).joinedload(MentorDomainExpertise.domain)
            )
            .filter(
                UserAccount.account_status == "ACTIVE",
                MentorProfile.accepting_requests == True
            )
        )
        if min_years is not None:
            query = query.filter(MentorProfile.years_experience >= min_years)
        if company_id is not None:
            query = query.filter(MentorProfile.current_company_id == company_id)
        if domain_id is not None:
            query = query.filter(
                MentorProfile.domain_expertises.any(MentorDomainExpertise.domain_id == domain_id)
            )
        if skill_id is not None:
            query = query.filter(
                MentorProfile.skills.any(MentorSkill.skill_id == skill_id)
            )
        return query.all()

    # --- Catalogues ---

    def list_skills(self) -> List[Skill]:
        return self.db.query(Skill).order_by(Skill.skill_name).all()

    def list_domains(self) -> List[MentorshipDomain]:
        return self.db.query(MentorshipDomain).order_by(MentorshipDomain.domain_name).all()

    def list_departments(self) -> List[Department]:
        return self.db.query(Department).order_by(Department.department_name).all()

    def list_companies(self) -> List[Company]:
        return self.db.query(Company).order_by(Company.company_name).all()

