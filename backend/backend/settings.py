"""
Django settings for the backend project.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from dotenv import load_dotenv


# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent

# Load the backend's private development environment file when present.
# In Docker/production, environment variables supplied by the runtime take precedence.
load_dotenv(BASE_DIR / ".env", override=False)


def env_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable using common truthy values."""
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# -----------------------------------------------------------------------------
# Core Django settings
# -----------------------------------------------------------------------------

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
DEBUG = env_bool("DJANGO_DEBUG", False)

if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY must be set in the environment or backend/.env")

if not DEBUG and (len(SECRET_KEY) < 50 or SECRET_KEY.startswith("replace-with-")):
    raise ValueError("Production DJANGO_SECRET_KEY must be a unique value of at least 50 characters")

# SECURITY WARNING: set these to the hostnames used by the deployment.
allowed_hosts_env = os.getenv("DJANGO_ALLOWED_HOSTS")

ALLOWED_HOSTS = [
    host.strip()
    for host in (allowed_hosts_env or "localhost,127.0.0.1,backend").split(",")
    if host.strip()
]

csrf_origins_env = os.getenv("CSRF_TRUSTED_ORIGINS")

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in (
        csrf_origins_env or "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

if not DEBUG and (not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS):
    raise ValueError("Production DJANGO_ALLOWED_HOSTS must list specific trusted hosts")

if not DEBUG and not allowed_hosts_env:
    raise ValueError("Production DJANGO_ALLOWED_HOSTS must be explicitly configured")

if not DEBUG and not csrf_origins_env:
    raise ValueError("Production CSRF_TRUSTED_ORIGINS must be explicitly configured")

if not DEBUG and any(not origin.startswith("https://") for origin in CSRF_TRUSTED_ORIGINS):
    raise ValueError("Production CSRF_TRUSTED_ORIGINS must contain only HTTPS origins")


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "users",
    "catalog",
    "carts",
    "orders",
    "staff_api",
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

ROOT_URLCONF = "backend.urls"

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

WSGI_APPLICATION = "backend.wsgi.application"


# Database
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
DB_PROVIDER = os.getenv("DB_PROVIDER", "standard").strip().lower()
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_CONN_MAX_AGE = int(os.getenv("DB_CONN_MAX_AGE", "60"))

if not DEBUG and DB_ENGINE != "postgres":
    raise ValueError("Production DB_ENGINE must be postgres")

if DB_ENGINE == "postgres" and DB_PROVIDER not in {"standard", "neon"}:
    raise ValueError("DB_PROVIDER must be either 'standard' or 'neon'.")

if DB_ENGINE == "postgres" and DB_PROVIDER == "standard":
    required_postgres_variables = (
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_HOST",
        "POSTGRES_PASSWORD",
    )

    if not DEBUG and any(not os.getenv(name) for name in required_postgres_variables):
        raise ValueError(
            "Production PostgreSQL database name, user, host, and password "
            "must be explicitly configured"
        )

    if not DEBUG and (
        len(POSTGRES_PASSWORD) < 16
        or POSTGRES_PASSWORD.startswith(("replace-with-", "local-dev-"))
    ):
        raise ValueError("Production POSTGRES_PASSWORD must be a unique value of at least 16 characters")

if DB_ENGINE == "postgres":
    if DB_PROVIDER == "neon":
        tmpPostgres = urlparse(os.getenv("DATABASE_URL", ""))
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": tmpPostgres.path.replace("/", ""),
                "USER": tmpPostgres.username,
                "PASSWORD": tmpPostgres.password,
                "HOST": tmpPostgres.hostname,
                "PORT": 5432,
                "CONN_MAX_AGE": DB_CONN_MAX_AGE,
                "OPTIONS": dict(parse_qsl(tmpPostgres.query)),
            }
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("POSTGRES_DB", "fish_ecommerce"),
                "USER": os.getenv("POSTGRES_USER", "fish_ecommerce"),
                "PASSWORD": POSTGRES_PASSWORD,
                "HOST": os.getenv("POSTGRES_HOST", "localhost"),
                "PORT": os.getenv("POSTGRES_PORT", "5432"),
                "CONN_MAX_AGE": DB_CONN_MAX_AGE,
                "OPTIONS": {
                    "sslmode": os.getenv(
                        "POSTGRES_SSLMODE", "prefer" if DEBUG else "require"
                    ),
                },
            },
        }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        },
    }


# Password validation
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


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static and media files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -----------------------------------------------------------------------------
# Project-specific settings
# -----------------------------------------------------------------------------

# Custom user model
AUTH_USER_MODEL = "users.User"


# Django REST framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "otp_request": "5/hour",
        "otp_verify": "10/hour",
        "staff_login": "10/hour",
        "delivery_quote": "30/hour",
    },
}


# JSON Web Token authentication
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

JWT_REFRESH_COOKIE_NAME = os.getenv("JWT_REFRESH_COOKIE_NAME", "refresh_token")
JWT_COOKIE_SECURE = env_bool("JWT_COOKIE_SECURE", not DEBUG)
JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
JWT_COOKIE_DOMAIN = os.getenv("JWT_COOKIE_DOMAIN") or None

if JWT_COOKIE_SAMESITE not in {"Lax", "Strict", "None"}:
    raise ValueError("JWT_COOKIE_SAMESITE must be Lax, Strict, or None")

if not DEBUG and not JWT_COOKIE_SECURE:
    raise ValueError("JWT_COOKIE_SECURE must be enabled in production")

if JWT_COOKIE_SAMESITE == "None" and not JWT_COOKIE_SECURE:
    raise ValueError("SameSite=None cookies require JWT_COOKIE_SECURE=true")


# Email-based one-time password authentication
OTP_TTL_SECONDS = int(os.getenv("OTP_TTL_SECONDS", "300"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
OTP_PEPPER = os.getenv("OTP_PEPPER", "" if not DEBUG else SECRET_KEY)

if not OTP_PEPPER:
    raise ValueError("OTP_PEPPER must be set when DEBUG is disabled")

if not DEBUG and (
    len(OTP_PEPPER) < 32
    or OTP_PEPPER.startswith("replace-with-")
    or OTP_PEPPER == SECRET_KEY
):
    raise ValueError("Production OTP_PEPPER must be a unique secret of at least 32 characters")


# Email delivery
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Machli <no-reply@example.com>")

if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ValueError("EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled")

if not DEBUG and not (EMAIL_HOST and EMAIL_HOST_USER and EMAIL_HOST_PASSWORD):
    raise ValueError("Production email OTP requires EMAIL_HOST, EMAIL_HOST_USER, and EMAIL_HOST_PASSWORD")

if not DEBUG and EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
    raise ValueError("The console email backend is not allowed in production")

if not DEBUG and not (EMAIL_USE_TLS or EMAIL_USE_SSL):
    raise ValueError("Production SMTP must use TLS or SSL")


# Order notifications
ORDER_NOTIFICATION_PROVIDER = os.getenv(
    "ORDER_NOTIFICATION_PROVIDER", "telegram"
).strip().lower()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")


# Security settings
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
