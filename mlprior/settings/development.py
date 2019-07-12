from .base import *

DEBUG = True

# STATICFILES_DIRS = [
#     STATICFILE_DIR,
# ]
ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mlpriordb',
        'USER': 'mlprioradmin',
        'PASSWORD': '1qwe324r6y8ytr',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


API_HOST = 'http://localhost:8000/'


CORS_ORIGIN_WHITELIST = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://localhost:4200',
    'http://127.0.0.1:4200',
    'http://127.0.0.1:4000',
    'http://localhost:4000',
]
