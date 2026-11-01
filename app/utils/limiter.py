from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded


def get_client_ip(request: Request) -> str:
    """Extract client IP address supporting reverse proxies and mobile clients."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in list is original client
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"


# Default rate limiter
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["120/minute"]
)


def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return friendly, structured JSON response when rate limit is exceeded (HTTP 429)."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Terlalu banyak permintaan (Rate limit exceeded: {exc.detail}). Silakan tunggu beberapa saat.",
            "error_code": "RATE_LIMIT_EXCEEDED"
        },
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))}
    )
