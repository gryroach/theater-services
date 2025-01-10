from core.config import settings
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_tracer() -> None:
    if settings.test_mode:
        return None
    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({SERVICE_NAME: "Auth API"}))
    )
    tracer_provider: TracerProvider = trace.get_tracer_provider()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            JaegerExporter(
                agent_host_name=settings.jaeger_host,
                agent_port=settings.jaeger_port,
            )
        )
    )
