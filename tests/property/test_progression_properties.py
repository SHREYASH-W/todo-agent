"""
Property-Based Tests for Progression Engine

Properties:
  1. Level Progression Through XP Accumulation (Requirements 1.1, 1.2, 1.4)
  2. Level Boundary Invariant (Requirement 1.5)
  3. Point Allocation Correctness (Requirements 1.3, 1.7, 3.3, 9.3, 9.4)
  4. Derived Stat Calculation (Requirements 3.5, 3.6, 3.7)
 17. Gold Balance Non-Negativity Invariant (Requirements 13.2, 13.3, 13.4)
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from src.engine.progression_engine import (
    ProgressionEngine,
    MAX_LEVEL,
    MIN_LEVEL,
    STAT_POINTS_PER_LEVEL,
    SKILL_POINTS_PER_LEVEL,
)

engine = ProgressionEngine()


# ──────────────────────────────────────────────────────────────────────────────
# Property 1: Level Progression Through XP Accumulation
# ──────────────────────────────────────────────────────────────────────────────


@given(
    level=st.integers(min_value=1, max_value=998),
    extra_xp=st.integers(min_value=0, max_value=50_000),
)
@settings(max_examples=200)
def test_level_progression_xp_accumulation(level: int, extra_xp: int):
    """
    Property 1: When a player accumulates XP >= threshold for next level,
    their level increments and XP resets relative to the new threshold.
    """
    threshold_next = engine.calculate_xp_requirement(level + 1)

    player = {
        "level": level,
        "xp": 0,
        "stat_points": 0,
        "skill_points": 0,
        "gold": 0,
        "rank": engine.get_rank_for_level(level),
        "vit_stat": 10,
        "int_stat": 10,
    }

    result = engine.award_xp(player, threshold_next + extra_xp)

    # Level must have incremented at least once
    assert result["leveled_up"] is True
    assert result["new_level"] >= level + 1

    # Level must stay within bounds
    assert MIN_LEVEL <= result["new_level"] <= MAX_LEVEL

    # XP to next level must be non-negative
    assert result["xp_to_next_level"] >= 0


# ──────────────────────────────────────────────────────────────────────────────
# Property 2: Level Boundary Invariant
# ──────────────────────────────────────────────────────────────────────────────


@given(
    level=st.integers(min_value=1, max_value=999),
    xp_award=st.integers(min_value=0, max_value=10_000_000),
)
@settings(max_examples=200)
def test_level_boundary_invariant(level: int, xp_award: int):
    """
    Property 2: Regardless of how much XP is awarded, level must always stay
    within [MIN_LEVEL, MAX_LEVEL].
    """
    player = {
        "level": level,
        "xp": 0,
        "stat_points": 0,
        "skill_points": 0,
        "gold": 0,
        "rank": engine.get_rank_for_level(level),
        "vit_stat": 10,
        "int_stat": 10,
    }

    result = engine.award_xp(player, xp_award)

    assert MIN_LEVEL <= result["new_level"] <= MAX_LEVEL
    assert player["level"] == result["new_level"]  # player dict updated in-place


# ──────────────────────────────────────────────────────────────────────────────
# Property 3: Stat Point Allocation Correctness
# ──────────────────────────────────────────────────────────────────────────────


@given(
    initial_points=st.integers(min_value=1, max_value=100),
    stat_name=st.sampled_from(
        ["str_stat", "int_stat", "agi_stat", "vit_stat", "sen_stat", "luk_stat"]
    ),
)
@settings(max_examples=200)
def test_stat_allocation_correctness(initial_points: int, stat_name: str):
    """
    Property 3: Allocating a stat point decrements available_points by 1,
    increments the target stat by 1, and available_points stays >= 0.
    """
    player = {
        "level": 10,
        "xp": 0,
        "stat_points": initial_points,
        "skill_points": 0,
        "gold": 0,
        "rank": "E",
        "str_stat": 10,
        "int_stat": 10,
        "agi_stat": 10,
        "vit_stat": 10,
        "sen_stat": 10,
        "luk_stat": 10,
    }
    before_stat = player[stat_name]
    before_points = player["stat_points"]

    success = engine.allocate_stat_point(player, stat_name)

    assert success is True
    assert player[stat_name] == before_stat + 1
    assert player["stat_points"] == before_points - 1
    assert player["stat_points"] >= 0


@given(
    stat_name=st.sampled_from(
        ["str_stat", "int_stat", "agi_stat", "vit_stat", "sen_stat", "luk_stat"]
    ),
)
@settings(max_examples=50)
def test_stat_allocation_no_points_fails(stat_name: str):
    """Allocation with zero points available must return False and not change stats."""
    player = {
        "level": 10,
        "xp": 0,
        "stat_points": 0,
        "skill_points": 0,
        "gold": 0,
        "rank": "E",
        "str_stat": 10,
        "int_stat": 10,
        "agi_stat": 10,
        "vit_stat": 10,
        "sen_stat": 10,
        "luk_stat": 10,
    }
    before = player[stat_name]

    success = engine.allocate_stat_point(player, stat_name)

    assert success is False
    assert player[stat_name] == before
    assert player["stat_points"] == 0


# ──────────────────────────────────────────────────────────────────────────────
# Property 4: Derived Stat Calculation
# ──────────────────────────────────────────────────────────────────────────────


@given(
    vit=st.integers(min_value=0, max_value=1000),
    int_stat=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=300)
def test_derived_stat_calculation(vit: int, int_stat: int):
    """
    Property 4: HP = 100 + (VIT * 10) and MP = 50 + (INT * 5) always hold.
    """
    player = {
        "level": 10,
        "xp": 0,
        "stat_points": 0,
        "skill_points": 0,
        "vit_stat": vit,
        "int_stat": int_stat,
    }
    derived = engine.calculate_derived_stats(player)

    assert derived["hp"] == 100 + (vit * 10)
    assert derived["mp"] == 50 + (int_stat * 5)
    assert player["hp"] == derived["hp"]  # Updated in-place
    assert player["mp"] == derived["mp"]


@given(
    vit=st.integers(min_value=1, max_value=500),
    int_stat=st.integers(min_value=1, max_value=500),
)
@settings(max_examples=100)
def test_derived_stats_recalculate_on_vit_int_change(vit: int, int_stat: int):
    """
    Property 4b: After allocating VIT or INT, derived stats are recalculated.
    """
    player = {
        "level": 10,
        "xp": 0,
        "stat_points": 5,
        "skill_points": 0,
        "str_stat": 10,
        "int_stat": int_stat,
        "agi_stat": 10,
        "vit_stat": vit,
        "sen_stat": 10,
        "luk_stat": 10,
        "rank": "E",
    }
    engine.calculate_derived_stats(player)
    old_hp = player["hp"]
    old_mp = player["mp"]

    engine.allocate_stat_point(player, "vit_stat")
    assert player["hp"] == old_hp + 10  # VIT increased by 1 → HP += 10

    engine.allocate_stat_point(player, "int_stat")
    assert player["mp"] == old_mp + 5   # INT increased by 1 → MP += 5


# ──────────────────────────────────────────────────────────────────────────────
# Property 17: Gold Balance Non-Negativity Invariant
# ──────────────────────────────────────────────────────────────────────────────


@given(
    initial_gold=st.integers(min_value=0, max_value=100_000),
    award_amount=st.integers(min_value=0, max_value=50_000),
    spend_amount=st.integers(min_value=0, max_value=150_000),
)
@settings(max_examples=300)
def test_gold_balance_non_negativity(
    initial_gold: int, award_amount: int, spend_amount: int
):
    """
    Property 17: Gold balance must never go negative.
    Spending more than available must be rejected; balance stays >= 0.
    """
    player = {"gold": initial_gold}

    engine.award_gold(player, award_amount)
    balance_after_award = player["gold"]
    assert balance_after_award >= 0
    assert balance_after_award == initial_gold + award_amount

    success = engine.spend_gold(player, spend_amount)
    final_balance = player["gold"]

    assert final_balance >= 0

    if spend_amount <= balance_after_award:
        assert success is True
        assert final_balance == balance_after_award - spend_amount
    else:
        assert success is False
        assert final_balance == balance_after_award  # Unchanged


@given(
    operations=st.lists(
        st.tuples(
            st.sampled_from(["award", "spend"]),
            st.integers(min_value=0, max_value=10_000),
        ),
        min_size=1,
        max_size=50,
    )
)
@settings(max_examples=100)
def test_gold_never_negative_under_arbitrary_operations(operations):
    """
    Property 17b: Under any sequence of award/spend operations,
    gold balance must never drop below 0.
    """
    player = {"gold": 0}

    for op, amount in operations:
        if op == "award":
            engine.award_gold(player, amount)
        else:
            engine.spend_gold(player, amount)
        assert player["gold"] >= 0


# ──────────────────────────────────────────────────────────────────────────────
# XP formula sanity check
# ──────────────────────────────────────────────────────────────────────────────


@given(level=st.integers(min_value=1, max_value=999))
@settings(max_examples=200)
def test_xp_requirement_monotonically_increasing(level: int):
    """XP required to reach a higher level must always be greater than for lower level."""
    if level < MAX_LEVEL:
        assert engine.calculate_xp_requirement(level + 1) > engine.calculate_xp_requirement(level)


@given(
    levels_gained=st.integers(min_value=1, max_value=10),
    start_level=st.integers(min_value=1, max_value=980),
)
@settings(max_examples=100)
def test_stat_and_skill_points_granted_on_level_up(levels_gained: int, start_level: int):
    """Each level-up grants exactly STAT_POINTS_PER_LEVEL stat points and 1 skill point."""
    assume(start_level + levels_gained <= MAX_LEVEL)

    # Calculate cumulative XP needed to reach start_level + levels_gained
    total_xp = sum(
        engine.calculate_xp_requirement(start_level + i)
        for i in range(1, levels_gained + 1)
    )

    player = {
        "level": start_level,
        "xp": 0,
        "stat_points": 0,
        "skill_points": 0,
        "gold": 0,
        "rank": engine.get_rank_for_level(start_level),
        "vit_stat": 10,
        "int_stat": 10,
    }

    result = engine.award_xp(player, total_xp)

    assert result["stat_points_granted"] == levels_gained * STAT_POINTS_PER_LEVEL
    assert result["skill_points_granted"] == levels_gained * SKILL_POINTS_PER_LEVEL
