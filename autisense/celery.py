import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autisense.settings')

app = Celery('autisense')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()