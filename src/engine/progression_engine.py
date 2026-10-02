"""
Progression Engine for LifeHunter System

Manages XP, levels, ranks, stat allocation, skill progression, and gold currency.

Key algorithms:
- XP Formula: xp_required = 100 * (level^1.5)
- HP Formula: HP = 100 + (VIT * 10)
- MP Formula: MP = 50 + (INT * 5)
- Rank Thresholds: E(1), D(10), C(25), B(40), A(60), S(80), National(100)

Requirements: 1.1-1.7, 2.1-2.8, 3.1-3.8, 9.1-9.8, 13.1-13.7
"""

import logging
import math
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Rank progression thresholds (level -> rank)
RANK_THRESHOLDS = {
    1: "E",
    10: "D",
    25: "C",
    40: "B",
    60: "A",
    80: "S",
    100: "National",
}

RANK_ORDER = ["E", "D", "C", "B", "A", "S", "National"]

# Stat points granted per level up
STAT_POINTS_PER_LEVEL = 5
# Skill points granted per level up
SKILL_POINTS_PER_LEVEL = 1
# Level boundaries
MIN_LEVEL = 1
MAX_LEVEL = 999


class ProgressionEngine:
    """
    Core engine for player progression in LifeHunter.

    All methods operate on in-memory player data dicts. Persistence is handled
    by the caller (DatabaseManager or SQLAlchemy session).
    """

    # ─── XP & Level ────────────────────────────────────────────────────────

    def calculate_xp_requirement(self, level: int) -> int:
        """
        Calculate total XP required to reach the given level.

        Formula: xp_required = 100 * (level ^ 1.5)  [Requirement 1.4]

        Args:
            level: Target level (1-999)

        Returns:
            int: XP required to reach this level
        """
        if level <= MIN_LEVEL:
            return 0
        return int(100 * (level ** 1.5))

    def award_xp(self, player: Dict[str, Any], xp_amount: int) -> Dict[str, Any]:
        """
        Award XP to a player and handle level-up if threshold reached.

        Requirements 1.1, 1.2, 1.3, 1.4, 1.5.

        Args:
            player: Player data dict with keys: level, xp, stat_points, skill_points
            xp_amount: Amount of XP to award (must be >= 0)

        Returns:
            dict: Result with keys: leveled_up (bool), new_level (int),
                  new_xp (int), levels_gained (int), rank_change (str|None),
                  stat_points_granted (int), skill_points_granted (int)
        """
        if xp_amount < 0:
            raise ValueError("XP amount cannot be negative")

        current_level = player.get("level", 1)
        current_xp = player.get("xp", 0) + xp_amount
        levels_gained = 0
        rank_change = None

        # Process level-ups
        while True:
            if current_level >= MAX_LEVEL:
                break
            threshold = self.calculate_xp_requirement(current_level + 1)
            if current_xp >= threshold:
                current_xp -= threshold
                current_level += 1
                levels_gained += 1
            else:
                break

        # Clamp level
        current_level = max(MIN_LEVEL, min(MAX_LEVEL, current_level))

        # Grant points for each level gained
        stat_points = player.get("stat_points", 0) + levels_gained * STAT_POINTS_PER_LEVEL
        skill_points = player.get("skill_points", 0) + levels_gained * SKILL_POINTS_PER_LEVEL

        # Check rank advancement
        old_rank = player.get("rank", "E")
        new_rank = self.get_rank_for_level(current_level)
        if new_rank != old_rank:
            rank_change = new_rank

        # Update player dict in-place
        player["level"] = current_level
        player["xp"] = current_xp
        player["stat_points"] = stat_points
        player["skill_points"] = skill_points
        if rank_change:
            player["rank"] = new_rank

        # Recalculate derived stats after level changes
        self.calculate_derived_stats(player)

        logger.info(
            f"XP awarded: +{xp_amount} XP, "
            f"level={current_level}, leveled_up={levels_gained > 0}"
        )

        return {
            "leveled_up": levels_gained > 0,
            "new_level": current_level,
            "new_xp": current_xp,
            "levels_gained": levels_gained,
            "rank_change": rank_change,
            "stat_points_granted": levels_gained * STAT_POINTS_PER_LEVEL,
            "skill_points_granted": levels_gained * SKILL_POINTS_PER_LEVEL,
            "xp_to_next_level": self.calculate_xp_requirement(current_level + 1) - current_xp,
        }

    # ─── Ranks ─────────────────────────────────────────────────────────────

    def get_rank_for_level(self, level: int) -> str:
        """
        Get the rank corresponding to a given level.

        Requirements 2.1-2.6.

        Args:
            level: Player level (1-999)

        Returns:
            str: Rank string ('E', 'D', 'C', 'B', 'A', 'S', 'National')
        """
        rank = "E"
        for threshold, r in sorted(RANK_THRESHOLDS.items()):
            if level >= threshold:
                rank = r
        return rank

    def check_rank_advancement(self, player: Dict[str, Any]) -> Optional[str]:
        """
        Check if a player qualifies for rank promotion.

        Requirement 2.7.

        Args:
            player: Player data dict with keys: level, rank

        Returns:
            str: New rank if promotion occurred, None otherwise
        """
        current_level = player.get("level", 1)
        current_rank = player.get("rank", "E")
        expected_rank = self.get_rank_for_level(current_level)

        if expected_rank != current_rank:
            logger.info(f"Rank advancement: {current_rank} -> {expected_rank}")
            player["rank"] = expected_rank
            return expected_rank
        return None

    # ─── Stats ─────────────────────────────────────────────────────────────

    def calculate_derived_stats(self, player: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate HP and MP from base stats.

        HP = 100 + (VIT * 10)  [Requirement 3.6]
        MP = 50 + (INT * 5)    [Requirement 3.7]

        Args:
            player: Player data dict (updated in-place)

        Returns:
            dict: {'hp': int, 'mp': int}
        """
        vit = player.get("vit_stat", 10)
        int_stat = player.get("int_stat", 10)

        hp = 100 + (vit * 10)
        mp = 50 + (int_stat * 5)

        player["hp"] = hp
        player["mp"] = mp

        return {"hp": hp, "mp": mp}

    def allocate_stat_point(self, player: Dict[str, Any], stat_name: str) -> bool:
        """
        Allocate one stat point to a specified attribute.

        Requirements 1.3, 1.6, 1.7, 3.3.

        Args:
            player: Player data dict
            stat_name: One of 'str_stat', 'int_stat', 'agi_stat',
                       'vit_stat', 'sen_stat', 'luk_stat'

        Returns:
            bool: True if allocation succeeded, False if no points available
                  or invalid stat name
        """
        valid_stats = {"str_stat", "int_stat", "agi_stat", "vit_stat", "sen_stat", "luk_stat"}

        if stat_name not in valid_stats:
            logger.warning(f"Invalid stat name: {stat_name}")
            return False

        available = player.get("stat_points", 0)
        if available <= 0:
            logger.warning("No stat points available for allocation")
            return False

        player[stat_name] = player.get(stat_name, 10) + 1
        player["stat_points"] = available - 1

        # Recalculate derived stats if VIT or INT changed
        if stat_name in {"vit_stat", "int_stat"}:
            self.calculate_derived_stats(player)

        logger.info(f"Stat point allocated to {stat_name}: now {player[stat_name]}")
        return True

    def get_player_stats(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve current player statistics including derived stats.

        Requirement 3.1-3.8.

        Args:
            player: Player data dict

        Returns:
            dict: Complete player stats snapshot
        """
        # Ensure derived stats are current
        self.calculate_derived_stats(player)

        return {
            "level": player.get("level", 1),
            "xp": player.get("xp", 0),
            "rank": player.get("rank", "E"),
            "gold": player.get("gold", 0),
            "hp": player.get("hp", 200),
            "mp": player.get("mp", 100),
            "str_stat": player.get("str_stat", 10),
            "int_stat": player.get("int_stat", 10),
            "agi_stat": player.get("agi_stat", 10),
            "vit_stat": player.get("vit_stat", 10),
            "sen_stat": player.get("sen_stat", 10),
            "luk_stat": player.get("luk_stat", 10),
            "stat_points": player.get("stat_points", 0),
            "skill_points": player.get("skill_points", 0),
            "xp_to_next_level": (
                self.calculate_xp_requirement(player.get("level", 1) + 1)
                - player.get("xp", 0)
            ),
        }

    # ─── Skills ────────────────────────────────────────────────────────────

    def allocate_skill_point(
        self,
        player: Dict[str, Any],
        player_skill: Dict[str, Any],
        skill_max_level: int = 10,
    ) -> bool:
        """
        Allocate one skill point to a specific skill.

        Requirements 9.3, 9.4, 9.5.

        Args:
            player: Player data dict
            player_skill: PlayerSkill data dict with 'current_level'
            skill_max_level: Maximum level for this skill (default 10)

        Returns:
            bool: True if allocation succeeded
        """
        available = player.get("skill_points", 0)
        if available <= 0:
            logger.warning("No skill points available for allocation")
            return False

        current = player_skill.get("current_level", 0)
        if current >= skill_max_level:
            logger.warning(f"Skill already at max level ({skill_max_level})")
            return False

        player_skill["current_level"] = current + 1
        player["skill_points"] = available - 1
        logger.info(f"Skill point allocated: skill level now {player_skill['current_level']}")
        return True

    # ─── Gold ──────────────────────────────────────────────────────────────

    def award_gold(self, player: Dict[str, Any], amount: int) -> int:
        """
        Award gold to a player.

        Requirement 13.1, 13.2.

        Args:
            player: Player data dict
            amount: Gold amount to award (must be >= 0)

        Returns:
            int: New gold balance
        """
        if amount < 0:
            raise ValueError("Gold amount cannot be negative")
        player["gold"] = player.get("gold", 0) + amount
        logger.info(f"Gold awarded: +{amount}, balance={player['gold']}")
        return player["gold"]

    def spend_gold(self, player: Dict[str, Any], amount: int) -> bool:
        """
        Deduct gold from a player's balance.

        Requirements 13.3, 13.4.

        Args:
            player: Player data dict
            amount: Gold to spend (must be >= 0)

        Returns:
            bool: True if purchase succeeded, False if insufficient gold
        """
        if amount < 0:
            raise ValueError("Spend amount cannot be negative")
        balance = player.get("gold", 0)
        if balance < amount:
            logger.warning(f"Insufficient gold: have {balance}, need {amount}")
            return False
        player["gold"] = balance - amount
        logger.info(f"Gold spent: -{amount}, balance={player['gold']}")
        return True
