"""AlumniConnect Authentication Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, TokenResponse, RegisterStudentRequest,
    RegisterMentorRequest, UserOut
)
from app.models.entities import UserAccount

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates user credentials and issues a signed JWT access token."""
    auth_service = AuthService(db)
    result = auth_service.authenticate_user(request.email, request.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user, token = result
    role_code = user.role.role_code if user.role else "STUDENT"
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "role": role_code,
        "display_name": user.display_name,
        "email": user.email
    }


@router.post("/register/student", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_student(request: RegisterStudentRequest, db: Session = Depends(get_db)):
    """Registers a new student mentee account with associated student profile."""
    auth_service = AuthService(db)
    try:
        user, token = auth_service.register_student(
            email=request.email,
            password=request.password,
            display_name=request.display_name,
            student_number=request.student_number,
            department_id=request.department_id,
            programme=request.programme,
            batch_year=request.batch_year,
            expected_grad_year=request.expected_graduation_year,
            career_goal=request.career_goal,
            bio=request.bio
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.user_id,
            "role": "STUDENT",
            "display_name": user.display_name,
            "email": user.email
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/register/mentor", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_mentor(request: RegisterMentorRequest, db: Session = Depends(get_db)):
    """Registers a new alumni mentor account with associated mentor profile."""
    auth_service = AuthService(db)
    try:
        user, token = auth_service.register_mentor(
            email=request.email,
            password=request.password,
            display_name=request.display_name,
            alumni_department_id=request.alumni_department_id,
            job_title=request.job_title,
            years_experience=request.years_experience,
            current_company_id=request.current_company_id,
            max_active_mentees=request.max_active_mentees,
            professional_summary=request.professional_summary
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.user_id,
            "role": "MENTOR",
            "display_name": user.display_name,
            "email": user.email
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserOut)
def get_current_actor(current_user: UserAccount = Depends(get_current_user)):
    """Returns the authenticated user's account identity and assigned role."""
    return {
        "user_id": current_user.user_id,
        "role_id": current_user.role_id,
        "role_code": current_user.role.role_code if current_user.role else "STUDENT",
        "email": current_user.email,
        "display_name": current_user.display_name,
        "account_status": current_user.account_status
    }

