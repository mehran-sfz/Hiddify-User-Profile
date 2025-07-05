from __future__ import absolute_import, unicode_literals

import os
from urllib.parse import quote

from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiddify.settings')

app = Celery('task_manager')

# Using a string here means the worker doesn’t have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


celery_broker_url_password = quote(os.environ.get('CELERY_BROKER_URL_PASSWORD', '123456'))
celery_result_backend_password = quote(os.environ.get('CELERY_RESULT_BACKEND_PASSWORD', '123456'))

app.conf.broker_connection_retry_on_startup = True
app.conf.broker_url = f'redis://:{celery_broker_url_password}@redis:6379/0'
app.conf.result_backend = f'redis://:{celery_result_backend_password}@redis:6379/0'
app.conf.accept_content = ['json']
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.celery_beat_schedule_file = os.path.join(settings.BASE_DIR, 'celerybeat_schedule')
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1 
app.conf.task_time_limit = 300  # Set a maximum of 5 minutes for tasks
app.conf.task_soft_time_limit = 280  # Set a soft time limit warning at 4 minutes 40 seconds
