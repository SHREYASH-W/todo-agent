"""
Player API endpoints.

GET  /api/player/<id>              - Player profile
GET  /api/player/<id>/stats        - Player statistics
POST /api/player/<id>/stats/allocate - Allocate stat point
GET  /api/player/<id>/skills       - Skill tree
POST /api/player/<id>/skills/allocate - Allocate skill point

Requirements: 22.1-22.7
"""

from flask import Blueprint, jsonify, request

from src.engine.progression_engine import ProgressionEngine
from src.engine.skill_system import SkillSystem
from src.models import SessionLocal, Player, PlayerSkill, Skill

player_bp = Blueprint("player", __name__, url_prefix="/api/player")

_progression = ProgressionEngine()
_skill_system = SkillSystem()


def _player_not_found(player_id):
    return jsonify({"error": f"Player {player_id} not found"}), 404


def _bad_request(msg):
    return jsonify({"error": msg}), 400


@player_bp.route("/<int:player_id>", methods=["GET"])
def get_player(player_id: int):
    """Retrieve player profile. Requirement 22.1"""
    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _player_not_found(player_id)

        active_title = None
        if player.active_title_id:
            from src.models import Title
            t = db.query(Title).filter_by(id=player.active_title_id).first()
            if t:
                active_title = {"id": t.id, "name": t.name}

        data = {
            "id": player.id,
            "username": player.username,
            "email": player.email,
            "level": player.level,
            "xp": player.xp,
            "rank": player.rank,
            "gold": player.gold,
            "hp": player.hp,
            "mp": player.mp,
            "str_stat": player.str_stat,
            "int_stat": player.int_stat,
            "agi_stat": player.agi_stat,
            "vit_stat": player.vit_stat,
            "sen_stat": player.sen_stat,
            "luk_stat": player.luk_stat,
            "stat_points": player.stat_points,
            "skill_points": player.skill_points,
            "active_title": active_title,
            "created_at": player.created_at.isoformat() if player.created_at else None,
            "last_login": player.last_login.isoformat() if player.last_login else None,
        }
        return jsonify(data)
    finally:
        db.close()


@player_bp.route("/<int:player_id>/stats", methods=["GET"])
def get_player_stats(player_id: int):
    """Get player statistics. Requirement 22.3"""
    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _player_not_found(player_id)

        player_dict = {
            "level": player.level, "xp": player.xp, "rank": player.rank,
            "gold": player.gold, "hp": player.hp, "mp": player.mp,
            "str_stat": player.str_stat, "int_stat": player.int_stat,
            "agi_stat": player.agi_stat, "vit_stat": player.vit_stat,
            "sen_stat": player.sen_stat, "luk_stat": player.luk_stat,
            "stat_points": player.stat_points, "skill_points": player.skill_points,
        }
        stats = _progression.get_player_stats(player_dict)
        return jsonify(stats)
    finally:
        db.close()


@player_bp.route("/<int:player_id>/stats/allocate", methods=["POST"])
def allocate_stat(player_id: int):
    """Allocate a stat point. Requirement 22.4"""
    data = request.get_json(silent=True) or {}
    stat_name = data.get("stat_name", "")

    valid_stats = {"str_stat", "int_stat", "agi_stat", "vit_stat", "sen_stat", "luk_stat"}
    if stat_name not in valid_stats:
        return _bad_request(f"Invalid stat_name. Must be one of: {sorted(valid_stats)}")

    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _player_not_found(player_id)

        player_dict = {
            "id": player.id, "stat_points": player.stat_points,
            "str_stat": player.str_stat, "int_stat": player.int_stat,
            "agi_stat": player.agi_stat, "vit_stat": player.vit_stat,
            "sen_stat": player.sen_stat, "luk_stat": player.luk_stat,
            "hp": player.hp, "mp": player.mp,
        }
        if not _progression.allocate_stat_point(player_dict, stat_name):
            return _bad_request("No stat points available")

        # Persist
        setattr(player, stat_name, player_dict[stat_name])
        player.stat_points = player_dict["stat_points"]
        player.hp = player_dict["hp"]
        player.mp = player_dict["mp"]
        db.commit()

        return jsonify({
            "success": True,
            "stat_name": stat_name,
            "new_value": player_dict[stat_name],
            "stat_points_remaining": player_dict["stat_points"],
        })
    finally:
        db.close()


@player_bp.route("/<int:player_id>/skills", methods=["GET"])
def get_skills(player_id: int):
    """Get player skill tree. Requirement 22.5"""
    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _player_not_found(player_id)

        all_skills = db.query(Skill).all()
        player_skills = db.query(PlayerSkill).filter(PlayerSkill.player_id == player_id).all()
        unlocked_ids = {ps.skill_id: ps.current_level for ps in player_skills}

        skill_tree = []
        for skill in all_skills:
            skill_tree.append({
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "skill_type": skill.skill_type,
                "max_level": skill.max_level,
                "unlock_level": skill.unlock_level,
                "prerequisite_skill_id": skill.prerequisite_skill_id,
                "unlocked": skill.id in unlocked_ids,
                "current_level": unlocked_ids.get(skill.id, 0),
                "can_unlock": _skill_system.can_unlock_skill(player.level, skill.unlock_level),
            })

        return jsonify({
            "skill_points_available": player.skill_points,
            "skills": skill_tree,
        })
    finally:
        db.close()


@player_bp.route("/<int:player_id>/skills/unlock", methods=["POST"])
def unlock_skill_endpoint(player_id: int):
    """Unlock a skill for a player (if level requirement met)."""
    data = request.get_json(silent=True) or {}
    skill_id = data.get("skill_id")
    if not skill_id:
        return _bad_request("skill_id is required")

    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _player_not_found(player_id)

        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            return _bad_request(f"Skill {skill_id} not found")

        if not _skill_system.can_unlock_skill(player.level, skill.unlock_level):
            return _bad_request(f"Requires level {skill.unlock_level} (you are level {player.level})")

        existing = db.query(PlayerSkill).filter(
            PlayerSkill.player_id == player_id,
            PlayerSkill.skill_id == skill_id,
        ).first()
        if existing:
            return jsonify({"success": True, "message": "Already unlocked", "current_level": existing.current_level})

        # Check prerequisite
        if skill.prerequisite_skill_id:
            has_prereq = db.query(PlayerSkill).filter(
                PlayerSkill.player_id == player_id,
                PlayerSkill.skill_id == skill.prerequisite_skill_id,
            ).first()
            if not has_prereq:
                return _bad_request("Prerequisite skill not unlocked")

        from datetime import datetime
        new_ps = PlayerSkill(
            player_id=player_id,
            skill_id=skill_id,
            current_level=1,
            unlocked_at=datetime.utcnow(),
        )
        db.add(new_ps)
        db.commit()

        return jsonify({"success": True, "skill_id": skill_id, "current_level": 1})
    finally:
        db.close()


@player_bp.route("/<int:player_id>/skills/allocate", methods=["POST"])
def allocate_skill(player_id: int):
    """Allocate a skill point. Requirement 22.6"""
    data = request.get_json(silent=True) or {}
    skill_id = data.get("skill_id")

    if not skill_id:
        return _bad_request("skill_id is required")

    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _player_not_found(player_id)

        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            return _bad_request(f"Skill {skill_id} not found")

        player_skill = db.query(PlayerSkill).filter(
            PlayerSkill.player_id == player_id,
            PlayerSkill.skill_id == skill_id,
        ).first()

        if not player_skill:
            return _bad_request("Skill not unlocked. Unlock the skill first.")

        p_dict = {"skill_points": player.skill_points}
        ps_dict = {"current_level": player_skill.current_level}

        if not _skill_system.allocate_skill_point(p_dict, ps_dict):
            return _bad_request("Cannot allocate skill point (no points or skill at max level)")

        player.skill_points = p_dict["skill_points"]
        player_skill.current_level = ps_dict["current_level"]
        db.commit()

        return jsonify({
            "success": True,
            "skill_id": skill_id,
            "new_level": ps_dict["current_level"],
            "skill_points_remaining": p_dict["skill_points"],
        })
    finally:
        db.close()


@player_bp.route("/<int:player_id>/notifications", methods=["GET"])
def get_notifications(player_id: int):
    """Get notifications for a player."""
    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _player_not_found(player_id)

        from src.models.notification import Notification
        notifications = (
            db.query(Notification)
            .filter(Notification.player_id == player_id)
            .order_by(Notification.created_at.desc())
            .limit(20)
            .all()
        )

        data = [
            {
                "id": n.id,
                "notification_type": n.notification_type,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ]
        return jsonify({"notifications": data, "unread_count": sum(1 for n in data if not n["is_read"])})
    finally:
        db.close()


@player_bp.route("/<int:player_id>/notifications/<int:notif_id>/read", methods=["POST"])
def mark_notification_read(player_id: int, notif_id: int):
    """Mark a notification as read."""
    db = SessionLocal()
    try:
        from src.models.notification import Notification
        n = db.query(Notification).filter(
            Notification.id == notif_id, Notification.player_id == player_id
        ).first()
        if not n:
            return jsonify({"error": "Notification not found"}), 404
        n.is_read = True
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()


@player_bp.route("/<int:player_id>/achievements", methods=["GET"])
def get_achievements(player_id: int):
    """Get all achievements with unlock status for a player."""
    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _player_not_found(player_id)

        from src.models.achievement import Achievement, PlayerAchievement
        all_achs = db.query(Achievement).all()
        player_achs = db.query(PlayerAchievement).filter(
            PlayerAchievement.player_id == player_id
        ).all()
        unlocked_map = {pa.achievement_id: pa.unlocked_at for pa in player_achs}

        achievements = []
        for ach in all_achs:
            achievements.append({
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "rarity": ach.rarity,
                "condition_type": ach.condition_type,
                "stat_bonus": ach.stat_bonus,
                "unlocked": ach.id in unlocked_map,
                "unlocked_at": (
                    unlocked_map[ach.id].isoformat()
                    if ach.id in unlocked_map and unlocked_map[ach.id]
                    else None
                ),
            })

        unlocked_count = sum(1 for a in achievements if a["unlocked"])
        return jsonify({
            "achievements": achievements,
            "total": len(achievements),
            "unlocked": unlocked_count,
            "completion_pct": round(unlocked_count / len(achievements) * 100, 1) if achievements else 0,
        })
    finally:
        db.close()


@player_bp.route("/<int:player_id>/quests/generate-daily", methods=["POST"])
def generate_daily_quests(player_id: int):
    """Generate today's daily quests for a player (if none exist today)."""
    from datetime import datetime
    from src.engine.quest_manager import QuestManager
    from src.models.quest import Quest

    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _player_not_found(player_id)

        today = datetime.utcnow().date()
        existing = db.query(Quest).filter(
            Quest.player_id == player_id,
            Quest.quest_type == "daily",
        ).all()
        todays = [q for q in existing if q.created_at and q.created_at.date() == today]

        if todays:
            return jsonify({"message": "Daily quests already exist", "count": len(todays), "generated": False})

        qm = QuestManager()
        quests_data = qm.create_daily_quests(player_id, datetime.utcnow())
        created = []
        for qd in quests_data:
            q = Quest(**qd)
            db.add(q)
            db.flush()
            created.append({"id": q.id, "title": q.title, "xp_reward": q.xp_reward})
        db.commit()
        return jsonify({"message": f"Created {len(created)} daily quests", "count": len(created), "generated": True, "quests": created})
    finally:
        db.close()


@player_bp.route("/<int:player_id>/analytics", methods=["GET"])
def get_analytics(player_id: int):
    """Get player analytics data for charts."""
    from datetime import datetime, timedelta
    from src.models.quest import Quest

    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return _player_not_found(player_id)

        days = request.args.get("days", 7, type=int) or 30

        # XP history: completed quests per day
        cutoff = datetime.utcnow() - timedelta(days=days)
        completed = db.query(Quest).filter(
            Quest.player_id == player_id,
            Quest.status == "completed",
            Quest.completed_at >= cutoff,
        ).all()

        # Group by date
        xp_by_date: dict = {}
        quests_by_type: dict = {"daily": 0, "main": 0, "instant": 0, "emergency": 0}
        for q in completed:
            if q.completed_at:
                d = q.completed_at.date().isoformat()
                xp_by_date[d] = xp_by_date.get(d, 0) + (q.xp_reward or 0)
            if q.quest_type in quests_by_type:
                quests_by_type[q.quest_type] += 1

        # Build time-series labels
        labels = []
        xp_data = []
        for i in range(days - 1, -1, -1):
            d = (datetime.utcnow() - timedelta(days=i)).date().isoformat()
            labels.append(d)
            xp_data.append(xp_by_date.get(d, 0))

        total_completed = db.query(Quest).filter(
            Quest.player_id == player_id,
            Quest.status == "completed",
        ).count()

        avg_xp = round(sum(xp_data) / days, 1) if days else 0

        return jsonify({
            "xp_over_time": {"labels": labels, "data": xp_data},
            "quests_by_type": quests_by_type,
            "stats": {
                "str_stat": player.str_stat,
                "int_stat": player.int_stat,
                "agi_stat": player.agi_stat,
                "vit_stat": player.vit_stat,
                "sen_stat": player.sen_stat,
                "luk_stat": player.luk_stat,
            },
            "kpis": {
                "total_quests_completed": total_completed,
                "avg_xp_per_day": avg_xp,
                "daily_streak": 0,  # Calculated separately
                "level": player.level,
                "rank": player.rank,
            },
        })
    finally:
        db.close()
