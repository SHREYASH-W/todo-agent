"""
Module Manager for LifeHunter System

Coordinates the six life area modules and enforces rank-based unlock requirements.

Module unlock requirements (Requirement 14.1-14.8):
  E-Rank:  Career Hunter  (always available)
  D-Rank:  Skill Trainer
  C-Rank:  Fitness Hunter
  B-Rank:  Finance Manager
  A-Rank:  Social Network
  S-Rank:  Habit Forge
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

RANK_ORDER = ["E", "D", "C", "B", "A", "S", "National"]

MODULE_UNLOCK_REQUIREMENTS: Dict[str, str] = {
    "career_hunter": "E",
    "skill_trainer": "D",
    "fitness_hunter": "C",
    "finance_manager": "B",
    "social_network": "A",
    "habit_forge": "S",
}

MODULE_DISPLAY_NAMES: Dict[str, str] = {
    "career_hunter": "Career Hunter",
    "skill_trainer": "Skill Trainer",
    "fitness_hunter": "Fitness Hunter",
    "finance_manager": "Finance Manager",
    "social_network": "Social Network",
    "habit_forge": "Habit Forge",
}


def _rank_index(rank: str) -> int:
    try:
        return RANK_ORDER.index(rank)
    except ValueError:
        return 0


class ModuleManager:
    """Coordinates life area modules and rank-based unlocking."""

    def check_module_unlock(self, player_rank: str, module_name: str) -> bool:
        """
        Check if a module is unlocked for a given player rank.

        Requirement 14.2-14.8.

        Args:
            player_rank: Player's current rank string
            module_name: Module identifier key

        Returns:
            bool: True if unlocked
        """
        required_rank = MODULE_UNLOCK_REQUIREMENTS.get(module_name)
        if required_rank is None:
            logger.warning(f"Unknown module: {module_name}")
            return False
        return _rank_index(player_rank) >= _rank_index(required_rank)

    def get_available_modules(self, player_rank: str) -> List[Dict[str, Any]]:
        """
        Return all modules available for the player's current rank.

        Requirement 14.8.

        Returns:
            List[Dict]: Module info dicts with name, display_name, unlocked, required_rank
        """
        modules = []
        for key, required_rank in MODULE_UNLOCK_REQUIREMENTS.items():
            unlocked = self.check_module_unlock(player_rank, key)
            modules.append({
                "name": key,
                "display_name": MODULE_DISPLAY_NAMES[key],
                "unlocked": unlocked,
                "required_rank": required_rank,
            })
        return modules

    def get_module_statistics(
        self,
        player_rank: str,
        module_stats: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate statistics from all unlocked modules.

        Returns a combined stats dict with module-level breakdowns.
        """
        stats: Dict[str, Any] = {}
        available = self.get_available_modules(player_rank)

        for mod in available:
            if mod["unlocked"] and module_stats:
                stats[mod["name"]] = module_stats.get(mod["name"], {})
            elif mod["unlocked"]:
                stats[mod["name"]] = {}

        return stats
