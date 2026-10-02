"""
Unit tests for AI Assistant Service with Ollama integration.

Tests cover:
- Cover letter generation with mocked Ollama responses
- Timeout handling and retry logic
- Error handling for unavailable Ollama service
- Temperature and token configurations
- Quest prioritization, difficulty adjustment, insight generation
- Job skill extraction

Requirements: 28.1-28.7, 29.1-29.7, 30.1-30.7, 31.1-31.7
"""

import json
import pytest
import requests
from unittest.mock import Mock, patch

from src.services.ai_assistant import (
    AIAssistant,
    AIAssistantError,
    OllamaError,
    OllamaUnavailableError,
    QuestPriority,
)


@pytest.fixture
def ai():
    """AI Assistant with no real network calls (retries disabled, zero delay)."""
    return AIAssistant(
        ollama_url="http://localhost:11434",
        model="qwen2.5-coder:7b",
        timeout=30,
        max_retries=1,  # Single attempt in tests — no real sleeps
    )


def _mock_response(text: str, status: int = 200) -> Mock:
    """Build a mock requests.Response that returns text from Ollama."""
    resp = Mock()
    resp.status_code = status
    resp.json.return_value = {"response": text}
    resp.raise_for_status = Mock()  # no-op for 200
    return resp


# ──────────────────────────────────────────────────────────────────────────────
# Initialization
# ──────────────────────────────────────────────────────────────────────────────


def test_default_initialization():
    a = AIAssistant()
    assert a.base_url == "http://localhost:11434"
    assert a.model == "qwen2.5-coder:7b"
    assert a.timeout == 30
    assert a.max_retries == 3


def test_custom_initialization():
    a = AIAssistant(ollama_url="http://custom:8080", model="llama3", timeout=60, max_retries=5)
    assert a.base_url == "http://custom:8080"
    assert a.model == "llama3"
    assert a.timeout == 60
    assert a.max_retries == 5


def test_trailing_slash_removed():
    a = AIAssistant(ollama_url="http://localhost:11434/")
    assert not a.base_url.endswith("/")


# ──────────────────────────────────────────────────────────────────────────────
# Cover Letter Generation (Task 4.2 / Requirements 28.1-28.7)
# ──────────────────────────────────────────────────────────────────────────────


@patch("src.services.ai_assistant.requests.post")
def test_cover_letter_success(mock_post, ai):
    mock_post.return_value = _mock_response("Dear Hiring Manager,\n\nI am interested in the role.")
    result = ai.generate_cover_letter("Python Dev job", "5 years Python")

    assert "Dear Hiring Manager" in result
    call_payload = mock_post.call_args[1]["json"]
    assert call_payload["options"]["temperature"] == 0.7
    assert call_payload["options"]["num_predict"] == 500


@patch("src.services.ai_assistant.requests.post")
def test_cover_letter_prompt_contains_inputs(mock_post, ai):
    mock_post.return_value = _mock_response("Letter content")
    job_desc = "Senior Engineer at ACME"
    resume = "10 years engineering experience"

    ai.generate_cover_letter(job_desc, resume)

    prompt = mock_post.call_args[1]["json"]["prompt"]
    assert job_desc in prompt
    assert resume in prompt


@patch("src.services.ai_assistant.requests.post")
def test_cover_letter_unavailable_returns_fallback(mock_post, ai):
    """If Ollama is down, generate_cover_letter returns a user-friendly fallback string."""
    mock_post.side_effect = requests.exceptions.ConnectionError("refused")

    result = ai.generate_cover_letter("job", "resume")

    assert isinstance(result, str)
    assert len(result) > 0
    # Should be a human-readable fallback, not a traceback
    assert "unavailable" in result.lower() or "unable" in result.lower() or "error" in result.lower()


# ──────────────────────────────────────────────────────────────────────────────
# Quest Prioritization (Requirements 29.1-29.7)
# ──────────────────────────────────────────────────────────────────────────────


def test_prioritize_empty_list(ai):
    assert ai.prioritize_quests([]) == []


@patch("src.services.ai_assistant.requests.post")
def test_prioritize_quests_uses_analytical_temperature(mock_post, ai):
    priority_json = json.dumps([
        {"quest_id": 1, "title": "Task", "priority": "High", "reasoning": "Important"}
    ])
    mock_post.return_value = _mock_response(priority_json)

    quests = [{"id": 1, "title": "Task", "quest_type": "daily", "xp_reward": 50, "difficulty": "easy"}]
    result = ai.prioritize_quests(quests)

    assert isinstance(result, list)
    call_payload = mock_post.call_args[1]["json"]
    assert call_payload["options"]["temperature"] == 0.3
    assert call_payload["options"]["num_predict"] == 200


@patch("src.services.ai_assistant.requests.post")
def test_prioritize_quests_fallback_on_parse_error(mock_post, ai):
    """Malformed JSON from Ollama falls back to Medium priority for all quests."""
    mock_post.return_value = _mock_response("not valid json at all")

    quests = [
        {"id": 1, "title": "Q1", "quest_type": "daily", "xp_reward": 30, "difficulty": "easy"},
        {"id": 2, "title": "Q2", "quest_type": "main", "xp_reward": 100, "difficulty": "hard"},
    ]
    result = ai.prioritize_quests(quests)

    assert len(result) == 2
    assert all(isinstance(p, QuestPriority) for p in result)
    assert all(p.priority == "Medium" for p in result)


@patch("src.services.ai_assistant.requests.post")
def test_prioritize_quests_json_wrapped_in_text(mock_post, ai):
    """Prioritization works when JSON array is embedded in text."""
    data = [{"quest_id": 5, "title": "Run", "priority": "Critical", "reasoning": "Deadline"}]
    mock_post.return_value = _mock_response(f"Here is the list:\n{json.dumps(data)}\nDone.")

    quests = [{"id": 5, "title": "Run", "quest_type": "emergency", "xp_reward": 200, "difficulty": "hard"}]
    result = ai.prioritize_quests(quests)

    assert len(result) == 1
    assert result[0].quest_id == 5


# ──────────────────────────────────────────────────────────────────────────────
# Difficulty Adjustment (Requirements 30.1-30.7)
# ──────────────────────────────────────────────────────────────────────────────


@patch("src.services.ai_assistant.requests.post")
def test_adjust_difficulty_success(mock_post, ai):
    mock_post.return_value = _mock_response("Increase difficulty. Completion rate is 95%.")
    result = ai.adjust_difficulty(1, {"completion_rate": 95, "streak": 10, "failed_quests": 0})

    assert isinstance(result, str)
    assert len(result) > 0
    call_payload = mock_post.call_args[1]["json"]
    assert call_payload["options"]["temperature"] == 0.3


@patch("src.services.ai_assistant.requests.post")
def test_adjust_difficulty_fallback_on_error(mock_post, ai):
    mock_post.side_effect = requests.exceptions.ConnectionError("refused")
    result = ai.adjust_difficulty(1, {})
    assert isinstance(result, str)
    assert "maintain" in result.lower() or "unavailable" in result.lower()


# ──────────────────────────────────────────────────────────────────────────────
# Performance Insights (Requirements 31.1-31.7)
# ──────────────────────────────────────────────────────────────────────────────


@patch("src.services.ai_assistant.requests.post")
def test_generate_insights_success(mock_post, ai):
    insights = ["Great streak!", "Focus on skill quests.", "Apply to more jobs.", "Level up soon."]
    mock_post.return_value = _mock_response(json.dumps(insights))

    result = ai.generate_insights(1, "7_days")

    assert isinstance(result, list)
    assert len(result) >= 1


@patch("src.services.ai_assistant.requests.post")
def test_generate_insights_fallback_on_error(mock_post, ai):
    mock_post.side_effect = requests.exceptions.ConnectionError("refused")
    result = ai.generate_insights(1, "30_days")
    assert isinstance(result, list)
    assert len(result) >= 1  # Always returns at least the static fallback insights


# ──────────────────────────────────────────────────────────────────────────────
# Motivational Messages
# ──────────────────────────────────────────────────────────────────────────────


@patch("src.services.ai_assistant.requests.post")
def test_motivational_message_uses_creative_temperature(mock_post, ai):
    mock_post.return_value = _mock_response("You are unstoppable, Hunter!")
    result = ai.generate_motivational_message("player just leveled up")

    assert isinstance(result, str)
    call_payload = mock_post.call_args[1]["json"]
    assert call_payload["options"]["temperature"] == 0.7


@patch("src.services.ai_assistant.requests.post")
def test_motivational_message_fallback(mock_post, ai):
    mock_post.side_effect = requests.exceptions.ConnectionError("refused")
    result = ai.generate_motivational_message("failed quest")
    assert isinstance(result, str)
    assert len(result) > 0


# ──────────────────────────────────────────────────────────────────────────────
# Job Skill Extraction
# ──────────────────────────────────────────────────────────────────────────────


@patch("src.services.ai_assistant.requests.post")
def test_extract_job_skills_success(mock_post, ai):
    skills = ["Python", "Flask", "SQLAlchemy", "Git"]
    mock_post.return_value = _mock_response(json.dumps(skills))

    result = ai.extract_job_skills("We need Python, Flask, SQLAlchemy and Git.")

    assert isinstance(result, list)
    assert "Python" in result
    call_payload = mock_post.call_args[1]["json"]
    assert call_payload["options"]["temperature"] == 0.3


@patch("src.services.ai_assistant.requests.post")
def test_extract_job_skills_fallback_empty_on_error(mock_post, ai):
    mock_post.side_effect = requests.exceptions.ConnectionError("refused")
    result = ai.extract_job_skills("some job description")
    assert isinstance(result, list)  # Returns empty list on failure


# ──────────────────────────────────────────────────────────────────────────────
# Retry Logic
# ──────────────────────────────────────────────────────────────────────────────


@patch("src.services.ai_assistant.time.sleep")
@patch("src.services.ai_assistant.requests.post")
def test_retry_uses_exponential_backoff(mock_post, mock_sleep):
    """3-attempt AI with ConnectionError should sleep 2s then 4s between retries."""
    ai3 = AIAssistant(ollama_url="http://localhost:11434", max_retries=3)
    mock_post.side_effect = requests.exceptions.ConnectionError("refused")

    # generate_cover_letter catches OllamaError and returns fallback
    ai3.generate_cover_letter("job", "resume")

    sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
    # 3 attempts → 2 sleeps between them (delays[0]=2, delays[1]=4)
    assert sleep_calls == [2, 4]


@patch("src.services.ai_assistant.time.sleep")
@patch("src.services.ai_assistant.requests.post")
def test_succeeds_on_third_attempt(mock_post, mock_sleep):
    """Success on 3rd attempt after 2 connection failures."""
    success_resp = _mock_response("Cover letter text here")
    mock_post.side_effect = [
        requests.exceptions.ConnectionError("fail 1"),
        requests.exceptions.ConnectionError("fail 2"),
        success_resp,
    ]

    ai3 = AIAssistant(ollama_url="http://localhost:11434", max_retries=3)
    result = ai3.generate_cover_letter("job", "resume")

    assert "Cover letter text here" in result
    assert mock_post.call_count == 3


# ──────────────────────────────────────────────────────────────────────────────
# is_available
# ──────────────────────────────────────────────────────────────────────────────


@patch("src.services.ai_assistant.requests.get")
def test_is_available_true(mock_get, ai):
    mock_get.return_value = Mock(status_code=200)
    assert ai.is_available() is True


@patch("src.services.ai_assistant.requests.get")
def test_is_available_false_on_connection_error(mock_get, ai):
    mock_get.side_effect = requests.exceptions.ConnectionError("refused")
    assert ai.is_available() is False
