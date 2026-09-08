import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aforro_backend.settings")

app = Celery("aforro_backend")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY"
)

app.autodiscover_tasks()