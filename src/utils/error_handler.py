"""
Centralized Error Handling for LifeHunter System

Requirements: Error handling requirements, 38.1
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, Tuple, Type

logger = logging.getLogger(__name__)


class LifeHunterError(Exception):
    """Base application error."""
    status_code: int = 500
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationError(LifeHunterError):
    status_code = 400


class AuthenticationError(LifeHunterError):
    status_code = 401


class AuthorizationError(LifeHunterError):
    status_code = 403


class NotFoundError(LifeHunterError):
    status_code = 404


class ConflictError(LifeHunterError):
    status_code = 409


class ServiceUnavailableError(LifeHunterError):
    status_code = 503


def format_error_response(error: LifeHunterError) -> Tuple[Dict[str, Any], int]:
    """Format an error as a JSON-safe dict and HTTP status code."""
    return {
        "error": error.message,
        "type": type(error).__name__,
    }, error.status_code


def retry(
    max_attempts: int = 3,
    delay_seconds: float = 2.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator that retries a function on transient failures with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (default 3)
        delay_seconds: Initial delay between attempts (default 2s)
        backoff: Multiplier applied to delay after each failure (default 2x)
        exceptions: Exception types to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = delay_seconds
            last_error: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                            f"Retrying in {delay:.1f}s…"
                        )
                        time.sleep(delay)
                        delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
            raise last_error  # type: ignore[misc]
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, fallback=None, **kwargs):
    """
    Execute a function and return fallback on any exception.
    Useful for graceful degradation when external services are unavailable.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"safe_execute: {func.__name__} failed ({e}), returning fallback")
        return fallback


def register_flask_error_handlers(app) -> None:
    """Register Flask JSON error handlers for all LifeHunter error types."""
    from flask import jsonify

    @app.errorhandler(LifeHunterError)
    def handle_lifehunter_error(e: LifeHunterError):
        body, code = format_error_response(e)
        return jsonify(body), code

    @app.errorhandler(400)
    def bad_request(_):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(_):
        return jsonify({"error": "Authentication required"}), 401

    @app.errorhandler(403)
    def forbidden(_):
        return jsonify({"error": "Access denied"}), 403

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": "Internal server error"}), 500
