IS_DEBUG = False


if IS_DEBUG:
    from .development import *
else:
    from .production import *
