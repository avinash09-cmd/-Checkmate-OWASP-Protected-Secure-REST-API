from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.models import Task, User
from app.schemas.schemas import TaskCreate, TaskOut, TaskUpdate
from app.services.audit import log_event

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task_or_404(db: Session, task_id: str, user: User) -> Task:
    """
    Ownership check: a task is only ever fetched if owner_id matches the
    current user. This single helper is what prevents IDOR (Broken Access
    Control) across every task endpoint.
    """
    task = db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    if not task:
        # 404, not 403 — don't reveal whether the task exists for someone else
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.scalars(select(Task).where(Task.owner_id == current_user.id)).all()


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    task = Task(title=payload.title, description=payload.description, owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_owned_task_or_404(db, task_id, current_user)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_owned_task_or_404(db, task_id, current_user)
    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.is_done is not None:
        task.is_done = payload.is_done
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = _get_owned_task_or_404(db, task_id, current_user)
    db.delete(task)
    db.commit()
    log_event(db, "TASK_DELETED", detail=task_id, user_email=current_user.email)
    return None
