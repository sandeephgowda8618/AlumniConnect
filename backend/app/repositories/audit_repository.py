"""AlumniConnect Audit Log Repository
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.models.entities import AuditLog, UserAccount


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_event(self, entity_type: str, entity_id: int, action: str,
                  actor_user_id: Optional[int] = None,
                  old_values: Optional[Dict[str, Any]] = None,
                  new_values: Optional[Dict[str, Any]] = None,
                  correlation_id: Optional[str] = None) -> AuditLog:
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_user_id=actor_user_id,
            old_values_json=old_values,
            new_values_json=new_values,
            occurred_at=datetime.utcnow(),
            correlation_id=correlation_id
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def list_audit_logs(self, limit: int = 100, entity_type: Optional[str] = None) -> List[AuditLog]:
        query = self.db.query(AuditLog).options(joinedload(AuditLog.actor))
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        return query.order_by(AuditLog.occurred_at.desc()).limit(limit).all()

