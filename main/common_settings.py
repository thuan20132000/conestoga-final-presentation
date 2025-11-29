import os
from datetime import timedelta
from dotenv import load_dotenv
from pathlib import Path
import django_filters
from decouple import config
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.settings import api_settings

# Load environment variables

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "main.middleware.TimezoneMiddleware",
]

ROOT_URLCONF = "main.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "main.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Use PostgreSQL in Docker, SQLite for local development
# if config("DATABASE_URL", default=""):
#     import dj_database_url

#     DATABASES = {"default": dj_database_url.parse(config("DATABASE_URL"))}
# else:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Custom User Model
AUTH_USER_MODEL = "staff.Staff"


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/Toronto"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# AWS S3 settings
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"


STATICFILES_LOCATION = "static"
MEDIA_LOCATION = "media"

STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{STATICFILES_LOCATION}/"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIA_LOCATION}/"

STORAGES = {
    "default": {
        "BACKEND": "main.custom_storage.MediaStorage",
    },
    "staticfiles": {
        "BACKEND": "main.custom_storage.StaticStorage",
    },
    "mediafiles": {
        "BACKEND": "main.custom_storage.MediaStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # "DEFAULT_PERMISSION_CLASSES": (
    #     "rest_framework.permissions.IsAuthenticated",
    # ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# Login/Logout URLs
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/staff/"
LOGOUT_REDIRECT_URL = "/admin/login/"

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Security Settings (for production)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Email Configuration (for password reset, etc.)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
        },
    },
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(message)s"},
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
            "formatter": "verbose",
        },
        "staff": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
            "formatter": "verbose",
        },
    },
}



# CORS and cookies
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Next.js dev origin
    "http://127.0.0.1:3000",  # Frontend dev origin
    "http://localhost:3000",  # Frontend dev origin
    "http://192.168.2.170:3000",  # Django dev origin
    "http://localhost:3001",  # Next.js dev origin
    "http://127.0.0.1:3001",  # Frontend dev origin
    "http://192.168.2.170:3000",  # FastAPI dev origin
    "https://192.168.2.170:3001",  # Django dev origin
    

]
CORS_ALLOW_CREDENTIALS = True

# Allow custom headers
CORS_ALLOW_HEADERS = [
    "X-Timezone",
    "Authorization",
    "Content-Type",
    "Accept",
    "X-Requested-With",
    "X-CSRFToken",
    "X-Forwarded-For",
    "X-Forwarded-Host",
    "X-Forwarded-Server",
    "X-Forwarded-Port",
    "X-Forwarded-Proto",
]
# Notification provider settings (placeholders)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@example.com")
SMS_DEFAULT_SENDER = config("SMS_DEFAULT_SENDER", default="")
PUSH_FCM_SERVER_KEY = config("PUSH_FCM_SERVER_KEY", default="")

# Twilio SMS settings
TWILIO_ACCOUNT_SID = config("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN = config("TWILIO_AUTH_TOKEN", default="")
TWILIO_PHONE_NUMBER = config("TWILIO_PHONE_NUMBER", default="")

OPT_OUT_MESSAGE = config('OPT_OUT_MESSAGE', default="To opt out, reply STOP")

# AWS settings
AWS_REGION = config('AWS_REGION')
AWS_LAMBDA_SEND_SMS_ARN = config('AWS_LAMBDA_SEND_SMS_ARN')
AWS_SCHEDULER_POLICY_ARN = config('AWS_SCHEDULER_POLICY_ARN')


# WebPush Configuration
VAPID_PRIVATE_KEY = config('VAPID_PRIVATE_KEY', default="")
VAPID_PUBLIC_KEY = config('VAPID_PUBLIC_KEY', default="")


WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": VAPID_PUBLIC_KEY,
    "VAPID_PRIVATE_KEY": VAPID_PRIVATE_KEY,
    "VAPID_ADMIN_EMAIL": "ethantruong1602@gmail.com"
}