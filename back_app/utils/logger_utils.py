import logging
from contextlib import contextmanager

import colorlog


def setup_peewee_logger():
    logger = logging.getLogger('peewee')
    logger.setLevel(logging.WARNING)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    log_colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red',
    }
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s',
        datefmt=None,
        reset=True,
        log_colors=log_colors,
        secondary_log_colors={},
        style='%'
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)


@contextmanager
def log_sql_statements():
    logger = logging.getLogger('peewee')
    logger.setLevel(logging.DEBUG)
    try:
        yield
    finally:
        logger.setLevel(logging.WARNING)
