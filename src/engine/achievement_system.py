"""
Achievement and Title Systems for LifeHunter System

Requirements: 10.1-10.7, 11.1-11.7
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AchievementSystem:
    """Manages achievement unlocking and stat bonus application."""

    def check_achievement_unlock(
        self,
        player: Dict[str, Any],
        achievement: Dict[str, Any],
        player_stats: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Evaluate whether a player meets an achievement's unlock conditions.

        Requirement 10.1.

        Args:
            player: Player data dict
            achievement: Achievement data dict
            player_stats: Optional extended stats (quest_count, streak, etc.)

        Returns:
            bool: True if conditions are met
        """
        condition_type = achievement.get("condition_type", "")
        condition_value_str = achievement.get("condition_value", "{}")

        try:
            condition = json.loads(condition_value_str) if isinstance(condition_value_str, str) else condition_value_str
        except (json.JSONDecodeError, TypeError):
            condition = {}

        stats = player_stats or {}

        if condition_type == "level":
            return player.get("level", 1) >= condition.get("level", 0)

        elif condition_type == "quest_count":
            return stats.get("total_quests_completed", 0) >= condition.get("count", 0)

        elif condition_type == "stat":
            stat_name = condition.get("stat_name", "")
            stat_value = condition.get("value", 0)
            return player.get(stat_name, 0) >= stat_value

        elif condition_type == "custom":
            custom_type = condition.get("type", "")

            if custom_type == "daily_streak":
                return stats.get("daily_streak", 0) >= condition.get("days", 0)
            elif custom_type == "applications":
                return stats.get("total_applications", 0) >= condition.get("count", 0)
            elif custom_type == "networking_quests":
                return stats.get("networking_quests_completed", 0) >= condition.get("count", 0)
            elif custom_type == "instant_dungeon_perfect":
                return stats.get("instant_dungeons_perfect", 0) >= condition.get("count", 0)
            elif custom_type == "perfect_matches":
                return stats.get("perfect_job_matches", 0) >= condition.get("count", 0)

        return False

    def unlock_achievement(
        self,
        player: Dict[str, Any],
        achievement: Dict[str, Any],
        unlocked_achievement_ids: List[int],
    ) -> Optional[Dict[str, Any]]:
        """
        Unlock an achievement and apply any permanent stat bonuses.

        Requirements 10.1, 10.5.

        Args:
            player: Player data dict (may be updated with stat bonuses)
            achievement: Achievement data dict
            unlocked_achievement_ids: List of already-unlocked achievement IDs

        Returns:
            Dict: PlayerAchievement record, or None if already unlocked
        """
        achievement_id = achievement.get("id")
        if achievement_id in unlocked_achievement_ids:
            return None

        # Apply stat bonuses permanently
        stat_bonus_str = achievement.get("stat_bonus", "{}")
        try:
            bonuses = json.loads(stat_bonus_str) if isinstance(stat_bonus_str, str) else stat_bonus_str or {}
        except (json.JSONDecodeError, TypeError):
            bonuses = {}

        self._apply_stat_bonuses(player, bonuses)

        player_achievement = {
            "player_id": player.get("id"),
            "achievement_id": achievement_id,
            "unlocked_at": datetime.utcnow(),
        }

        logger.info(
            f"Achievement unlocked: '{achievement.get('name')}' "
            f"(rarity={achievement.get('rarity')}) for player {player.get('id')}"
        )
        return player_achievement

    def _apply_stat_bonuses(self, player: Dict[str, Any], bonuses: Dict[str, Any]):
        """Apply achievement stat bonuses to a player dict."""
        stat_map = {
            "str_stat": "str_stat",
            "int_stat": "int_stat",
            "agi_stat": "agi_stat",
            "vit_stat": "vit_stat",
            "sen_stat": "sen_stat",
            "luk_stat": "luk_stat",
        }

        for key, value in bonuses.items():
            if key in stat_map:
                player[key] = player.get(key, 10) + int(value)
            elif key == "all_stats":
                for stat in stat_map:
                    player[stat] = player.get(stat, 10) + int(value)
            elif key == "xp_bonus":
                player["xp"] = player.get("xp", 0) + int(value)
            elif key == "gold_bonus":
                player["gold"] = player.get("gold", 0) + int(value)
            # xp_multiplier and other non-stat bonuses are tracked externally

    def get_completion_percentage(
        self,
        total_achievements: int,
        unlocked_count: int,
    ) -> float:
        """
        Calculate achievement completion percentage.

        Requirement 10.4.
        """
        if total_achievements <= 0:
            return 0.0
        return round((unlocked_count / total_achievements) * 100, 1)


class TitleSystem:
    """Manages title unlocking, equipping, and stat bonus toggling."""

    def unlock_title(
        self,
        player: Dict[str, Any],
        title: Dict[str, Any],
        unlocked_title_ids: List[int],
    ) -> Optional[Dict[str, Any]]:
        """
        Add a title to the player's collection.

        Requirement 11.1.

        Returns:
            Dict: PlayerTitle record, or None if already unlocked
        """
        title_id = title.get("id")
        if title_id in unlocked_title_ids:
            return None

        player_title = {
            "player_id": player.get("id"),
            "title_id": title_id,
            "unlocked_at": datetime.utcnow(),
        }
        logger.info(f"Title unlocked: '{title.get('name')}' for player {player.get('id')}")
        return player_title

    def equip_title(
        self,
        player: Dict[str, Any],
        title: Dict[str, Any],
    ) -> bool:
        """
        Equip a title and apply its stat bonuses.

        Requirements 11.2, 11.3.

        Args:
            player: Player data dict (updated in-place)
            title: Title data dict

        Returns:
            bool: True if equipped successfully
        """
        # Remove old title bonuses first
        old_title_id = player.get("active_title_id")
        if old_title_id == title.get("id"):
            return True  # Already equipped

        title_id = title.get("id")
        bonuses = self._parse_bonuses(title.get("stat_bonuses", "{}"))
        self._apply_title_bonuses(player, bonuses, add=True)
        player["active_title_id"] = title_id

        logger.info(f"Title equipped: '{title.get('name')}' for player {player.get('id')}")
        return True

    def unequip_title(
        self,
        player: Dict[str, Any],
        title: Dict[str, Any],
    ) -> bool:
        """
        Unequip the active title and remove its stat bonuses.

        Requirements 11.4.

        Returns:
            bool: True if unequipped successfully
        """
        if player.get("active_title_id") != title.get("id"):
            return False

        bonuses = self._parse_bonuses(title.get("stat_bonuses", "{}"))
        self._apply_title_bonuses(player, bonuses, add=False)
        player["active_title_id"] = None

        logger.info(f"Title unequipped: '{title.get('name')}' for player {player.get('id')}")
        return True

    def _parse_bonuses(self, bonuses_str) -> Dict[str, Any]:
        try:
            return json.loads(bonuses_str) if isinstance(bonuses_str, str) else bonuses_str or {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def _apply_title_bonuses(
        self,
        player: Dict[str, Any],
        bonuses: Dict[str, Any],
        add: bool,
    ):
        """Apply or remove title stat bonuses (flat values only for base stats)."""
        sign = 1 if add else -1
        stat_keys = {"str_stat", "int_stat", "agi_stat", "vit_stat", "sen_stat", "luk_stat"}

        for key, value in bonuses.items():
            if key in stat_keys:
                player[key] = player.get(key, 10) + sign * int(value)
            elif key == "all_stats":
                for stat in stat_keys:
                    player[stat] = player.get(stat, 10) + sign * int(value)
            # Percentage bonuses (xp_gain, gold_gain, etc.) tracked in progression engine
