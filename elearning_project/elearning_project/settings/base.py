# base.py - Updated with CSRF fixes for Elastic Beanstalk
from logging import DEBUG
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'
DEBUG = True  # Set to True for development, but should be False in production

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Always add these hosts for Elastic Beanstalk, regardless of DEBUG mode
ALLOWED_HOSTS.extend(['.elasticbeanstalk.com', '.amazonaws.com', 'localhost', '127.0.0.1', '*'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'drf_yasg',
    'rest_framework.authtoken',
    'corsheaders',
    'import_export',
    'django_filters',

    # Custom apps
    'registration_app',
    'courses_app',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        },
    },
    'USE_SESSION_AUTH': False,
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================
# CSRF & CORS SETTINGS - FIXED FOR ELASTIC BEANSTALK
# ============================================

# Define your Elastic Beanstalk domain
EB_DOMAIN = 'elearning-api-env.eba-gjr4ta8a.us-east-1.elasticbeanstalk.com'
EB_URL = f'http://{EB_DOMAIN}'

# CSRF Trusted Origins - Add ALL possible variations
CSRF_TRUSTED_ORIGINS = [
    EB_URL,
    f'https://{EB_DOMAIN}',
    'http://localhost:3000',  # Next.js default
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3001',
    'http://127.0.0.1:3000',
]

# Add any from environment variable
additional_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if additional_origins:
    CSRF_TRUSTED_ORIGINS.extend(additional_origins.split(','))

# ======================
# COOKIE SETTINGS - CRITICAL FOR CSRF
# ======================

# For HTTP-only Elastic Beanstalk (without HTTPS)
CSRF_COOKIE_SECURE = False  # Must be False for HTTP
SESSION_COOKIE_SECURE = False  # Must be False for HTTP
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read cookie (needed for frontend)
SESSION_COOKIE_HTTPONLY = True  # Keep session cookie HTTP-only for security

# SameSite settings - Use 'Lax' for better compatibility
CSRF_COOKIE_SAMESITE = 'Lax'  # Changed from 'None' to 'Lax' for better compatibility
SESSION_COOKIE_SAMESITE = 'Lax'  # Changed from 'None' to 'Lax'

# Domain settings - Let browser handle it for now
CSRF_COOKIE_DOMAIN = None  # Set to None to let browser handle it
SESSION_COOKIE_DOMAIN = None  # Set to None to let browser handle it

# Path settings
CSRF_COOKIE_PATH = '/'
SESSION_COOKIE_PATH = '/'

# Cookie names
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'

# ======================
# CORS SETTINGS FOR NEXT.JS
# ======================

# If you have a Next.js frontend
NEXTJS_URL = os.getenv('NEXTJS_URL', 'http://localhost:3000')

# CORS Configuration
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        NEXTJS_URL,
        EB_URL,
        'http://localhost:3000',
        'http://localhost:3001',
    ]
    # Add from environment
    env_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
    if env_origins:
        CORS_ALLOWED_ORIGINS.extend(env_origins.split(','))
    
    CORS_ALLOW_CREDENTIALS = True  # Important for cookies/sessions

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ======================
# PROXY/LOAD BALANCER SETTINGS
# ======================

# Important for Elastic Beanstalk
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ======================
# ADDITIONAL SECURITY SETTINGS
# ======================

if not DEBUG:
    # Static files storage
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'elearning_project.wsgi.application'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'elearningdb'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# Fallback to SQLite if PostgreSQL credentials are missing
if not all([os.getenv('POSTGRES_DB'), os.getenv('POSTGRES_USER'), os.getenv('POSTGRES_PASSWORD')]):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))

os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'videos'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'thumbnails'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'materials'), exist_ok=True)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'registration_app.CustomUser'
INSTRUCTOR_USERNAME = "instructor_user"

ROOT_URLCONF = 'elearning_project.urls'