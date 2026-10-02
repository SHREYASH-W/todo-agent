"""
Security Utilities for LifeHunter System

Implements:
- Input validation and sanitization
- CSRF token generation/validation
- Rate limiting (per-user, per-minute)
- Security headers middleware
- XSS output escaping

Requirements: Security requirements, 39.1
"""

import hashlib
import hmac
import html
import logging
import re
import secrets
import time
from collections import defaultdict
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Rate limit: 100 requests per minute per user
RATE_LIMIT_WINDOW = 60       # seconds
RATE_LIMIT_MAX    = 100      # requests per window

# In-memory rate limit store: {identifier: [(timestamp, count)]}
_rate_limit_store: Dict[str, list] = defaultdict(list)

# CSRF token store: {token: expiry_ts}
_csrf_tokens: Dict[str, float] = {}
CSRF_TOKEN_TTL = 3600  # 1 hour


# ── Input Validation ────────────────────────────────────────

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Strip leading/trailing whitespace and truncate to max_length."""
    return str(value).strip()[:max_length]


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_username(username: str) -> bool:
    """Username: 3-50 chars, alphanumeric + underscore/hyphen."""
    return bool(re.match(r'^[a-zA-Z0-9_\-]{3,50}$', username))


def escape_html(value: str) -> str:
    """Escape HTML special characters to prevent XSS. Requirement 39.1"""
    return html.escape(str(value), quote=True)


# ── CSRF Protection ─────────────────────────────────────────

def generate_csrf_token() -> str:
    """Generate a new CSRF token valid for 1 hour."""
    token = secrets.token_urlsafe(32)
    _csrf_tokens[token] = time.time() + CSRF_TOKEN_TTL
    return token


def validate_csrf_token(token: str) -> bool:
    """Validate a CSRF token. Returns True if valid and not expired."""
    if not token:
        return False
    expiry = _csrf_tokens.get(token)
    if expiry is None:
        return False
    if time.time() > expiry:
        del _csrf_tokens[token]
        return False
    return True


def revoke_csrf_token(token: str) -> None:
    """Revoke a CSRF token after use (one-time tokens)."""
    _csrf_tokens.pop(token, None)


# ── Rate Limiting ────────────────────────────────────────────

def check_rate_limit(identifier: str, max_requests: int = RATE_LIMIT_MAX) -> bool:
    """
    Check if an identifier (user_id or IP) is within rate limits.

    Sliding window algorithm: counts requests in the last 60 seconds.

    Args:
        identifier: User ID or IP address string
        max_requests: Maximum requests allowed per window

    Returns:
        bool: True if request is allowed, False if rate limited
    """
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Remove expired entries
    _rate_limit_store[identifier] = [
        ts for ts in _rate_limit_store[identifier] if ts > window_start
    ]

    count = len(_rate_limit_store[identifier])
    if count >= max_requests:
        logger.warning(f"Rate limit exceeded for {identifier}: {count}/{max_requests} req/min")
        return False

    _rate_limit_store[identifier].append(now)
    return True


def get_rate_limit_remaining(identifier: str, max_requests: int = RATE_LIMIT_MAX) -> int:
    """Return remaining requests in the current window."""
    now          = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    recent       = [ts for ts in _rate_limit_store[identifier] if ts > window_start]
    return max(0, max_requests - len(recent))


# ── Security Headers ─────────────────────────────────────────

SECURITY_HEADERS = {
    "X-Content-Type-Options":    "nosniff",
    "X-Frame-Options":           "SAMEORIGIN",
    "X-XSS-Protection":          "1; mode=block",
    "Referrer-Policy":           "strict-origin-when-cross-origin",
    "Permissions-Policy":        "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data:;"
    ),
}


def add_security_headers(response):
    """Add security headers to a Flask response object."""
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


def register_security_middleware(app) -> None:
    """Register security middleware on a Flask app."""
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)

    logger.info("Security middleware registered")
