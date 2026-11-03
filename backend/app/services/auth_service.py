"""AlumniConnect Authentication Service
Handles authentication, password validation, token issuing, and registration.
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.security import verify_password, get_password_hash, create_access_token
from app.repositories.user_repository import UserRepository
from app.repositories.profile_repository import ProfileRepository
from app.models.entities import UserAccount, MentorshipDomain
from app.core.graph_client import graph_client


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.profile_repo = ProfileRepository(db)

    def authenticate_user(self, email: str, password: str) -> Optional[Tuple[UserAccount, str]]:
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if user.account_status != "ACTIVE":
            return None

        role_code = user.role.role_code if user.role else "STUDENT"
        token = create_access_token(subject=user.user_id, role=role_code)
        return user, token

    def register_student(self, email: str, password: str, display_name: str,
                         student_number: str, department_id: int, programme: str,
                         batch_year: int, expected_grad_year: Optional[int] = None,
                         career_goal: Optional[str] = None, bio: Optional[str] = None) -> Tuple[UserAccount, str]:
        existing = self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("An account with this email already exists")

        role = self.user_repo.get_role_by_code("STUDENT")
        if not role:
            raise ValueError("Student role not found in system")

        pwd_hash = get_password_hash(password)
        user = self.user_repo.create_user(email, pwd_hash, display_name, role.role_id)
        
        self.profile_repo.create_student_profile(
            user_id=user.user_id,
            student_number=student_number,
            department_id=department_id,
            programme=programme,
            batch_year=batch_year,
            expected_grad_year=expected_grad_year,
            career_goal=career_goal,
            bio=bio
        )

        # Automatically link target career domain interest in DB if matching domain exists
        if career_goal:
            # 1. Try exact match (case-insensitive)
            domain = self.db.query(MentorshipDomain).filter(
                func.lower(MentorshipDomain.domain_name) == career_goal.lower().strip()
            ).first()

            # 2. Try keyword / substring matching
            if not domain:
                cg_words = set(career_goal.lower().replace('&', ' ').replace('-', ' ').split())
                for d in self.db.query(MentorshipDomain).all():
                    dom_words = set(d.domain_name.lower().replace('&', ' ').replace('-', ' ').split())
                    if cg_words.intersection(dom_words) - {'and', 'in', 'the', 'of'}:
                        domain = d
                        break

            # 3. Fallback to first catalogue domain
            if not domain:
                domain = self.db.query(MentorshipDomain).first()

            if domain:
                self.profile_repo.add_student_domain(
                    student_id=user.user_id,
                    domain_id=domain.domain_id,
                    priority=1,
                    notes=f"Primary career track ({career_goal}) selected at registration"
                )
                graph_client.engine.set_student_domain_interest(user.user_id, domain.domain_id, priority=1)

        # Update in-memory graph
        graph_client.engine.upsert_user(user.user_id, display_name, "ACTIVE")
        graph_client.engine.upsert_student(user.user_id, user.user_id, department_id, programme, expected_grad_year or 0)

        # Commit transaction to ensure user and profile persist
        self.db.commit()

        token = create_access_token(subject=user.user_id, role="STUDENT")
        return user, token

    def register_mentor(self, email: str, password: str, display_name: str,
                        alumni_department_id: int, job_title: str,
                        years_experience: float, current_company_id: Optional[int] = None,
                        max_active_mentees: int = 2,
                        professional_summary: Optional[str] = None) -> Tuple[UserAccount, str]:
        existing = self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("An account with this email already exists")

        role = self.user_repo.get_role_by_code("MENTOR")
        if not role:
            raise ValueError("Mentor role not found in system")

        pwd_hash = get_password_hash(password)
        user = self.user_repo.create_user(email, pwd_hash, display_name, role.role_id)

        self.profile_repo.create_mentor_profile(
            user_id=user.user_id,
            alumni_department_id=alumni_department_id,
            current_company_id=current_company_id,
            job_title=job_title,
            years_experience=years_experience,
            max_active_mentees=max_active_mentees,
            professional_summary=professional_summary
        )

        # Update in-memory graph
        graph_client.engine.upsert_user(user.user_id, display_name, "ACTIVE")
        graph_client.engine.upsert_mentor(user.user_id, user.user_id, alumni_department_id, current_company_id, job_title, years_experience)

        # Commit transaction to ensure user and profile persist
        self.db.commit()

        token = create_access_token(subject=user.user_id, role="MENTOR")
        return user, token

