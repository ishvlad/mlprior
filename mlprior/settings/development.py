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
