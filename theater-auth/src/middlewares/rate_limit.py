from typing import Callable

from core.rate_limit import RateLimitException, RateLimitService
from fastapi import Request, status
from fastapi.responses import ORJSONResponse


async def rate_limit_middleware(
    request: Request,
    call_next: Callable,
) -> ORJSONResponse:
    ip_address = request.client.host
    rate_limit_service = RateLimitService(ip_address)
    try:
        await rate_limit_service()
    except RateLimitException:
        return ORJSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit error"},
        )
    return await call_next(request)
