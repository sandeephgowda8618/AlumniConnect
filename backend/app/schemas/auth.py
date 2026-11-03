"""AlumniConnect Pydantic Schemas for Authentication and Identity
"""

from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    display_name: str
    email: str


class UserOut(BaseModel):
    user_id: int
    role_id: int
    role_code: str
    email: str
    display_name: str
    account_status: str

    class Config:
        from_attributes = True


class RegisterStudentRequest(BaseModel):
    email: str
    password: str
    display_name: str
    student_number: str
    department_id: int
    programme: str
    batch_year: int
    expected_graduation_year: Optional[int] = None
    career_goal: Optional[str] = None
    bio: Optional[str] = None


class RegisterMentorRequest(BaseModel):
    email: str
    password: str
    display_name: str
    alumni_department_id: int
    current_company_id: Optional[int] = None
    job_title: str
    years_experience: float
    max_active_mentees: int = 2
    professional_summary: Optional[str] = None
