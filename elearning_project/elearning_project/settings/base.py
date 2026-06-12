from pathlib import Path
import os

# ======================
# BASE
# ======================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# For Elastic Beanstalk - load their env file
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env.elasticbeanstalk')  # EB-specific env file
load_dotenv(BASE_DIR / '.env')  # Fallback for local development

# Get SECRET_KEY - try multiple methods
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.getenv("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    # Last resort - read directly from EB config
    try:
        with open('/opt/elasticbeanstalk/deployment/env', 'r') as f:
            for line in f:
                if line.startswith('DJANGO_SECRET_KEY='):
                    SECRET_KEY = line.split('=', 1)[1].strip().strip('"').strip("'")
                    break
    except:
        pass

if not SECRET_KEY:
    raise Exception("DJANGO_SECRET_KEY is not set in environment variables")

DEBUG = os.environ.get("DJANGO_DEBUG", os.getenv("DJANGO_DEBUG", "False")).lower() == "true"

# Clean ALLOWED_HOSTS (no duplicates, no '*')
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "ALLOWED_HOSTS",
        os.getenv(
            "ALLOWED_HOSTS",
            "api.btee-zm.com,localhost,127.0.0.1,.elasticbeanstalk.com,.amazonaws.com",
        ),
    ).split(",")
    if host.strip()
]

# ======================
# INSTALLED APPS
# ======================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "drf_yasg",
    "rest_framework.authtoken",
    "corsheaders",
    "import_export",
    "django_filters",

    # Local apps
    "registration_app",
    "courses_app",
]

# ======================
# MIDDLEWARE (ORDER MATTERS)
# ======================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ======================
# CSRF + CORS
# ======================
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        os.getenv(
            "CSRF_TRUSTED_ORIGINS",
            "https://www.btee-zm.com,https://api.btee-zm.com,https://btee-lms.vercel.app",
        ),
    ).split(",")
    if origin.strip()
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "https://www.btee-zm.com,https://btee-lms.vercel.app,http://localhost:3000",
        ),
    ).split(",")
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

# ======================
# SECURITY
# ======================
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Disable SSL redirect for now (enable after HTTPS is set up)
SECURE_SSL_REDIRECT = False  # Changed from True

SESSION_COOKIE_SECURE = False  # Changed - set to True only with HTTPS
CSRF_COOKIE_SECURE = False  # Changed - set to True only with HTTPS

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# ======================
# STATIC FILES
# ======================
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Only use Manifest storage if not DEBUG
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ======================
# TEMPLATES
# ======================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "elearning_project.wsgi.application"

# ======================
# DATABASE
# ======================
# Check for PostgreSQL credentials
if os.environ.get("POSTGRES_HOST") or os.getenv("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB") or os.getenv("POSTGRES_DB"),
            "USER": os.environ.get("POSTGRES_USER") or os.getenv("POSTGRES_USER"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD") or os.getenv("POSTGRES_PASSWORD"),
            "HOST": os.environ.get("POSTGRES_HOST") or os.getenv("POSTGRES_HOST"),
            "PORT": os.environ.get("POSTGRES_PORT") or os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    # Fallback to SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ======================
# REST FRAMEWORK
# ======================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# ======================
# SWAGGER
# ======================
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Token": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
        },
    },
    "USE_SESSION_AUTH": False,
}

# ======================
# AUTH
# ======================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "registration_app.CustomUser"

# ======================
# INTERNATIONALIZATION
# ======================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ======================
# DEFAULT AUTO FIELD
# ======================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ROOT_URLCONF = "elearning_project.urls"
INSTRUCTOR_USERNAME = "instructor_user"