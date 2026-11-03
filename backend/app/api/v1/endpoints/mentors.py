"""AlumniConnect Mentor Portal & Directory Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_mentor, get_current_user
from app.services.profile_service import ProfileService
from app.schemas.profile import (
    MentorProfileOut, MentorProfileUpdate, MentorSkillAdd, MentorDomainAdd
)
from app.models.entities import UserAccount

router = APIRouter()


@router.get("/profile", response_model=MentorProfileOut)
def get_own_profile(
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Retrieves the authenticated mentor's full professional profile."""
    profile_service = ProfileService(db)
    profile = profile_service.get_mentor_profile(current_user.user_id, is_owner=True)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor profile not found")
    return profile


@router.put("/profile", response_model=MentorProfileOut)
def update_profile(
    update_data: MentorProfileUpdate,
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Updates the authenticated mentor's professional details and availability settings."""
    profile_service = ProfileService(db)
    profile = profile_service.update_mentor_profile(
        user_id=current_user.user_id,
        job_title=update_data.job_title,
        company_id=update_data.current_company_id,
        years_exp=update_data.years_experience,
        max_mentees=update_data.max_active_mentees,
        accepting_req=update_data.accepting_requests,
        summary=update_data.professional_summary
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor profile not found")
    return profile


@router.post("/skills", status_code=status.HTTP_201_CREATED)
def add_skill(
    skill_data: MentorSkillAdd,
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Associates a technical skill with the mentor's profile."""
    profile_service = ProfileService(db)
    return profile_service.add_mentor_skill(
        mentor_id=current_user.user_id,
        skill_id=skill_data.skill_id,
        proficiency=skill_data.proficiency_level,
        years=skill_data.years_experience or 0.0
    )


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_skill(
    skill_id: int,
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Removes a technical skill from the mentor's profile."""
    profile_service = ProfileService(db)
    profile_service.remove_mentor_skill(current_user.user_id, skill_id)
    return None


@router.post("/domains", status_code=status.HTTP_201_CREATED)
def add_domain_expertise(
    domain_data: MentorDomainAdd,
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Associates a domain specialization with the mentor's profile."""
    profile_service = ProfileService(db)
    return profile_service.add_mentor_domain(
        mentor_id=current_user.user_id,
        domain_id=domain_data.domain_id,
        level=domain_data.expertise_level,
        years=domain_data.years_experience or 0.0,
        is_primary=domain_data.is_primary
    )


@router.delete("/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_domain_expertise(
    domain_id: int,
    current_user: UserAccount = Depends(require_mentor),
    db: Session = Depends(get_db)
):
    """Removes a domain specialization from the mentor's profile."""
    profile_service = ProfileService(db)
    profile_service.remove_mentor_domain(current_user.user_id, domain_id)
    return None


@router.get("/directory", response_model=List[MentorProfileOut])
def list_public_mentor_directory(
    domain_id: Optional[int] = Query(None, description="Filter by mentorship domain ID"),
    skill_id: Optional[int] = Query(None, description="Filter by technical skill ID"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    min_years: Optional[float] = Query(None, description="Minimum years of professional experience"),
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Public mentor directory (Q02 / V01). Excludes private emails, passwords, and sensitive identifiers."""
    profile_service = ProfileService(db)
    return profile_service.list_public_mentors(
        domain_id=domain_id,
        skill_id=skill_id,
        company_id=company_id,
        min_years=min_years
    )


@router.get("/{mentor_id}", response_model=MentorProfileOut)
def get_public_mentor_card(
    mentor_id: int,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves a public mentor profile card with review stats and domain expertise."""
    profile_service = ProfileService(db)
    profile = profile_service.get_mentor_profile(mentor_id, is_owner=False)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor profile not found")
    return profile

