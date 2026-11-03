"""AlumniConnect Public Catalogues Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.catalogue_service import CatalogueService
from app.schemas.profile import SkillOut, MentorshipDomainOut, DepartmentOut, CompanyOut

router = APIRouter()


@router.get("/skills", response_model=List[SkillOut])
def get_skills_catalogue(db: Session = Depends(get_db)):
    """Retrieves standard skills catalogue with Redis caching."""
    service = CatalogueService(db)
    return service.get_skills()


@router.get("/domains", response_model=List[MentorshipDomainOut])
def get_domains_catalogue(db: Session = Depends(get_db)):
    """Retrieves standard mentorship domains catalogue with Redis caching."""
    service = CatalogueService(db)
    return service.get_domains()


@router.get("/departments", response_model=List[DepartmentOut])
def get_departments_catalogue(db: Session = Depends(get_db)):
    """Retrieves academic departments."""
    service = CatalogueService(db)
    return service.get_departments()


@router.get("/companies", response_model=List[CompanyOut])
def get_companies_catalogue(db: Session = Depends(get_db)):
    """Retrieves companies list."""
    service = CatalogueService(db)
    return service.get_companies()

