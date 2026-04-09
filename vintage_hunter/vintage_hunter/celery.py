import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vintage_hunter.settings')

app = Celery('vintage_hunter')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()