"""
Audit logging. Never log passwords, tokens, or other secrets here.
"""
from sqlalchemy.orm import Session

from app.models.models import AuditLog


def log_event(db: Session, event_type: str, detail: str = "", user_email: str | None = None) -> None:
    entry = AuditLog(event_type=event_type, detail=detail[:500], user_email=user_email)
    db.add(entry)
    db.commit()
