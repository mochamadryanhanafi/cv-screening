import os
import re
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv('DEBUG', 'True') in ('True', '1', 'true')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "api",
    "core.domain",
    "evaluations.apps.EvaluationsConfig",
    "django_extensions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cv_screening.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cv_screening.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_KWARGS': {'encoding': 'utf8'},
            'POOL_KWARGS': {'max_connections': 50, 'retry_on_timeout': True},
        },
        'KEY_PREFIX': 'cv_screening',
        'TIMEOUT': 300,
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'api.throttles.DefaultThrottle',
        'api.throttles.AnonDefaultThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'upload': os.getenv('THROTTLE_UPLOAD', '5/hour'),
        'evaluate': os.getenv('THROTTLE_EVALUATE', '3/hour'),
        'result': os.getenv('THROTTLE_RESULT', '20/hour'),
        'default': os.getenv('THROTTLE_DEFAULT', '30/min'),
        'admin': os.getenv('THROTTLE_ADMIN', '5/min'),
        'anon': os.getenv('THROTTLE_ANON', '10/min'),
        'token_obtain': os.getenv('THROTTLE_TOKEN', '5/min'),
    },
    'EXCEPTION_HANDLER': 'cv_screening.exceptions.custom_exception_handler',
}

def parse_duration(value, default=None):
    """Parse a duration string like '15m', '1h', '30s', '1d' into timedelta.

    If value is already a timedelta, return it. If it's numeric, treat as seconds.
    """
    if value is None:
        value = default
    if isinstance(value, timedelta):
        return value
    try:
        # numeric strings are seconds
        if isinstance(value, (int, float)) or re.fullmatch(r"\d+", str(value)):
            return timedelta(seconds=int(value))
        s = str(value).strip().lower()
        m = re.fullmatch(r"(\d+)\s*(ms|s|sec|secs|m|min|h|hr|d)?", s)
        if not m:
            return default
        qty = int(m.group(1))
        unit = m.group(2) or 's'
        if unit in ('ms',):
            return timedelta(milliseconds=qty)
        if unit in ('s', 'sec', 'secs'):
            return timedelta(seconds=qty)
        if unit in ('m', 'min'):
            return timedelta(minutes=qty)
        if unit in ('h', 'hr'):
            return timedelta(hours=qty)
        if unit in ('d',):
            return timedelta(days=qty)
    except Exception:
        return default


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': parse_duration(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', '15m')),
    'REFRESH_TOKEN_LIFETIME': parse_duration(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', '1d')),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
