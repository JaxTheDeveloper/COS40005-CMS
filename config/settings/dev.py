from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-development-key-change-this'

ALLOWED_HOSTS = ['*']

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# n8n webhook used for CSV imports in development (set to your ngrok or n8n URL)
N8N_IMPORT_WEBHOOK = 'https://conditionally-brimful-exie.ngrok-free.dev/webhook-test/import-schedule'
