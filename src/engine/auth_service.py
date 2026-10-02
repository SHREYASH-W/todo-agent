"""
Authentication Service for LifeHunter System

Handles user registration, login, sessions, password hashing, and account lockout.

Requirements: Authentication requirements
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt

logger = logging.getLogger(__name__)

SESSION_TIMEOUT_MINUTES = 30
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# In-memory session store (replace with DB-backed store in production)
_sessions: Dict[str, Dict[str, Any]] = {}
_failed_attempts: Dict[str, Dict[str, Any]] = {}  # username -> {count, locked_until}


class AuthError(Exception):
    pass


class AuthService:
    """Handles authentication and session management."""

    def hash_password(self, password: str) -> str:
        """Hash a password with bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def register(
        self,
        username: str,
        email: str,
        password: str,
    ) -> Dict[str, Any]:
        """
        Create a new player account.

        Returns a new player data dict ready for DB insertion.
        """
        if len(password) < 8:
            raise AuthError("Password must be at least 8 characters")

        return {
            "username": username.strip(),
            "email": email.strip().lower(),
            "password_hash": self.hash_password(password),
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "level": 1,
            "xp": 0,
            "rank": "E",
            "gold": 0,
            "str_stat": 10,
            "int_stat": 10,
            "agi_stat": 10,
            "vit_stat": 10,
            "sen_stat": 10,
            "luk_stat": 10,
            "hp": 200,
            "mp": 100,
            "stat_points": 0,
            "skill_points": 0,
            "active_title_id": None,
        }

    def login(
        self,
        username: str,
        password: str,
        player: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """
        Authenticate a player and create a session.

        Args:
            username: Username
            password: Plain-text password
            player: Player data dict from DB (or None if not found)

        Returns:
            str: Session token, or None if authentication fails

        Raises:
            AuthError: If account is locked
        """
        # Check lockout
        lockout_info = _failed_attempts.get(username, {})
        locked_until = lockout_info.get("locked_until")
        if locked_until and datetime.utcnow() < locked_until:
            remaining = int((locked_until - datetime.utcnow()).total_seconds() / 60)
            raise AuthError(f"Account locked. Try again in {remaining} minutes.")

        if player is None or not self.verify_password(password, player.get("password_hash", "")):
            # Record failed attempt
            count = lockout_info.get("count", 0) + 1
            _failed_attempts[username] = {"count": count, "locked_until": None}
            if count >= MAX_FAILED_ATTEMPTS:
                _failed_attempts[username]["locked_until"] = (
                    datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                )
                raise AuthError(
                    f"Too many failed attempts. Account locked for {LOCKOUT_DURATION_MINUTES} minutes."
                )
            logger.warning(f"Failed login for '{username}' ({count}/{MAX_FAILED_ATTEMPTS})")
            return None

        # Success: clear failed attempts, create session
        _failed_attempts.pop(username, None)
        session_token = secrets.token_urlsafe(32)
        _sessions[session_token] = {
            "player_id": player.get("id"),
            "username": username,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=SESSION_TIMEOUT_MINUTES),
        }
        logger.info(f"Session created for player '{username}'")
        return session_token

    def logout(self, session_token: str) -> bool:
        """End a session."""
        if session_token in _sessions:
            del _sessions[session_token]
            logger.info("Session ended")
            return True
        return False

    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token and return session data if valid.

        Returns:
            Dict: Session data, or None if invalid/expired
        """
        session = _sessions.get(session_token)
        if not session:
            return None
        if datetime.utcnow() > session["expires_at"]:
            del _sessions[session_token]
            return None
        # Refresh expiry on activity
        session["expires_at"] = datetime.utcnow() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        return session

    def reset_password(
        self,
        email: str,
        new_password: str,
        player: Optional[Dict[str, Any]],
    ) -> bool:
        """
        Reset a player's password.

        Args:
            email: Player's email address
            new_password: New plain-text password
            player: Player data dict (updated in-place)

        Returns:
            bool: True if reset succeeded
        """
        if player is None:
            logger.warning(f"Password reset requested for unknown email: {email}")
            return False
        if len(new_password) < 8:
            raise AuthError("Password must be at least 8 characters")

        player["password_hash"] = self.hash_password(new_password)
        logger.info(f"Password reset for {email}")
        return True
