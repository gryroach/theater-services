import os

from django.core.wsgi import get_wsgi_application
from opentelemetry.instrumentation.django import DjangoInstrumentor

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
DjangoInstrumentor().instrument()

application = get_wsgi_application()
