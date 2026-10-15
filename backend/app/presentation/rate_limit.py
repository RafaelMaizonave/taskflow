from fastapi import HTTPException, Request

from app.infrastructure.rate_limit import SlidingWindowRateLimiter


def enforce_auth_rate_limit(request: Request) -> None:
    limiter: SlidingWindowRateLimiter = request.app.state.auth_rate_limiter
    client = request.client.host if request.client else "unknown"
    key = f"{client}:{request.url.path}"
    if limiter.allow(key):
        return
    raise HTTPException(
        status_code=429,
        detail="Muitas tentativas. Tente novamente em instantes.",
        headers={"Retry-After": str(limiter.retry_after_seconds(key))},
    )
