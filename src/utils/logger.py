"""
Logging and Performance Monitoring for LifeHunter System

Configures structured application logging with rotation and
provides a decorator for API endpoint performance tracking.

Requirements: Monitoring requirements, 37.1
"""

import functools
import logging
import os
import time
from logging.handlers import TimedRotatingFileHandler
from typing import Callable

LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "lifehunter.log")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s – %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO", log_file: str = LOG_FILE) -> None:
    """
    Configure root logger with console and rotating file handlers.

    Rotation: daily, kept for 7 days.

    Args:
        level:    Log level string (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to the log file
    """
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Avoid duplicate handlers on re-import
    if root.handlers:
        return

    fmt = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(numeric_level)
    console.setFormatter(fmt)
    root.addHandler(console)

    # Rotating file handler (daily, 7 backups)
    try:
        file_handler = TimedRotatingFileHandler(
            log_file, when="midnight", backupCount=7, encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError as e:
        logging.warning(f"Could not create file log handler: {e}")

    logging.info(f"Logging configured (level={level}, file={log_file})")


def log_performance(endpoint_name: str = "") -> Callable:
    """
    Decorator that logs execution time for API endpoints or functions.

    Usage:
        @log_performance("GET /api/player")
        def get_player(player_id):
            ...

    Args:
        endpoint_name: Human-readable name for the endpoint/function

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        logger = logging.getLogger("performance")
        name   = endpoint_name or func.__qualname__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start   = time.perf_counter()
            status  = "OK"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = f"ERROR: {type(e).__name__}"
                raise
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info(f"{name} – {elapsed_ms:.1f}ms – {status}")

        return wrapper
    return decorator


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
