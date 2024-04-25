from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'centrodeservicios.settings')

app = Celery('centrodeservicios')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.task_routes = {
    'login.tasks.*': {'database': 'default'},
    'login.tasks.*': {'database': 'intranetcercafe2'},
    'login.tasks.*': {'database': 'frigotun'},
}


app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

