"""AlumniConnect Administrator Portal Endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import require_admin
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.models.entities import UserAccount, Skill, MentorshipDomain, Department, Company

router = APIRouter()


class AccountStatusUpdate(BaseModel):
    new_status: str  # 'ACTIVE', 'SUSPENDED', 'DEACTIVATED'
    reason: Optional[str] = None


class SkillCreate(BaseModel):
    skill_name: str
    category: Optional[str] = None
    description: Optional[str] = None


class DomainCreate(BaseModel):
    domain_name: str
    description: Optional[str] = None


@router.get("/users")
def list_users(
    role: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    current_admin: UserAccount = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin views all platform users with filtering."""
    query = db.query(UserAccount)
    if role:
        query = query.join(UserAccount.role).filter(UserAccount.role.has(role_code=role))
    if status_filter:
        query = query.filter(UserAccount.account_status == status_filter)
    users = query.all()
    return [
        {
            "user_id": u.user_id,
            "display_name": u.display_name,
            "email": u.email,
            "role": u.role.role_code if u.role else "STUDENT",
            "account_status": u.account_status,
            "created_at": u.created_at
        } for u in users
    ]


@router.post("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    status_data: AccountStatusUpdate,
    current_admin: UserAccount = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin updates user account status (ACTIVE, SUSPENDED, DEACTIVATED)."""
    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)

    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_status = user.account_status
    user.account_status = status_data.new_status
    db.flush()

    audit_repo.log_event(
        entity_type="USER_ACCOUNT",
        entity_id=user_id,
        action="STATUS_CHANGED",
        actor_user_id=current_admin.user_id,
        old_values={"account_status": old_status},
        new_values={"account_status": status_data.new_status, "reason": status_data.reason}
    )
    db.commit()
    return {"user_id": user_id, "new_status": user.account_status}


@router.post("/catalogues/skills", status_code=status.HTTP_201_CREATED)
def add_skill_catalogue(
    skill: SkillCreate,
    current_admin: UserAccount = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin adds a new technical skill to the canonical catalogue."""
    s = Skill(skill_name=skill.skill_name.strip(), category=skill.category, description=skill.description)
    db.add(s)
    db.commit()
    return {"skill_id": s.skill_id, "skill_name": s.skill_name}


@router.post("/catalogues/domains", status_code=status.HTTP_201_CREATED)
def add_domain_catalogue(
    domain: DomainCreate,
    current_admin: UserAccount = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin adds a new mentorship domain to the catalogue."""
    d = MentorshipDomain(domain_name=domain.domain_name.strip(), description=domain.description)
    db.add(d)
    db.commit()
    return {"domain_id": d.domain_id, "domain_name": d.domain_name}


@router.get("/audit-logs")
@router.get("/audit")
def view_audit_log(
    limit: int = Query(50, le=200),
    entity_type: Optional[str] = Query(None),
    current_admin: UserAccount = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin views system audit logs for critical transactions."""
    audit_repo = AuditRepository(db)
    logs = audit_repo.list_audit_logs(limit=limit, entity_type=entity_type)
    return [
        {
            "audit_id": a.audit_id,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "action": a.action,
            "actor_user_id": a.actor_user_id,
            "actor_name": a.actor.display_name if a.actor else "System",
            "occurred_at": a.occurred_at,
            "old_values": a.old_values_json,
            "new_values": a.new_values_json
        } for a in logs
    ]

