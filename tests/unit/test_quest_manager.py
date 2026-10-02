"""
Unit tests for the Quest Manager.
Requirements: 4.1-4.7, 5.1-5.7, 6.1-6.7, 7.1-7.7, 8.1-8.7
"""

from datetime import datetime, timedelta
import pytest

from src.engine.quest_manager import (
    QuestManager,
    STATUS_ACTIVE,
    STATUS_COMPLETED,
    STATUS_FAILED,
    TYPE_DAILY,
    TYPE_MAIN,
    TYPE_INSTANT,
    TYPE_EMERGENCY,
    MAX_MAIN_QUESTS,
    MAX_INSTANT_DUNGEONS,
    MAX_EMERGENCY_QUESTS,
    MIN_DAILY_QUESTS,
    MAX_DAILY_QUESTS,
    EMERGENCY_XP_MULTIPLIER,
    DAILY_COMPLETION_BONUS_XP,
)

qm = QuestManager()


# ─── Daily Quests ──────────────────────────────────────────────────────────


def test_create_daily_quests_count_range():
    for _ in range(10):  # Run multiple times due to randomness
        quests = qm.create_daily_quests(1)
        assert MIN_DAILY_QUESTS <= len(quests) <= MAX_DAILY_QUESTS


def test_create_daily_quests_type_and_status():
    quests = qm.create_daily_quests(1)
    for q in quests:
        assert q["quest_type"] == TYPE_DAILY
        assert q["status"] == STATUS_ACTIVE
        assert q["player_id"] == 1
        assert q["deadline"] is not None


def test_daily_completion_percentage_empty():
    assert qm.get_daily_completion_percentage([]) == 0.0


def test_daily_completion_percentage_none_done():
    quests = [{"status": STATUS_ACTIVE} for _ in range(3)]
    assert qm.get_daily_completion_percentage(quests) == 0.0


def test_daily_completion_percentage_all_done():
    quests = [{"status": STATUS_COMPLETED} for _ in range(4)]
    assert qm.get_daily_completion_percentage(quests) == 100.0


def test_daily_completion_percentage_partial():
    quests = [
        {"status": STATUS_COMPLETED},
        {"status": STATUS_COMPLETED},
        {"status": STATUS_ACTIVE},
        {"status": STATUS_ACTIVE},
    ]
    assert qm.get_daily_completion_percentage(quests) == 50.0


def test_check_daily_quest_failure_past_deadline():
    past = datetime.utcnow() - timedelta(hours=1)
    quests = [{"quest_type": TYPE_DAILY, "status": STATUS_ACTIVE, "deadline": past}]
    assert qm.check_daily_quest_failure(quests) is True


def test_check_daily_quest_failure_future_deadline():
    future = datetime.utcnow() + timedelta(hours=2)
    quests = [{"quest_type": TYPE_DAILY, "status": STATUS_ACTIVE, "deadline": future}]
    assert qm.check_daily_quest_failure(quests) is False


def test_check_daily_quest_failure_all_completed():
    past = datetime.utcnow() - timedelta(hours=1)
    quests = [{"quest_type": TYPE_DAILY, "status": STATUS_COMPLETED, "deadline": past}]
    assert qm.check_daily_quest_failure(quests) is False


def test_check_daily_quest_failure_empty_list():
    assert qm.check_daily_quest_failure([]) is False


# ─── Main Quests ───────────────────────────────────────────────────────────


def test_create_main_quest_success():
    data = {"title": "Get a Job", "description": "Apply to 10 companies"}
    quest = qm.create_main_quest(1, data, active_main_quests_count=0)

    assert quest is not None
    assert quest["quest_type"] == TYPE_MAIN
    assert quest["title"] == "Get a Job"
    assert quest["status"] == STATUS_ACTIVE


def test_create_main_quest_at_limit():
    data = {"title": "Quest", "description": "Desc"}
    quest = qm.create_main_quest(1, data, active_main_quests_count=MAX_MAIN_QUESTS)
    assert quest is None


def test_create_main_quest_one_below_limit():
    data = {"title": "Quest", "description": "Desc"}
    quest = qm.create_main_quest(1, data, active_main_quests_count=MAX_MAIN_QUESTS - 1)
    assert quest is not None


def test_main_quest_progress_no_sub_quests():
    assert qm.get_main_quest_progress([]) == 0.0


def test_main_quest_progress_partial():
    sub_quests = [
        {"status": STATUS_COMPLETED},
        {"status": STATUS_ACTIVE},
        {"status": STATUS_ACTIVE},
        {"status": STATUS_ACTIVE},
    ]
    assert qm.get_main_quest_progress(sub_quests) == 25.0


def test_check_main_quest_completion_all_done():
    main = {"id": 1, "status": STATUS_ACTIVE, "completed_at": None}
    subs = [{"status": STATUS_COMPLETED} for _ in range(3)]

    result = qm.check_main_quest_completion(main, subs)

    assert result is True
    assert main["status"] == STATUS_COMPLETED


def test_check_main_quest_completion_partial_not_done():
    main = {"id": 1, "status": STATUS_ACTIVE, "completed_at": None}
    subs = [
        {"status": STATUS_COMPLETED},
        {"status": STATUS_ACTIVE},
    ]

    result = qm.check_main_quest_completion(main, subs)

    assert result is False
    assert main["status"] == STATUS_ACTIVE


def test_check_main_quest_completion_empty_subs():
    main = {"id": 1, "status": STATUS_ACTIVE, "completed_at": None}
    result = qm.check_main_quest_completion(main, [])
    assert result is False


# ─── Instant Dungeons ──────────────────────────────────────────────────────


def test_start_instant_dungeon_success():
    data = {"title": "Speed Run", "duration_minutes": 30}
    dungeon = qm.start_instant_dungeon(1, data, active_instant_count=0)

    assert dungeon is not None
    assert dungeon["quest_type"] == TYPE_INSTANT
    assert dungeon["status"] == STATUS_ACTIVE
    assert dungeon["duration_minutes"] == 30
    assert dungeon["deadline"] > datetime.utcnow()


def test_start_instant_dungeon_duration_clamped_min():
    data = {"title": "Quick", "duration_minutes": 5}  # Below minimum
    dungeon = qm.start_instant_dungeon(1, data, active_instant_count=0)
    assert dungeon["duration_minutes"] == 15  # Clamped to min


def test_start_instant_dungeon_duration_clamped_max():
    data = {"title": "Marathon", "duration_minutes": 1000}  # Above maximum
    dungeon = qm.start_instant_dungeon(1, data, active_instant_count=0)
    assert dungeon["duration_minutes"] == 240  # Clamped to max


def test_start_instant_dungeon_limit():
    data = {"title": "Dungeon", "duration_minutes": 60}
    result = qm.start_instant_dungeon(1, data, active_instant_count=MAX_INSTANT_DUNGEONS)
    assert result is None


def test_instant_dungeon_remaining_time():
    data = {"title": "Dungeon", "duration_minutes": 60}
    dungeon = qm.start_instant_dungeon(1, data, active_instant_count=0)
    remaining = qm.get_instant_dungeon_remaining_time(dungeon)

    assert remaining > 3500  # ~60 minutes minus a tiny bit
    assert remaining <= 3600


def test_instant_dungeon_remaining_time_expired():
    dungeon = {
        "deadline": datetime.utcnow() - timedelta(minutes=5),
        "status": STATUS_ACTIVE,
    }
    remaining = qm.get_instant_dungeon_remaining_time(dungeon)
    assert remaining == 0


# ─── Emergency Quests ──────────────────────────────────────────────────────


def test_create_emergency_quest_doubles_xp():
    data = {"title": "Emergency!", "xp_reward": 50, "deadline": datetime.utcnow() + timedelta(hours=2)}
    quest = qm.create_emergency_quest(1, data, active_emergency_count=0)

    assert quest is not None
    assert quest["xp_reward"] == 50 * EMERGENCY_XP_MULTIPLIER
    assert quest["base_xp"] == 50
    assert quest.get("is_emergency") is True


def test_create_emergency_quest_at_limit():
    data = {"title": "Emergency!", "xp_reward": 50}
    result = qm.create_emergency_quest(1, data, active_emergency_count=MAX_EMERGENCY_QUESTS)
    assert result is None


# ─── Quest Completion ──────────────────────────────────────────────────────


def test_complete_quest_rewards():
    quest = {
        "id": 1,
        "quest_type": TYPE_DAILY,
        "title": "Test Quest",
        "xp_reward": 100,
        "gold_reward": 50,
        "status": STATUS_ACTIVE,
        "deadline": datetime.utcnow() + timedelta(hours=2),
    }

    result = qm.complete_quest(quest)

    assert result.success is True
    assert result.xp_awarded == 100
    assert result.gold_awarded == 50
    assert quest["status"] == STATUS_COMPLETED


def test_complete_quest_daily_bonus_when_all_done():
    quests = [
        {"id": i, "quest_type": TYPE_DAILY, "xp_reward": 30, "gold_reward": 10,
         "status": STATUS_ACTIVE, "deadline": datetime.utcnow() + timedelta(hours=2)}
        for i in range(3)
    ]
    # Complete first two
    for q in quests[:2]:
        q["status"] = STATUS_COMPLETED

    # Complete last one
    result = qm.complete_quest(quests[2], all_daily_quests=quests)

    assert result.success is True
    assert result.bonus_xp == DAILY_COMPLETION_BONUS_XP


def test_complete_expired_instant_dungeon_fails():
    quest = {
        "id": 1,
        "quest_type": TYPE_INSTANT,
        "title": "Expired Dungeon",
        "xp_reward": 100,
        "gold_reward": 50,
        "status": STATUS_ACTIVE,
        "deadline": datetime.utcnow() - timedelta(minutes=5),
    }

    result = qm.complete_quest(quest)

    assert result.success is False
    assert quest["status"] == STATUS_FAILED


def test_complete_already_completed_quest_fails():
    quest = {
        "id": 1,
        "quest_type": TYPE_DAILY,
        "title": "Done",
        "xp_reward": 50,
        "gold_reward": 20,
        "status": STATUS_COMPLETED,
    }

    result = qm.complete_quest(quest)
    assert result.success is False


# ─── Penalty Zone ──────────────────────────────────────────────────────────


def test_penalty_zone_activation():
    failed_date = datetime.utcnow()
    penalty = qm.activate_penalty_zone(1, failed_date)

    assert penalty["active"] is True
    assert "challenge_quest" in penalty
    assert penalty["challenge_quest"]["status"] == STATUS_ACTIVE


def test_penalty_zone_deadline_24_hours():
    failed_date = datetime.utcnow()
    penalty = qm.activate_penalty_zone(1, failed_date)

    delta = penalty["deadline"] - failed_date
    assert abs(delta.total_seconds() - 86400) < 5  # ~24 hours


# ─── Active Quest Retrieval ────────────────────────────────────────────────


def test_get_active_quests_grouped_by_type():
    all_quests = [
        {"id": 1, "quest_type": TYPE_DAILY, "status": STATUS_ACTIVE},
        {"id": 2, "quest_type": TYPE_DAILY, "status": STATUS_COMPLETED},  # Excluded
        {"id": 3, "quest_type": TYPE_MAIN, "status": STATUS_ACTIVE},
        {"id": 4, "quest_type": TYPE_INSTANT, "status": STATUS_ACTIVE},
        {"id": 5, "quest_type": TYPE_EMERGENCY, "status": STATUS_ACTIVE},
    ]

    collection = qm.get_active_quests(all_quests)

    assert len(collection.daily) == 1
    assert len(collection.main) == 1
    assert len(collection.instant) == 1
    assert len(collection.emergency) == 1


def test_get_active_quests_total():
    quests = [
        {"quest_type": TYPE_DAILY, "status": STATUS_ACTIVE},
        {"quest_type": TYPE_MAIN, "status": STATUS_ACTIVE},
    ]
    collection = qm.get_active_quests(quests)
    assert collection.to_dict()["total_active"] == 2
