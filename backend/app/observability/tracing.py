from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from app.config import settings
from app.utils.logger import logger


def setup_tracing():


    if not settings.otel_enabled:
        logger.info("OpenTelemetry devre dışı")
        return trace.get_tracer(__name__)

    resource = Resource(attributes={"service.name": settings.app_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    logger.info(f"OpenTelemetry etkinleştirildi, exporter: {settings.otel_exporter_endpoint}")
    return trace.get_tracer(__name__)


tracer = setup_tracing()
