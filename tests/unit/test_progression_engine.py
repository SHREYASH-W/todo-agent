"""
Unit tests for the Progression Engine.
Validates XP formula, rank advancement, stat allocation, and gold operations.
Requirements: 1.1-1.7, 2.1-2.8, 3.1-3.8, 13.1-13.7
"""

import pytest
from src.engine.progression_engine import (
    ProgressionEngine,
    MAX_LEVEL,
    MIN_LEVEL,
    RANK_THRESHOLDS,
    STAT_POINTS_PER_LEVEL,
    SKILL_POINTS_PER_LEVEL,
)

engine = ProgressionEngine()


def make_player(**kwargs):
    defaults = {
        "id": 1,
        "level": 1,
        "xp": 0,
        "rank": "E",
        "gold": 0,
        "stat_points": 0,
        "skill_points": 0,
        "str_stat": 10,
        "int_stat": 10,
        "agi_stat": 10,
        "vit_stat": 10,
        "sen_stat": 10,
        "luk_stat": 10,
    }
    defaults.update(kwargs)
    return defaults


# ─── XP Formula ────────────────────────────────────────────────────────────


def test_xp_requirement_level_1_is_zero():
    assert engine.calculate_xp_requirement(1) == 0


def test_xp_requirement_level_2():
    # 100 * 2^1.5 ≈ 283
    expected = int(100 * (2 ** 1.5))
    assert engine.calculate_xp_requirement(2) == expected


def test_xp_requirement_level_10():
    expected = int(100 * (10 ** 1.5))
    assert engine.calculate_xp_requirement(10) == expected


def test_xp_requirement_monotonically_increasing():
    for lvl in range(1, 100):
        assert engine.calculate_xp_requirement(lvl + 1) > engine.calculate_xp_requirement(lvl)


# ─── Award XP / Level Up ───────────────────────────────────────────────────


def test_award_xp_no_level_up():
    player = make_player(level=1, xp=0)
    threshold = engine.calculate_xp_requirement(2)
    result = engine.award_xp(player, threshold - 1)

    assert result["leveled_up"] is False
    assert result["new_level"] == 1
    assert result["new_xp"] == threshold - 1


def test_award_xp_exact_level_up():
    player = make_player(level=1, xp=0)
    threshold = engine.calculate_xp_requirement(2)
    result = engine.award_xp(player, threshold)

    assert result["leveled_up"] is True
    assert result["new_level"] == 2
    assert result["new_xp"] == 0  # Exactly consumed


def test_award_xp_grants_stat_and_skill_points():
    player = make_player(level=1, xp=0, stat_points=0, skill_points=0)
    threshold = engine.calculate_xp_requirement(2)
    result = engine.award_xp(player, threshold)

    assert player["stat_points"] == STAT_POINTS_PER_LEVEL
    assert player["skill_points"] == SKILL_POINTS_PER_LEVEL


def test_award_xp_multiple_level_ups():
    player = make_player(level=1, xp=0, stat_points=0, skill_points=0)
    # Enough XP for 3 levels
    total = sum(engine.calculate_xp_requirement(lvl) for lvl in range(2, 5))
    result = engine.award_xp(player, total)

    assert result["new_level"] == 4
    assert result["levels_gained"] == 3
    assert player["stat_points"] == 3 * STAT_POINTS_PER_LEVEL


def test_award_xp_negative_raises():
    player = make_player()
    with pytest.raises(ValueError):
        engine.award_xp(player, -1)


def test_award_xp_at_max_level_no_overflow():
    player = make_player(level=MAX_LEVEL, xp=0)
    result = engine.award_xp(player, 999_999_999)

    assert result["new_level"] == MAX_LEVEL


# ─── Ranks ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("level,expected_rank", [
    (1, "E"), (9, "E"),
    (10, "D"), (24, "D"),
    (25, "C"), (39, "C"),
    (40, "B"), (59, "B"),
    (60, "A"), (79, "A"),
    (80, "S"), (99, "S"),
    (100, "National"), (999, "National"),
])
def test_rank_for_level(level: int, expected_rank: str):
    assert engine.get_rank_for_level(level) == expected_rank


def test_check_rank_advancement_triggers_on_level_10():
    player = make_player(level=10, rank="E")
    new_rank = engine.check_rank_advancement(player)
    assert new_rank == "D"
    assert player["rank"] == "D"


def test_check_rank_advancement_no_change_same_rank():
    player = make_player(level=5, rank="E")
    result = engine.check_rank_advancement(player)
    assert result is None


# ─── Stat Allocation ───────────────────────────────────────────────────────


def test_allocate_stat_point_success():
    player = make_player(stat_points=3, str_stat=10)
    success = engine.allocate_stat_point(player, "str_stat")

    assert success is True
    assert player["str_stat"] == 11
    assert player["stat_points"] == 2


def test_allocate_stat_point_no_points():
    player = make_player(stat_points=0, str_stat=10)
    success = engine.allocate_stat_point(player, "str_stat")

    assert success is False
    assert player["str_stat"] == 10


def test_allocate_stat_point_invalid_stat():
    player = make_player(stat_points=5)
    success = engine.allocate_stat_point(player, "invalid_stat")
    assert success is False


def test_allocate_vit_updates_hp():
    player = make_player(stat_points=2, vit_stat=10)
    engine.calculate_derived_stats(player)
    old_hp = player["hp"]

    engine.allocate_stat_point(player, "vit_stat")

    assert player["hp"] == old_hp + 10  # VIT+1 → HP+10


def test_allocate_int_updates_mp():
    player = make_player(stat_points=2, int_stat=10)
    engine.calculate_derived_stats(player)
    old_mp = player["mp"]

    engine.allocate_stat_point(player, "int_stat")

    assert player["mp"] == old_mp + 5  # INT+1 → MP+5


# ─── Derived Stats ─────────────────────────────────────────────────────────


def test_derived_stats_base_values():
    player = make_player(vit_stat=10, int_stat=10)
    derived = engine.calculate_derived_stats(player)

    assert derived["hp"] == 200  # 100 + (10 * 10)
    assert derived["mp"] == 100  # 50 + (10 * 5)


def test_derived_stats_zero_vit_int():
    player = make_player(vit_stat=0, int_stat=0)
    derived = engine.calculate_derived_stats(player)

    assert derived["hp"] == 100
    assert derived["mp"] == 50


# ─── Gold ──────────────────────────────────────────────────────────────────


def test_award_gold_increases_balance():
    player = make_player(gold=100)
    new_balance = engine.award_gold(player, 50)
    assert new_balance == 150
    assert player["gold"] == 150


def test_spend_gold_success():
    player = make_player(gold=100)
    success = engine.spend_gold(player, 60)
    assert success is True
    assert player["gold"] == 40


def test_spend_gold_exact_amount():
    player = make_player(gold=50)
    success = engine.spend_gold(player, 50)
    assert success is True
    assert player["gold"] == 0


def test_spend_gold_insufficient():
    player = make_player(gold=30)
    success = engine.spend_gold(player, 50)
    assert success is False
    assert player["gold"] == 30  # Unchanged


def test_award_gold_negative_raises():
    player = make_player(gold=100)
    with pytest.raises(ValueError):
        engine.award_gold(player, -10)


def test_spend_gold_negative_raises():
    player = make_player(gold=100)
    with pytest.raises(ValueError):
        engine.spend_gold(player, -5)
