"""
Quest API endpoints.

GET    /api/quests          - All active quests
POST   /api/quests          - Create new quest
POST   /api/quests/<id>/complete - Mark quest complete
DELETE /api/quests/<id>     - Delete quest
GET    /api/quests/daily    - Today's daily quests

Requirements: 23.1-23.7
"""

from datetime import datetime

from flask import Blueprint, jsonify, request

from src.engine.quest_manager import QuestManager
from src.engine.progression_engine import ProgressionEngine
from src.models import SessionLocal, Player
from src.models.quest import Quest

quest_bp = Blueprint("quest", __name__, url_prefix="/api/quests")

_quest_mgr = QuestManager()
_progression = ProgressionEngine()


def _not_found(msg):
    return jsonify({"error": msg}), 404


def _bad_request(msg):
    return jsonify({"error": msg}), 400


def _conflict(msg):
    return jsonify({"error": msg}), 409


def _quest_to_dict(q: Quest) -> dict:
    return {
        "id": q.id,
        "player_id": q.player_id,
        "quest_type": q.quest_type,
        "title": q.title,
        "description": q.description,
        "xp_reward": q.xp_reward,
        "gold_reward": q.gold_reward,
        "difficulty": q.difficulty,
        "status": q.status,
        "created_at": q.created_at.isoformat() if q.created_at else None,
        "deadline": q.deadline.isoformat() if q.deadline else None,
        "completed_at": q.completed_at.isoformat() if q.completed_at else None,
        "parent_quest_id": q.parent_quest_id,
    }


@quest_bp.route("", methods=["GET"])
def get_quests():
    """Get all active quests for the authenticated player. Requirement 23.1"""
    player_id = request.args.get("player_id", type=int)
    if not player_id:
        return _bad_request("player_id query parameter required")

    db = SessionLocal()
    try:
        quests = db.query(Quest).filter(
            Quest.player_id == player_id,
            Quest.status == "active",
        ).all()

        quest_dicts = [_quest_to_dict(q) for q in quests]
        collection = _quest_mgr.get_active_quests(quest_dicts)
        return jsonify(collection.to_dict())
    finally:
        db.close()


@quest_bp.route("/daily", methods=["GET"])
def get_daily_quests():
    """Get today's daily quests. Requirement 23.5"""
    player_id = request.args.get("player_id", type=int)
    if not player_id:
        return _bad_request("player_id query parameter required")

    today = datetime.utcnow().date()
    db = SessionLocal()
    try:
        quests = db.query(Quest).filter(
            Quest.player_id == player_id,
            Quest.quest_type == "daily",
            Quest.status == "active",
        ).all()

        # Filter to today's quests
        today_quests = [
            _quest_to_dict(q) for q in quests
            if q.created_at and q.created_at.date() == today
        ]

        completion_pct = _quest_mgr.get_daily_completion_percentage(
            [_quest_to_dict(q) for q in quests]
        )

        return jsonify({
            "quests": today_quests,
            "completion_percentage": completion_pct,
            "total": len(today_quests),
        })
    finally:
        db.close()


@quest_bp.route("", methods=["POST"])
def create_quest():
    """Create a new quest. Requirement 23.2"""
    data = request.get_json(silent=True) or {}
    player_id = data.get("player_id")
    quest_type = data.get("quest_type", "main")

    if not player_id:
        return _bad_request("player_id is required")

    if quest_type not in {"main", "instant", "emergency", "daily"}:
        return _bad_request("Invalid quest_type")

    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _not_found(f"Player {player_id} not found")

        # Enforce limits for main quests
        if quest_type == "main":
            active_count = db.query(Quest).filter(
                Quest.player_id == player_id,
                Quest.quest_type == "main",
                Quest.status == "active",
                Quest.parent_quest_id.is_(None),
            ).count()
            quest_data = _quest_mgr.create_main_quest(player_id, data, active_count)
            if quest_data is None:
                return _conflict("Maximum of 10 active main quests reached")
        else:
            from datetime import timedelta
            deadline_str = data.get("deadline")
            deadline = (
                datetime.fromisoformat(deadline_str) if deadline_str
                else datetime.utcnow() + timedelta(hours=24)
            )
            quest_data = {
                "player_id": player_id,
                "quest_type": quest_type,
                "title": data.get("title", "New Quest"),
                "description": data.get("description", ""),
                "xp_reward": data.get("xp_reward", 30),
                "gold_reward": data.get("gold_reward", 10),
                "difficulty": data.get("difficulty", "medium"),
                "status": "active",
                "created_at": datetime.utcnow(),
                "deadline": deadline,
                "completed_at": None,
                "parent_quest_id": data.get("parent_quest_id"),
            }

        quest = Quest(**quest_data)
        db.add(quest)
        db.commit()
        db.refresh(quest)
        return jsonify(_quest_to_dict(quest)), 201
    finally:
        db.close()


@quest_bp.route("/<int:quest_id>/complete", methods=["POST"])
def complete_quest(quest_id: int):
    """Mark a quest as completed. Requirement 23.4"""
    player_id = (request.get_json(silent=True) or {}).get("player_id")
    if not player_id:
        player_id = request.args.get("player_id", type=int)
    if not player_id:
        return _bad_request("player_id is required")

    db = SessionLocal()
    try:
        quest = db.query(Quest).filter(Quest.id == quest_id, Quest.player_id == player_id).first()
        if not quest:
            return _not_found(f"Quest {quest_id} not found")

        if quest.status != "active":
            return _conflict(f"Quest is not active (status={quest.status})")

        # Get all daily quests for bonus check
        all_daily = []
        if quest.quest_type == "daily":
            all_daily_db = db.query(Quest).filter(
                Quest.player_id == player_id,
                Quest.quest_type == "daily",
                Quest.status.in_(["active", "completed"]),
            ).all()
            all_daily = [_quest_to_dict(q) for q in all_daily_db]
            # Reflect the completion we're about to make
            for d in all_daily:
                if d["id"] == quest_id:
                    d["status"] = "completed"

        quest_dict = _quest_to_dict(quest)
        result = _quest_mgr.complete_quest(quest_dict, all_daily if quest.quest_type == "daily" else None)

        if result.success:
            quest.status = "completed"
            quest.completed_at = datetime.utcnow()

            # Award XP and gold to player
            player = db.query(Player).filter(Player.id == player_id).first()
            if player:
                p_dict = {"level": player.level, "xp": player.xp, "rank": player.rank,
                          "gold": player.gold, "stat_points": player.stat_points,
                          "skill_points": player.skill_points,
                          "hp": player.hp, "mp": player.mp,
                          "vit_stat": player.vit_stat, "int_stat": player.int_stat}
                xp_result = _progression.award_xp(p_dict, result.xp_awarded + result.bonus_xp)
                _progression.award_gold(p_dict, result.gold_awarded)

                player.xp = p_dict["xp"]
                player.level = p_dict["level"]
                player.rank = p_dict["rank"]
                player.stat_points = p_dict["stat_points"]
                player.skill_points = p_dict["skill_points"]
                player.gold = p_dict["gold"]
                player.hp = p_dict["hp"]
                player.mp = p_dict["mp"]

            db.commit()

        return jsonify(result.to_dict())
    finally:
        db.close()


@quest_bp.route("/<int:quest_id>", methods=["DELETE"])
def delete_quest(quest_id: int):
    """Delete a quest. Requirement 23.3"""
    player_id = request.args.get("player_id", type=int)
    if not player_id:
        return _bad_request("player_id query parameter required")

    db = SessionLocal()
    try:
        quest = db.query(Quest).filter(Quest.id == quest_id, Quest.player_id == player_id).first()
        if not quest:
            return _not_found(f"Quest {quest_id} not found")

        db.delete(quest)
        db.commit()
        return jsonify({"success": True, "deleted_quest_id": quest_id})
    finally:
        db.close()
