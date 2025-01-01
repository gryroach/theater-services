import os

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Настройка OpenTelemetry и Jaeger
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "Movies Admin"})
    )
)
jaeger_exporter = JaegerExporter(
    agent_host_name=os.environ.get('ADMIN_JAEGER_HOST', 'jaeger'),
    agent_port=os.environ.get('ADMIN_JAEGER_PORT', 6831),
)
tracer_provider: TracerProvider = trace.get_tracer_provider()
tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
