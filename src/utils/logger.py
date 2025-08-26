import logging
from logging.handlers import TimedRotatingFileHandler
import os
from typing import Optional
from src.config import LOG_LEVEL, LOG_FILENAME, LOG_DIRNAME
import sys

log_levels = {
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def get_logger(name: Optional[str] = None):
    """Get Logger object"""
    if name is None:
        name = "Box Office"

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    log_level = log_levels.get(LOG_LEVEL.upper(), "INFO")
    logger.setLevel(log_level)
    logger.propagate = False

    if LOG_DIRNAME and LOG_FILENAME:
        if not os.path.exists(LOG_DIRNAME):
            os.makedirs(LOG_DIRNAME)

        log_file = os.path.join(LOG_DIRNAME, LOG_FILENAME)
        file_handler = TimedRotatingFileHandler(
            log_file, when="midnight", interval=1, backupCount=7
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    return logger
