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
