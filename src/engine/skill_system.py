"""
Skill System for LifeHunter System

Manages skill unlocking, upgrading, passive bonuses, and active skill cooldowns.

Requirements: 9.1-9.8
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_SKILL_LEVEL = 10  # Requirement 9.5


class SkillSystem:
    """Manages skill unlocking, point allocation, and bonus application."""

    def can_unlock_skill(self, player_level: int, skill_unlock_level: int) -> bool:
        """
        Check if player level meets skill unlock threshold.

        Requirement 9.1.
        """
        return player_level >= skill_unlock_level

    def unlock_skill(
        self,
        player: Dict[str, Any],
        skill: Dict[str, Any],
        existing_player_skills: List[Dict],
    ) -> Optional[Dict[str, Any]]:
        """
        Unlock a skill for a player if level requirement is met.

        Requirement 9.1.

        Returns:
            Dict: New PlayerSkill record, or None if conditions not met
        """
        player_level = player.get("level", 1)
        unlock_level = skill.get("unlock_level", 1)

        if not self.can_unlock_skill(player_level, unlock_level):
            logger.warning(
                f"Cannot unlock skill '{skill.get('name')}': "
                f"requires level {unlock_level}, player is level {player_level}"
            )
            return None

        # Check if already unlocked
        skill_id = skill.get("id")
        already_unlocked = any(ps.get("skill_id") == skill_id for ps in existing_player_skills)
        if already_unlocked:
            logger.info(f"Skill '{skill.get('name')}' already unlocked")
            return None

        # Check prerequisite
        prereq_id = skill.get("prerequisite_skill_id")
        if prereq_id is not None:
            has_prereq = any(ps.get("skill_id") == prereq_id for ps in existing_player_skills)
            if not has_prereq:
                logger.warning(f"Skill '{skill.get('name')}' prerequisite not met")
                return None

        player_skill = {
            "player_id": player.get("id"),
            "skill_id": skill_id,
            "current_level": 1,
            "unlocked_at": datetime.utcnow(),
        }
        logger.info(f"Skill '{skill.get('name')}' unlocked for player {player.get('id')}")
        return player_skill

    def allocate_skill_point(
        self,
        player: Dict[str, Any],
        player_skill: Dict[str, Any],
    ) -> bool:
        """
        Allocate one skill point, capped at MAX_SKILL_LEVEL.

        Requirements 9.3, 9.4, 9.5.
        """
        if player.get("skill_points", 0) <= 0:
            logger.warning("No skill points available")
            return False
        if player_skill.get("current_level", 0) >= MAX_SKILL_LEVEL:
            logger.warning("Skill already at maximum level")
            return False

        player_skill["current_level"] = player_skill.get("current_level", 0) + 1
        player["skill_points"] = player.get("skill_points", 0) - 1
        logger.info(f"Skill level now {player_skill['current_level']}")
        return True

    def apply_passive_bonuses(
        self,
        player: Dict[str, Any],
        player_skills: List[Dict],
        all_skills: List[Dict],
    ) -> Dict[str, float]:
        """
        Calculate combined passive skill bonuses for a player.

        Requirement 9.6. Bonuses are applied automatically without activation.

        Returns:
            Dict: Bonus multipliers/additions keyed by bonus type
        """
        bonuses: Dict[str, float] = {}

        for ps in player_skills:
            skill_id = ps.get("skill_id")
            skill = next((s for s in all_skills if s.get("id") == skill_id), None)
            if not skill or skill.get("skill_type") != "passive":
                continue

            level = ps.get("current_level", 0)
            name = skill.get("name", "")

            # Map known passive skills to their bonuses
            if name == "Task Focus":
                bonuses["xp_gain_pct"] = bonuses.get("xp_gain_pct", 0) + 5 * level
            elif name == "Quick Learner":
                bonuses["int_effectiveness_pct"] = bonuses.get("int_effectiveness_pct", 0) + 2 * level
            elif name == "Stamina Boost":
                bonuses["hp_regen_pct"] = bonuses.get("hp_regen_pct", 0) + 5 * level
            elif name == "Multi-Tasking":
                bonuses["parallel_quests"] = 2 if level >= MAX_SKILL_LEVEL else 1
            elif name == "Career Momentum":
                bonuses["job_match_bonus_pct"] = bonuses.get("job_match_bonus_pct", 0) + 3 * level
            elif name == "Golden Touch":
                bonuses["gold_reward_pct"] = bonuses.get("gold_reward_pct", 0) + 10 * level
            elif name == "Strategic Mind":
                bonuses["quest_efficiency_pct"] = bonuses.get("quest_efficiency_pct", 0) + 5 * level
            elif name == "Interview Mastery":
                bonuses["interview_xp_pct"] = bonuses.get("interview_xp_pct", 0) + 15 * level
            elif name == "Perfect Execution":
                bonuses["early_completion_xp_pct"] = bonuses.get("early_completion_xp_pct", 0) + 20 * level
            elif name == "Network Effect":
                bonuses["networking_reward_pct"] = bonuses.get("networking_reward_pct", 0) + 25 * level
            elif name == "Master of All":
                bonuses["all_stats_flat"] = bonuses.get("all_stats_flat", 0) + level

        return bonuses

    def activate_active_skill(
        self,
        player_id: int,
        skill: Dict[str, Any],
        player_skill: Dict[str, Any],
        active_cooldowns: Dict[int, datetime],
    ) -> Dict[str, Any]:
        """
        Activate an active skill and start its cooldown.

        Requirement 9.7.

        Args:
            player_id: Player ID
            skill: Skill definition dict
            player_skill: PlayerSkill dict
            active_cooldowns: Dict mapping skill_id -> cooldown_expiry

        Returns:
            Dict with success, effect, cooldown_until
        """
        skill_id = skill.get("id")
        name = skill.get("name", "")

        # Check cooldown
        cooldown_until = active_cooldowns.get(skill_id)
        if cooldown_until and datetime.utcnow() < cooldown_until:
            remaining = int((cooldown_until - datetime.utcnow()).total_seconds())
            return {
                "success": False,
                "message": f"Skill on cooldown for {remaining}s",
                "cooldown_remaining_seconds": remaining,
            }

        if skill.get("skill_type") != "active":
            return {"success": False, "message": "Skill is not an active skill"}

        # Apply effect and set cooldown
        effect = self._get_active_skill_effect(name, player_skill.get("current_level", 1))
        cooldown_hours = self._get_cooldown_hours(name)
        cooldown_until = datetime.utcnow() + timedelta(hours=cooldown_hours)
        active_cooldowns[skill_id] = cooldown_until

        logger.info(
            f"Active skill '{name}' activated for player {player_id} "
            f"(cooldown={cooldown_hours}h)"
        )
        return {
            "success": True,
            "effect": effect,
            "cooldown_until": cooldown_until.isoformat(),
            "cooldown_hours": cooldown_hours,
        }

    def _get_active_skill_effect(self, skill_name: str, level: int) -> Dict[str, Any]:
        """Return the effect dict for an active skill."""
        effects = {
            "Rush Hour": {"xp_multiplier": 2.0, "duration_minutes": 60},
            "Second Wind": {"hp_restore_pct": 50, "remove_negative_status": True},
            "Overdrive": {"xp_multiplier": 3.0, "duration_minutes": 30},
            "Limit Break": {"remove_all_cooldowns": True, "xp_multiplier": 5.0, "duration_minutes": 15},
        }
        return effects.get(skill_name, {"effect": f"{skill_name} activated (level {level})"})

    def _get_cooldown_hours(self, skill_name: str) -> int:
        """Return cooldown in hours for an active skill."""
        cooldowns = {
            "Rush Hour": 24,
            "Second Wind": 48,
            "Overdrive": 72,
            "Limit Break": 168,
        }
        return cooldowns.get(skill_name, 24)
