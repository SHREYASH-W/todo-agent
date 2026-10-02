"""
Notification Service for LifeHunter System

Handles notification generation, delivery, rate limiting (1 per event type/minute),
and read-state management.

Requirements: Notification requirements, 13.2 rate limiting property test
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = 60  # 1 notification per event type per minute


class NotificationService:
    """Generates and manages system notifications for players."""

    def __init__(self):
        # In-memory rate limit tracker: {player_id: {event_type: last_sent_time}}
        self._rate_limits: Dict[int, Dict[str, datetime]] = {}

    def _is_rate_limited(self, player_id: int, event_type: str) -> bool:
        """Check if a notification is rate-limited."""
        player_limits = self._rate_limits.get(player_id, {})
        last_sent = player_limits.get(event_type)
        if last_sent is None:
            return False
        elapsed = (datetime.utcnow() - last_sent).total_seconds()
        return elapsed < RATE_LIMIT_WINDOW_SECONDS

    def _record_send(self, player_id: int, event_type: str):
        """Record that a notification was sent."""
        if player_id not in self._rate_limits:
            self._rate_limits[player_id] = {}
        self._rate_limits[player_id][event_type] = datetime.utcnow()

    def _create_notification(
        self,
        player_id: int,
        event_type: str,
        title: str,
        message: str,
    ) -> Optional[Dict[str, Any]]:
        """Create a notification dict, respecting rate limits."""
        if self._is_rate_limited(player_id, event_type):
            logger.debug(f"Rate limited: {event_type} for player {player_id}")
            return None

        self._record_send(player_id, event_type)
        notification = {
            "player_id": player_id,
            "notification_type": event_type,
            "title": title,
            "message": message,
            "is_read": False,
            "created_at": datetime.utcnow(),
        }
        logger.info(f"Notification created: [{event_type}] for player {player_id}")
        return notification

    def notify_level_up(self, player_id: int, new_level: int) -> Optional[Dict]:
        return self._create_notification(
            player_id,
            "level_up",
            f"Level Up! You are now Level {new_level}!",
            f"Congratulations! You've reached Level {new_level}. "
            f"Stat points and skill points have been granted.",
        )

    def notify_quest_complete(self, player_id: int, quest_title: str, xp_awarded: int) -> Optional[Dict]:
        return self._create_notification(
            player_id,
            "quest_complete",
            "Quest Completed!",
            f"You completed '{quest_title}' and earned {xp_awarded} XP!",
        )

    def notify_achievement_unlock(self, player_id: int, achievement_name: str, rarity: str) -> Optional[Dict]:
        return self._create_notification(
            player_id,
            "achievement_unlock",
            f"Achievement Unlocked: {achievement_name}",
            f"You've earned the {rarity.upper()} achievement '{achievement_name}'!",
        )

    def notify_penalty_zone(self, player_id: int) -> Optional[Dict]:
        return self._create_notification(
            player_id,
            "penalty_zone",
            "⚠️ Penalty Zone Activated",
            "You failed to complete your daily quests. "
            "Complete the penalty challenge within 24 hours to escape!",
        )

    def notify_rank_up(self, player_id: int, new_rank: str) -> Optional[Dict]:
        return self._create_notification(
            player_id,
            "rank_up",
            f"Rank Advancement: {new_rank}-Rank!",
            f"You have advanced to {new_rank}-Rank! New modules and features are now available.",
        )

    def notify_emergency_quest(self, player_id: int, quest_title: str) -> Optional[Dict]:
        return self._create_notification(
            player_id,
            "emergency_quest",
            f"🚨 Emergency Quest: {quest_title}",
            f"A new emergency quest '{quest_title}' requires your immediate attention!",
        )

    def get_unread_notifications(self, notifications: List[Dict]) -> List[Dict]:
        """Return all unread notifications, newest first."""
        unread = [n for n in notifications if not n.get("is_read", False)]
        return sorted(unread, key=lambda n: n.get("created_at", datetime.min), reverse=True)

    def mark_as_read(self, notification: Dict) -> bool:
        """Mark a single notification as read."""
        if notification.get("is_read"):
            return False
        notification["is_read"] = True
        return True

    def mark_all_as_read(self, notifications: List[Dict]) -> int:
        """Mark all notifications as read. Returns count marked."""
        count = 0
        for n in notifications:
            if not n.get("is_read"):
                n["is_read"] = True
                count += 1
        return count
