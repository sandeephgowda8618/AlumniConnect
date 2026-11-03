"""AlumniConnect Student Portal Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_student
from app.services.profile_service import ProfileService
from app.schemas.profile import (
    StudentProfileOut, StudentProfileUpdate, StudentSkillAdd, StudentDomainAdd,
    StudentSkillsAndDomainsSync
)
from app.models.entities import UserAccount

router = APIRouter()


@router.get("/profile", response_model=StudentProfileOut)
def get_own_profile(
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Retrieves the authenticated student's profile, skills, and domain interests."""
    profile_service = ProfileService(db)
    profile = profile_service.get_student_profile(current_user.user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    return profile


@router.put("/profile", response_model=StudentProfileOut)
def update_profile(
    update_data: StudentProfileUpdate,
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Updates the authenticated student's academic and biography details."""
    profile_service = ProfileService(db)
    profile = profile_service.update_student_profile(
        user_id=current_user.user_id,
        programme=update_data.programme,
        expected_grad_year=update_data.expected_graduation_year,
        career_goal=update_data.career_goal,
        bio=update_data.bio
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    return profile


@router.post("/skills", status_code=status.HTTP_201_CREATED)
def add_skill(
    skill_data: StudentSkillAdd,
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Associates a technical skill with the student's profile."""
    profile_service = ProfileService(db)
    return profile_service.add_student_skill(
        student_id=current_user.user_id,
        skill_id=skill_data.skill_id,
        proficiency=skill_data.proficiency_level,
        years=skill_data.years_experience or 0.0
    )


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_skill(
    skill_id: int,
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Removes a technical skill from the student's profile."""
    profile_service = ProfileService(db)
    profile_service.remove_student_skill(current_user.user_id, skill_id)
    return None


@router.post("/domains", status_code=status.HTTP_201_CREATED)
def add_domain_interest(
    domain_data: StudentDomainAdd,
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Associates a prioritized mentorship domain interest with the student's profile."""
    profile_service = ProfileService(db)
    return profile_service.add_student_domain(
        student_id=current_user.user_id,
        domain_id=domain_data.domain_id,
        priority=domain_data.priority_order,
        notes=domain_data.interest_notes
    )


@router.delete("/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_domain_interest(
    domain_id: int,
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Removes a mentorship domain interest from the student's profile."""
    profile_service = ProfileService(db)
    profile_service.remove_student_domain(current_user.user_id, domain_id)
    return None


@router.put("/skills-and-domains", response_model=StudentProfileOut)
def sync_skills_and_domains(
    payload: StudentSkillsAndDomainsSync,
    current_user: UserAccount = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Atomically synchronizes student skills and domain interests in SQL, graph, and invalidates recommendation cache."""
    profile_service = ProfileService(db)
    skills_data = [s.model_dump() for s in payload.skills]
    domains_data = [d.model_dump() for d in payload.domains]
    profile = profile_service.sync_student_skills_and_domains(current_user.user_id, skills_data, domains_data)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    return profile

