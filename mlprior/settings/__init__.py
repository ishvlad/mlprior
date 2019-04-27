IS_DEBUG = True


if IS_DEBUG:
    from .development import *
else:
    from .production import *
