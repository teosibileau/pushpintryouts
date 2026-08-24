import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "chat",
]

MIDDLEWARE = [
    "django_grip.GripMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

REST_FRAMEWORK = {
    # Session auth without CSRF enforcement: the only authenticated
    # mutations travel over the websocket, and this is an internal PoC api.
    "DEFAULT_AUTHENTICATION_CLASSES": ["chat.auth.CsrfExemptSessionAuthentication"],
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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
