"""
Quest Manager for LifeHunter System

Creates and tracks quests of all types:
- Daily Quests: 3-5 per day, refresh at midnight, mandatory completion
- Main Quests: Long-term goals with sub-quests (max 10 active)
- Instant Dungeons: Time-limited challenges (15 min - 4 hours, max 1 active)
- Emergency Quests: High-priority with 2x XP and -50 XP penalty on failure (max 3 active)
- Penalty Zone: Activated when daily quests fail at midnight

Requirements: 4.1-4.7, 5.1-5.7, 6.1-6.7, 7.1-7.7, 8.1-8.7
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Quest type constants
TYPE_DAILY = "daily"
TYPE_MAIN = "main"
TYPE_INSTANT = "instant"
TYPE_EMERGENCY = "emergency"

# Quest status constants
STATUS_ACTIVE = "active"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# Quest limits
MAX_MAIN_QUESTS = 10         # Requirement 5.6
MAX_INSTANT_DUNGEONS = 1     # Requirement 6.6
MAX_EMERGENCY_QUESTS = 3     # Requirement 7.5
MIN_DAILY_QUESTS = 3         # Requirement 4.2
MAX_DAILY_QUESTS = 5         # Requirement 4.2

# XP constants
DAILY_COMPLETION_BONUS_XP = 50    # Requirement 4.7
EMERGENCY_XP_MULTIPLIER = 2       # Requirement 7.3
EMERGENCY_FAILURE_PENALTY_XP = -50  # Requirement 7.7
PENALTY_ZONE_FAILURE_XP = -100    # Requirement 8.4

# Instant dungeon timer bounds (in minutes)
INSTANT_DUNGEON_MIN_MINUTES = 15
INSTANT_DUNGEON_MAX_MINUTES = 240  # 4 hours

# Daily quest templates for seed generation
DAILY_QUEST_TEMPLATES = [
    {"title": "Morning Workout", "description": "Complete a 30-minute workout session", "xp_reward": 30, "gold_reward": 10, "difficulty": "easy"},
    {"title": "Job Applications", "description": "Apply to at least 3 job positions today", "xp_reward": 50, "gold_reward": 20, "difficulty": "medium"},
    {"title": "Skill Practice", "description": "Spend 1 hour practicing a new skill", "xp_reward": 35, "gold_reward": 15, "difficulty": "easy"},
    {"title": "Networking", "description": "Reach out to 2 professional contacts", "xp_reward": 40, "gold_reward": 15, "difficulty": "medium"},
    {"title": "Read & Learn", "description": "Read for at least 30 minutes on a relevant topic", "xp_reward": 25, "gold_reward": 10, "difficulty": "very_easy"},
    {"title": "Code Review", "description": "Review or write 50+ lines of code", "xp_reward": 45, "gold_reward": 20, "difficulty": "medium"},
    {"title": "Portfolio Update", "description": "Update one section of your portfolio or resume", "xp_reward": 40, "gold_reward": 15, "difficulty": "medium"},
    {"title": "Financial Check", "description": "Review your budget and track expenses", "xp_reward": 20, "gold_reward": 10, "difficulty": "very_easy"},
]


class QuestResult:
    """Represents the result of a quest completion."""

    def __init__(
        self,
        success: bool,
        quest_id: int,
        xp_awarded: int,
        gold_awarded: int,
        bonus_xp: int = 0,
        message: str = "",
        level_up: bool = False,
    ):
        self.success = success
        self.quest_id = quest_id
        self.xp_awarded = xp_awarded
        self.gold_awarded = gold_awarded
        self.bonus_xp = bonus_xp
        self.message = message
        self.level_up = level_up

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "quest_id": self.quest_id,
            "xp_awarded": self.xp_awarded,
            "gold_awarded": self.gold_awarded,
            "bonus_xp": self.bonus_xp,
            "total_xp": self.xp_awarded + self.bonus_xp,
            "message": self.message,
            "level_up": self.level_up,
        }


class QuestCollection:
    """Groups active quests by type."""

    def __init__(
        self,
        daily: List[Dict] = None,
        main: List[Dict] = None,
        instant: List[Dict] = None,
        emergency: List[Dict] = None,
    ):
        self.daily = daily or []
        self.main = main or []
        self.instant = instant or []
        self.emergency = emergency or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "daily": self.daily,
            "main": self.main,
            "instant": self.instant,
            "emergency": self.emergency,
            "total_active": len(self.daily) + len(self.main) + len(self.instant) + len(self.emergency),
        }


class QuestManager:
    """
    Manages all quest types in the LifeHunter system.

    Works with plain dicts for quest data so it can be used independently
    of the ORM session. Persistence is the caller's responsibility.
    """

    # ─── Daily Quests ──────────────────────────────────────────────────────

    def create_daily_quests(
        self,
        player_id: int,
        date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate 3-5 daily quests for a player for the given date.

        Requirement 4.1, 4.2.

        Args:
            player_id: Player ID
            date: Target date (defaults to today)

        Returns:
            List[Dict]: List of 3-5 daily quest data dicts
        """
        if date is None:
            date = datetime.utcnow()

        # Randomly pick 3-5 templates
        count = random.randint(MIN_DAILY_QUESTS, MAX_DAILY_QUESTS)
        templates = random.sample(DAILY_QUEST_TEMPLATES, min(count, len(DAILY_QUEST_TEMPLATES)))

        deadline = date.replace(hour=23, minute=59, second=59, microsecond=0)

        quests = []
        for template in templates:
            quest = {
                "player_id": player_id,
                "quest_type": TYPE_DAILY,
                "title": template["title"],
                "description": template["description"],
                "xp_reward": template["xp_reward"],
                "gold_reward": template["gold_reward"],
                "difficulty": template["difficulty"],
                "status": STATUS_ACTIVE,
                "created_at": datetime.utcnow(),
                "deadline": deadline,
                "completed_at": None,
                "parent_quest_id": None,
            }
            quests.append(quest)

        logger.info(f"Created {len(quests)} daily quests for player {player_id} on {date.date()}")
        return quests

    def check_daily_quest_failure(
        self,
        quests: List[Dict[str, Any]],
        check_time: Optional[datetime] = None,
    ) -> bool:
        """
        Check if daily quests are incomplete at midnight.

        Requirement 4.4, 8.1.

        Args:
            quests: List of daily quest dicts for today
            check_time: Time to check against (defaults to now)

        Returns:
            bool: True if daily quests failed (incomplete at midnight)
        """
        if not quests:
            return False

        if check_time is None:
            check_time = datetime.utcnow()

        daily_quests = [q for q in quests if q.get("quest_type") == TYPE_DAILY]
        if not daily_quests:
            return False

        # Check if any daily quest is still active past its deadline
        for quest in daily_quests:
            deadline = quest.get("deadline")
            status = quest.get("status")
            if status == STATUS_ACTIVE and deadline and check_time > deadline:
                return True

        return False

    def get_daily_completion_percentage(self, daily_quests: List[Dict]) -> float:
        """
        Calculate completion percentage of daily quests.

        Requirement 4.6.

        Args:
            daily_quests: List of daily quest dicts

        Returns:
            float: Completion percentage (0.0 to 100.0)
        """
        if not daily_quests:
            return 0.0
        completed = sum(1 for q in daily_quests if q.get("status") == STATUS_COMPLETED)
        return round((completed / len(daily_quests)) * 100, 1)

    # ─── Main Quests ───────────────────────────────────────────────────────

    def create_main_quest(
        self,
        player_id: int,
        quest_data: Dict[str, Any],
        active_main_quests_count: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new main quest with sub-quest support.

        Requirement 5.1, 5.2, 5.6.

        Args:
            player_id: Player ID
            quest_data: Dict with keys: title, description, deadline (optional)
            active_main_quests_count: Number of currently active main quests

        Returns:
            Dict: Quest data, or None if limit reached (max 10)
        """
        if active_main_quests_count >= MAX_MAIN_QUESTS:
            logger.warning(
                f"Cannot create main quest: limit of {MAX_MAIN_QUESTS} reached "
                f"for player {player_id}"
            )
            return None

        quest = {
            "player_id": player_id,
            "quest_type": TYPE_MAIN,
            "title": quest_data.get("title", "New Main Quest"),
            "description": quest_data.get("description", ""),
            "xp_reward": quest_data.get("xp_reward", 100),
            "gold_reward": quest_data.get("gold_reward", 50),
            "difficulty": quest_data.get("difficulty", "medium"),
            "status": STATUS_ACTIVE,
            "created_at": datetime.utcnow(),
            "deadline": quest_data.get("deadline"),
            "completed_at": None,
            "parent_quest_id": None,
        }
        logger.info(f"Created main quest '{quest['title']}' for player {player_id}")
        return quest

    def create_sub_quest(
        self,
        player_id: int,
        parent_quest_id: int,
        sub_quest_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a sub-quest attached to a main quest.

        Requirement 5.2.

        Args:
            player_id: Player ID
            parent_quest_id: ID of the parent main quest
            sub_quest_data: Dict with title, description, xp_reward, difficulty

        Returns:
            Dict: Sub-quest data dict
        """
        sub_quest = {
            "player_id": player_id,
            "quest_type": TYPE_MAIN,
            "title": sub_quest_data.get("title", "Sub-quest"),
            "description": sub_quest_data.get("description", ""),
            "xp_reward": sub_quest_data.get("xp_reward", 25),
            "gold_reward": sub_quest_data.get("gold_reward", 10),
            "difficulty": sub_quest_data.get("difficulty", "easy"),
            "status": STATUS_ACTIVE,
            "created_at": datetime.utcnow(),
            "deadline": sub_quest_data.get("deadline"),
            "completed_at": None,
            "parent_quest_id": parent_quest_id,
        }
        return sub_quest

    def get_main_quest_progress(self, sub_quests: List[Dict]) -> float:
        """
        Calculate progress percentage for a main quest.

        Requirement 5.5.

        Args:
            sub_quests: List of sub-quest dicts for this main quest

        Returns:
            float: Progress percentage (0.0 to 100.0)
        """
        if not sub_quests:
            return 0.0
        completed = sum(1 for q in sub_quests if q.get("status") == STATUS_COMPLETED)
        return round((completed / len(sub_quests)) * 100, 1)

    def check_main_quest_completion(
        self,
        main_quest: Dict,
        sub_quests: List[Dict],
    ) -> bool:
        """
        Check if all sub-quests are complete and auto-complete the main quest.

        Requirement 5.3.

        Args:
            main_quest: Main quest data dict (updated in-place if complete)
            sub_quests: List of sub-quest dicts

        Returns:
            bool: True if main quest was just completed
        """
        if not sub_quests:
            return False
        if main_quest.get("status") == STATUS_COMPLETED:
            return False

        all_done = all(q.get("status") == STATUS_COMPLETED for q in sub_quests)
        if all_done:
            main_quest["status"] = STATUS_COMPLETED
            main_quest["completed_at"] = datetime.utcnow()
            logger.info(f"Main quest '{main_quest.get('title')}' auto-completed")
            return True
        return False

    # ─── Instant Dungeons ──────────────────────────────────────────────────

    def start_instant_dungeon(
        self,
        player_id: int,
        dungeon_data: Dict[str, Any],
        active_instant_count: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Start an instant dungeon with a countdown timer.

        Requirements 6.1, 6.2, 6.6.

        Args:
            player_id: Player ID
            dungeon_data: Dict with title, description, duration_minutes, xp_reward
            active_instant_count: Number of active instant dungeons

        Returns:
            Dict: Dungeon quest data, or None if limit reached (max 1)
        """
        if active_instant_count >= MAX_INSTANT_DUNGEONS:
            logger.warning(f"Player {player_id} already has an active instant dungeon")
            return None

        duration = dungeon_data.get("duration_minutes", 60)
        duration = max(INSTANT_DUNGEON_MIN_MINUTES, min(INSTANT_DUNGEON_MAX_MINUTES, duration))

        now = datetime.utcnow()
        deadline = now + timedelta(minutes=duration)

        dungeon = {
            "player_id": player_id,
            "quest_type": TYPE_INSTANT,
            "title": dungeon_data.get("title", "Instant Dungeon"),
            "description": dungeon_data.get("description", "Complete before time expires!"),
            "xp_reward": dungeon_data.get("xp_reward", 75),
            "gold_reward": dungeon_data.get("gold_reward", 30),
            "difficulty": dungeon_data.get("difficulty", "medium"),
            "status": STATUS_ACTIVE,
            "created_at": now,
            "deadline": deadline,
            "completed_at": None,
            "parent_quest_id": None,
            "duration_minutes": duration,
        }
        logger.info(
            f"Instant dungeon started for player {player_id}: "
            f"'{dungeon['title']}' (deadline={deadline})"
        )
        return dungeon

    def get_instant_dungeon_remaining_time(self, dungeon: Dict) -> int:
        """
        Get remaining time for an instant dungeon in seconds.

        Requirement 6.7.

        Returns:
            int: Seconds remaining (0 if expired)
        """
        deadline = dungeon.get("deadline")
        if not deadline:
            return 0
        remaining = (deadline - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))

    # ─── Emergency Quests ──────────────────────────────────────────────────

    def create_emergency_quest(
        self,
        player_id: int,
        quest_data: Dict[str, Any],
        active_emergency_count: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Create an emergency quest with 2x XP multiplier.

        Requirements 7.1, 7.2, 7.3, 7.5.

        Args:
            player_id: Player ID
            quest_data: Dict with title, description, deadline, base_xp_reward
            active_emergency_count: Number of currently active emergency quests

        Returns:
            Dict: Emergency quest data, or None if limit reached (max 3)
        """
        if active_emergency_count >= MAX_EMERGENCY_QUESTS:
            logger.warning(f"Emergency quest limit reached for player {player_id}")
            return None

        base_xp = quest_data.get("xp_reward", 50)
        # 2x XP multiplier for emergency quests
        doubled_xp = base_xp * EMERGENCY_XP_MULTIPLIER

        quest = {
            "player_id": player_id,
            "quest_type": TYPE_EMERGENCY,
            "title": quest_data.get("title", "Emergency Quest"),
            "description": quest_data.get("description", "URGENT: Complete immediately!"),
            "xp_reward": doubled_xp,
            "gold_reward": quest_data.get("gold_reward", 25),
            "difficulty": quest_data.get("difficulty", "hard"),
            "status": STATUS_ACTIVE,
            "created_at": datetime.utcnow(),
            "deadline": quest_data.get("deadline"),
            "completed_at": None,
            "parent_quest_id": None,
            "is_emergency": True,
            "base_xp": base_xp,
        }
        logger.info(
            f"Emergency quest created for player {player_id}: "
            f"'{quest['title']}' (2x XP = {doubled_xp})"
        )
        return quest

    # ─── Penalty Zone ──────────────────────────────────────────────────────

    def activate_penalty_zone(
        self,
        player_id: int,
        failed_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Activate penalty zone for failed daily quests.

        Requirements 8.1, 8.2, 8.6.

        Args:
            player_id: Player ID
            failed_date: Date when daily quests were failed

        Returns:
            Dict: Penalty zone data with challenge quest
        """
        if failed_date is None:
            failed_date = datetime.utcnow()

        # Penalty must be cleared within 24 hours
        penalty_deadline = failed_date + timedelta(hours=24)

        penalty_zone = {
            "player_id": player_id,
            "active": True,
            "activated_at": failed_date,
            "deadline": penalty_deadline,
            "challenge_quest": {
                "player_id": player_id,
                "quest_type": TYPE_DAILY,
                "title": "Penalty Challenge: Redemption",
                "description": (
                    "You failed your daily quests! Complete this penalty challenge "
                    "within 24 hours to escape the Penalty Zone."
                ),
                "xp_reward": 0,
                "gold_reward": 0,
                "difficulty": "hard",
                "status": STATUS_ACTIVE,
                "created_at": failed_date,
                "deadline": penalty_deadline,
                "completed_at": None,
                "is_penalty_challenge": True,
            },
        }

        logger.warning(f"Penalty zone activated for player {player_id}")
        return penalty_zone

    # ─── Quest Completion ──────────────────────────────────────────────────

    def complete_quest(
        self,
        quest: Dict[str, Any],
        all_daily_quests: Optional[List[Dict]] = None,
    ) -> QuestResult:
        """
        Mark a quest as completed and calculate rewards.

        Requirements 1.1, 4.3, 4.7, 5.4, 6.4, 7.3.

        Args:
            quest: Quest data dict (updated in-place)
            all_daily_quests: All daily quests for today (for bonus check)

        Returns:
            QuestResult: Completion result with XP and gold awarded
        """
        if quest.get("status") != STATUS_ACTIVE:
            return QuestResult(
                success=False,
                quest_id=quest.get("id", 0),
                xp_awarded=0,
                gold_awarded=0,
                message=f"Quest cannot be completed (status={quest.get('status')})",
            )

        # Check instant dungeon time expiry
        if quest.get("quest_type") == TYPE_INSTANT:
            remaining = self.get_instant_dungeon_remaining_time(quest)
            if remaining <= 0:
                quest["status"] = STATUS_FAILED
                return QuestResult(
                    success=False,
                    quest_id=quest.get("id", 0),
                    xp_awarded=0,
                    gold_awarded=0,
                    message="Instant dungeon expired — no XP awarded",
                )

        quest["status"] = STATUS_COMPLETED
        quest["completed_at"] = datetime.utcnow()

        xp = quest.get("xp_reward", 0)
        gold = quest.get("gold_reward", 0)
        bonus_xp = 0
        message = f"Quest completed! +{xp} XP, +{gold} Gold"

        # Check for daily completion bonus (all daily quests done)
        if quest.get("quest_type") == TYPE_DAILY and all_daily_quests:
            all_completed = all(
                q.get("status") == STATUS_COMPLETED
                for q in all_daily_quests
            )
            if all_completed:
                bonus_xp = DAILY_COMPLETION_BONUS_XP
                message += f" + {bonus_xp} daily completion bonus!"

        logger.info(
            f"Quest completed: '{quest.get('title')}' "
            f"(xp={xp}, gold={gold}, bonus={bonus_xp})"
        )

        return QuestResult(
            success=True,
            quest_id=quest.get("id", 0),
            xp_awarded=xp,
            gold_awarded=gold,
            bonus_xp=bonus_xp,
            message=message,
        )

    def fail_quest(
        self,
        quest: Dict[str, Any],
        player: Optional[Dict[str, Any]] = None,
    ) -> QuestResult:
        """
        Mark a quest as failed and apply penalties if applicable.

        Requirements 6.5, 7.4, 7.7, 8.4.

        Args:
            quest: Quest data dict (updated in-place)
            player: Player dict for applying XP penalties (optional)

        Returns:
            QuestResult: Failure result with any XP penalties
        """
        quest["status"] = STATUS_FAILED

        xp_penalty = 0
        message = f"Quest failed: {quest.get('title')}"

        if quest.get("quest_type") == TYPE_EMERGENCY:
            xp_penalty = EMERGENCY_FAILURE_PENALTY_XP
            message += f" ({xp_penalty} XP penalty)"
            if player:
                player["xp"] = max(0, player.get("xp", 0) + xp_penalty)

        logger.warning(f"Quest failed: '{quest.get('title')}' (penalty={xp_penalty} XP)")

        return QuestResult(
            success=False,
            quest_id=quest.get("id", 0),
            xp_awarded=xp_penalty,  # negative value = penalty
            gold_awarded=0,
            message=message,
        )

    # ─── Active Quest Retrieval ────────────────────────────────────────────

    def get_active_quests(self, all_quests: List[Dict]) -> QuestCollection:
        """
        Group active quests by type.

        Requirement 4.5, 23.1.

        Args:
            all_quests: All quest dicts for a player

        Returns:
            QuestCollection: Quests organized by type
        """
        active = [q for q in all_quests if q.get("status") == STATUS_ACTIVE]

        return QuestCollection(
            daily=[q for q in active if q.get("quest_type") == TYPE_DAILY],
            main=[q for q in active if q.get("quest_type") == TYPE_MAIN],
            instant=[q for q in active if q.get("quest_type") == TYPE_INSTANT],
            emergency=[q for q in active if q.get("quest_type") == TYPE_EMERGENCY],
        )
