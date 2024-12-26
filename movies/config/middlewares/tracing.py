from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from opentelemetry import trace
from rest_framework import status


class RequestIDSpanMiddleware(MiddlewareMixin):
    def process_request(self, request: WSGIRequest) -> JsonResponse | None:
        tracer = trace.get_tracer(__name__)

        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            return JsonResponse(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": "X-Request-Id is required"},
            )

        with tracer.start_as_current_span(request.get_full_path()) as span:
            span.set_attribute("http.request_id", request_id)
            request.request_id = request_id

    def process_response(
            self, request: WSGIRequest, response: HttpResponse
    ) -> HttpResponse:
        return response
