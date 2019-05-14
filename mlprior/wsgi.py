"""
WSGI config for mlprior project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")


from .settings import IS_DEBUG

if IS_DEBUG:
    application = get_wsgi_application()
else:
    application = StaticFilesHandler(get_wsgi_application())
