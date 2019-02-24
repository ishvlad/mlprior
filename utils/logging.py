import functools
import logging
import time
import os


def timeit(logger, tag=None, level=None, format='%s: %s minutes'):
    if level is None:
        level = logging.INFO

    def decorator(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            start = time.time()
            result = fn(*args, **kwargs)
            duration = time.time() - start

            function_name = tag if tag else repr(fn)
            logger.log(level, format, function_name, duration / 60)
            return result
        return inner

    return decorator


def get_logger(name, log_file=None, level=logging.DEBUG):
    if log_file is None:
        log_file = 'logs/' + name + '.log'

    if not os.path.exists('logs'):
        os.mkdir('logs')

    formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')

    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger
