from __future__ import absolute_import, unicode_literals
from datetime import datetime
import os
import subprocess
from celery.schedules import crontab
from celery import shared_task
import django
from .script import main
from .script2 import main2
from .script3 import main3
from django.db import connection
from django.conf import settings


@shared_task
def ejecutar_script():
    print("La tarea de prueba se ha ejecutado correctamente.")
    main()

@shared_task
def ejecutar_script2():
    main2()

@shared_task
def ejecutar_script3():
    main3()