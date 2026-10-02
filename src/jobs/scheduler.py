"""
Background Job Scheduler for LifeHunter System

Implements scheduled tasks using APScheduler:
- Daily quest generation at midnight          (Requirement 4.1)
- Job scraping every 6 hours                  (Requirement 15.6)
- Database backup daily at 02:00 AM
- Penalty zone check at midnight              (Requirement 8.1)
- Achievement check triggered on actions

Requirements: 4.1, 15.6, Backup, 8.1
"""

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


# ── Job Functions ───────────────────────────────────────────

def job_generate_daily_quests():
    """Generate daily quests for all active players at midnight. Requirement 4.1"""
    logger.info(f"[scheduler] Generating daily quests at {datetime.utcnow().isoformat()}")
    try:
        from src.models import SessionLocal, Player
        from src.engine.quest_manager import QuestManager
        from src.models.quest import Quest

        db = SessionLocal()
        qm = QuestManager()
        try:
            players = db.query(Player).all()
            today   = datetime.utcnow()
            created = 0
            for player in players:
                quests_data = qm.create_daily_quests(player.id, today)
                for qd in quests_data:
                    db.add(Quest(**qd))
                    created += 1
            db.commit()
            logger.info(f"[scheduler] Created {created} daily quests for {len(players)} players")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[scheduler] Daily quest generation failed: {e}")


def job_check_penalty_zones():
    """Activate penalty zones for players who failed daily quests. Requirement 8.1"""
    logger.info(f"[scheduler] Checking penalty zones at {datetime.utcnow().isoformat()}")
    try:
        from src.models import SessionLocal, Player
        from src.models.quest import Quest
        from src.engine.quest_manager import QuestManager

        db  = SessionLocal()
        qm  = QuestManager()
        now = datetime.utcnow()
        try:
            players = db.query(Player).all()
            for player in players:
                today_quests = db.query(Quest).filter(
                    Quest.player_id == player.id,
                    Quest.quest_type == "daily",
                ).all()
                quest_dicts = [
                    {"id": q.id, "quest_type": q.quest_type,
                     "status": q.status, "deadline": q.deadline}
                    for q in today_quests
                ]
                if qm.check_daily_quest_failure(quest_dicts, now):
                    logger.warning(f"[scheduler] Player {player.id} failed daily quests — penalty zone")
                    # Notification created by notification_service; penalty activated in-game
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[scheduler] Penalty zone check failed: {e}")


def job_scrape_jobs():
    """Scrape job listings from all sources every 6 hours. Requirement 15.6"""
    logger.info(f"[scheduler] Job scraping started at {datetime.utcnow().isoformat()}")
    try:
        from src.services.job_scraper import get_job_scraper
        from src.models import SessionLocal
        from src.models.job import Job

        scraper  = get_job_scraper()
        keywords = ["Python Developer", "Software Engineer", "Full Stack Developer"]
        jobs     = scraper.scrape_all(keywords)

        if jobs:
            db = SessionLocal()
            try:
                added = 0
                for jd in jobs:
                    jd_dict = jd.to_dict() if hasattr(jd, "to_dict") else jd
                    existing = db.query(Job).filter(Job.url == jd_dict.get("url")).first()
                    if not existing:
                        db.add(Job(**jd_dict))
                        added += 1
                db.commit()
                logger.info(f"[scheduler] Saved {added} new jobs to database")
            finally:
                db.close()
    except Exception as e:
        logger.error(f"[scheduler] Job scraping failed: {e}")


def job_backup_database():
    """Create daily database backup at 02:00 AM."""
    logger.info(f"[scheduler] Database backup started at {datetime.utcnow().isoformat()}")
    try:
        from src.services.database_manager import get_database_manager
        import os

        os.makedirs("backups", exist_ok=True)
        ts      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path    = f"backups/lifehunter_{ts}.db"
        db_mgr  = get_database_manager()
        success = db_mgr.backup_database(path)
        if success:
            logger.info(f"[scheduler] Backup saved to {path}")
    except Exception as e:
        logger.error(f"[scheduler] Database backup failed: {e}")


# ── Scheduler Management ────────────────────────────────────

def start_scheduler():
    """Start the background scheduler with all jobs."""
    global _scheduler

    if _scheduler and _scheduler.running:
        logger.warning("[scheduler] Already running")
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="UTC")

    # Daily quests at midnight UTC
    _scheduler.add_job(
        job_generate_daily_quests,
        CronTrigger(hour=0, minute=0, second=5),
        id="daily_quests",
        name="Generate Daily Quests",
        replace_existing=True,
    )

    # Penalty zone check at midnight + 1 min
    _scheduler.add_job(
        job_check_penalty_zones,
        CronTrigger(hour=0, minute=1, second=0),
        id="penalty_zones",
        name="Check Penalty Zones",
        replace_existing=True,
    )

    # Job scraping every 6 hours
    _scheduler.add_job(
        job_scrape_jobs,
        IntervalTrigger(hours=6),
        id="job_scraping",
        name="Scrape Job Listings",
        replace_existing=True,
    )

    # Database backup at 02:00 AM daily
    _scheduler.add_job(
        job_backup_database,
        CronTrigger(hour=2, minute=0, second=0),
        id="db_backup",
        name="Database Backup",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("[scheduler] Background scheduler started with 4 jobs")
    return _scheduler


def stop_scheduler():
    """Stop the background scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[scheduler] Background scheduler stopped")


def get_scheduler() -> BackgroundScheduler | None:
    """Return the global scheduler instance."""
    return _scheduler
