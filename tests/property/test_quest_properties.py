"""
Property-Based Tests for Quest Manager

Properties:
  5. Daily Quest Count Constraint (Requirement 4.2)
  6. Quest Completion Rewards (Requirements 1.1, 4.3, 5.4)
  7. Daily Quest Completion Percentage (Requirement 4.6)
  8. Main Quest Sub-quest Completion Propagation (Requirement 5.3)
  9. Main Quest Progress Percentage (Requirement 5.5)
 10. Concurrent Main Quest Limit (Requirement 5.6)
 11. Penalty Zone State Machine (Requirements 8.1-8.4)
"""

from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from src.engine.quest_manager import (
    QuestManager,
    STATUS_ACTIVE,
    STATUS_COMPLETED,
    STATUS_FAILED,
    TYPE_DAILY,
    TYPE_MAIN,
    TYPE_EMERGENCY,
    MAX_MAIN_QUESTS,
    MIN_DAILY_QUESTS,
    MAX_DAILY_QUESTS,
    EMERGENCY_XP_MULTIPLIER,
)

qm = QuestManager()


# ──────────────────────────────────────────────────────────────────────────────
# Property 5: Daily Quest Count Constraint
# ──────────────────────────────────────────────────────────────────────────────


@given(
    player_id=st.integers(min_value=1, max_value=1000),
    date_offset_days=st.integers(min_value=0, max_value=365),
)
@settings(max_examples=200)
def test_daily_quest_count_constraint(player_id: int, date_offset_days: int):
    """
    Property 5: Daily quest generation always produces between MIN_DAILY and MAX_DAILY quests.
    """
    date = datetime.utcnow() + timedelta(days=date_offset_days)
    quests = qm.create_daily_quests(player_id, date)

    assert MIN_DAILY_QUESTS <= len(quests) <= MAX_DAILY_QUESTS
    for q in quests:
        assert q["quest_type"] == TYPE_DAILY
        assert q["player_id"] == player_id
        assert q["status"] == STATUS_ACTIVE


# ──────────────────────────────────────────────────────────────────────────────
# Property 6: Quest Completion Rewards
# ──────────────────────────────────────────────────────────────────────────────


@given(
    xp_reward=st.integers(min_value=0, max_value=10_000),
    gold_reward=st.integers(min_value=0, max_value=5_000),
)
@settings(max_examples=200)
def test_quest_completion_rewards(xp_reward: int, gold_reward: int):
    """
    Property 6: Completing a quest awards exactly the specified XP and gold,
    and quest status changes to 'completed'.
    """
    quest = {
        "id": 1,
        "player_id": 1,
        "quest_type": TYPE_DAILY,
        "title": "Test Quest",
        "description": "A test quest",
        "xp_reward": xp_reward,
        "gold_reward": gold_reward,
        "status": STATUS_ACTIVE,
        "deadline": datetime.utcnow() + timedelta(hours=2),
    }

    result = qm.complete_quest(quest)

    assert result.success is True
    assert result.xp_awarded == xp_reward
    assert result.gold_awarded == gold_reward
    assert quest["status"] == STATUS_COMPLETED
    assert quest["completed_at"] is not None


@given(
    xp_reward=st.integers(min_value=10, max_value=500),
)
@settings(max_examples=100)
def test_already_completed_quest_cannot_be_completed_again(xp_reward: int):
    """
    Property 6b: Completing an already-completed quest returns failure.
    """
    quest = {
        "id": 1,
        "player_id": 1,
        "quest_type": TYPE_DAILY,
        "title": "Done Quest",
        "xp_reward": xp_reward,
        "gold_reward": 0,
        "status": STATUS_COMPLETED,
    }

    result = qm.complete_quest(quest)
    assert result.success is False


# ──────────────────────────────────────────────────────────────────────────────
# Property 7: Daily Quest Completion Percentage
# ──────────────────────────────────────────────────────────────────────────────


@given(
    total=st.integers(min_value=MIN_DAILY_QUESTS, max_value=MAX_DAILY_QUESTS),
    completed=st.integers(min_value=0, max_value=MAX_DAILY_QUESTS),
)
@settings(max_examples=200)
def test_daily_quest_completion_percentage(total: int, completed: int):
    """
    Property 7: completion_pct = (completed / total) * 100, always in [0, 100].
    """
    assume(completed <= total)

    daily_quests = []
    for i in range(total):
        daily_quests.append({
            "id": i,
            "quest_type": TYPE_DAILY,
            "status": STATUS_COMPLETED if i < completed else STATUS_ACTIVE,
        })

    pct = qm.get_daily_completion_percentage(daily_quests)

    expected = round((completed / total) * 100, 1)
    assert pct == expected
    assert 0.0 <= pct <= 100.0


@given(total=st.integers(min_value=MIN_DAILY_QUESTS, max_value=MAX_DAILY_QUESTS))
@settings(max_examples=50)
def test_daily_quest_completion_percentage_all_done(total: int):
    """All daily quests completed → 100%."""
    quests = [{"id": i, "quest_type": TYPE_DAILY, "status": STATUS_COMPLETED} for i in range(total)]
    assert qm.get_daily_completion_percentage(quests) == 100.0


# ──────────────────────────────────────────────────────────────────────────────
# Property 8: Main Quest Sub-quest Completion Propagation
# ──────────────────────────────────────────────────────────────────────────────


@given(
    n_sub=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=200)
def test_main_quest_completes_when_all_subquests_done(n_sub: int):
    """
    Property 8: Main quest status becomes 'completed' only when ALL sub-quests
    are completed.
    """
    main_quest = {
        "id": 1,
        "quest_type": TYPE_MAIN,
        "title": "Main Quest",
        "status": STATUS_ACTIVE,
        "completed_at": None,
    }
    sub_quests = [
        {"id": i + 10, "quest_type": TYPE_MAIN, "status": STATUS_ACTIVE}
        for i in range(n_sub)
    ]

    # Complete all but last sub-quest
    for i in range(n_sub - 1):
        sub_quests[i]["status"] = STATUS_COMPLETED
        completed = qm.check_main_quest_completion(main_quest, sub_quests)
        assert completed is False
        assert main_quest["status"] == STATUS_ACTIVE

    # Complete the last sub-quest
    sub_quests[-1]["status"] = STATUS_COMPLETED
    completed = qm.check_main_quest_completion(main_quest, sub_quests)
    assert completed is True
    assert main_quest["status"] == STATUS_COMPLETED


@given(
    n_sub=st.integers(min_value=2, max_value=10),
    k_completed=st.integers(min_value=0, max_value=9),
)
@settings(max_examples=200)
def test_main_quest_does_not_complete_until_all_subquests_done(n_sub: int, k_completed: int):
    """
    Property 8b: Partial completion does not auto-complete the main quest.
    """
    assume(k_completed < n_sub)

    main_quest = {
        "id": 1,
        "quest_type": TYPE_MAIN,
        "title": "Main Quest",
        "status": STATUS_ACTIVE,
        "completed_at": None,
    }
    sub_quests = [
        {
            "id": i + 10,
            "quest_type": TYPE_MAIN,
            "status": STATUS_COMPLETED if i < k_completed else STATUS_ACTIVE,
        }
        for i in range(n_sub)
    ]

    completed = qm.check_main_quest_completion(main_quest, sub_quests)
    assert completed is False
    assert main_quest["status"] == STATUS_ACTIVE


# ──────────────────────────────────────────────────────────────────────────────
# Property 9: Main Quest Progress Percentage
# ──────────────────────────────────────────────────────────────────────────────


@given(
    n_sub=st.integers(min_value=1, max_value=20),
    k_completed=st.integers(min_value=0, max_value=20),
)
@settings(max_examples=300)
def test_main_quest_progress_percentage(n_sub: int, k_completed: int):
    """
    Property 9: progress = (k_completed / n_sub) * 100, always in [0, 100].
    """
    assume(k_completed <= n_sub)

    sub_quests = [
        {"id": i, "status": STATUS_COMPLETED if i < k_completed else STATUS_ACTIVE}
        for i in range(n_sub)
    ]

    pct = qm.get_main_quest_progress(sub_quests)
    expected = round((k_completed / n_sub) * 100, 1)

    assert pct == expected
    assert 0.0 <= pct <= 100.0


# ──────────────────────────────────────────────────────────────────────────────
# Property 10: Concurrent Main Quest Limit
# ──────────────────────────────────────────────────────────────────────────────


@given(
    active_count=st.integers(min_value=0, max_value=MAX_MAIN_QUESTS + 5),
)
@settings(max_examples=100)
def test_main_quest_limit_enforcement(active_count: int):
    """
    Property 10: Main quest creation succeeds when active < MAX_MAIN_QUESTS,
    fails when active >= MAX_MAIN_QUESTS.
    """
    quest_data = {"title": "New Main Quest", "description": "Test quest"}
    result = qm.create_main_quest(1, quest_data, active_count)

    if active_count < MAX_MAIN_QUESTS:
        assert result is not None
        assert result["quest_type"] == TYPE_MAIN
        assert result["status"] == STATUS_ACTIVE
    else:
        assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# Property 11: Penalty Zone State Machine
# ──────────────────────────────────────────────────────────────────────────────


@given(
    n_daily=st.integers(min_value=MIN_DAILY_QUESTS, max_value=MAX_DAILY_QUESTS),
)
@settings(max_examples=100)
def test_penalty_zone_activates_on_failed_daily_quests(n_daily: int):
    """
    Property 11: Penalty zone activates when any daily quest is still active past its deadline.
    """
    past_deadline = datetime.utcnow() - timedelta(hours=1)
    daily_quests = [
        {
            "id": i,
            "quest_type": TYPE_DAILY,
            "status": STATUS_ACTIVE,
            "deadline": past_deadline,
        }
        for i in range(n_daily)
    ]

    failed = qm.check_daily_quest_failure(daily_quests, datetime.utcnow())
    assert failed is True


@given(
    n_daily=st.integers(min_value=MIN_DAILY_QUESTS, max_value=MAX_DAILY_QUESTS),
)
@settings(max_examples=100)
def test_penalty_zone_does_not_activate_when_all_completed(n_daily: int):
    """
    Property 11b: Penalty zone does NOT activate when all daily quests are completed.
    """
    past_deadline = datetime.utcnow() - timedelta(hours=1)
    daily_quests = [
        {
            "id": i,
            "quest_type": TYPE_DAILY,
            "status": STATUS_COMPLETED,
            "deadline": past_deadline,
        }
        for i in range(n_daily)
    ]

    failed = qm.check_daily_quest_failure(daily_quests, datetime.utcnow())
    assert failed is False


def test_penalty_zone_challenge_quest_created():
    """
    Property 11c: Activating penalty zone creates a challenge quest with 24h deadline.
    """
    failed_date = datetime.utcnow()
    penalty = qm.activate_penalty_zone(1, failed_date)

    assert penalty["active"] is True
    assert penalty["player_id"] == 1
    assert "challenge_quest" in penalty
    cq = penalty["challenge_quest"]
    assert cq["status"] == STATUS_ACTIVE
    assert cq.get("is_penalty_challenge") is True

    # Deadline should be ~24 hours from activation
    expected_deadline = failed_date + timedelta(hours=24)
    diff = abs((penalty["deadline"] - expected_deadline).total_seconds())
    assert diff < 5  # Within 5 seconds tolerance


# ──────────────────────────────────────────────────────────────────────────────
# Emergency Quest XP Multiplier
# ──────────────────────────────────────────────────────────────────────────────


@given(
    base_xp=st.integers(min_value=10, max_value=500),
)
@settings(max_examples=100)
def test_emergency_quest_xp_multiplier(base_xp: int):
    """Emergency quests award 2x XP of the base reward."""
    quest_data = {
        "title": "Emergency Quest",
        "description": "URGENT",
        "xp_reward": base_xp,
        "gold_reward": 10,
        "deadline": datetime.utcnow() + timedelta(hours=2),
    }

    quest = qm.create_emergency_quest(1, quest_data, active_emergency_count=0)
    assert quest is not None
    assert quest["xp_reward"] == base_xp * EMERGENCY_XP_MULTIPLIER
