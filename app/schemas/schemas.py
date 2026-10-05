import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


# ---------- Auth ----------
class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")  # reject unexpected fields

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must include an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must include a lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must include a digit")
        return v


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    # password_hash is intentionally NEVER included here


# ---------- Tasks ----------
class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    description: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 200:
            raise ValueError("Title must be 1-200 characters")
        return v


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = None
    description: str | None = None
    is_done: bool | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str | None
    is_done: bool
    created_at: datetime


# ---------- Admin ----------
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    event_type: str
    detail: str | None
    user_email: str | None
    created_at: datetime
