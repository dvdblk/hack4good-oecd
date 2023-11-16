"""Custom logger for the application."""
import logging
import os
import sys

loggers = dict()


def init_logger(name):
    """Create and return a custom logger"""
    if existing_log := loggers.get(name, None):
        return existing_log
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d %(name)s %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.addHandler(handler)
        logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG"))
        loggers[name] = logger
        return logger
