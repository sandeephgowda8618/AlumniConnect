"""AlumniConnect User & Identity Repository
Handles account retrieval, registration, and status validation.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.entities import UserAccount, Role, StudentProfile, MentorProfile


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[UserAccount]:
        return self.db.query(UserAccount).filter(UserAccount.user_id == user_id).first()

    def get_by_email(self, email: str) -> Optional[UserAccount]:
        return self.db.query(UserAccount).filter(UserAccount.email == email.lower().strip()).first()

    def get_role_by_code(self, role_code: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.role_code == role_code).first()

    def create_user(self, email: str, password_hash: str, display_name: str, role_id: int) -> UserAccount:
        user = UserAccount(
            email=email.lower().strip(),
            password_hash=password_hash,
            display_name=display_name.strip(),
            role_id=role_id,
            account_status="ACTIVE"
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_account_status(self, user_id: int, new_status: str) -> Optional[UserAccount]:
        user = self.get_by_id(user_id)
        if user:
            user.account_status = new_status
            self.db.flush()
        return user

