"""
LifeHunter Flask Application

Entry point for the web server. Registers all API blueprints,
serves frontend templates, wires security middleware, logging,
and background scheduler.

Usage:
    python -m src.app
    # or
    flask --app src.app run --debug
"""

from flask import Flask, jsonify, render_template, redirect, url_for

from src.api.routes.player import player_bp
from src.api.routes.quest import quest_bp
from src.api.routes.career import career_bp
from src.api.routes.modules import modules_bp
from src.api.routes.auth import auth_bp
from src.utils.logger import setup_logging
from src.utils.security import register_security_middleware
from src.utils.error_handler import register_flask_error_handlers
from src.config.config import get_config


def create_app() -> Flask:
    """Application factory."""
    cfg = get_config()

    # Configure logging before anything else
    setup_logging(level=cfg.log_level, log_file=cfg.log_file)

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config["SECRET_KEY"] = cfg.secret_key
    app.config["JSON_SORT_KEYS"] = False

    # ── API Blueprints ──────────────────────────────────────
    app.register_blueprint(player_bp)
    app.register_blueprint(quest_bp)
    app.register_blueprint(career_bp)
    app.register_blueprint(modules_bp)
    app.register_blueprint(auth_bp)

    # ── Security middleware ─────────────────────────────────
    register_security_middleware(app)
    register_flask_error_handlers(app)

    # ── HTML page routes ────────────────────────────────────
    @app.route("/")
    def index():
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html", player_id=1)

    @app.route("/quests")
    def quests():
        return render_template("quest_log.html", player_id=1)

    @app.route("/skills")
    def skills():
        return render_template("skill_tree.html", player_id=1)

    @app.route("/achievements")
    def achievements():
        return render_template("achievements.html", player_id=1)

    @app.route("/modules")
    def modules():
        return render_template("modules.html", player_id=1)

    @app.route("/modules/<module_name>")
    def module_page(module_name):
        template_map = {
            "career_hunter":  "modules/career_hunter.html",
            "skill_trainer":  "modules/skill_trainer.html",
            "fitness_hunter": "modules/fitness_hunter.html",
            "finance_manager":"modules/finance_manager.html",
            "social_network": "modules/social_network.html",
            "habit_forge":    "modules/habit_forge.html",
        }
        tmpl = template_map.get(module_name)
        if not tmpl:
            return jsonify({"error": "Unknown module"}), 404
        return render_template(tmpl, player_id=1)

    @app.route("/analytics")
    def analytics():
        return render_template("analytics.html", player_id=1)

    @app.route("/logout")
    def logout():
        return redirect(url_for("index"))

    # ── Health check ─────────────────────────────────────────
    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "app": "LifeHunter"})

    return app


def main():
    """Start the application with background scheduler."""
    from src.jobs.scheduler import start_scheduler, stop_scheduler
    import atexit

    app = create_app()

    # Start background jobs
    start_scheduler()
    atexit.register(stop_scheduler)

    app.run(debug=False, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
