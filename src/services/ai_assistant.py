"""
AI Assistant for LifeHunter System

Interfaces with Ollama service using qwen2.5-coder:7b model to provide:
- Cover letter generation (temperature=0.7, max_tokens=500)
- Quest prioritization (temperature=0.3, max_tokens=200)
- Difficulty adjustment based on performance
- Performance insights
- Motivational messages
- Job skill extraction

Usage:
    ai = AIAssistant()
    cover_letter = ai.generate_cover_letter(job_description, resume)
    priorities = ai.prioritize_quests(quests)
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-coder:7b"
OLLAMA_TIMEOUT = 30  # seconds

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # exponential backoff in seconds


class OllamaError(Exception):
    """Raised when Ollama service is unavailable or returns an error."""
    pass


class QuestPriority:
    """Represents a prioritized quest with reasoning."""

    def __init__(self, quest_id: int, title: str, priority: str, reasoning: str):
        self.quest_id = quest_id
        self.title = title
        self.priority = priority  # Critical / High / Medium / Low
        self.reasoning = reasoning

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quest_id": self.quest_id,
            "title": self.title,
            "priority": self.priority,
            "reasoning": self.reasoning,
        }


class AIAssistant:
    """
    AI Assistant powered by Ollama's qwen2.5-coder:7b model.

    Provides AI-driven features for the LifeHunter gamified life management
    system including cover letter generation, quest prioritization, and
    performance insights.
    """

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
        logger.info(f"AIAssistant initialized (model={model}, url={base_url})")

    def _call_ollama(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = OLLAMA_TIMEOUT,
    ) -> str:
        """
        Call the Ollama API with retry logic.

        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (0.3=analytical, 0.7=creative)
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds

        Returns:
            str: Generated text from the model

        Raises:
            OllamaError: If service unavailable after all retries
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        last_error: Optional[Exception] = None

        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"Ollama request attempt {attempt + 1}/{MAX_RETRIES}")
                response = requests.post(
                    self.generate_url,
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                data = response.json()
                result = data.get("response", "").strip()
                logger.debug(f"Ollama response received ({len(result)} chars)")
                return result

            except requests.exceptions.ConnectionError as e:
                last_error = e
                logger.warning(f"Ollama connection failed (attempt {attempt + 1}): {e}")
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"Ollama request timed out (attempt {attempt + 1})")
            except requests.exceptions.HTTPError as e:
                last_error = e
                logger.warning(f"Ollama HTTP error (attempt {attempt + 1}): {e}")
            except Exception as e:
                last_error = e
                logger.warning(f"Unexpected Ollama error (attempt {attempt + 1}): {e}")

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)

        raise OllamaError(
            f"Ollama service unavailable after {MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    def generate_cover_letter(self, job_description: str, resume: str) -> str:
        """
        Generate a customized cover letter for a job application.

        Uses temperature=0.7 for creative output and targets 250-400 words
        in proper business letter format. Requirement 28.1-28.7.

        Args:
            job_description: Full text of the job posting
            resume: Player's resume text or template

        Returns:
            str: Generated cover letter (250-400 words, business letter format)
                 or error message if Ollama is unavailable
        """
        prompt = f"""Write a professional cover letter for the following job application.

JOB DESCRIPTION:
{job_description}

APPLICANT RESUME/BACKGROUND:
{resume}

INSTRUCTIONS:
- Write a compelling cover letter between 250-400 words
- Use proper business letter format (opening, 2-3 body paragraphs, closing)
- Highlight relevant skills and experiences that match the job requirements
- Be specific and avoid generic phrases
- Show enthusiasm for the role and company
- End with a clear call to action

Write only the cover letter text, starting with "Dear Hiring Manager," and ending with a professional sign-off."""

        try:
            result = self._call_ollama(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500,
                timeout=OLLAMA_TIMEOUT,
            )
            logger.info("Cover letter generated successfully")
            return result
        except OllamaError as e:
            error_msg = (
                "Cover letter generation is temporarily unavailable. "
                "The AI service (Ollama) could not be reached. "
                "Please ensure Ollama is running and try again."
            )
            logger.error(f"Cover letter generation failed: {e}")
            return error_msg

    def prioritize_quests(self, quests: List[Dict[str, Any]]) -> List[QuestPriority]:
        """
        Analyze and prioritize a list of quests.

        Uses temperature=0.3 for analytical output. Returns quests with
        priority labels: Critical, High, Medium, Low. Requirement 29.1-29.7.

        Args:
            quests: List of quest dicts with keys: id, title, description,
                    xp_reward, difficulty, deadline, quest_type

        Returns:
            List[QuestPriority]: Quests ordered by priority with reasoning
        """
        if not quests:
            return []

        quest_list_text = "\n".join(
            f"- ID {q.get('id', '?')}: {q.get('title', 'Untitled')} "
            f"(type={q.get('quest_type', 'unknown')}, "
            f"xp={q.get('xp_reward', 0)}, "
            f"difficulty={q.get('difficulty', 'medium')}, "
            f"deadline={q.get('deadline', 'none')})"
            for q in quests
        )

        prompt = f"""Analyze and prioritize these quests for a life management app player.

QUESTS:
{quest_list_text}

PRIORITY CRITERIA:
- Critical: Emergency quests, overdue items, or time-sensitive with deadline < 2 hours
- High: Important main quests, daily quests near deadline, high XP rewards
- Medium: Regular quests with moderate XP and flexible deadlines
- Low: Optional quests, low XP, no deadline pressure

Respond with JSON array only, no other text:
[{{"quest_id": <id>, "title": "<title>", "priority": "<Critical|High|Medium|Low>", "reasoning": "<brief reason>"}}]"""

        try:
            result = self._call_ollama(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200,
                timeout=10,
            )

            # Parse JSON response
            # Find JSON array in response
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = result[start:end]
                data = json.loads(json_str)
                priorities = [
                    QuestPriority(
                        quest_id=item.get("quest_id", 0),
                        title=item.get("title", ""),
                        priority=item.get("priority", "Medium"),
                        reasoning=item.get("reasoning", ""),
                    )
                    for item in data
                ]
                logger.info(f"Quest prioritization complete ({len(priorities)} quests)")
                return priorities

        except OllamaError as e:
            logger.error(f"Quest prioritization failed: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse prioritization response: {e}")

        # Fallback: return quests in original order with Medium priority
        return [
            QuestPriority(
                quest_id=q.get("id", 0),
                title=q.get("title", "Untitled"),
                priority="Medium",
                reasoning="AI prioritization unavailable",
            )
            for q in quests
        ]

    def adjust_difficulty(self, player_id: int, performance_data: Dict[str, Any]) -> str:
        """
        Calculate a difficulty adjustment recommendation based on player performance.

        Uses temperature=0.3. Requirement 30.1-30.7.

        Args:
            player_id: Player's ID
            performance_data: Dict with keys like completion_rate, avg_time,
                              streak, failed_quests, xp_per_day

        Returns:
            str: Difficulty adjustment recommendation (easier/maintain/harder)
                 with reasoning
        """
        prompt = f"""Analyze player performance data and recommend quest difficulty adjustment.

PLAYER ID: {player_id}
PERFORMANCE DATA:
- Quest completion rate: {performance_data.get('completion_rate', 'unknown')}%
- Average time per quest: {performance_data.get('avg_time_minutes', 'unknown')} minutes
- Current streak: {performance_data.get('streak', 0)} days
- Failed quests (last 7 days): {performance_data.get('failed_quests', 0)}
- XP earned per day (average): {performance_data.get('xp_per_day', 0)}

ADJUSTMENT RULES:
- If completion rate > 90% consistently: suggest increasing difficulty
- If completion rate < 50%: suggest decreasing difficulty  
- Otherwise: maintain current difficulty

Respond in 2-3 sentences: state the recommendation (easier/maintain/harder) and brief reasoning."""

        try:
            result = self._call_ollama(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200,
                timeout=OLLAMA_TIMEOUT,
            )
            logger.info(f"Difficulty adjustment generated for player {player_id}")
            return result
        except OllamaError as e:
            logger.error(f"Difficulty adjustment failed: {e}")
            return "Difficulty adjustment unavailable. Maintain current difficulty level."

    def generate_insights(self, player_id: int, period: str) -> List[str]:
        """
        Generate performance insights and recommendations for a player.

        Uses temperature=0.3 for analytical output. Requirement 31.1-31.7.

        Args:
            player_id: Player's ID
            period: Time period string ('7_days', '30_days', '90_days', 'all_time')

        Returns:
            List[str]: 3-5 insight strings with actionable recommendations
        """
        prompt = f"""Generate performance insights for a life management app player.

PLAYER ID: {player_id}
ANALYSIS PERIOD: {period}

Generate exactly 4 concise, actionable insights covering:
1. Progress trend (positive or areas for improvement)
2. Quest completion patterns
3. Skill development recommendation
4. Career/goal advancement suggestion

Respond with JSON array of strings only:
["insight 1", "insight 2", "insight 3", "insight 4"]"""

        try:
            result = self._call_ollama(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200,
                timeout=OLLAMA_TIMEOUT,
            )

            # Parse JSON array
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                insights = json.loads(result[start:end])
                if isinstance(insights, list):
                    logger.info(f"Generated {len(insights)} insights for player {player_id}")
                    return [str(i) for i in insights]

        except OllamaError as e:
            logger.error(f"Insight generation failed: {e}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse insights response: {e}")

        return [
            "Keep up the great work completing your daily quests!",
            "Consider allocating skill points to boost your primary stats.",
            "Networking quests can accelerate your career progression.",
            "Consistency is key — try to maintain your daily streak.",
        ]

    def generate_motivational_message(self, context: str) -> str:
        """
        Generate a contextual motivational message for the player.

        Uses temperature=0.7 for creative, engaging output. Requirement 31.x.

        Args:
            context: Context string describing the situation
                     (e.g. "player just leveled up to 15", "player failed daily quest")

        Returns:
            str: Short motivational message (1-3 sentences)
        """
        prompt = f"""Generate a short, motivational message for a player in a gamified life management app.

CONTEXT: {context}

The message should be:
- Encouraging and positive
- Relevant to the specific context
- Between 1-3 sentences
- Written in second person ("You...")
- Inspired by RPG/Solo Leveling themes

Write only the motivational message, nothing else."""

        try:
            result = self._call_ollama(
                prompt=prompt,
                temperature=0.7,
                max_tokens=100,
                timeout=OLLAMA_TIMEOUT,
            )
            logger.info("Motivational message generated")
            return result
        except OllamaError as e:
            logger.error(f"Motivational message generation failed: {e}")
            return "Every step forward is progress. Keep pushing your limits, Hunter!"

    def extract_job_skills(self, job_description: str) -> List[str]:
        """
        Extract required and preferred skills from a job description.

        Uses temperature=0.3 for precise extraction. Used by Career Hunter
        module for job matching.

        Args:
            job_description: Full text of the job posting

        Returns:
            List[str]: List of skill names extracted from the description
        """
        prompt = f"""Extract all technical and professional skills mentioned in this job description.

JOB DESCRIPTION:
{job_description}

Extract both required and preferred skills. Include:
- Programming languages
- Frameworks and libraries
- Tools and platforms
- Soft skills if explicitly mentioned

Respond with JSON array of skill strings only, no other text:
["skill1", "skill2", "skill3"]"""

        try:
            result = self._call_ollama(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200,
                timeout=OLLAMA_TIMEOUT,
            )

            # Parse JSON array
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                skills = json.loads(result[start:end])
                if isinstance(skills, list):
                    skill_list = [str(s).strip() for s in skills if s]
                    logger.info(f"Extracted {len(skill_list)} skills from job description")
                    return skill_list

        except OllamaError as e:
            logger.error(f"Skill extraction failed: {e}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse skill extraction response: {e}")

        return []

    def is_available(self) -> bool:
        """
        Check if Ollama service is available.

        Returns:
            bool: True if Ollama is reachable, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


# Singleton instance
_ai_assistant_instance: Optional[AIAssistant] = None


def get_ai_assistant() -> AIAssistant:
    """
    Get singleton AIAssistant instance.

    Returns:
        AIAssistant: Singleton AI assistant instance
    """
    global _ai_assistant_instance
    if _ai_assistant_instance is None:
        _ai_assistant_instance = AIAssistant()
    return _ai_assistant_instance
