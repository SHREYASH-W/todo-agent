"""
Property-Based Tests for Skill, Achievement, Title, Inventory, and Module systems.

Properties:
 12. Skill Unlock Based on Level Threshold (Requirement 9.1)
 13. Passive Skill Bonus Application (Requirement 9.6)
 14. Achievement Unlock Based on Conditions (Requirement 10.1)
 15. Title Bonus Application Toggle (Requirements 11.3, 11.4)
 16. Inventory Item Addition and Removal (Requirements 12.2, 12.4, 12.5)
 18. Module Unlock Based on Rank (Requirements 14.1-14.7)
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from src.engine.skill_system import SkillSystem, MAX_SKILL_LEVEL
from src.engine.achievement_system import AchievementSystem, TitleSystem
from src.engine.inventory_system import InventorySystem, MAX_ITEMS_PER_CATEGORY
from src.engine.module_manager import (
    ModuleManager,
    MODULE_UNLOCK_REQUIREMENTS,
    RANK_ORDER,
    _rank_index,
)

skill_sys = SkillSystem()
achievement_sys = AchievementSystem()
title_sys = TitleSystem()
inventory_sys = InventorySystem()
module_mgr = ModuleManager()


# ──────────────────────────────────────────────────────────────────────────────
# Property 12: Skill Unlock Based on Level Threshold
# ──────────────────────────────────────────────────────────────────────────────


@given(
    player_level=st.integers(min_value=1, max_value=999),
    unlock_level=st.integers(min_value=1, max_value=999),
)
@settings(max_examples=500)
def test_skill_unlock_based_on_level_threshold(player_level: int, unlock_level: int):
    """
    Property 12: Skill unlocks if and only if player_level >= unlock_level.
    """
    result = skill_sys.can_unlock_skill(player_level, unlock_level)

    if player_level >= unlock_level:
        assert result is True
    else:
        assert result is False


@given(
    player_level=st.integers(min_value=1, max_value=999),
    unlock_level=st.integers(min_value=1, max_value=999),
)
@settings(max_examples=200)
def test_skill_unlock_creates_player_skill_record(player_level: int, unlock_level: int):
    """
    Property 12b: unlock_skill returns a PlayerSkill record when level requirement met,
    and None when not met.
    """
    player = {"id": 1, "level": player_level, "skill_points": 5}
    skill = {"id": 42, "name": "Test Skill", "unlock_level": unlock_level, "prerequisite_skill_id": None}

    result = skill_sys.unlock_skill(player, skill, [])

    if player_level >= unlock_level:
        assert result is not None
        assert result["skill_id"] == 42
        assert result["current_level"] == 1
    else:
        assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# Property 13: Passive Skill Bonus Application
# ──────────────────────────────────────────────────────────────────────────────


@given(
    task_focus_level=st.integers(min_value=0, max_value=MAX_SKILL_LEVEL),
    golden_touch_level=st.integers(min_value=0, max_value=MAX_SKILL_LEVEL),
)
@settings(max_examples=200)
def test_passive_skill_bonuses_applied_automatically(
    task_focus_level: int, golden_touch_level: int
):
    """
    Property 13: Passive bonuses are calculated from skill levels without activation.
    Task Focus: +5% XP per level; Golden Touch: +10% gold per level.
    """
    player = {"id": 1, "level": 20}
    skills = [
        {"id": 1, "name": "Task Focus", "skill_type": "passive"},
        {"id": 2, "name": "Golden Touch", "skill_type": "passive"},
    ]
    player_skills = []
    if task_focus_level > 0:
        player_skills.append({"skill_id": 1, "current_level": task_focus_level})
    if golden_touch_level > 0:
        player_skills.append({"skill_id": 2, "current_level": golden_touch_level})

    bonuses = skill_sys.apply_passive_bonuses(player, player_skills, skills)

    if task_focus_level > 0:
        assert bonuses.get("xp_gain_pct", 0) == 5 * task_focus_level
    else:
        assert bonuses.get("xp_gain_pct", 0) == 0

    if golden_touch_level > 0:
        assert bonuses.get("gold_reward_pct", 0) == 10 * golden_touch_level
    else:
        assert bonuses.get("gold_reward_pct", 0) == 0


@given(
    level=st.integers(min_value=1, max_value=MAX_SKILL_LEVEL),
)
@settings(max_examples=100)
def test_passive_bonuses_scale_with_skill_level(level: int):
    """Passive bonus magnitude scales linearly with skill level."""
    player = {"id": 1, "level": 50}
    skills = [{"id": 1, "name": "Task Focus", "skill_type": "passive"}]
    player_skills = [{"skill_id": 1, "current_level": level}]

    bonuses = skill_sys.apply_passive_bonuses(player, player_skills, skills)
    assert bonuses["xp_gain_pct"] == 5 * level


# ──────────────────────────────────────────────────────────────────────────────
# Property 14: Achievement Unlock Based on Conditions
# ──────────────────────────────────────────────────────────────────────────────


@given(
    player_level=st.integers(min_value=1, max_value=999),
    required_level=st.integers(min_value=1, max_value=999),
)
@settings(max_examples=300)
def test_achievement_unlock_level_condition(player_level: int, required_level: int):
    """
    Property 14: Achievement with level condition unlocks iff player_level >= required_level.
    """
    import json
    achievement = {
        "id": 1,
        "name": "Leveler",
        "condition_type": "level",
        "condition_value": json.dumps({"level": required_level}),
    }
    player = {"id": 1, "level": player_level}

    result = achievement_sys.check_achievement_unlock(player, achievement)

    if player_level >= required_level:
        assert result is True
    else:
        assert result is False


@given(
    total_quests=st.integers(min_value=0, max_value=1000),
    required_count=st.integers(min_value=1, max_value=1000),
)
@settings(max_examples=200)
def test_achievement_unlock_quest_count_condition(total_quests: int, required_count: int):
    """
    Property 14b: Achievement with quest_count condition unlocks iff total_quests >= required_count.
    """
    import json
    achievement = {
        "id": 2,
        "name": "Quester",
        "condition_type": "quest_count",
        "condition_value": json.dumps({"count": required_count}),
    }
    player = {"id": 1, "level": 10}
    stats = {"total_quests_completed": total_quests}

    result = achievement_sys.check_achievement_unlock(player, achievement, stats)

    if total_quests >= required_count:
        assert result is True
    else:
        assert result is False


# ──────────────────────────────────────────────────────────────────────────────
# Property 15: Title Bonus Application Toggle
# ──────────────────────────────────────────────────────────────────────────────


@given(
    str_bonus=st.integers(min_value=1, max_value=50),
    int_bonus=st.integers(min_value=1, max_value=50),
)
@settings(max_examples=300)
def test_title_bonus_equip_increases_stats(str_bonus: int, int_bonus: int):
    """
    Property 15: Equipping a title increases stats by the bonus values.
    """
    import json
    player = {
        "id": 1,
        "level": 20,
        "str_stat": 10,
        "int_stat": 10,
        "agi_stat": 10,
        "vit_stat": 10,
        "sen_stat": 10,
        "luk_stat": 10,
        "active_title_id": None,
    }
    title = {
        "id": 5,
        "name": "The Warrior",
        "stat_bonuses": json.dumps({"str_stat": str_bonus, "int_stat": int_bonus}),
    }

    before_str = player["str_stat"]
    before_int = player["int_stat"]

    success = title_sys.equip_title(player, title)
    assert success is True
    assert player["str_stat"] == before_str + str_bonus
    assert player["int_stat"] == before_int + int_bonus
    assert player["active_title_id"] == 5


@given(
    str_bonus=st.integers(min_value=1, max_value=50),
    int_bonus=st.integers(min_value=1, max_value=50),
)
@settings(max_examples=300)
def test_title_bonus_unequip_removes_stats(str_bonus: int, int_bonus: int):
    """
    Property 15b: Unequipping a title decreases stats back to original values.
    """
    import json
    original_str = 10
    original_int = 10
    player = {
        "id": 1,
        "level": 20,
        "str_stat": original_str + str_bonus,  # Already has bonus applied
        "int_stat": original_int + int_bonus,
        "agi_stat": 10,
        "vit_stat": 10,
        "sen_stat": 10,
        "luk_stat": 10,
        "active_title_id": 5,
    }
    title = {
        "id": 5,
        "name": "The Warrior",
        "stat_bonuses": json.dumps({"str_stat": str_bonus, "int_stat": int_bonus}),
    }

    success = title_sys.unequip_title(player, title)
    assert success is True
    assert player["str_stat"] == original_str
    assert player["int_stat"] == original_int
    assert player["active_title_id"] is None


@given(
    stat_bonus=st.integers(min_value=1, max_value=50),
)
@settings(max_examples=200)
def test_title_equip_then_unequip_returns_to_original(stat_bonus: int):
    """
    Property 15c: equip(title) then unequip(title) returns exact original stat values.
    """
    import json
    original_str = 15
    player = {
        "id": 1,
        "level": 20,
        "str_stat": original_str,
        "int_stat": 10,
        "agi_stat": 10,
        "vit_stat": 10,
        "sen_stat": 10,
        "luk_stat": 10,
        "active_title_id": None,
    }
    title = {
        "id": 7,
        "name": "Gladiator",
        "stat_bonuses": json.dumps({"str_stat": stat_bonus}),
    }

    title_sys.equip_title(player, title)
    title_sys.unequip_title(player, title)

    assert player["str_stat"] == original_str


# ──────────────────────────────────────────────────────────────────────────────
# Property 16: Inventory Item Addition and Removal
# ──────────────────────────────────────────────────────────────────────────────


@given(
    current_count=st.integers(min_value=0, max_value=MAX_ITEMS_PER_CATEGORY + 5),
    category=st.sampled_from(["template", "certificate", "consumable"]),
)
@settings(max_examples=300)
def test_inventory_addition_respects_capacity(current_count: int, category: str):
    """
    Property 16: Adding an item succeeds when count < MAX_ITEMS_PER_CATEGORY,
    fails when count >= MAX_ITEMS_PER_CATEGORY.
    """
    items = [
        {"id": i, "item_type": category, "name": f"Item {i}"}
        for i in range(current_count)
    ]
    item_data = {"name": "New Item", "item_type": category, "content": "test"}

    result = inventory_sys.add_item(player_id=1, item_data=item_data, current_items=items)

    if current_count < MAX_ITEMS_PER_CATEGORY:
        assert result is not None
        assert result["item_type"] == category
        assert result["name"] == "New Item"
    else:
        assert result is None


@given(
    n_items=st.integers(min_value=1, max_value=20),
    category=st.sampled_from(["template", "certificate", "consumable"]),
)
@settings(max_examples=200)
def test_inventory_removal_decreases_count(n_items: int, category: str):
    """
    Property 16b: Removing an existing item decreases count by exactly 1.
    """
    items = [
        {"id": i, "item_type": category, "name": f"Item {i}"}
        for i in range(n_items)
    ]
    before = len(items)
    target_id = items[0]["id"]

    success = inventory_sys.remove_item(target_id, items)

    assert success is True
    assert len(items) == before - 1
    assert all(i["id"] != target_id for i in items)


def test_inventory_removal_non_existent_item_fails():
    """
    Property 16c: Removing a non-existent item returns False.
    """
    items = [{"id": 1, "item_type": "consumable", "name": "Item 1"}]
    success = inventory_sys.remove_item(999, items)
    assert success is False


@given(
    n_items=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_inventory_category_count_consistent(n_items: int):
    """Count of items per category remains consistent after add/remove operations."""
    items = []
    for i in range(n_items):
        item = inventory_sys.add_item(
            player_id=1,
            item_data={"name": f"Template {i}", "item_type": "template", "content": ""},
            current_items=items,
        )
        if item:
            item["id"] = i
            items.append(item)

    count = inventory_sys.get_category_count(items, "template")
    assert count == len(items)


# ──────────────────────────────────────────────────────────────────────────────
# Property 18: Module Unlock Based on Rank
# ──────────────────────────────────────────────────────────────────────────────


@given(
    player_rank=st.sampled_from(RANK_ORDER),
)
@settings(max_examples=50)
def test_module_unlock_based_on_rank(player_rank: str):
    """
    Property 18: Available modules = all modules where unlock_rank <= player_rank.
    Verify cumulative unlock pattern: E→Career, D→+Skill, C→+Fitness, etc.
    """
    available = module_mgr.get_available_modules(player_rank)
    player_rank_idx = _rank_index(player_rank)

    for mod in available:
        required_rank_idx = _rank_index(mod["required_rank"])
        if mod["unlocked"]:
            assert required_rank_idx <= player_rank_idx
        else:
            assert required_rank_idx > player_rank_idx


@given(
    module_name=st.sampled_from(list(MODULE_UNLOCK_REQUIREMENTS.keys())),
    player_rank=st.sampled_from(RANK_ORDER),
)
@settings(max_examples=200)
def test_module_unlock_check_correct(module_name: str, player_rank: str):
    """
    Property 18b: check_module_unlock returns True iff player_rank >= required_rank.
    """
    required_rank = MODULE_UNLOCK_REQUIREMENTS[module_name]
    result = module_mgr.check_module_unlock(player_rank, module_name)

    if _rank_index(player_rank) >= _rank_index(required_rank):
        assert result is True
    else:
        assert result is False


def test_e_rank_only_career_hunter_available():
    """E-rank player only has Career Hunter unlocked."""
    available = module_mgr.get_available_modules("E")
    unlocked = [m for m in available if m["unlocked"]]
    assert len(unlocked) == 1
    assert unlocked[0]["name"] == "career_hunter"


def test_s_rank_all_modules_available():
    """S-rank player has all 6 modules unlocked."""
    available = module_mgr.get_available_modules("S")
    unlocked = [m for m in available if m["unlocked"]]
    assert len(unlocked) == 6


def test_rank_progression_modules():
    """Each rank step unlocks exactly one new module."""
    previous_count = 0
    # Rank progression: E→D→C→B→A→S
    for rank in ["E", "D", "C", "B", "A", "S"]:
        available = module_mgr.get_available_modules(rank)
        unlocked_count = sum(1 for m in available if m["unlocked"])
        assert unlocked_count == previous_count + 1
        previous_count = unlocked_count
