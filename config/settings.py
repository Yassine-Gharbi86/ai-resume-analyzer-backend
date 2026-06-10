"""
Django settings for AI Resume Analyzer.
Phase 1: Basic setup with DRF and CORS.
"""

from pathlib import Path

# ─────────────────────────────────────────────
# BASE DIRECTORY
# ─────────────────────────────────────────────
# This is the root of the backend/ folder.
# All paths are built relative to this.
BASE_DIR = Path(__file__).resolve().parent.parent



SECRET_KEY = 'django-insecure-phase1-dev-key-change-this-in-production'

# DEBUG = True enables detailed error pages. Turn off in production.
DEBUG = True

# ALLOWED_HOSTS controls which domain names can reach this server.
# Empty list is fine for local development with DEBUG = True.
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# ─────────────────────────────────────────────
# INSTALLED APPS
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',
    'corsheaders',


    'api',
]


# ─────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────
# Middleware runs on every request/response cycle.
# CorsMiddleware MUST come before CommonMiddleware.
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ─────────────────────────────────────────────
# URL CONFIGURATION
# ─────────────────────────────────────────────
ROOT_URLCONF = 'config.urls'


# ─────────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ─────────────────────────────────────────────
# DJANGO REST FRAMEWORK
# ─────────────────────────────────────────────
REST_FRAMEWORK = {
    # Default renderer: return JSON responses
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Default parser: accept JSON request bodies
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}


# ─────────────────────────────────────────────
# CORS CONFIGURATION
# ─────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]


# ─────────────────────────────────────────────
# INTERNATIONALIZATION
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ─────────────────────────────────────────────
# STATIC FILES
# ─────────────────────────────────────────────
STATIC_URL = 'static/'

# ─────────────────────────────────────────────
# MEDIA FILES (user uploads)
# ─────────────────────────────────────────────
# MEDIA_ROOT: absolute path on disk where uploaded files are saved.
# In dev, this creates a backend/media/ folder.
MEDIA_ROOT = BASE_DIR / 'media'

# MEDIA_URL: the URL prefix browsers use to access uploaded files.
# e.g., a file at media/resumes/foo.pdf is served at /media/resumes/foo.pdf
MEDIA_URL = '/media/'

# Default primary key type for models
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────
# FILE UPLOAD SETTINGS
# ─────────────────────────────────────────────
# Maximum upload size: 5 MB (in bytes).
# We'll enforce this in the view as well, but good to set globally.
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB

# ─────────────────────────────────────────────
# AI — GROQ
# ─────────────────────────────────────────────

import os
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
