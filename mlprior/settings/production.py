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
        'HOST': 'rc1b-wfrxb8mx74s5tr3q.mdb.yandexcloud.net',
        'PORT': '6432',
    }
}


API_HOST = 'http://mlprior.com/'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'gunicorn': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/home/mlprior/git_app/gunicorn.errors',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        }
    },
    'loggers': {
        'gunicorn.errors': {
            'level': 'DEBUG',
            'handlers': ['gunicorn'],
            'propagate': True,
        },
    },
}

CORS_ORIGIN_WHITELIST = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://localhost:4200',
    'http://127.0.0.1:4200',
    'http://mlprior.com'
]