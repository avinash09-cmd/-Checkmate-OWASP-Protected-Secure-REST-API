import logging

from fastapi import FastAPI, Request, status
from sqlalchemy.exc import OperationalError
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.db.database import Base, engine
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import admin, auth, tasks
from app.routers.auth import limiter

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger("checkmate")

# Creates tables if they don't exist yet. For real schema changes, use Alembic migrations instead.
# Wrapped so that importing this module (e.g. in tests, which use their own
# separate test database and override get_db) never fails just because the
# real MySQL server isn't running.
try:
    Base.metadata.create_all(bind=engine)
except OperationalError:
    logger.warning(
        "Could not connect to the configured database at import time "
        "(this is expected when running tests against a separate test DB)."
    )

app = FastAPI(
    title="Checkmate API",
    description="A secure task-management REST API hardened against OWASP Top 10 risks.",
    version="1.0.0",
    # Hide interactive docs in production to reduce attack surface / info disclosure
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Generic message to the client; never echo raw internals back
    logger.info("Validation error on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request data"},
    )


app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(admin.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


# Serves the Checkmate web frontend (login/register + task dashboard) at /app.
# This is a plain static site that talks to the API above via fetch() calls
# from the same origin, so no extra CORS configuration is needed for it.
app.mount("/app", StaticFiles(directory="app/static", html=True), name="frontend")
