import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autisense.settings')

app = Celery('autisense')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Make task discovery explicit to avoid "unregistered task" after new tasks are added.
app.conf.update(
    CELERY_IMPORTS=('apps.notifications.tasks',),
)

app.autodiscover_tasks()
