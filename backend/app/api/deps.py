"""AlumniConnect FastAPI Security Dependencies
Implements RBAC + Resource Ownership + Lifecycle State checks.
Never trusts user IDs, roles, or permissions supplied in the request body.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository
from app.models.entities import UserAccount

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> UserAccount:
    """Authenticates the bearer token, checks signature, and loads active UserAccount."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token subject missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(int(user_id_str))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.account_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account status is {user.account_status}. Access restricted."
        )

    return user


def require_role(required_role_code: str):
    """Enforces that the authenticated actor has the specific primary operating role."""
    def role_checker(current_user: UserAccount = Depends(get_current_user)) -> UserAccount:
        if not current_user.role or current_user.role.role_code != required_role_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role_code} role authority"
            )
        return current_user
    return role_checker


require_student = require_role("STUDENT")
require_mentor = require_role("MENTOR")
require_admin = require_role("ADMINISTRATOR")

