from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.database import get_db
from app.models.models import AuditLog, User
from app.schemas.schemas import AuditLogOut, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User)).all()


@router.get("/audit-logs", response_model=list[AuditLogOut], dependencies=[Depends(require_admin)])
def list_audit_logs(db: Session = Depends(get_db)):
    return db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)).all()
