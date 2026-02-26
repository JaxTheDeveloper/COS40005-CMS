from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-development-key-change-this'

ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', '0.0.0.0', 'localhost:8000', '127.0.0.1:8000']

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# n8n webhooks for development
# Uses internal Docker network hostname for backend->n8n communication
N8N_IMPORT_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/csv-import'
N8N_REFINE_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/event-refinement'

# Optional: n8n API key (set if your n8n instance requires authentication)
N8N_API_KEY = None
N8N_WEBHOOK_SECRET = None
