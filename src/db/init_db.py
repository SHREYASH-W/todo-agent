"""
Database initialization script for LifeHunter system.

This module provides functions to:
- Create all database tables using SQLAlchemy metadata
- Seed initial data for skills, achievements, titles
- Validate database connection
- Initialize the complete database from scratch
"""

import json
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text

from src.models import (
    Base,
    engine,
    SessionLocal,
    Skill,
    Achievement,
    Title,
    Job,
    JobMatch,
    Application,
)


def validate_connection() -> bool:
    """
    Validate database connection by executing a simple query.
    
    Returns:
        bool: True if connection is valid, False otherwise
        
    Example:
        if validate_connection():
            print("Database connection is valid")
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        return True
    except OperationalError as e:
        print(f"Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during connection validation: {e}")
        return False


def create_all_tables() -> bool:
    """
    Create all database tables using SQLAlchemy metadata.
    
    This function creates tables for all entities defined in the models:
    - Player
    - Quest
    - Skill, PlayerSkill
    - Achievement, PlayerAchievement
    - Title, PlayerTitle
    - InventoryItem
    - Notification
    - Job, JobMatch, Application
    - PerformanceLog, DatabaseBackup
    
    Returns:
        bool: True if tables were created successfully, False otherwise
        
    Example:
        if create_all_tables():
            print("All tables created successfully")
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ All database tables created successfully")
        return True
    except SQLAlchemyError as e:
        print(f"✗ Error creating tables: {e}")
        return False


def seed_skills() -> bool:
    """
    Seed initial skills into the database.
    
    Creates a comprehensive skill tree with both active and passive skills
    across different player level requirements.
    
    Returns:
        bool: True if skills were seeded successfully, False otherwise
    """
    skills_data = [
        # === Early Game Skills (Level 1-10) ===
        {
            "name": "Task Focus",
            "description": "Passive ability that increases XP gain from daily quests by 5% per level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 1,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Quick Learner",
            "description": "Passive ability that increases INT stat effectiveness by 2% per level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 3,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Rush Hour",
            "description": "Active skill that doubles XP gain for 1 hour. Cooldown: 24 hours.",
            "skill_type": "active",
            "max_level": 5,
            "unlock_level": 5,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Stamina Boost",
            "description": "Passive ability that increases HP regeneration by 5% per level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 7,
            "prerequisite_skill_id": None,
        },
        
        # === Mid Game Skills (Level 10-40) ===
        {
            "name": "Multi-Tasking",
            "description": "Passive ability that allows completing 2 quests simultaneously. Unlocks at max level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 10,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Career Momentum",
            "description": "Passive ability that increases job match scores by 3% per level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 10,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Golden Touch",
            "description": "Passive ability that increases gold rewards from quests by 10% per level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 15,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Second Wind",
            "description": "Active skill that restores 50% HP and removes all negative status effects. Cooldown: 48 hours.",
            "skill_type": "active",
            "max_level": 5,
            "unlock_level": 20,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Strategic Mind",
            "description": "Passive ability that reveals optimal quest completion order. Increases quest efficiency by 5% per level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 25,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Interview Mastery",
            "description": "Passive ability that increases interview preparation quest XP by 15% per level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 30,
            "prerequisite_skill_id": None,
        },
        
        # === Late Game Skills (Level 40-60) ===
        {
            "name": "Overdrive",
            "description": "Active skill that triples XP gain for 30 minutes. Cooldown: 72 hours.",
            "skill_type": "active",
            "max_level": 5,
            "unlock_level": 40,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Perfect Execution",
            "description": "Passive ability that grants bonus XP for completing quests before deadline. +20% per level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 45,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Network Effect",
            "description": "Passive ability that increases networking quest rewards by 25% per level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 50,
            "prerequisite_skill_id": None,
        },
        
        # === End Game Skills (Level 60+) ===
        {
            "name": "Unstoppable",
            "description": "Passive ability that prevents penalty zone activation. Unlock at max level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 60,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Master of All",
            "description": "Passive ability that grants +1 to all stats per level.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 70,
            "prerequisite_skill_id": None,
        },
        {
            "name": "Limit Break",
            "description": "Active skill that removes all cooldowns and grants 5x XP for 15 minutes. Cooldown: 168 hours (1 week).",
            "skill_type": "active",
            "max_level": 1,
            "unlock_level": 80,
            "prerequisite_skill_id": None,
        },
        {
            "name": "National Authority",
            "description": "Passive ability exclusive to National Level players. All quest rewards increased by 100%.",
            "skill_type": "passive",
            "max_level": 10,
            "unlock_level": 100,
            "prerequisite_skill_id": None,
        },
    ]
    
    db = SessionLocal()
    try:
        # Check if skills already exist
        existing_count = db.query(Skill).count()
        if existing_count > 0:
            print(f"⚠ Skills already seeded ({existing_count} skills exist). Skipping...")
            return True
        
        # Add all skills
        for skill_data in skills_data:
            skill = Skill(**skill_data)
            db.add(skill)
        
        db.commit()
        print(f"✓ Seeded {len(skills_data)} skills successfully")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"✗ Error seeding skills: {e}")
        return False
    finally:
        db.close()


def seed_achievements() -> bool:
    """
    Seed initial achievements into the database.
    
    Creates achievements across all rarity tiers with various unlock conditions.
    
    Returns:
        bool: True if achievements were seeded successfully, False otherwise
    """
    achievements_data = [
        # === Common Achievements ===
        {
            "name": "First Steps",
            "description": "Complete your first quest and begin your journey as a LifeHunter.",
            "rarity": "common",
            "condition_type": "quest_count",
            "condition_value": json.dumps({"count": 1}),
            "stat_bonus": json.dumps({"xp_bonus": 50}),
            "icon_url": "/static/images/achievements/first_steps.png",
        },
        {
            "name": "Getting Started",
            "description": "Reach level 5 and unlock your potential.",
            "rarity": "common",
            "condition_type": "level",
            "condition_value": json.dumps({"level": 5}),
            "stat_bonus": json.dumps({"str_stat": 1, "int_stat": 1}),
            "icon_url": "/static/images/achievements/getting_started.png",
        },
        {
            "name": "Daily Grind",
            "description": "Complete 7 consecutive days of daily quests.",
            "rarity": "common",
            "condition_type": "custom",
            "condition_value": json.dumps({"type": "daily_streak", "days": 7}),
            "stat_bonus": json.dumps({"gold_bonus": 100}),
            "icon_url": "/static/images/achievements/daily_grind.png",
        },
        {
            "name": "Quest Novice",
            "description": "Complete 10 quests of any type.",
            "rarity": "common",
            "condition_type": "quest_count",
            "condition_value": json.dumps({"count": 10}),
            "stat_bonus": json.dumps({"xp_bonus": 100}),
            "icon_url": "/static/images/achievements/quest_novice.png",
        },
        
        # === Rare Achievements ===
        {
            "name": "Rising Star",
            "description": "Reach level 25 and unlock D-Rank capabilities.",
            "rarity": "rare",
            "condition_type": "level",
            "condition_value": json.dumps({"level": 25}),
            "stat_bonus": json.dumps({"str_stat": 3, "int_stat": 3, "agi_stat": 2}),
            "icon_url": "/static/images/achievements/rising_star.png",
        },
        {
            "name": "Career Hunter",
            "description": "Submit 25 job applications through the Career Hunter module.",
            "rarity": "rare",
            "condition_type": "custom",
            "condition_value": json.dumps({"type": "applications", "count": 25}),
            "stat_bonus": json.dumps({"int_stat": 5, "luk_stat": 3}),
            "icon_url": "/static/images/achievements/career_hunter.png",
        },
        {
            "name": "Dedicated",
            "description": "Complete 30 consecutive days of daily quests.",
            "rarity": "rare",
            "condition_type": "custom",
            "condition_value": json.dumps({"type": "daily_streak", "days": 30}),
            "stat_bonus": json.dumps({"vit_stat": 5, "gold_bonus": 500}),
            "icon_url": "/static/images/achievements/dedicated.png",
        },
        {
            "name": "Quest Adept",
            "description": "Complete 50 quests of any type.",
            "rarity": "rare",
            "condition_type": "quest_count",
            "condition_value": json.dumps({"count": 50}),
            "stat_bonus": json.dumps({"xp_bonus": 500}),
            "icon_url": "/static/images/achievements/quest_adept.png",
        },
        {
            "name": "Speed Runner",
            "description": "Complete 5 Instant Dungeons with perfect timing.",
            "rarity": "rare",
            "condition_type": "custom",
            "condition_value": json.dumps({"type": "instant_dungeon_perfect", "count": 5}),
            "stat_bonus": json.dumps({"agi_stat": 5, "xp_bonus": 300}),
            "icon_url": "/static/images/achievements/speed_runner.png",
        },
        
        # === Epic Achievements ===
        {
            "name": "Elite Hunter",
            "description": "Reach level 60 and achieve A-Rank status.",
            "rarity": "epic",
            "condition_type": "level",
            "condition_value": json.dumps({"level": 60}),
            "stat_bonus": json.dumps({"str_stat": 5, "int_stat": 5, "agi_stat": 5, "vit_stat": 5}),
            "icon_url": "/static/images/achievements/elite_hunter.png",
        },
        {
            "name": "Network Master",
            "description": "Complete 100 networking quests and build meaningful connections.",
            "rarity": "epic",
            "condition_type": "custom",
            "condition_value": json.dumps({"type": "networking_quests", "count": 100}),
            "stat_bonus": json.dumps({"int_stat": 10, "sen_stat": 10}),
            "icon_url": "/static/images/achievements/network_master.png",
        },
        {
            "name": "Unstoppable Force",
            "description": "Complete 100 consecutive days of daily quests.",
            "rarity": "epic",
            "condition_type": "custom",
            "condition_value": json.dumps({"type": "daily_streak", "days": 100}),
            "stat_bonus": json.dumps({"all_stats": 10, "gold_bonus": 5000}),
            "icon_url": "/static/images/achievements/unstoppable_force.png",
        },
        {
            "name": "Quest Master",
            "description": "Complete 200 quests of any type.",
            "rarity": "epic",
            "condition_type": "quest_count",
            "condition_value": json.dumps({"count": 200}),
            "stat_bonus": json.dumps({"xp_bonus": 2000}),
            "icon_url": "/static/images/achievements/quest_master.png",
        },
        
        # === Legendary Achievements ===
        {
            "name": "National Level Authority",
            "description": "Reach level 100 and achieve National Level rank. You stand among the elite.",
            "rarity": "legendary",
            "condition_type": "level",
            "condition_value": json.dumps({"level": 100}),
            "stat_bonus": json.dumps({"all_stats": 25, "xp_multiplier": 1.5}),
            "icon_url": "/static/images/achievements/national_level.png",
        },
        {
            "name": "Legendary Hunter",
            "description": "Complete 500 quests and cement your legacy.",
            "rarity": "legendary",
            "condition_type": "quest_count",
            "condition_value": json.dumps({"count": 500}),
            "stat_bonus": json.dumps({"all_stats": 20, "xp_bonus": 10000}),
            "icon_url": "/static/images/achievements/legendary_hunter.png",
        },
        {
            "name": "Eternal Dedication",
            "description": "Complete 365 consecutive days of daily quests. A full year of commitment.",
            "rarity": "legendary",
            "condition_type": "custom",
            "condition_value": json.dumps({"type": "daily_streak", "days": 365}),
            "stat_bonus": json.dumps({"all_stats": 50, "gold_bonus": 50000, "xp_multiplier": 2.0}),
            "icon_url": "/static/images/achievements/eternal_dedication.png",
        },
        {
            "name": "Perfect Score",
            "description": "Achieve 100% match score on 50 job applications.",
            "rarity": "legendary",
            "condition_type": "custom",
            "condition_value": json.dumps({"type": "perfect_matches", "count": 50}),
            "stat_bonus": json.dumps({"int_stat": 25, "luk_stat": 25, "sen_stat": 25}),
            "icon_url": "/static/images/achievements/perfect_score.png",
        },
    ]
    
    db = SessionLocal()
    try:
        # Check if achievements already exist
        existing_count = db.query(Achievement).count()
        if existing_count > 0:
            print(f"⚠ Achievements already seeded ({existing_count} achievements exist). Skipping...")
            return True
        
        # Add all achievements
        for achievement_data in achievements_data:
            achievement = Achievement(**achievement_data)
            db.add(achievement)
        
        db.commit()
        print(f"✓ Seeded {len(achievements_data)} achievements successfully")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"✗ Error seeding achievements: {e}")
        return False
    finally:
        db.close()


def seed_titles() -> bool:
    """
    Seed initial titles into the database.
    
    Creates earnable titles with stat bonuses that players can unlock
    and equip for passive benefits.
    
    Returns:
        bool: True if titles were seeded successfully, False otherwise
    """
    titles_data = [
        # === Early Game Titles ===
        {
            "name": "Novice Hunter",
            "description": "A beginner taking their first steps into the world of LifeHunter.",
            "unlock_condition": "Complete your first quest",
            "stat_bonuses": json.dumps({"xp_gain": 5}),  # +5% XP gain
        },
        {
            "name": "The Dedicated",
            "description": "One who maintains consistency through daily effort.",
            "unlock_condition": "Complete 7 consecutive daily quests",
            "stat_bonuses": json.dumps({"vit_stat": 2, "daily_quest_xp": 10}),
        },
        {
            "name": "Career Seeker",
            "description": "An ambitious individual actively pursuing career opportunities.",
            "unlock_condition": "Submit 10 job applications",
            "stat_bonuses": json.dumps({"int_stat": 3, "job_match_bonus": 5}),
        },
        
        # === Mid Game Titles ===
        {
            "name": "Skilled Combatant",
            "description": "A well-rounded individual with diverse capabilities.",
            "unlock_condition": "Unlock 10 different skills",
            "stat_bonuses": json.dumps({"str_stat": 3, "agi_stat": 3, "skill_effectiveness": 10}),
        },
        {
            "name": "Quest Enthusiast",
            "description": "Someone who eagerly tackles challenges and completes objectives.",
            "unlock_condition": "Complete 50 quests",
            "stat_bonuses": json.dumps({"xp_gain": 15, "quest_rewards": 10}),
        },
        {
            "name": "Network Builder",
            "description": "A master of connections who understands the value of relationships.",
            "unlock_condition": "Complete 50 networking quests",
            "stat_bonuses": json.dumps({"sen_stat": 5, "networking_xp": 25}),
        },
        {
            "name": "D-Rank Hunter",
            "description": "A capable hunter who has proven their worth.",
            "unlock_condition": "Reach D-Rank (Level 10)",
            "stat_bonuses": json.dumps({"all_stats": 2, "xp_gain": 10}),
        },
        {
            "name": "C-Rank Hunter",
            "description": "An experienced hunter with notable achievements.",
            "unlock_condition": "Reach C-Rank (Level 25)",
            "stat_bonuses": json.dumps({"all_stats": 4, "xp_gain": 15}),
        },
        
        # === Late Game Titles ===
        {
            "name": "B-Rank Hunter",
            "description": "An elite hunter recognized for exceptional performance.",
            "unlock_condition": "Reach B-Rank (Level 40)",
            "stat_bonuses": json.dumps({"all_stats": 6, "xp_gain": 20, "gold_gain": 15}),
        },
        {
            "name": "A-Rank Hunter",
            "description": "A master hunter operating at the highest levels of excellence.",
            "unlock_condition": "Reach A-Rank (Level 60)",
            "stat_bonuses": json.dumps({"all_stats": 8, "xp_gain": 25, "gold_gain": 20}),
        },
        {
            "name": "The Relentless",
            "description": "One who never gives up, pushing through every challenge.",
            "unlock_condition": "Complete 100 consecutive daily quests",
            "stat_bonuses": json.dumps({"vit_stat": 15, "penalty_resistance": 50}),
        },
        {
            "name": "Fortune's Favorite",
            "description": "Blessed with exceptional luck in all endeavors.",
            "unlock_condition": "Unlock 5 legendary achievements",
            "stat_bonuses": json.dumps({"luk_stat": 20, "rare_drop_rate": 25}),
        },
        
        # === End Game Titles ===
        {
            "name": "S-Rank Hunter",
            "description": "A legendary hunter whose reputation precedes them.",
            "unlock_condition": "Reach S-Rank (Level 80)",
            "stat_bonuses": json.dumps({"all_stats": 10, "xp_gain": 30, "gold_gain": 30, "all_rewards": 15}),
        },
        {
            "name": "National Level Hunter",
            "description": "The pinnacle of achievement. A hunter who stands above all others.",
            "unlock_condition": "Reach National Level (Level 100)",
            "stat_bonuses": json.dumps({"all_stats": 25, "xp_gain": 50, "gold_gain": 50, "all_rewards": 25}),
        },
        {
            "name": "The Immortal",
            "description": "One who has maintained unwavering dedication for an entire year.",
            "unlock_condition": "Complete 365 consecutive daily quests",
            "stat_bonuses": json.dumps({"all_stats": 30, "xp_multiplier": 2.0, "immunity": 100}),
        },
        {
            "name": "Legend",
            "description": "A mythical figure whose accomplishments will be remembered forever.",
            "unlock_condition": "Complete 500 quests and reach National Level",
            "stat_bonuses": json.dumps({"all_stats": 50, "xp_multiplier": 2.5, "gold_multiplier": 2.0, "perfect_completion": 100}),
        },
    ]
    
    db = SessionLocal()
    try:
        # Check if titles already exist
        existing_count = db.query(Title).count()
        if existing_count > 0:
            print(f"⚠ Titles already seeded ({existing_count} titles exist). Skipping...")
            return True
        
        # Add all titles
        for title_data in titles_data:
            title = Title(**title_data)
            db.add(title)
        
        db.commit()
        print(f"✓ Seeded {len(titles_data)} titles successfully")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"✗ Error seeding titles: {e}")
        return False
    finally:
        db.close()


def seed_jobs() -> bool:
    """
    Seed sample job listings into the database.
    
    Creates diverse job postings for testing job scraping, matching,
    and application tracking functionality.
    
    Returns:
        bool: True if jobs were seeded successfully, False otherwise
    """
    jobs_data = [
        # === Software Development Jobs ===
        {
            "source": "linkedin",
            "title": "Senior Python Developer",
            "company": "TechCorp Inc",
            "location": "San Francisco, CA (Remote)",
            "description": "We're seeking a Senior Python Developer with 5+ years of experience. Must have expertise in Django/Flask, SQLAlchemy, REST APIs, and database design. Experience with AI/ML integration and MCP protocols is a plus. You'll work on our core platform handling real-time data processing and gamification systems.",
            "url": "https://linkedin.com/jobs/senior-python-developer-techcorp-12345",
            "posted_date": datetime(2025, 1, 15, 10, 30, 0),
            "scraped_at": datetime.utcnow(),
        },
        {
            "source": "indeed",
            "title": "Full Stack Developer (Python/JavaScript)",
            "company": "StartupXYZ",
            "location": "Austin, TX",
            "description": "Join our fast-growing startup! We need a Full Stack Developer proficient in Python backend (FastAPI/Flask) and modern JavaScript frontend (React, Vue). Experience with SQLite, PostgreSQL, and RESTful API design required. Bonus: gamification, real-time systems, Chart.js.",
            "url": "https://indeed.com/jobs/fullstack-developer-startupxyz-67890",
            "posted_date": datetime(2025, 1, 18, 14, 0, 0),
            "scraped_at": datetime.utcnow(),
        },
        {
            "source": "linkedin",
            "title": "Backend Engineer - Python",
            "company": "CloudSolutions Ltd",
            "location": "Seattle, WA (Hybrid)",
            "description": "CloudSolutions is hiring a Backend Engineer with strong Python skills. Requirements: 3+ years Python, SQLAlchemy ORM, database optimization, API development, microservices architecture. Experience with job scheduling (APScheduler) and web scraping is valuable. Work on scalable cloud infrastructure.",
            "url": "https://linkedin.com/jobs/backend-engineer-cloudsolutions-24680",
            "posted_date": datetime(2025, 1, 20, 9, 15, 0),
            "scraped_at": datetime.utcnow(),
        },
        {
            "source": "indeed",
            "title": "Junior Python Developer",
            "company": "DevShop Agency",
            "location": "Remote",
            "description": "Entry-level opportunity for a Junior Python Developer! 1-2 years experience or strong bootcamp graduate. Knowledge of Python fundamentals, Flask/Django basics, SQL, and Git required. We'll train you in our tech stack including SQLAlchemy, REST APIs, and modern web development practices.",
            "url": "https://indeed.com/jobs/junior-python-developer-devshop-13579",
            "posted_date": datetime(2025, 1, 22, 11, 45, 0),
            "scraped_at": datetime.utcnow(),
        },
        {
            "source": "linkedin",
            "title": "AI/ML Engineer with Python",
            "company": "IntelliTech Systems",
            "location": "Boston, MA",
            "description": "IntelliTech is seeking an AI/ML Engineer. Must have 4+ years Python, experience with Ollama/LLMs, machine learning frameworks (TensorFlow, PyTorch), and data processing. You'll build intelligent systems for natural language processing, recommendation engines, and predictive analytics.",
            "url": "https://linkedin.com/jobs/ai-ml-engineer-intellitech-97531",
            "posted_date": datetime(2025, 1, 16, 13, 20, 0),
            "scraped_at": datetime.utcnow(),
        },
        
        # === Web Development Jobs ===
        {
            "source": "indeed",
            "title": "Frontend Developer (JavaScript/React)",
            "company": "WebWorks Studio",
            "location": "New York, NY",
            "description": "WebWorks needs a Frontend Developer specializing in React. Requirements: 3+ years JavaScript/ES6+, React hooks, state management (Redux/Context), responsive design, HTML5/CSS3. Experience with Chart.js for data visualization and real-time updates with Fetch API preferred.",
            "url": "https://indeed.com/jobs/frontend-developer-webworks-86420",
            "posted_date": datetime(2025, 1, 19, 16, 10, 0),
            "scraped_at": datetime.utcnow(),
        },
        {
            "source": "linkedin",
            "title": "Web Developer (Python/JavaScript)",
            "company": "DigitalCraft Solutions",
            "location": "Denver, CO (Remote)",
            "description": "DigitalCraft seeks a Web Developer with balanced frontend/backend skills. Python (Flask/FastAPI), JavaScript, HTML/CSS, SQL required. Build web applications, REST APIs, and interactive dashboards. Experience with gamification elements and progressive web apps is a plus.",
            "url": "https://linkedin.com/jobs/web-developer-digitalcraft-15935",
            "posted_date": datetime(2025, 1, 21, 10, 5, 0),
            "scraped_at": datetime.utcnow(),
        },
        
        # === Data & Analytics Jobs ===
        {
            "source": "indeed",
            "title": "Data Engineer - Python",
            "company": "DataFlow Analytics",
            "location": "Chicago, IL",
            "description": "DataFlow Analytics is hiring a Data Engineer. Strong Python skills required, plus experience with SQL databases (SQLite, PostgreSQL), data pipelines, ETL processes, and API integration. Familiarity with web scraping, scheduled jobs, and data validation workflows beneficial.",
            "url": "https://indeed.com/jobs/data-engineer-dataflow-75312",
            "posted_date": datetime(2025, 1, 17, 8, 40, 0),
            "scraped_at": datetime.utcnow(),
        },
        {
            "source": "linkedin",
            "title": "Database Administrator (SQL/Python)",
            "company": "SecureData Corp",
            "location": "Miami, FL",
            "description": "SecureData needs a Database Administrator with Python automation skills. Manage SQLite and PostgreSQL databases, optimize queries, implement backup strategies, write Python scripts for database operations. SQLAlchemy ORM experience and database security knowledge essential.",
            "url": "https://linkedin.com/jobs/database-admin-securedata-95175",
            "posted_date": datetime(2025, 1, 14, 15, 25, 0),
            "scraped_at": datetime.utcnow(),
        },
        
        # === DevOps & System Jobs ===
        {
            "source": "indeed",
            "title": "DevOps Engineer (Python/Automation)",
            "company": "AutomateNow Inc",
            "location": "Portland, OR",
            "description": "AutomateNow seeks a DevOps Engineer. Python scripting for automation, CI/CD pipelines, Git workflows, containerization (Docker), and infrastructure as code required. Experience with Flask/FastAPI deployment, monitoring systems, and scheduled task management preferred.",
            "url": "https://indeed.com/jobs/devops-engineer-automatenow-35791",
            "posted_date": datetime(2025, 1, 23, 12, 30, 0),
            "scraped_at": datetime.utcnow(),
        },
    ]
    
    db = SessionLocal()
    try:
        # Check if jobs already exist
        existing_count = db.query(Job).count()
        if existing_count > 0:
            print(f"⚠ Jobs already seeded ({existing_count} jobs exist). Skipping...")
            return True
        
        # Add all jobs
        for job_data in jobs_data:
            job = Job(**job_data)
            db.add(job)
        
        db.commit()
        print(f"✓ Seeded {len(jobs_data)} jobs successfully")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"✗ Error seeding jobs: {e}")
        return False
    finally:
        db.close()


def seed_job_matches() -> bool:
    """
    Seed sample job matches into the database.
    
    Creates job match records linking players to jobs with match scores.
    Note: This assumes player_id=1 exists for testing. In production,
    matches are generated dynamically by the Career Hunter module.
    
    Returns:
        bool: True if job matches were seeded successfully, False otherwise
    """
    # Note: Match scores are calculated based on hypothetical player skills
    # Player 1 is assumed to be a Python developer with web development skills
    job_matches_data = [
        {
            "player_id": 1,  # Assumes test player exists
            "job_id": 1,  # Senior Python Developer at TechCorp
            "match_score": 92,
            "matching_skills": json.dumps([
                "Python", "Django", "Flask", "SQLAlchemy", "REST APIs", 
                "Database Design", "Real-time Processing"
            ]),
            "calculated_at": datetime.utcnow(),
        },
        {
            "player_id": 1,
            "job_id": 2,  # Full Stack Developer at StartupXYZ
            "match_score": 88,
            "matching_skills": json.dumps([
                "Python", "Flask", "FastAPI", "JavaScript", "REST APIs",
                "SQLite", "PostgreSQL"
            ]),
            "calculated_at": datetime.utcnow(),
        },
        {
            "player_id": 1,
            "job_id": 3,  # Backend Engineer at CloudSolutions
            "match_score": 85,
            "matching_skills": json.dumps([
                "Python", "SQLAlchemy", "API Development", 
                "Database Optimization", "Web Scraping"
            ]),
            "calculated_at": datetime.utcnow(),
        },
        {
            "player_id": 1,
            "job_id": 4,  # Junior Python Developer at DevShop
            "match_score": 78,
            "matching_skills": json.dumps([
                "Python", "Flask", "SQL", "Git", "REST APIs"
            ]),
            "calculated_at": datetime.utcnow(),
        },
        {
            "player_id": 1,
            "job_id": 5,  # AI/ML Engineer at IntelliTech
            "match_score": 72,
            "matching_skills": json.dumps([
                "Python", "Data Processing", "Ollama/LLMs"
            ]),
            "calculated_at": datetime.utcnow(),
        },
        {
            "player_id": 1,
            "job_id": 6,  # Frontend Developer at WebWorks
            "match_score": 65,
            "matching_skills": json.dumps([
                "JavaScript", "HTML5/CSS3", "Chart.js", "Fetch API"
            ]),
            "calculated_at": datetime.utcnow(),
        },
        {
            "player_id": 1,
            "job_id": 7,  # Web Developer at DigitalCraft
            "match_score": 90,
            "matching_skills": json.dumps([
                "Python", "Flask", "FastAPI", "JavaScript", 
                "REST APIs", "SQL", "Web Applications"
            ]),
            "calculated_at": datetime.utcnow(),
        },
        {
            "player_id": 1,
            "job_id": 8,  # Data Engineer at DataFlow
            "match_score": 80,
            "matching_skills": json.dumps([
                "Python", "SQL", "SQLite", "PostgreSQL", 
                "API Integration", "Web Scraping"
            ]),
            "calculated_at": datetime.utcnow(),
        },
        {
            "player_id": 1,
            "job_id": 9,  # Database Administrator at SecureData
            "match_score": 75,
            "matching_skills": json.dumps([
                "SQL", "SQLite", "PostgreSQL", "SQLAlchemy", "Python"
            ]),
            "calculated_at": datetime.utcnow(),
        },
        {
            "player_id": 1,
            "job_id": 10,  # DevOps Engineer at AutomateNow
            "match_score": 70,
            "matching_skills": json.dumps([
                "Python", "Automation", "Git", "Flask/FastAPI Deployment"
            ]),
            "calculated_at": datetime.utcnow(),
        },
    ]
    
    db = SessionLocal()
    try:
        # Check if job matches already exist
        existing_count = db.query(JobMatch).count()
        if existing_count > 0:
            print(f"⚠ Job matches already seeded ({existing_count} matches exist). Skipping...")
            return True
        
        # Check if player_id=1 exists
        from src.models import Player
        player_exists = db.query(Player).filter(Player.id == 1).first() is not None
        if not player_exists:
            print("⚠ Player ID 1 does not exist. Skipping job match seeding.")
            print("  (Job matches will be generated when a player uses the Career Hunter module)")
            return True
        
        # Add all job matches
        for match_data in job_matches_data:
            job_match = JobMatch(**match_data)
            db.add(job_match)
        
        db.commit()
        print(f"✓ Seeded {len(job_matches_data)} job matches successfully")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"✗ Error seeding job matches: {e}")
        return False
    finally:
        db.close()


def seed_applications() -> bool:
    """
    Seed sample applications into the database.
    
    Creates application records showing various application statuses
    for testing the application tracking system.
    Note: This assumes player_id=1 exists for testing.
    
    Returns:
        bool: True if applications were seeded successfully, False otherwise
    """
    applications_data = [
        {
            "player_id": 1,  # Assumes test player exists
            "job_id": 1,  # Senior Python Developer at TechCorp
            "status": "interview",
            "cover_letter": "Dear Hiring Manager,\n\nI am writing to express my strong interest in the Senior Python Developer position at TechCorp Inc. With over 5 years of hands-on experience in Python development, including extensive work with Django, Flask, and SQLAlchemy, I am confident in my ability to contribute to your core platform.\n\nMy recent project involved building a gamification system with real-time data processing, which aligns perfectly with your requirements. I have deep expertise in REST API design, database optimization, and integrating AI/ML capabilities using modern protocols.\n\nI am particularly excited about TechCorp's innovative approach to platform development and would welcome the opportunity to discuss how my skills can contribute to your team's success.\n\nBest regards",
            "submitted_at": datetime(2025, 1, 16, 14, 30, 0),
            "updated_at": datetime(2025, 1, 23, 10, 15, 0),
            "interview_date": datetime(2025, 1, 28, 14, 0, 0),
            "notes": "Interview scheduled! Prepare system design questions and be ready to discuss gamification architecture.",
        },
        {
            "player_id": 1,
            "job_id": 7,  # Web Developer at DigitalCraft
            "status": "under_review",
            "cover_letter": "Dear DigitalCraft Solutions Team,\n\nI am excited to apply for the Web Developer position at DigitalCraft Solutions. My balanced skill set in both frontend JavaScript and backend Python development makes me an ideal candidate for this role.\n\nI have extensive experience with Flask and FastAPI for building robust REST APIs, combined with proficiency in modern JavaScript for creating interactive user interfaces. My recent work includes developing progressive web applications with gamification elements, which demonstrates my ability to create engaging user experiences.\n\nI would love to contribute to DigitalCraft's innovative projects and bring my full-stack expertise to your team.\n\nSincerely",
            "submitted_at": datetime(2025, 1, 20, 9, 45, 0),
            "updated_at": datetime(2025, 1, 22, 16, 20, 0),
            "interview_date": None,
            "notes": "Strong match score (90). Follow up in 5 days if no response.",
        },
        {
            "player_id": 1,
            "job_id": 2,  # Full Stack Developer at StartupXYZ
            "status": "submitted",
            "cover_letter": "Dear StartupXYZ Hiring Team,\n\nI am thrilled to apply for the Full Stack Developer position at your fast-growing startup. With comprehensive experience in Python backend development using FastAPI and Flask, along with modern JavaScript frontend frameworks, I can hit the ground running.\n\nMy technical expertise spans the full stack: RESTful API design, database management (SQLite, PostgreSQL), React for dynamic UIs, and real-time systems implementation. I've also worked with Chart.js for data visualization, which aligns with your bonus requirements.\n\nI'm passionate about startup environments and excited about the opportunity to contribute to StartupXYZ's growth.\n\nBest regards",
            "submitted_at": datetime(2025, 1, 23, 11, 20, 0),
            "updated_at": datetime(2025, 1, 23, 11, 20, 0),
            "interview_date": None,
            "notes": "Just submitted. High match score (88).",
        },
        {
            "player_id": 1,
            "job_id": 3,  # Backend Engineer at CloudSolutions
            "status": "rejected",
            "cover_letter": "Dear CloudSolutions Hiring Manager,\n\nI am interested in the Backend Engineer position at CloudSolutions Ltd. With 3+ years of Python development experience, I have built scalable microservices architectures and optimized database performance for high-traffic applications.\n\nMy expertise includes SQLAlchemy ORM, API development, and job scheduling with APScheduler. I have also implemented web scraping solutions for data collection pipelines. I am confident I can contribute to your cloud infrastructure projects.\n\nThank you for considering my application.\n\nSincerely",
            "submitted_at": datetime(2025, 1, 18, 15, 10, 0),
            "updated_at": datetime(2025, 1, 21, 9, 30, 0),
            "interview_date": None,
            "notes": "Rejected - they went with a candidate with more cloud infrastructure experience. Learn AWS/Azure for future applications.",
        },
        {
            "player_id": 1,
            "job_id": 8,  # Data Engineer at DataFlow
            "status": "submitted",
            "cover_letter": "Dear DataFlow Analytics Team,\n\nI am writing to apply for the Data Engineer position at DataFlow Analytics. My strong Python skills, combined with extensive SQL database experience, make me well-suited for this role.\n\nI have designed and implemented data pipelines, ETL processes, and API integrations for complex data workflows. My experience with web scraping and scheduled data collection jobs aligns perfectly with your requirements. I am also well-versed in data validation and quality assurance processes.\n\nI look forward to the opportunity to contribute to DataFlow's analytics capabilities.\n\nBest regards",
            "submitted_at": datetime(2025, 1, 22, 13, 40, 0),
            "updated_at": datetime(2025, 1, 22, 13, 40, 0),
            "interview_date": None,
            "notes": "Good match (80). Emphasis on data pipeline experience.",
        },
    ]
    
    db = SessionLocal()
    try:
        # Check if applications already exist
        existing_count = db.query(Application).count()
        if existing_count > 0:
            print(f"⚠ Applications already seeded ({existing_count} applications exist). Skipping...")
            return True
        
        # Check if player_id=1 exists
        from src.models import Player
        player_exists = db.query(Player).filter(Player.id == 1).first() is not None
        if not player_exists:
            print("⚠ Player ID 1 does not exist. Skipping application seeding.")
            print("  (Applications will be created when a player submits job applications)")
            return True
        
        # Add all applications
        for app_data in applications_data:
            application = Application(**app_data)
            db.add(application)
        
        db.commit()
        print(f"✓ Seeded {len(applications_data)} applications successfully")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"✗ Error seeding applications: {e}")
        return False
    finally:
        db.close()


def seed_initial_data() -> bool:
    """
    Seed all initial data into the database.
    
    Seeds skills, achievements, titles, jobs, job matches, and applications.
    This function should be called after create_all_tables() to populate
    the database with initial content for testing and development.
    
    Returns:
        bool: True if all data was seeded successfully, False otherwise
        
    Example:
        if seed_initial_data():
            print("Database seeded with initial data")
    """
    print("\n=== Seeding Initial Data ===")
    
    # Seed core progression data
    skills_success = seed_skills()
    achievements_success = seed_achievements()
    titles_success = seed_titles()
    
    # Seed Career module data
    jobs_success = seed_jobs()
    job_matches_success = seed_job_matches()
    applications_success = seed_applications()
    
    all_success = (
        skills_success and 
        achievements_success and 
        titles_success and 
        jobs_success and 
        job_matches_success and 
        applications_success
    )
    
    if all_success:
        print("\n✓ All initial data seeded successfully\n")
    else:
        print("\n✗ Some data seeding operations failed\n")
    
    return all_success


def initialize_database() -> bool:
    """
    Complete database initialization workflow.
    
    Performs the following operations in order:
    1. Validate database connection
    2. Create all tables
    3. Seed initial data
    
    Returns:
        bool: True if initialization completed successfully, False otherwise
        
    Example:
        if initialize_database():
            print("Database ready for use")
    """
    print("\n" + "=" * 60)
    print("     LifeHunter Database Initialization")
    print("=" * 60 + "\n")
    
    # Step 1: Validate connection
    print("Step 1: Validating database connection...")
    if not validate_connection():
        print("\n✗ Database initialization failed: Cannot connect to database\n")
        return False
    print("✓ Database connection validated\n")
    
    # Step 2: Create tables
    print("Step 2: Creating database tables...")
    if not create_all_tables():
        print("\n✗ Database initialization failed: Cannot create tables\n")
        return False
    print()
    
    # Step 3: Seed initial data
    print("Step 3: Seeding initial data...")
    if not seed_initial_data():
        print("\n✗ Database initialization failed: Cannot seed initial data\n")
        return False
    
    print("=" * 60)
    print("     Database Initialization Complete!")
    print("=" * 60 + "\n")
    
    return True


if __name__ == "__main__":
    """Run database initialization when script is executed directly."""
    initialize_database()
