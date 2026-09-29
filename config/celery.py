"""
Celery application entrypoint.

Configures Celery to use Redis as both the message broker and the result
backend, and auto-discovers tasks from every installed Django app (so
``payments/tasks.py`` is picked up automatically).
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("eve_healthcare")

# Read CELERY_* settings from Django settings.py (namespace="CELERY" means
# every celery setting there must be prefixed with CELERY_).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in each app listed in INSTALLED_APPS.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
