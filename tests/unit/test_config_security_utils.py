"""
Unit tests for:
- Configuration system (Tasks 35.1, 35.2)
- Security utilities (Task 39.1, 39.2)
- Error handler (Task 38.1, 38.2)
- Logger/performance monitoring (Task 37.1, 37.2)
- Scheduled jobs (Task 34.2)
"""

import json
import os
import tempfile
import time
import pytest

from src.config.config import LifeHunterConfig, load_config, save_config
from src.utils.security import (
    validate_email,
    validate_username,
    escape_html,
    generate_csrf_token,
    validate_csrf_token,
    revoke_csrf_token,
    check_rate_limit,
    get_rate_limit_remaining,
    _rate_limit_store,
    _csrf_tokens,
    RATE_LIMIT_MAX,
    RATE_LIMIT_WINDOW,
)
from src.utils.error_handler import (
    LifeHunterError,
    ValidationError,
    NotFoundError,
    ServiceUnavailableError,
    format_error_response,
    retry,
    safe_execute,
)
from src.utils.logger import setup_logging, log_performance


# ──────────────────────────────────────────────────────────────────────────────
# Configuration System Tests (Task 35.2)
# ──────────────────────────────────────────────────────────────────────────────


def test_default_config_values():
    config = LifeHunterConfig()
    assert config.database_path == "database.db"
    assert config.min_daily_quests == 3
    assert config.max_daily_quests == 5
    assert config.session_timeout_minutes == 30
    assert config.api_rate_limit_per_minute == 100


def test_config_to_dict_has_all_fields():
    config = LifeHunterConfig()
    d = config.to_dict()
    assert "database_path" in d
    assert "ollama_host" in d
    assert "session_timeout_minutes" in d
    assert "log_level" in d


def test_save_and_load_config_round_trip():
    """Property 22: save → load produces equivalent configuration."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        f.write("{}")
        path = f.name
    try:
        original = LifeHunterConfig(
            database_path="test.db",
            session_timeout_minutes=60,
            log_level="DEBUG",
            api_rate_limit_per_minute=50,
        )
        save_config(original, path)

        loaded = load_config(path)
        assert loaded.database_path == "test.db"
        assert loaded.session_timeout_minutes == 60
        assert loaded.log_level == "DEBUG"
        assert loaded.api_rate_limit_per_minute == 50
    finally:
        os.unlink(path)


def test_load_config_missing_file_uses_defaults():
    config = load_config("nonexistent_config_12345.json")
    defaults = LifeHunterConfig()
    assert config.database_path == defaults.database_path
    assert config.log_level == defaults.log_level


def test_load_config_env_override(monkeypatch):
    monkeypatch.setenv("LH_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LH_SESSION_TIMEOUT_MINUTES", "120")

    config = load_config("nonexistent_override_test.json")
    assert config.log_level == "DEBUG"
    assert config.session_timeout_minutes == 120


def test_load_config_invalid_int_env_uses_default(monkeypatch):
    monkeypatch.setenv("LH_SESSION_TIMEOUT_MINUTES", "not_a_number")
    # Should not raise; bad env vars are ignored
    config = load_config("nonexistent_fallback.json")
    assert config.session_timeout_minutes == 30  # Default


def test_save_config_creates_directory():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "subdir", "config.json")
        result = save_config(LifeHunterConfig(), path)
        assert result is True
        assert os.path.exists(path)


def test_config_json_round_trip_preserves_types():
    config = LifeHunterConfig(session_timeout_minutes=45, min_daily_quests=3)
    d = config.to_dict()
    serialized = json.dumps(d)
    deserialized = json.loads(serialized)

    assert isinstance(deserialized["session_timeout_minutes"], int)
    assert isinstance(deserialized["min_daily_quests"], int)
    assert isinstance(deserialized["log_level"], str)


# ──────────────────────────────────────────────────────────────────────────────
# Security Tests (Task 39.2)
# ──────────────────────────────────────────────────────────────────────────────


class TestEmailValidation:
    def test_valid_email(self):
        assert validate_email("user@example.com") is True

    def test_valid_email_with_plus(self):
        assert validate_email("user+tag@domain.co.uk") is True

    def test_invalid_email_no_at(self):
        assert validate_email("userexample.com") is False

    def test_invalid_email_no_domain(self):
        assert validate_email("user@") is False

    def test_invalid_email_empty(self):
        assert validate_email("") is False

    def test_invalid_email_spaces(self):
        assert validate_email("user name@example.com") is False


class TestUsernameValidation:
    def test_valid_username(self):
        assert validate_username("john_doe") is True

    def test_valid_username_with_hyphen(self):
        assert validate_username("john-doe123") is True

    def test_too_short(self):
        assert validate_username("ab") is False

    def test_too_long(self):
        assert validate_username("a" * 51) is False

    def test_special_characters(self):
        assert validate_username("user@name") is False

    def test_spaces_not_allowed(self):
        assert validate_username("user name") is False


class TestXSSPrevention:
    def test_escape_script_tag(self):
        result = escape_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_escape_on_click(self):
        result = escape_html('<img onerror="alert(1)" src="x">')
        assert "onerror" in result  # Text preserved
        assert "<img" not in result  # Tag escaped

    def test_escape_quotes(self):
        result = escape_html('"double" and \'single\'')
        assert "&quot;" in result

    def test_safe_string_unchanged(self):
        safe = "Hello, World! 123"
        assert escape_html(safe) == safe


class TestCSRFProtection:
    def setup_method(self):
        _csrf_tokens.clear()

    def test_generate_csrf_token_unique(self):
        t1 = generate_csrf_token()
        t2 = generate_csrf_token()
        assert t1 != t2

    def test_validate_valid_token(self):
        token = generate_csrf_token()
        assert validate_csrf_token(token) is True

    def test_validate_invalid_token(self):
        assert validate_csrf_token("fake-token-xyz") is False

    def test_validate_empty_token(self):
        assert validate_csrf_token("") is False

    def test_revoke_token(self):
        token = generate_csrf_token()
        revoke_csrf_token(token)
        assert validate_csrf_token(token) is False

    def test_token_length_secure(self):
        token = generate_csrf_token()
        assert len(token) >= 32


class TestRateLimiting:
    def setup_method(self):
        _rate_limit_store.clear()

    def test_first_request_allowed(self):
        assert check_rate_limit("user_test_1") is True

    def test_requests_within_limit_allowed(self):
        uid = "rate_test_user"
        for _ in range(10):
            assert check_rate_limit(uid, max_requests=10) is True

    def test_exceeding_limit_blocked(self):
        uid = "over_limit_user"
        for _ in range(5):
            check_rate_limit(uid, max_requests=5)
        # 6th request should be blocked
        assert check_rate_limit(uid, max_requests=5) is False

    def test_remaining_decrements(self):
        uid = "remaining_test"
        before = get_rate_limit_remaining(uid, max_requests=10)
        check_rate_limit(uid, max_requests=10)
        after = get_rate_limit_remaining(uid, max_requests=10)
        assert after == before - 1

    def test_different_users_independent(self):
        assert check_rate_limit("user_a", max_requests=1) is True
        assert check_rate_limit("user_b", max_requests=1) is True
        # user_a is now rate limited
        assert check_rate_limit("user_a", max_requests=1) is False
        # user_b still has one request (also rate limited now)
        assert check_rate_limit("user_b", max_requests=1) is False


# ──────────────────────────────────────────────────────────────────────────────
# Error Handler Tests (Task 38.2)
# ──────────────────────────────────────────────────────────────────────────────


def test_validation_error_status_code():
    err = ValidationError("Invalid input")
    _, code = format_error_response(err)
    assert code == 400


def test_not_found_error_status_code():
    err = NotFoundError("Resource not found")
    _, code = format_error_response(err)
    assert code == 404


def test_service_unavailable_status_code():
    err = ServiceUnavailableError("Service down")
    _, code = format_error_response(err)
    assert code == 503


def test_format_error_response_no_internal_details():
    err = ValidationError("Bad input")
    body, _ = format_error_response(err)
    # Should NOT expose stack traces or internal details
    assert "traceback" not in str(body).lower()
    assert "error" in body


def test_retry_succeeds_on_first_attempt():
    call_count = [0]

    @retry(max_attempts=3, delay_seconds=0)
    def succeeds():
        call_count[0] += 1
        return "ok"

    result = succeeds()
    assert result == "ok"
    assert call_count[0] == 1


def test_retry_retries_on_failure():
    call_count = [0]

    @retry(max_attempts=3, delay_seconds=0, exceptions=(ValueError,))
    def fails_twice():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError("Transient failure")
        return "recovered"

    result = fails_twice()
    assert result == "recovered"
    assert call_count[0] == 3


def test_retry_raises_after_max_attempts():
    @retry(max_attempts=2, delay_seconds=0, exceptions=(RuntimeError,))
    def always_fails():
        raise RuntimeError("Permanent failure")

    with pytest.raises(RuntimeError):
        always_fails()


def test_safe_execute_returns_fallback_on_error():
    def risky():
        raise ConnectionError("Service down")

    result = safe_execute(risky, fallback=[])
    assert result == []


def test_safe_execute_returns_result_on_success():
    def safe_func():
        return 42

    result = safe_execute(safe_func, fallback=0)
    assert result == 42


# ──────────────────────────────────────────────────────────────────────────────
# Logger Tests (Task 37.2)
# ──────────────────────────────────────────────────────────────────────────────


def test_log_performance_decorator_returns_result():
    @log_performance("test_function")
    def compute():
        return 99

    result = compute()
    assert result == 99


def test_log_performance_decorator_reraises_exception():
    @log_performance("failing_function")
    def fails():
        raise ValueError("Oops")

    with pytest.raises(ValueError):
        fails()


def test_setup_logging_runs_without_error(tmp_path):
    log_file = str(tmp_path / "test.log")
    # Should not raise
    setup_logging(level="INFO", log_file=log_file)
    import logging
    logger = logging.getLogger("test_setup")
    logger.info("test message")
