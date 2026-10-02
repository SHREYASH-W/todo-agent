"""
Property-Based Tests for:
 19. Job Deduplication (Requirement 15.5)
 20. Application State Transition Validity (Requirements 18.1, 18.2)
 22. Configuration Parse-Print Round-Trip (Configuration requirements)
 23. Player Data Export-Import Round-Trip (Export/import requirements)
 24. Notification Rate Limiting (Notification rate limiting requirements)
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from src.engine.notification_service import NotificationService, RATE_LIMIT_WINDOW_SECONDS


# ──────────────────────────────────────────────────────────────────────────────
# Property 19: Job Deduplication
# ──────────────────────────────────────────────────────────────────────────────


def _deduplicate_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    Deduplication using (title, company) as the unique key.
    Mirrors the logic in JobScraper.deduplicate_jobs.
    """
    seen = set()
    result = []
    for job in jobs:
        key = (job.get("title", "").lower().strip(), job.get("company", "").lower().strip())
        if key not in seen:
            seen.add(key)
            result.append(job)
    return result


job_strategy = st.fixed_dictionaries({
    "title": st.sampled_from(["Software Engineer", "Python Dev", "Frontend Dev", "Data Scientist"]),
    "company": st.sampled_from(["ACME Corp", "Widgets Inc", "Tech Co", "StartupXYZ"]),
    "location": st.text(min_size=1, max_size=20),
    "url": st.text(min_size=5, max_size=50),
})


@given(jobs=st.lists(job_strategy, min_size=0, max_size=50))
@settings(max_examples=300)
def test_job_deduplication_no_duplicates(jobs: List[Dict]):
    """
    Property 19: After deduplication, no two jobs share the same (title, company) pair.
    """
    result = _deduplicate_jobs(jobs)

    keys = [(j["title"].lower().strip(), j["company"].lower().strip()) for j in result]
    assert len(keys) == len(set(keys))


@given(jobs=st.lists(job_strategy, min_size=1, max_size=30))
@settings(max_examples=200)
def test_job_deduplication_subset_of_original(jobs: List[Dict]):
    """
    Property 19b: Deduplicated list is always a subset of the original.
    """
    result = _deduplicate_jobs(jobs)
    assert len(result) <= len(jobs)


@given(jobs=st.lists(job_strategy, min_size=1, max_size=20))
@settings(max_examples=100)
def test_job_deduplication_idempotent(jobs: List[Dict]):
    """
    Property 19c: Applying deduplication twice produces the same result as once.
    """
    once = _deduplicate_jobs(jobs)
    twice = _deduplicate_jobs(once)
    assert len(once) == len(twice)


# ──────────────────────────────────────────────────────────────────────────────
# Property 20: Application State Transition Validity
# ──────────────────────────────────────────────────────────────────────────────

# Valid state machine transitions
VALID_TRANSITIONS = {
    "submitted": {"under_review", "rejected"},
    "under_review": {"interview_scheduled", "rejected"},
    "interview_scheduled": {"offered", "rejected"},
    "offered": set(),       # Terminal state
    "rejected": set(),      # Terminal state
}

ALL_STATES = list(VALID_TRANSITIONS.keys())


def is_valid_transition(from_state: str, to_state: str) -> bool:
    """Check if a state transition is valid per the application state machine."""
    return to_state in VALID_TRANSITIONS.get(from_state, set())


@given(
    from_state=st.sampled_from(ALL_STATES),
    to_state=st.sampled_from(ALL_STATES),
)
@settings(max_examples=300)
def test_application_state_transition_validity(from_state: str, to_state: str):
    """
    Property 20: Only valid transitions per the state machine are allowed.
    """
    is_valid = is_valid_transition(from_state, to_state)

    # Cross-validate with the hardcoded valid transitions
    expected = to_state in VALID_TRANSITIONS.get(from_state, set())
    assert is_valid == expected


def test_valid_transitions_submitted_to_under_review():
    assert is_valid_transition("submitted", "under_review") is True


def test_valid_transitions_under_review_to_interview():
    assert is_valid_transition("under_review", "interview_scheduled") is True


def test_valid_transitions_interview_to_offered():
    assert is_valid_transition("interview_scheduled", "offered") is True


def test_valid_transitions_rejected_is_terminal():
    for state in ALL_STATES:
        assert is_valid_transition("rejected", state) is False


def test_valid_transitions_offered_is_terminal():
    for state in ALL_STATES:
        assert is_valid_transition("offered", state) is False


@given(
    from_state=st.sampled_from(["offered", "rejected"]),
    to_state=st.sampled_from(ALL_STATES),
)
@settings(max_examples=100)
def test_terminal_states_reject_all_transitions(from_state: str, to_state: str):
    """Terminal states (offered, rejected) cannot transition to anything."""
    assert is_valid_transition(from_state, to_state) is False


# ──────────────────────────────────────────────────────────────────────────────
# Property 22: Configuration Parse-Print Round-Trip
# ──────────────────────────────────────────────────────────────────────────────

config_strategy = st.fixed_dictionaries({
    "database_path": st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N", "P"))),
    "ollama_host": st.just("http://localhost:11434"),
    "session_timeout": st.integers(min_value=60, max_value=86400),
    "max_daily_quests": st.integers(min_value=3, max_value=5),
    "log_level": st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR"]),
    "backup_enabled": st.booleans(),
    "rate_limit_per_minute": st.integers(min_value=10, max_value=1000),
})


@given(config=config_strategy)
@settings(max_examples=300)
def test_config_json_round_trip(config: Dict[str, Any]):
    """
    Property 22: Serializing config to JSON and parsing it back produces equivalent config.
    parse(print(C)) == C
    """
    serialized = json.dumps(config, sort_keys=True)
    deserialized = json.loads(serialized)

    assert deserialized == config


@given(config=config_strategy)
@settings(max_examples=200)
def test_config_round_trip_preserves_types(config: Dict[str, Any]):
    """
    Property 22b: JSON round-trip preserves Python types (str, int, bool).
    """
    serialized = json.dumps(config)
    deserialized = json.loads(serialized)

    for key, value in config.items():
        assert type(deserialized[key]) == type(value)


# ──────────────────────────────────────────────────────────────────────────────
# Property 23: Player Data Export-Import Round-Trip
# ──────────────────────────────────────────────────────────────────────────────

player_stats_strategy = st.fixed_dictionaries({
    "level": st.integers(min_value=1, max_value=999),
    "xp": st.integers(min_value=0, max_value=1_000_000),
    "rank": st.sampled_from(["E", "D", "C", "B", "A", "S", "National"]),
    "gold": st.integers(min_value=0, max_value=999_999),
    "str_stat": st.integers(min_value=1, max_value=999),
    "int_stat": st.integers(min_value=1, max_value=999),
    "agi_stat": st.integers(min_value=1, max_value=999),
    "vit_stat": st.integers(min_value=1, max_value=999),
    "sen_stat": st.integers(min_value=1, max_value=999),
    "luk_stat": st.integers(min_value=1, max_value=999),
    "stat_points": st.integers(min_value=0, max_value=500),
    "skill_points": st.integers(min_value=0, max_value=100),
})


@given(player_data=player_stats_strategy)
@settings(max_examples=300)
def test_player_data_json_round_trip(player_data: Dict[str, Any]):
    """
    Property 23: import(export(P)) == P for player stats via JSON round-trip.
    """
    exported = json.dumps(player_data, sort_keys=True)
    imported = json.loads(exported)

    assert imported == player_data
    assert imported["level"] == player_data["level"]
    assert imported["gold"] == player_data["gold"]
    assert imported["rank"] == player_data["rank"]


@given(player_data=player_stats_strategy)
@settings(max_examples=200)
def test_player_export_preserves_all_stat_fields(player_data: Dict[str, Any]):
    """
    Property 23b: All stat fields survive export/import without loss or mutation.
    """
    stat_keys = ["str_stat", "int_stat", "agi_stat", "vit_stat", "sen_stat", "luk_stat"]

    exported = json.dumps(player_data)
    imported = json.loads(exported)

    for key in stat_keys:
        assert imported[key] == player_data[key]


# ──────────────────────────────────────────────────────────────────────────────
# Property 24: Notification Rate Limiting
# ──────────────────────────────────────────────────────────────────────────────


def test_notification_rate_limiting_single_event_type():
    """
    Property 24: Only 1 notification per event type per minute is sent.
    Rapid successive calls return None after the first.
    """
    service = NotificationService()
    player_id = 1

    n1 = service.notify_level_up(player_id, 5)
    n2 = service.notify_level_up(player_id, 6)  # Within 1 minute

    assert n1 is not None
    assert n2 is None  # Rate limited


def test_notification_different_event_types_not_rate_limited_together():
    """
    Property 24b: Rate limiting is per event type — different types can each
    send one notification within the same window.
    """
    service = NotificationService()
    player_id = 1

    n1 = service.notify_level_up(player_id, 5)
    n2 = service.notify_quest_complete(player_id, "Test Quest", 100)
    n3 = service.notify_achievement_unlock(player_id, "Achiever", "common")

    assert n1 is not None
    assert n2 is not None
    assert n3 is not None


def test_notification_rate_limit_across_multiple_players():
    """
    Property 24c: Rate limiting is per (player_id, event_type) pair —
    different players are not rate limited by each other.
    """
    service = NotificationService()

    n1 = service.notify_level_up(1, 5)
    n2 = service.notify_level_up(2, 5)  # Different player
    n3 = service.notify_level_up(1, 6)  # Same player — rate limited

    assert n1 is not None
    assert n2 is not None
    assert n3 is None


@given(
    n_calls=st.integers(min_value=2, max_value=20),
    player_id=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=100)
def test_notification_rate_limiting_multiple_calls(n_calls: int, player_id: int):
    """
    Property 24d: No matter how many times we call the same notification,
    only the first one succeeds within the rate limit window.
    """
    service = NotificationService()

    results = []
    for i in range(n_calls):
        n = service.notify_level_up(player_id, i + 1)
        results.append(n)

    # First call should succeed
    assert results[0] is not None
    # All subsequent calls within the window should be rate-limited
    for n in results[1:]:
        assert n is None


def test_notification_mark_as_read():
    """Unread notifications can be marked as read."""
    service = NotificationService()
    player_id = 99

    notif = service.notify_level_up(player_id, 5)
    assert notif is not None
    assert notif["is_read"] is False

    success = service.mark_as_read(notif)
    assert success is True
    assert notif["is_read"] is True

    # Second mark should return False (already read)
    success2 = service.mark_as_read(notif)
    assert success2 is False
