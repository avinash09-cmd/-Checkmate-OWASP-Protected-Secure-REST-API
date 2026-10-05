from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Routes that need to load their own external CSS/JS (FastAPI's built-in docs UI)
DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds common OWASP-recommended security response headers."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"

        if request.url.path.startswith("/app"):
            # The Checkmate frontend: static HTML/CSS/JS served from this
            # same origin, plus Google Fonts for the stylesheet's @import.
            # No inline scripts are used, so script-src stays strict.
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "style-src 'self' https://fonts.googleapis.com; "
                "font-src https://fonts.gstatic.com; "
                "script-src 'self'; "
                "connect-src 'self'; "
                "img-src 'self' data:"
            )
        elif request.url.path in DOCS_PATHS:
            # Relaxed CSP just for the interactive docs page. Swagger UI's
            # page ships an inline <script> to boot itself and loads its
            # JS/CSS/source-map from jsdelivr, so all of those need to be
            # explicitly allowed here. Real app routes below still get the
            # strict policy.
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "connect-src 'self' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com"
            )
        else:
            response.headers["Content-Security-Policy"] = "default-src 'none'"

        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        # Avoid leaking server/framework details
        if "Server" in response.headers:
            del response.headers["Server"]
        return response
