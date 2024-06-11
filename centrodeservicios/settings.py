"""
Django settings for centrodeservicios project.

Generated by 'django-admin startproject' using Django 5.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from datetime import timedelta
from pathlib import Path
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', default='1234')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = []

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'login',
    'adminlte3',
    'adminlte3_theme',
    'wkhtmltopdf',
    'django_celery_beat',
    'django_celery_results',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',

]
CORS_ALLOW_ALL_ORIGINS = True
ROOT_URLCONF = 'centrodeservicios.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [''],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
  
CSRF_COOKIE_HTTPONLY = True 


#---------cierre de sesion a los 5 minutos --------
AUTO_LOGOUT_DELAY = 5 
SESSION_COOKIE_AGE = 600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

WSGI_APPLICATION = 'centrodeservicios.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     'default': dj_database_url.config(
#         # Replace this value with your local database's connection string.
#         default='postgresql://postgres:postgres@localhost/postgres',
#         conn_max_age=600
#     )
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'centrodeservicios',
        'USER': 'root',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '3306',
        
    },
    'int': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'intranetcercafe2',
    'USER': 'DEV_USER',
    'PASSWORD': 'D3V-US3R1234+*+*',
    'HOST': '192.241.142.141',
    'PORT': '3306',
    'OPTIONS': {
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'charset': 'utf8mb4'
    }
}

   
}

# Lista de nombres de esquemas adicionales
esquemas = [
    'b_gc', 'b_gt', 'b_ca', 'b_gab', 'b_ci',
    'b_m', 'b_c', 'b_gd', 'b_gaf', 'b_gh',
    'b_ti', 'b_sac', 'b_sig', 'b_gg', 'dhc','intranetcercafe2','oinc','frigotun'

]
# qqqqqqqqqqqqq
# ppppppppppppppppp
# eeeeeeeeeeaaaaaaaaaaaa
# Configuración base para todas las bases de datos adicionales
base_config = {
    'ENGINE': 'django.db.backends.mysql',
    'USER': 'DEV_USER',
    'PASSWORD': 'DEV-USER12345',
    'HOST': '192.168.9.41',
    'PORT': '3306',
}

# Crear la configuración para cada esquema adicional
for esquema in esquemas:
    DATABASES[esquema] = {
        'NAME': esquema,
        **base_config,
    }



# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')



# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL='/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 0
CACHE_MIDDLEWARE_KEY_PREFIX = ''
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True


#-------auqi esta configurado todo lo relacionado con el correo
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'mesadeservicios@cercafe.com.co'
EMAIL_HOST_PASSWORD = 'zxyskzbzpmstbyfm'
DEFAULT_FROM_EMAIL = 'mesadeservicios@cercafe.com.co'


email_from = 'mesadeservicios@cercafe.com.co'
recipient_list = ['mesadeservicios@cercafe.com.co']
from celery.schedules import crontab
from datetime import datetime
today = datetime.now().weekday()
friday = (5 - today) % 7



horario_ejecucion = crontab(hour=9, minute=00)
CELERY_BEAT_SCHEDULE = {
    "scheduled_task": {
        "task": "login.tasks.ejecutar_script",
        "schedule": horario_ejecucion,
    },
    "scheduled_task2": {
        "task": "login.tasks.ejecutar_script2",
        "schedule": 50.0,
    }
}



