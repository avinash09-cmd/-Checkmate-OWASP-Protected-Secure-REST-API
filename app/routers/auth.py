from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.models import RoleEnum, User
from app.schemas.schemas import TokenResponse, UserLogin, UserOut, UserRegister
from app.services.audit import log_event

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

GENERIC_LOGIN_ERROR = "Invalid email or password"


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        # Same status/message style as a real failure to avoid confirming which emails exist,
        # though 400 here is acceptable since registration intentionally confirms uniqueness.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not register user")

    # First ever user becomes admin for local bootstrapping; everyone else is a normal user.
    is_first_user = db.scalar(select(User).limit(1)) is None
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=RoleEnum.admin if is_first_user else RoleEnum.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event(db, "USER_REGISTERED", user_email=user.email)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))

    # Always run verify_password (even on a dummy hash) to keep timing consistent
    # and avoid leaking which emails exist via response time.
    dummy_hash = "$argon2id$v=19$m=65536,t=3,p=4$00000000000000000000000000000000$0000000000000000000000000000000000000000000000000000000000000000"
    password_ok = verify_password(payload.password, user.password_hash if user else dummy_hash)

    if not user or not password_ok or not user.is_active:
        log_event(db, "LOGIN_FAILED", user_email=payload.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_LOGIN_ERROR)

    token = create_access_token(subject=user.id, role=user.role.value)
    log_event(db, "LOGIN_SUCCESS", user_email=user.email)
    return TokenResponse(access_token=token)
