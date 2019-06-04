from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


ALLOWED_HOSTS = ['www.mlprior.com', 'mlprior.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mlpriordb',
        'USER': 'mlprioradmin',
        'PASSWORD': '1qwe324r6y8ytr',
        'HOST': 'rc1b-q8r2m5cebprs15nq.mdb.yandexcloud.net',
        'PORT': '6432',
    }
}


API_HOST = 'http://mlprior.com/'