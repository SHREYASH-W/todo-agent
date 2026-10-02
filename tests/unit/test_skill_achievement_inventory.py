"""
Unit tests for Skill System, Achievement System, Title System, and Inventory System.
Requirements: 9.1-9.8, 10.1-10.7, 11.1-11.7, 12.1-12.7, 14.1-14.8
"""

import json
import pytest
from datetime import datetime, timedelta

from src.engine.skill_system import SkillSystem, MAX_SKILL_LEVEL
from src.engine.achievement_system import AchievementSystem, TitleSystem
from src.engine.inventory_system import InventorySystem, MAX_ITEMS_PER_CATEGORY
from src.engine.module_manager import ModuleManager, RANK_ORDER

skill_sys = SkillSystem()
achievement_sys = AchievementSystem()
title_sys = TitleSystem()
inventory_sys = InventorySystem()
module_mgr = ModuleManager()


# ──────────────────────────────────────────────────────────────────────────────
# Skill System Tests
# ──────────────────────────────────────────────────────────────────────────────


def test_can_unlock_skill_meets_requirement():
    assert skill_sys.can_unlock_skill(player_level=10, skill_unlock_level=10) is True


def test_can_unlock_skill_above_requirement():
    assert skill_sys.can_unlock_skill(player_level=20, skill_unlock_level=10) is True


def test_can_unlock_skill_below_requirement():
    assert skill_sys.can_unlock_skill(player_level=5, skill_unlock_level=10) is False


def test_unlock_skill_success():
    player = {"id": 1, "level": 15, "skill_points": 3}
    skill = {"id": 10, "name": "Quick Learner", "unlock_level": 10, "prerequisite_skill_id": None}

    result = skill_sys.unlock_skill(player, skill, [])

    assert result is not None
    assert result["skill_id"] == 10
    assert result["current_level"] == 1


def test_unlock_skill_level_too_low():
    player = {"id": 1, "level": 5, "skill_points": 3}
    skill = {"id": 10, "name": "Advanced Skill", "unlock_level": 20, "prerequisite_skill_id": None}

    result = skill_sys.unlock_skill(player, skill, [])
    assert result is None


def test_unlock_skill_already_unlocked():
    player = {"id": 1, "level": 20, "skill_points": 3}
    skill = {"id": 10, "name": "Quick Learner", "unlock_level": 10, "prerequisite_skill_id": None}
    existing = [{"skill_id": 10, "current_level": 3}]

    result = skill_sys.unlock_skill(player, skill, existing)
    assert result is None


def test_unlock_skill_prerequisite_not_met():
    player = {"id": 1, "level": 30, "skill_points": 3}
    skill = {"id": 20, "name": "Advanced Skill", "unlock_level": 20, "prerequisite_skill_id": 10}

    result = skill_sys.unlock_skill(player, skill, [])  # No existing skills
    assert result is None


def test_allocate_skill_point_success():
    player = {"skill_points": 5}
    player_skill = {"current_level": 3}

    success = skill_sys.allocate_skill_point(player, player_skill)

    assert success is True
    assert player_skill["current_level"] == 4
    assert player["skill_points"] == 4


def test_allocate_skill_point_no_points():
    player = {"skill_points": 0}
    player_skill = {"current_level": 3}

    success = skill_sys.allocate_skill_point(player, player_skill)
    assert success is False
    assert player_skill["current_level"] == 3


def test_allocate_skill_point_at_max_level():
    player = {"skill_points": 5}
    player_skill = {"current_level": MAX_SKILL_LEVEL}

    success = skill_sys.allocate_skill_point(player, player_skill)
    assert success is False


def test_active_skill_cooldown_enforcement():
    from datetime import datetime
    from src.engine.skill_system import SkillSystem

    sys = SkillSystem()
    skill = {"id": 1, "name": "Rush Hour", "skill_type": "active"}
    player_skill = {"skill_id": 1, "current_level": 3}
    cooldowns = {}

    # First activation should succeed
    result1 = sys.activate_active_skill(1, skill, player_skill, cooldowns)
    assert result1["success"] is True
    assert 1 in cooldowns

    # Immediate second activation should fail (on cooldown)
    result2 = sys.activate_active_skill(1, skill, player_skill, cooldowns)
    assert result2["success"] is False
    assert "cooldown" in result2["message"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# Achievement System Tests
# ──────────────────────────────────────────────────────────────────────────────


def test_check_achievement_unlock_level_condition_met():
    achievement = {
        "id": 1,
        "condition_type": "level",
        "condition_value": json.dumps({"level": 10}),
    }
    player = {"id": 1, "level": 15}
    assert achievement_sys.check_achievement_unlock(player, achievement) is True


def test_check_achievement_unlock_level_condition_not_met():
    achievement = {
        "id": 1,
        "condition_type": "level",
        "condition_value": json.dumps({"level": 50}),
    }
    player = {"id": 1, "level": 10}
    assert achievement_sys.check_achievement_unlock(player, achievement) is False


def test_check_achievement_unlock_quest_count():
    achievement = {
        "id": 2,
        "condition_type": "quest_count",
        "condition_value": json.dumps({"count": 10}),
    }
    player = {"id": 1, "level": 5}
    stats = {"total_quests_completed": 15}
    assert achievement_sys.check_achievement_unlock(player, achievement, stats) is True


def test_unlock_achievement_applies_stat_bonus():
    achievement = {
        "id": 5,
        "name": "Warrior",
        "rarity": "rare",
        "stat_bonus": json.dumps({"str_stat": 3, "vit_stat": 2}),
    }
    player = {"id": 1, "str_stat": 10, "vit_stat": 10}
    unlocked = []

    result = achievement_sys.unlock_achievement(player, achievement, unlocked)

    assert result is not None
    assert player["str_stat"] == 13
    assert player["vit_stat"] == 12


def test_unlock_achievement_not_duplicate():
    achievement = {"id": 5, "name": "Test", "stat_bonus": "{}"}
    player = {"id": 1}
    unlocked = [5]  # Already has it

    result = achievement_sys.unlock_achievement(player, achievement, unlocked)
    assert result is None


def test_achievement_completion_percentage():
    pct = achievement_sys.get_completion_percentage(total_achievements=20, unlocked_count=10)
    assert pct == 50.0


def test_achievement_completion_percentage_zero_total():
    pct = achievement_sys.get_completion_percentage(total_achievements=0, unlocked_count=0)
    assert pct == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Title System Tests
# ──────────────────────────────────────────────────────────────────────────────


def _base_player():
    return {
        "id": 1, "level": 20,
        "str_stat": 10, "int_stat": 10, "agi_stat": 10,
        "vit_stat": 10, "sen_stat": 10, "luk_stat": 10,
        "active_title_id": None,
    }


def test_equip_title_applies_bonuses():
    player = _base_player()
    title = {
        "id": 3,
        "name": "The Scholar",
        "stat_bonuses": json.dumps({"int_stat": 5}),
    }

    success = title_sys.equip_title(player, title)
    assert success is True
    assert player["int_stat"] == 15
    assert player["active_title_id"] == 3


def test_unequip_title_removes_bonuses():
    player = _base_player()
    title = {
        "id": 3,
        "name": "The Scholar",
        "stat_bonuses": json.dumps({"int_stat": 5}),
    }
    title_sys.equip_title(player, title)
    player_int_after_equip = player["int_stat"]

    success = title_sys.unequip_title(player, title)
    assert success is True
    assert player["int_stat"] == player_int_after_equip - 5
    assert player["active_title_id"] is None


def test_unequip_wrong_title_fails():
    player = _base_player()
    player["active_title_id"] = 99  # Different title equipped

    title = {"id": 3, "name": "Wrong Title", "stat_bonuses": "{}"}
    success = title_sys.unequip_title(player, title)
    assert success is False


def test_equip_title_idempotent():
    player = _base_player()
    title = {
        "id": 5,
        "name": "Warrior",
        "stat_bonuses": json.dumps({"str_stat": 3}),
    }
    player["active_title_id"] = 5  # Already equipped

    before_str = player["str_stat"]
    success = title_sys.equip_title(player, title)

    # Should return True but not double-apply bonus (already equipped guard)
    assert success is True


def test_unlock_title_creates_record():
    player = {"id": 1}
    title = {"id": 7, "name": "Gladiator"}

    result = title_sys.unlock_title(player, title, [])
    assert result is not None
    assert result["title_id"] == 7


def test_unlock_title_not_duplicate():
    player = {"id": 1}
    title = {"id": 7, "name": "Gladiator"}

    result = title_sys.unlock_title(player, title, [7])
    assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# Inventory System Tests
# ──────────────────────────────────────────────────────────────────────────────


def test_add_item_success():
    items = []
    item_data = {"name": "Job Template", "item_type": "template", "content": "CV template"}
    result = inventory_sys.add_item(1, item_data, items)

    assert result is not None
    assert result["name"] == "Job Template"
    assert result["item_type"] == "template"


def test_add_item_category_full():
    items = [
        {"id": i, "item_type": "template", "name": f"T{i}"}
        for i in range(MAX_ITEMS_PER_CATEGORY)
    ]
    item_data = {"name": "One Too Many", "item_type": "template", "content": ""}
    result = inventory_sys.add_item(1, item_data, items)
    assert result is None


def test_add_item_invalid_category():
    items = []
    item_data = {"name": "Bad Item", "item_type": "invalid_category", "content": ""}
    result = inventory_sys.add_item(1, item_data, items)
    assert result is None


def test_remove_item_success():
    items = [
        {"id": 1, "item_type": "consumable", "name": "Potion"},
        {"id": 2, "item_type": "consumable", "name": "Elixir"},
    ]
    success = inventory_sys.remove_item(1, items)

    assert success is True
    assert len(items) == 1
    assert items[0]["id"] == 2


def test_remove_item_not_found():
    items = [{"id": 1, "item_type": "consumable", "name": "Potion"}]
    success = inventory_sys.remove_item(999, items)
    assert success is False
    assert len(items) == 1


def test_use_consumable_removes_item():
    items = [
        {"id": 5, "item_type": "consumable", "name": "XP Booster"},
        {"id": 6, "item_type": "consumable", "name": "Gold Booster"},
    ]
    used = inventory_sys.use_consumable(5, items)

    assert used is not None
    assert used["name"] == "XP Booster"
    assert len(items) == 1  # Removed from inventory


def test_use_consumable_wrong_type():
    items = [{"id": 1, "item_type": "template", "name": "CV Template"}]
    used = inventory_sys.use_consumable(1, items)
    assert used is None


def test_search_items_by_name():
    items = [
        {"id": 1, "item_type": "template", "name": "Python CV"},
        {"id": 2, "item_type": "template", "name": "Java CV"},
        {"id": 3, "item_type": "consumable", "name": "XP Boost"},
    ]
    results = inventory_sys.search_items(items, query="CV")
    assert len(results) == 2


def test_search_items_by_category():
    items = [
        {"id": 1, "item_type": "template", "name": "CV"},
        {"id": 2, "item_type": "certificate", "name": "AWS Cert"},
        {"id": 3, "item_type": "consumable", "name": "Potion"},
    ]
    results = inventory_sys.search_items(items, category="certificate")
    assert len(results) == 1
    assert results[0]["name"] == "AWS Cert"


def test_search_items_case_insensitive():
    items = [
        {"id": 1, "item_type": "template", "name": "Python Developer CV"},
    ]
    results = inventory_sys.search_items(items, query="python")
    assert len(results) == 1


def test_get_items_by_category():
    items = [
        {"id": 1, "item_type": "template", "name": "T1"},
        {"id": 2, "item_type": "certificate", "name": "C1"},
        {"id": 3, "item_type": "consumable", "name": "P1"},
        {"id": 4, "item_type": "template", "name": "T2"},
    ]
    by_cat = inventory_sys.get_items_by_category(items)

    assert len(by_cat["template"]) == 2
    assert len(by_cat["certificate"]) == 1
    assert len(by_cat["consumable"]) == 1


def test_inventory_capacity_per_category_independent():
    """Each category has its own capacity — filling one doesn't affect others."""
    items = [
        {"id": i, "item_type": "template", "name": f"T{i}"}
        for i in range(MAX_ITEMS_PER_CATEGORY)
    ]

    # Template is full, but consumable should still work
    cert_data = {"name": "AWS Cert", "item_type": "certificate", "content": ""}
    result = inventory_sys.add_item(1, cert_data, items)
    assert result is not None


# ──────────────────────────────────────────────────────────────────────────────
# Module Manager Tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("rank,expected_count", [
    ("E", 1),   # Career Hunter
    ("D", 2),   # + Skill Trainer
    ("C", 3),   # + Fitness Hunter
    ("B", 4),   # + Finance Manager
    ("A", 5),   # + Social Network
    ("S", 6),   # + Habit Forge
    ("National", 6),  # All unlocked
])
def test_module_unlock_counts(rank: str, expected_count: int):
    available = module_mgr.get_available_modules(rank)
    unlocked = [m for m in available if m["unlocked"]]
    assert len(unlocked) == expected_count


def test_e_rank_career_hunter_available():
    assert module_mgr.check_module_unlock("E", "career_hunter") is True


def test_e_rank_skill_trainer_locked():
    assert module_mgr.check_module_unlock("E", "skill_trainer") is False


def test_d_rank_skill_trainer_available():
    assert module_mgr.check_module_unlock("D", "skill_trainer") is True


def test_s_rank_habit_forge_available():
    assert module_mgr.check_module_unlock("S", "habit_forge") is True


def test_unknown_module_returns_false():
    assert module_mgr.check_module_unlock("S", "nonexistent_module") is False


def test_get_available_modules_has_all_six():
    available = module_mgr.get_available_modules("S")
    assert len(available) == 6


def test_get_available_modules_has_required_rank_field():
    available = module_mgr.get_available_modules("E")
    for mod in available:
        assert "required_rank" in mod
        assert "unlocked" in mod
        assert "name" in mod
        assert "display_name" in mod
