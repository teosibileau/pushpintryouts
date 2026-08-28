import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "chat",
]

MIDDLEWARE = [
    "django_grip.GripMiddleware",
    "django.middleware.common.CommonMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

SIMPLE_JWT = {
    # generous access lifetime so the PoC front can skip the refresh dance
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
}

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
    }
}

GRIP_URL = os.environ.get("GRIP_URL", "http://pushpin:5561")

# identifies which backend variant answered, e.g. django5-py312
SERVED_BY = os.environ.get("SERVED_BY", "unknown")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
