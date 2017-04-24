from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

from bot.schedule import periodicUpdateRate

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rps.settings')

app = Celery('rps')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, periodicUpdateRate.s(), name='add every 10')

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
