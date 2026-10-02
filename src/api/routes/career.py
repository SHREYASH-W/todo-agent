"""
Career Hunter API endpoints.

GET  /api/career/jobs              - Get matched jobs
POST /api/career/scrape            - Trigger job scraping
POST /api/career/applications      - Create application
GET  /api/career/applications      - Get application history
PUT  /api/career/applications/<id> - Update application status
POST /api/career/cover-letter      - Generate cover letter

Requirements: 15.1-21.7
"""

from flask import Blueprint, jsonify, request

from src.models import SessionLocal, Player
from src.models.job import Job
from src.models.application import Application
from src.models.job_match import JobMatch
from src.modules.career_hunter import CareerHunterModule
from src.services.job_scraper import get_job_scraper
from src.services.ai_assistant import get_ai_assistant
from src.engine.progression_engine import ProgressionEngine

career_bp = Blueprint("career", __name__, url_prefix="/api/career")

_progression = ProgressionEngine()


def _get_career_module() -> CareerHunterModule:
    return CareerHunterModule(
        job_scraper=get_job_scraper(),
        ai_assistant=get_ai_assistant(),
        progression_engine=_progression,
    )


def _app_to_dict(a: Application) -> dict:
    return {
        "id": a.id,
        "player_id": a.player_id,
        "job_id": a.job_id,
        "status": a.status,
        "cover_letter": a.cover_letter,
        "notes": a.notes,
        "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        "interview_date": a.interview_date.isoformat() if a.interview_date else None,
    }


def _job_to_dict(j: Job) -> dict:
    return {
        "id": j.id,
        "source": j.source,
        "title": j.title,
        "company": j.company,
        "location": j.location,
        "description": j.description,
        "url": j.url,
        "posted_date": j.posted_date.isoformat() if j.posted_date else None,
        "scraped_at": j.scraped_at.isoformat() if j.scraped_at else None,
    }


@career_bp.route("/jobs", methods=["GET"])
def get_jobs():
    """Get matched jobs for a player. Requirement 16.4, 16.5"""
    player_id = request.args.get("player_id", type=int)
    min_score = request.args.get("min_score", 0, type=int)

    if not player_id:
        return jsonify({"error": "player_id required"}), 400

    db = SessionLocal()
    try:
        query = db.query(JobMatch, Job).join(Job, JobMatch.job_id == Job.id).filter(
            JobMatch.player_id == player_id,
            JobMatch.match_score >= min_score,
        ).order_by(JobMatch.match_score.desc()).limit(20)

        results = []
        for match, job in query:
            job_dict = _job_to_dict(job)
            job_dict["match_score"] = match.match_score
            job_dict["matching_skills"] = match.matching_skills
            results.append(job_dict)

        return jsonify({"jobs": results, "total": len(results)})
    finally:
        db.close()


@career_bp.route("/scrape", methods=["POST"])
def trigger_scrape():
    """Trigger job scraping. Requirement 15.1-15.7"""
    data = request.get_json(silent=True) or {}
    keywords = data.get("keywords", ["Python Developer", "Software Engineer"])
    location = data.get("location", "")
    sources = data.get("sources", ["linkedin", "indeed"])

    try:
        career = _get_career_module()
        jobs = career.scrape_jobs(sources, keywords, location)
        return jsonify({
            "success": True,
            "jobs_found": len(jobs),
            "keywords": keywords,
            "location": location,
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 503


@career_bp.route("/applications", methods=["POST"])
def create_application():
    """Create a new job application. Requirement 17.5, 17.6, 17.7"""
    data = request.get_json(silent=True) or {}
    player_id = data.get("player_id")
    job_id = data.get("job_id")
    cover_letter = data.get("cover_letter", "")

    if not player_id or not job_id:
        return jsonify({"error": "player_id and job_id are required"}), 400

    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return jsonify({"error": f"Player {player_id} not found"}), 404

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return jsonify({"error": f"Job {job_id} not found"}), 404

        # Award XP for applying
        p_dict = {"level": player.level, "xp": player.xp, "rank": player.rank,
                  "gold": player.gold, "stat_points": player.stat_points,
                  "skill_points": player.skill_points,
                  "hp": player.hp, "mp": player.mp,
                  "vit_stat": player.vit_stat, "int_stat": player.int_stat}
        _progression.award_xp(p_dict, 50)
        player.xp = p_dict["xp"]
        player.level = p_dict["level"]
        player.rank = p_dict["rank"]
        player.stat_points = p_dict["stat_points"]
        player.skill_points = p_dict["skill_points"]

        from datetime import datetime
        application = Application(
            player_id=player_id,
            job_id=job_id,
            status="submitted",
            cover_letter=cover_letter,
            submitted_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(application)
        db.commit()
        db.refresh(application)

        return jsonify(_app_to_dict(application)), 201
    finally:
        db.close()


@career_bp.route("/applications", methods=["GET"])
def get_applications():
    """Get application history. Requirement 18.3, 18.6"""
    player_id = request.args.get("player_id", type=int)
    status_filter = request.args.get("status")

    if not player_id:
        return jsonify({"error": "player_id required"}), 400

    db = SessionLocal()
    try:
        query = db.query(Application).filter(Application.player_id == player_id)
        if status_filter:
            query = query.filter(Application.status == status_filter)
        applications = query.order_by(Application.submitted_at.desc()).all()

        career = CareerHunterModule()
        app_dicts = [_app_to_dict(a) for a in applications]
        stats = career.get_application_stats(app_dicts)

        return jsonify({"applications": app_dicts, "stats": stats, "total": len(app_dicts)})
    finally:
        db.close()


@career_bp.route("/applications/<int:app_id>", methods=["PUT"])
def update_application(app_id: int):
    """Update application status. Requirement 18.2"""
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    player_id = data.get("player_id")

    if not new_status:
        return jsonify({"error": "status is required"}), 400

    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.id == app_id).first()
        if not app:
            return jsonify({"error": f"Application {app_id} not found"}), 404

        career = CareerHunterModule()
        app_dict = _app_to_dict(app)

        if not career.update_application_status(app_dict, new_status):
            return jsonify({
                "error": f"Invalid status transition: {app.status} -> {new_status}"
            }), 400

        app.status = new_status
        from datetime import datetime
        app.updated_at = datetime.utcnow()
        if new_status == "interview" and data.get("interview_date"):
            app.interview_date = datetime.fromisoformat(data["interview_date"])
        if data.get("notes"):
            app.notes = data["notes"]

        db.commit()
        return jsonify(_app_to_dict(app))
    finally:
        db.close()


@career_bp.route("/cover-letter", methods=["POST"])
def generate_cover_letter():
    """Generate AI cover letter. Requirement 17.2, 17.3, 28.1-28.7"""
    data = request.get_json(silent=True) or {}
    job_description = data.get("job_description", "")
    resume = data.get("resume", "")
    job_title = data.get("job_title", "the position")
    company = data.get("company", "your company")

    if not job_description:
        return jsonify({"error": "job_description is required"}), 400

    try:
        ai = get_ai_assistant()
        if not ai.is_available():
            return jsonify({
                "error": "AI service unavailable. Please ensure Ollama is running.",
                "cover_letter": None,
            }), 503

        cover_letter = ai.generate_cover_letter(
            job_description,
            resume or f"Experienced professional applying for {job_title} at {company}.",
        )
        return jsonify({"cover_letter": cover_letter, "success": True})
    except Exception as e:
        return jsonify({"error": str(e), "cover_letter": None}), 503
