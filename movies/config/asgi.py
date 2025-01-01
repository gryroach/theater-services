import os

from django.core.asgi import get_asgi_application
from opentelemetry.instrumentation.django import DjangoInstrumentor

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
DjangoInstrumentor().instrument()

application = get_asgi_application()
