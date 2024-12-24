from typing import Callable

from fastapi import Request, status
from fastapi.responses import ORJSONResponse
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


async def request_id_span(
    request: Request,
    call_next: Callable,
) -> ORJSONResponse:
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "X-Request-Id is required"},
        )
    with tracer.start_as_current_span(str(request.url.path)) as span:
        span.set_attribute("http.request_id", request_id)
        response = await call_next(request)
        return response
