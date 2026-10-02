"""
Module API endpoints.

GET /api/modules                   - Available modules for player
GET /api/modules/<name>/dashboard  - Module dashboard data

Requirements: 14.1-14.8, 26.1-26.7
"""

from flask import Blueprint, jsonify, request

from src.engine.module_manager import ModuleManager
from src.models import SessionLocal, Player

modules_bp = Blueprint("modules", __name__, url_prefix="/api/modules")
_module_mgr = ModuleManager()


def _get_player(db, player_id):
    return db.query(Player).filter(Player.id == player_id).first()


@modules_bp.route("", methods=["GET"])
def get_modules():
    """Get available modules based on player rank. Requirement 14.8"""
    player_id = request.args.get("player_id", type=int)
    if not player_id:
        return jsonify({"error": "player_id required"}), 400

    db = SessionLocal()
    try:
        player = _get_player(db, player_id)
        if not player:
            return jsonify({"error": f"Player {player_id} not found"}), 404

        modules = _module_mgr.get_available_modules(player.rank)
        return jsonify({"modules": modules, "player_rank": player.rank})
    finally:
        db.close()


@modules_bp.route("/<module_name>/dashboard", methods=["GET"])
def get_module_dashboard(module_name: str):
    """Get module dashboard data. Requirement 26.1-26.7"""
    player_id = request.args.get("player_id", type=int)
    if not player_id:
        return jsonify({"error": "player_id required"}), 400

    db = SessionLocal()
    try:
        player = _get_player(db, player_id)
        if not player:
            return jsonify({"error": f"Player {player_id} not found"}), 404

        if not _module_mgr.check_module_unlock(player.rank, module_name):
            from src.engine.module_manager import MODULE_UNLOCK_REQUIREMENTS, MODULE_DISPLAY_NAMES
            required = MODULE_UNLOCK_REQUIREMENTS.get(module_name, "Unknown")
            return jsonify({
                "error": "Module locked",
                "module": module_name,
                "display_name": MODULE_DISPLAY_NAMES.get(module_name, module_name),
                "required_rank": required,
                "player_rank": player.rank,
            }), 403

        # Route to the appropriate module
        data = _get_module_dashboard_data(module_name, player_id)
        return jsonify(data)
    finally:
        db.close()


def _get_module_dashboard_data(module_name: str, player_id: int) -> dict:
    """Fetch dashboard data from the relevant module class."""
    if module_name == "career_hunter":
        db = SessionLocal()
        try:
            from src.models.application import Application
            from src.models.job_match import JobMatch
            app_count = db.query(Application).filter(Application.player_id == player_id).count()
            match_count = db.query(JobMatch).filter(JobMatch.player_id == player_id).count()
            return {
                "module": "career_hunter",
                "total_applications": app_count,
                "total_job_matches": match_count,
            }
        finally:
            db.close()

    module_classes = {
        "skill_trainer": ("src.modules.skill_trainer", "SkillTrainerModule"),
        "fitness_hunter": ("src.modules.fitness_hunter", "FitnessHunterModule"),
        "finance_manager": ("src.modules.finance_manager", "FinanceManagerModule"),
        "social_network": ("src.modules.social_network", "SocialNetworkModule"),
        "habit_forge": ("src.modules.habit_forge", "HabitForgeModule"),
    }

    if module_name in module_classes:
        module_path, class_name = module_classes[module_name]
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        return cls().get_dashboard_data(player_id)

    return {"module": module_name, "error": "Unknown module"}
