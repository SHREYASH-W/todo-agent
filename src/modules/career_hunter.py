"""
Career Hunter Module for LifeHunter System

Implements job scraping, AI job matching, cover letter generation,
application tracking, interview prep, follow-up tasks, and networking quests.

Requirements: 15.1-21.7
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# XP rewards (Requirements 17.7, 19.7, 20.5, 21.4)
APPLICATION_XP = 50
INTERVIEW_PREP_XP = 75
FOLLOWUP_TASK_XP = 25
NETWORKING_QUEST_XP = 40

# Valid application status transitions
# submitted -> under_review -> interview -> offered
#                           -> rejected
VALID_TRANSITIONS = {
    "submitted": {"under_review", "rejected"},
    "under_review": {"interview", "rejected"},
    "interview": {"offered", "rejected"},
    "offered": set(),
    "rejected": set(),
}

TERMINAL_STATUSES = {"offered", "rejected"}

NETWORKING_TEMPLATES = [
    "LinkedIn Outreach Template",
    "Coffee Meeting Request",
    "Conference Networking Script",
    "Informational Interview Request",
]

NETWORKING_ACTIVITIES = [
    {
        "title": "LinkedIn Outreach",
        "description": "Connect with 3 professionals in your target industry on LinkedIn.",
        "xp_reward": NETWORKING_QUEST_XP,
        "difficulty": "easy",
    },
    {
        "title": "Informational Interview",
        "description": "Schedule and conduct an informational interview with someone in your target role.",
        "xp_reward": NETWORKING_QUEST_XP,
        "difficulty": "medium",
    },
    {
        "title": "Attend Networking Event",
        "description": "Attend a professional meetup, conference, or virtual networking event.",
        "xp_reward": NETWORKING_QUEST_XP,
        "difficulty": "medium",
    },
    {
        "title": "Coffee Meeting",
        "description": "Meet a professional contact for coffee to discuss career insights.",
        "xp_reward": NETWORKING_QUEST_XP,
        "difficulty": "easy",
    },
]


class CareerHunterModule:
    """
    Career Hunter module — handles the full job search and application lifecycle.

    Depends on:
    - JobScraper for web scraping
    - AIAssistant for cover letter generation and skill extraction
    - ProgressionEngine for awarding XP
    - QuestManager for creating follow-up and interview prep quests
    - InventorySystem for storing cover letters and interview notes
    """

    def __init__(
        self,
        job_scraper=None,
        ai_assistant=None,
        progression_engine=None,
        quest_manager=None,
        inventory_system=None,
    ):
        self.job_scraper = job_scraper
        self.ai_assistant = ai_assistant
        self.progression_engine = progression_engine
        self.quest_manager = quest_manager
        self.inventory_system = inventory_system

    # ─── Job Scraping ──────────────────────────────────────────────────────

    def scrape_jobs(
        self,
        sources: List[str],
        keywords: List[str],
        location: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Scrape jobs from specified sources with keyword filters.

        Requirement 15.1-15.5.
        """
        if self.job_scraper is None:
            logger.warning("No job scraper configured")
            return []

        all_jobs = []
        for source in sources:
            if source == "linkedin":
                jobs = self.job_scraper.scrape_linkedin(keywords, location)
            elif source == "indeed":
                jobs = self.job_scraper.scrape_indeed(keywords, location)
            else:
                logger.warning(f"Unknown source: {source}")
                continue
            all_jobs.extend(jobs)

        # Deduplicate across sources
        unique_jobs = self.job_scraper.deduplicate_jobs(all_jobs)
        logger.info(f"Scraped {len(unique_jobs)} unique jobs from {sources}")
        return [j.to_dict() if hasattr(j, "to_dict") else j for j in unique_jobs]

    # ─── Job Matching ──────────────────────────────────────────────────────

    def match_jobs(
        self,
        player_skills: List[str],
        jobs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Calculate match scores for jobs against player skills.

        Algorithm (Requirement 16.1-16.7):
        1. Extract required skills from job description via AI
        2. Compare against player skill inventory
        3. Calculate overlap percentage
        4. Weight required vs preferred skills
        5. Return score 0-100

        Returns:
            List[Dict]: Jobs with match_score, sorted descending
        """
        if not jobs:
            return []

        player_skill_set = {s.lower() for s in player_skills}
        scored_jobs = []

        for job in jobs:
            description = job.get("description", "")

            # Extract skills from description (AI or fallback keyword scan)
            if self.ai_assistant:
                try:
                    extracted = self.ai_assistant.extract_job_skills(description)
                except Exception:
                    extracted = self._keyword_skill_extract(description)
            else:
                extracted = self._keyword_skill_extract(description)

            extracted_lower = {s.lower() for s in extracted}

            # Calculate overlap
            if not extracted_lower:
                score = 0
            else:
                overlap = len(player_skill_set & extracted_lower)
                score = min(100, int((overlap / len(extracted_lower)) * 100))

            job_match = dict(job)
            job_match["match_score"] = score
            job_match["matching_skills"] = json.dumps(
                list(player_skill_set & extracted_lower)
            )
            job_match["calculated_at"] = datetime.utcnow().isoformat()
            scored_jobs.append(job_match)

        # Sort by match score descending (Requirement 16.4)
        scored_jobs.sort(key=lambda j: j["match_score"], reverse=True)

        logger.info(f"Matched {len(scored_jobs)} jobs, top score={scored_jobs[0]['match_score'] if scored_jobs else 0}")
        return scored_jobs[:20]  # Top 20 (Requirement 16.5)

    def _keyword_skill_extract(self, description: str) -> List[str]:
        """Fallback keyword-based skill extraction."""
        common_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Flask", "FastAPI",
            "Django", "SQLAlchemy", "SQL", "SQLite", "PostgreSQL", "MySQL",
            "REST API", "Git", "Docker", "AWS", "Linux", "HTML", "CSS",
            "Machine Learning", "TensorFlow", "PyTorch", "Pandas", "NumPy",
        ]
        desc_lower = description.lower()
        return [s for s in common_skills if s.lower() in desc_lower]

    # ─── Cover Letter & Applications ───────────────────────────────────────

    def generate_cover_letter(
        self,
        job: Dict[str, Any],
        resume: str,
    ) -> str:
        """
        Generate a customized cover letter using the AI Assistant.

        Requirements 17.2, 17.3, 28.1-28.7.
        """
        if self.ai_assistant:
            return self.ai_assistant.generate_cover_letter(
                job.get("description", ""),
                resume,
            )
        # Fallback template
        return (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my strong interest in the {job.get('title', 'position')} "
            f"role at {job.get('company', 'your company')}.\n\n"
            f"[AI service unavailable — please customize this letter manually.]\n\n"
            f"Sincerely,\n[Your Name]"
        )

    def create_application(
        self,
        player_id: int,
        job: Dict[str, Any],
        cover_letter: str,
        player: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create an application record and award XP.

        Requirements 17.5, 17.6, 17.7.
        """
        application = {
            "player_id": player_id,
            "job_id": job.get("id"),
            "status": "submitted",
            "cover_letter": cover_letter,
            "submitted_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "interview_date": None,
            "notes": "",
        }

        # Award XP
        if player and self.progression_engine:
            self.progression_engine.award_xp(player, APPLICATION_XP)
            logger.info(f"Awarded {APPLICATION_XP} XP for application submission")

        logger.info(
            f"Application created: player={player_id}, job={job.get('title')} "
            f"@ {job.get('company')}"
        )
        return application

    # ─── Application Status ────────────────────────────────────────────────

    def is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """
        Check if a status transition is valid.

        Requirement 18.1, 18.2. Used by property test 20.
        """
        return new_status in VALID_TRANSITIONS.get(current_status, set())

    def update_application_status(
        self,
        application: Dict[str, Any],
        new_status: str,
        player_id: Optional[int] = None,
    ) -> bool:
        """
        Update application status and trigger related actions.

        Requirements 18.2, 19.1, 20.7.
        """
        current = application.get("status", "submitted")
        if not self.is_valid_status_transition(current, new_status):
            logger.warning(f"Invalid transition: {current} -> {new_status}")
            return False

        application["status"] = new_status
        application["updated_at"] = datetime.utcnow()
        logger.info(f"Application status: {current} -> {new_status}")
        return True

    def get_application_stats(self, applications: List[Dict]) -> Dict[str, Any]:
        """
        Calculate application statistics.

        Requirement 18.5.
        """
        total = len(applications)
        if total == 0:
            return {
                "total": 0,
                "response_rate": 0.0,
                "interview_rate": 0.0,
                "offer_rate": 0.0,
            }

        got_response = sum(
            1 for a in applications
            if a.get("status") in {"under_review", "interview", "offered", "rejected"}
        )
        got_interview = sum(1 for a in applications if a.get("status") in {"interview", "offered"})
        got_offer = sum(1 for a in applications if a.get("status") == "offered")

        return {
            "total": total,
            "response_rate": round(got_response / total * 100, 1),
            "interview_rate": round(got_interview / total * 100, 1),
            "offer_rate": round(got_offer / total * 100, 1),
        }

    # ─── Interview Preparation ─────────────────────────────────────────────

    def generate_interview_prep(
        self,
        application: Dict[str, Any],
        job: Dict[str, Any],
        player_id: int,
        active_main_quests_count: int,
        current_items: Optional[List] = None,
    ) -> Dict[str, Any]:
        """
        Generate interview preparation quest and resources.

        Requirements 19.1-19.7.
        """
        result: Dict[str, Any] = {}

        # Create interview prep quest (75 XP reward)
        if self.quest_manager:
            quest = self.quest_manager.create_main_quest(
                player_id,
                {
                    "title": f"Interview Prep: {job.get('title')} @ {job.get('company')}",
                    "description": (
                        f"Prepare for your interview at {job.get('company')}. "
                        "Research the company, practice common questions, and review your materials."
                    ),
                    "xp_reward": INTERVIEW_PREP_XP,
                    "gold_reward": 0,
                    "difficulty": "medium",
                },
                active_main_quests_count,
            )
            result["prep_quest"] = quest

        # Generate interview questions via AI
        if self.ai_assistant:
            try:
                prompt = (
                    f"Generate 10 common interview questions for a "
                    f"{job.get('title')} role at {job.get('company')}. "
                    f"Job description: {job.get('description', '')[:300]}"
                )
                questions = self.ai_assistant.generate_motivational_message(prompt)
                result["interview_questions"] = questions
            except Exception as e:
                logger.warning(f"Failed to generate interview questions: {e}")

        logger.info(f"Interview prep generated for application {application.get('id')}")
        return result

    # ─── Follow-up Tasks ───────────────────────────────────────────────────

    def create_followup_task(
        self,
        player_id: int,
        application: Dict[str, Any],
        job: Dict[str, Any],
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Create a follow-up task scheduled N days after application.

        Requirements 20.1-20.6.
        """
        scheduled_date = datetime.utcnow() + timedelta(days=days)

        task = {
            "player_id": player_id,
            "quest_type": "daily",
            "title": f"Follow Up: {job.get('title')} @ {job.get('company')}",
            "description": (
                f"Follow up on your application to {job.get('company')} "
                f"for the {job.get('title')} position submitted on "
                f"{application.get('submitted_at', 'recently')}."
            ),
            "xp_reward": FOLLOWUP_TASK_XP,
            "gold_reward": 10,
            "difficulty": "easy",
            "status": "active",
            "created_at": datetime.utcnow(),
            "deadline": scheduled_date,
            "completed_at": None,
            "parent_quest_id": None,
            "application_id": application.get("id"),
        }
        logger.info(
            f"Follow-up task created for player {player_id}: "
            f"due {scheduled_date.date()}"
        )
        return task

    def cancel_followup_tasks(
        self,
        application_id: int,
        tasks: List[Dict[str, Any]],
    ) -> int:
        """
        Cancel all pending follow-up tasks for an application that reached terminal status.

        Requirement 20.7.

        Returns:
            int: Number of tasks cancelled
        """
        count = 0
        for task in tasks:
            if (
                task.get("application_id") == application_id
                and task.get("status") == "active"
            ):
                task["status"] = "cancelled"
                count += 1
        if count:
            logger.info(f"Cancelled {count} follow-up tasks for application {application_id}")
        return count

    # ─── Networking Quests ─────────────────────────────────────────────────

    def get_networking_suggestions(self) -> List[Dict[str, Any]]:
        """
        Return networking activity suggestions.

        Requirement 21.1, 21.7.
        """
        return NETWORKING_ACTIVITIES

    def create_networking_quest(
        self,
        player_id: int,
        activity: Dict[str, Any],
        active_main_quests_count: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a networking quest from a suggestion.

        Requirements 21.2, 21.3, 21.4.
        """
        if self.quest_manager:
            quest = self.quest_manager.create_main_quest(
                player_id,
                {
                    "title": activity.get("title"),
                    "description": activity.get("description"),
                    "xp_reward": NETWORKING_QUEST_XP,
                    "gold_reward": 15,
                    "difficulty": activity.get("difficulty", "easy"),
                },
                active_main_quests_count,
            )
            return quest

        # Fallback direct quest creation
        return {
            "player_id": player_id,
            "quest_type": "main",
            "title": activity.get("title"),
            "description": activity.get("description"),
            "xp_reward": NETWORKING_QUEST_XP,
            "gold_reward": 15,
            "difficulty": activity.get("difficulty", "easy"),
            "status": "active",
            "created_at": datetime.utcnow(),
            "deadline": None,
            "completed_at": None,
        }
