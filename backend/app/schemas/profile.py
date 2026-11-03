"""AlumniConnect Pydantic Schemas for Student & Mentor Profiles, Skills, and Domains
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class SkillOut(BaseModel):
    skill_id: int
    skill_name: str
    category: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class MentorshipDomainOut(BaseModel):
    domain_id: int
    domain_name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class DepartmentOut(BaseModel):
    department_id: int
    department_code: str
    department_name: str
    institution_name: str

    class Config:
        from_attributes = True


class CompanyOut(BaseModel):
    company_id: int
    company_name: str
    website_url: Optional[str] = None
    industry: Optional[str] = None

    class Config:
        from_attributes = True


class StudentSkillItem(BaseModel):
    skill_id: int
    skill_name: str
    proficiency_level: str
    years_experience: Optional[float] = None

    class Config:
        from_attributes = True


class StudentDomainInterestItem(BaseModel):
    domain_id: int
    domain_name: str
    priority_order: int
    interest_notes: Optional[str] = None

    class Config:
        from_attributes = True


class StudentProfileOut(BaseModel):
    user_id: int
    display_name: str
    email: str
    student_number: str
    department_id: int
    department_name: Optional[str] = None
    programme: str
    batch_year: int
    expected_graduation_year: Optional[int] = None
    career_goal: Optional[str] = None
    bio: Optional[str] = None
    skills: List[StudentSkillItem] = []
    domain_interests: List[StudentDomainInterestItem] = []

    class Config:
        from_attributes = True


class StudentProfileUpdate(BaseModel):
    programme: Optional[str] = None
    expected_graduation_year: Optional[int] = None
    career_goal: Optional[str] = None
    bio: Optional[str] = None


class StudentSkillAdd(BaseModel):
    skill_id: int
    proficiency_level: str
    years_experience: Optional[float] = 0.0


class StudentDomainAdd(BaseModel):
    domain_id: int
    priority_order: int
    interest_notes: Optional[str] = None


class StudentSkillInput(BaseModel):
    skill_id: int
    proficiency_level: str = "INTERMEDIATE"
    years_experience: Optional[float] = 0.0


class StudentDomainInput(BaseModel):
    domain_id: int
    priority_order: int = 1
    interest_notes: Optional[str] = None


class StudentSkillsAndDomainsSync(BaseModel):
    skills: List[StudentSkillInput] = []
    domains: List[StudentDomainInput] = []


class MentorSkillItem(BaseModel):
    skill_id: int
    skill_name: str
    proficiency_level: str
    years_experience: Optional[float] = None

    class Config:
        from_attributes = True


class MentorDomainExpertiseItem(BaseModel):
    domain_id: int
    domain_name: str
    expertise_level: str
    years_experience: Optional[float] = None
    is_primary: bool = False

    class Config:
        from_attributes = True


class MentorProfileOut(BaseModel):
    user_id: int
    display_name: str
    email: Optional[str] = None  # Filtered out in public views
    job_title: str
    years_experience: float
    max_active_mentees: int
    accepting_requests: bool
    professional_summary: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    department_id: int
    department_name: Optional[str] = None
    skills: List[MentorSkillItem] = []
    domain_expertises: List[MentorDomainExpertiseItem] = []
    active_mentees_count: Optional[int] = 0
    average_rating: Optional[float] = None
    review_count: Optional[int] = 0

    class Config:
        from_attributes = True


class MentorProfileUpdate(BaseModel):
    job_title: Optional[str] = None
    current_company_id: Optional[int] = None
    years_experience: Optional[float] = None
    max_active_mentees: Optional[int] = None
    accepting_requests: Optional[bool] = None
    professional_summary: Optional[str] = None


class MentorSkillAdd(BaseModel):
    skill_id: int
    proficiency_level: str
    years_experience: Optional[float] = 0.0


class MentorDomainAdd(BaseModel):
    domain_id: int
    expertise_level: str
    years_experience: Optional[float] = 0.0
    is_primary: bool = False

