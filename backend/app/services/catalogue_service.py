"""AlumniConnect Catalogue Service
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.profile_repository import ProfileRepository
from app.services.cache_service import CacheService


class CatalogueService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProfileRepository(db)

    def get_skills(self) -> List[Dict[str, Any]]:
        cached = CacheService.get_skills_catalog()
        if cached is not None:
            return cached

        skills = self.repo.list_skills()
        res = [{"skill_id": s.skill_id, "skill_name": s.skill_name, "category": s.category, "description": s.description} for s in skills]
        CacheService.set_skills_catalog(res)
        return res

    def get_domains(self) -> List[Dict[str, Any]]:
        cached = CacheService.get_domains_catalog()
        if cached is not None:
            return cached

        domains = self.repo.list_domains()
        res = [{"domain_id": d.domain_id, "domain_name": d.domain_name, "description": d.description} for d in domains]
        CacheService.set_domains_catalog(res)
        return res

    def get_departments(self) -> List[Dict[str, Any]]:
        depts = self.repo.list_departments()
        return [{"department_id": d.department_id, "department_code": d.department_code, "department_name": d.department_name, "institution_name": d.institution_name} for d in depts]

    def get_companies(self) -> List[Dict[str, Any]]:
        comps = self.repo.list_companies()
        return [{"company_id": c.company_id, "company_name": c.company_name, "website_url": c.website_url, "industry": c.industry} for c in comps]

