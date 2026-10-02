"""
Unit tests for AI Assistant Service with Ollama integration.

Tests cover:
- Cover letter generation with mocked Ollama responses
- Timeout handling and retry logic
- Error handling for unavailable Ollama service
- All temperature and token configurations
- Quest prioritization
- Difficulty adjustment
- Performance insights generation
- Motivational message generation
- Job skill extraction

Requirements: 28.1-28.7, 29.1-29.7, 30.1-30.7, 31.1-31.7
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests
from src.services.ai_assistant import (
    AIAssistant,
    AIAssistantError,
    OllamaUnavailableError,
    QuestPriority
)


@pytest.fixture
def ai_assistant():
    """Create AIAssistant instance for testing."""
    return AIAssistant(
        ollama_url="http://localhost:11434",
        model="qwen2.5-coder:7b",
        timeout=30,
        max_retries=3
    )


@pytest.fixture
def mock_requests():
    """Mock requests module for testing HTTP calls."""
    with patch('src.services.ai_assistant.requests') as mock:
        yield mock


class TestAIAssistantInitialization:
    """Test AI Assistant initialization and configuration."""
    
    def test_default_initialization(self):
        """Test AI Assistant initializes with default parameters."""
        assistant = AIAssistant()
        assert assistant.ollama_url == "http://localhost:11434"
        assert assistant.model == "qwen2.5-coder:7b"
        assert assistant.timeout == 30
        assert assistant.max_retries == 3
    
    def test_custom_initialization(self):
        """Test AI Assistant initializes with custom parameters."""
        assistant = AIAssistant(
            ollama_url="http://custom:8080",
            model="custom-model",
            timeout=60,
            max_retries=5
        )
        assert assistant.ollama_url == "http://custom:8080"
        assert assistant.model == "custom-model"
        assert assistant.timeout == 60
        assert assistant.max_retries == 5
    
    def test_url_trailing_slash_removed(self):
        """Test trailing slash is removed from Ollama URL."""
        assistant = AIAssistant(ollama_url="http://localhost:11434/")
        assert assistant.ollama_url == "http://localhost:11434"


class TestCoverLetterGeneration:
    """Test cover letter generation functionality.
    
    Requirements: 28.1-28.7
    - 250-400 words
    - 30 second timeout
    - Temperature: 0.7 (creative)
    - Max tokens: 500
    - Proper business letter structure
    """
    
    def test_successful_cover_letter_generation(self, ai_assistant, mock_requests):
        """Test successful cover letter generation with mocked Ollama response."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Dear Hiring Manager,\n\nI am writing to express my strong interest..."
        }
        mock_requests.post.return_value = mock_response
        
        job_description = "Python Developer position requiring Flask, SQLAlchemy, and REST API experience."
        resume = "Software Engineer with 5 years Python experience, expert in Flask and SQLAlchemy."
        
        result = ai_assistant.generate_cover_letter(job_description, resume)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Dear Hiring Manager" in result
        
        # Verify Ollama was called with correct parameters
        call_args = mock_requests.post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/generate"
        payload = call_args[1]["json"]
        assert payload["model"] == "qwen2.5-coder:7b"
        assert payload["temperature"] == 0.7  # Creative temperature
        assert payload["num_predict"] == 500  # Max tokens for cover letters
        assert job_description in payload["prompt"]
        assert resume in payload["prompt"]
    
    def test_cover_letter_includes_job_description_and_resume(self, ai_assistant, mock_requests):
        """Test cover letter generation includes both job description and resume in prompt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Cover letter content"}
        mock_requests.post.return_value = mock_response
        
        job_desc = "Senior Python Developer"
        resume_text = "Experienced Python developer"
        
        ai_assistant.generate_cover_letter(job_desc, resume_text)
        
        call_args = mock_requests.post.call_args
        prompt = call_args[1]["json"]["prompt"]
        assert job_desc in prompt
        assert resume_text in prompt


class TestQuestPrioritization:
    """Test quest prioritization functionality.
    
    Requirements: 29.1-29.7
    - Temperature: 0.3 (analytical)
    - Max tokens: 200
    - Return within 10 seconds
    """
    
    def test_successful_quest_prioritization(self, ai_assistant, mock_requests):
        """Test successful quest prioritization with mocked Ollama response."""
        # Mock successful JSON response
        priority_data = [
            {
                "quest_id": 1,
                "priority_level": "Critical",
                "reasoning": "Emergency quest with imminent deadline",
                "suggested_order": 1
            },
            {
                "quest_id": 2,
                "priority_level": "High",
                "reasoning": "Daily quest must be completed today",
                "suggested_order": 2
            }
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": json.dumps(priority_data)
        }
        mock_requests.post.return_value = mock_response
        
        quests = [
            {"id": 1, "title": "Emergency Task", "quest_type": "emergency", "xp_reward": 100, "difficulty": "hard"},
            {"id": 2, "title": "Daily Task", "quest_type": "daily", "xp_reward": 50, "difficulty": "medium"}
        ]
        
        result = ai_assistant.prioritize_quests(quests)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(p, QuestPriority) for p in result)
        assert result[0].quest_id == 1
        assert result[0].priority_level == "Critical"
        assert result[1].suggested_order == 2
        
        # Verify analytical temperature used
        call_args = mock_requests.post.call_args
        payload = call_args[1]["json"]
        assert payload["temperature"] == 0.3  # Analytical temperature
        assert payload["num_predict"] == 200  # Max tokens for prioritization
    
    def test_empty_quest_list(self, ai_assistant):
        """Test prioritization with empty quest list returns empty result."""
        result = ai_assistant.prioritize_quests([])
        assert result == []
    
    def test_prioritization_with_json_wrapped_in_text(self, ai_assistant, mock_requests):
        """Test prioritization handles JSON wrapped in explanatory text."""
        priority_data = [
            {"quest_id": 1, "priority_level": "High", "reasoning": "Important", "suggested_order": 1}
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": f"Here's the prioritization:\n{json.dumps(priority_data)}\nHope this helps!"
        }
        mock_requests.post.return_value = mock_response
        
        quests = [{"id": 1, "title": "Task", "quest_type": "daily", "xp_reward": 50, "difficulty": "easy"}]
        
        result = ai_assistant.prioritize_quests(quests)
        
        assert len(result) == 1
        assert result[0].quest_id == 1


class TestDifficultyAdjustment:
    """Test difficulty adjustment functionality.
    
    Requirements: 30.1-30.7
    """
    
    def test_successful_difficulty_adjustment(self, ai_assistant, mock_requests):
        """Test successful difficulty adjustment recommendation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "RECOMMENDATION: increase\nREASONING: High completion rate indicates ready for challenge"
        }
        mock_requests.post.return_value = mock_response
        
        performance_data = {
            "completion_rate": 0.85,
            "average_time": 300,
            "failure_count": 1,
            "success_streak": 10
        }
        
        result = ai_assistant.adjust_difficulty(player_id=123, performance_data=performance_data)
        
        assert isinstance(result, str)
        assert "increase" in result.lower()
        
        # Verify analytical temperature used
        call_args = mock_requests.post.call_args
        payload = call_args[1]["json"]
        assert payload["temperature"] == 0.3
        assert payload["num_predict"] == 200


class TestInsightGeneration:
    """Test performance insight generation.
    
    Requirements: 31.1-31.7
    """
    
    def test_successful_insight_generation(self, ai_assistant, mock_requests):
        """Test successful performance insight generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "- Your daily quest streak is impressive\n- Consider focusing on career quests\n- Explore new skill categories"
        }
        mock_requests.post.return_value = mock_response
        
        stats = {
            "total_quests": 50,
            "xp_gained": 1000,
            "daily_streak": 7,
            "top_categories": ["career", "fitness"],
            "completion_by_type": {"daily": 0.9, "main": 0.7}
        }
        
        result = ai_assistant.generate_insights(player_id=123, period="7 days", stats=stats)
        
        assert isinstance(result, list)
        assert len(result) >= 3
        assert all(isinstance(insight, str) for insight in result)
    
    def test_insight_parsing_bullet_points(self, ai_assistant, mock_requests):
        """Test insight parsing handles various bullet point formats."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "- Insight 1\n• Insight 2\n- Insight 3"
        }
        mock_requests.post.return_value = mock_response
        
        stats = {"total_quests": 10, "xp_gained": 200, "daily_streak": 3, "top_categories": [], "completion_by_type": {}}
        
        result = ai_assistant.generate_insights(123, "7 days", stats)
        
        assert len(result) == 3


class TestMotivationalMessages:
    """Test motivational message generation."""
    
    def test_level_up_message(self, ai_assistant, mock_requests):
        """Test motivational message for level up context."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Congratulations on leveling up! Your dedication is paying off. Keep pushing forward!"
        }
        mock_requests.post.return_value = mock_response
        
        result = ai_assistant.generate_motivational_message("level_up")
        
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify creative temperature used
        call_args = mock_requests.post.call_args
        payload = call_args[1]["json"]
        assert payload["temperature"] == 0.7  # Creative temperature
    
    def test_quest_failed_message(self, ai_assistant, mock_requests):
        """Test motivational message for quest failure context."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Failure is part of growth. Learn from this and come back stronger!"
        }
        mock_requests.post.return_value = mock_response
        
        result = ai_assistant.generate_motivational_message("quest_failed")
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestJobSkillExtraction:
    """Test job skill extraction functionality."""
    
    def test_successful_skill_extraction(self, ai_assistant, mock_requests):
        """Test successful skill extraction from job description."""
        skills = ["Python", "Flask", "SQLAlchemy", "REST APIs", "Git"]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": json.dumps(skills)
        }
        mock_requests.post.return_value = mock_response
        
        job_description = """
        We are looking for a Python developer with experience in Flask, SQLAlchemy, 
        and REST API development. Git version control knowledge required.
        """
        
        result = ai_assistant.extract_job_skills(job_description)
        
        assert isinstance(result, list)
        assert len(result) == 5
        assert "Python" in result
        assert "Flask" in result
        
        # Verify analytical temperature used
        call_args = mock_requests.post.call_args
        payload = call_args[1]["json"]
        assert payload["temperature"] == 0.3
    
    def test_skill_extraction_with_wrapped_json(self, ai_assistant, mock_requests):
        """Test skill extraction handles JSON wrapped in text."""
        skills = ["Python", "Docker"]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": f"Here are the skills:\n{json.dumps(skills)}\nThese are the main requirements."
        }
        mock_requests.post.return_value = mock_response
        
        result = ai_assistant.extract_job_skills("Python and Docker required")
        
        assert len(result) == 2
        assert "Python" in result
    
    def test_skill_extraction_fallback_parsing(self, ai_assistant, mock_requests):
        """Test skill extraction fallback when JSON parsing fails."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Python, Flask, SQLAlchemy"
        }
        mock_requests.post.return_value = mock_response
        
        result = ai_assistant.extract_job_skills("Job description")
        
        assert isinstance(result, list)
        assert len(result) > 0


class TestErrorHandling:
    """Test error handling and retry logic."""
    
    def test_ollama_unavailable_after_retries(self, ai_assistant, mock_requests):
        """Test error raised when Ollama is unavailable after all retries."""
        mock_requests.post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        with pytest.raises(OllamaUnavailableError) as exc_info:
            ai_assistant.generate_cover_letter("job desc", "resume")
        
        assert "Could not connect to Ollama" in str(exc_info.value)
        # Should retry 3 times
        assert mock_requests.post.call_count == 3
    
    def test_timeout_error_with_retries(self, ai_assistant, mock_requests):
        """Test timeout error triggers retry logic."""
        mock_requests.post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        with pytest.raises(OllamaUnavailableError) as exc_info:
            ai_assistant.generate_motivational_message("context")
        
        assert "timed out" in str(exc_info.value)
        assert mock_requests.post.call_count == 3
    
    def test_model_not_found_error(self, ai_assistant, mock_requests):
        """Test error when model is not found in Ollama."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Model not found"
        mock_requests.post.return_value = mock_response
        
        with pytest.raises(AIAssistantError) as exc_info:
            ai_assistant.generate_cover_letter("job", "resume")
        
        assert "Model" in str(exc_info.value)
        assert "not found" in str(exc_info.value)
    
    def test_http_error_response(self, ai_assistant, mock_requests):
        """Test handling of HTTP error responses."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_requests.post.return_value = mock_response
        
        with pytest.raises(AIAssistantError):
            ai_assistant.generate_cover_letter("job", "resume")
    
    def test_successful_after_retry(self, ai_assistant, mock_requests):
        """Test successful response after initial failures."""
        # First two calls fail, third succeeds
        mock_requests.post.side_effect = [
            requests.exceptions.ConnectionError("Connection refused"),
            requests.exceptions.ConnectionError("Connection refused"),
            Mock(status_code=200, json=lambda: {"response": "Success"})
        ]
        
        result = ai_assistant.generate_motivational_message("level_up")
        
        assert result == "Success"
        assert mock_requests.post.call_count == 3


class TestRetryLogic:
    """Test retry logic with exponential backoff."""
    
    @patch('src.services.ai_assistant.time.sleep')
    def test_exponential_backoff_delays(self, mock_sleep, ai_assistant, mock_requests):
        """Test retry delays follow exponential backoff: 2s, 4s, 8s."""
        mock_requests.post.side_effect = requests.exceptions.ConnectionError("Connection error")
        
        with pytest.raises(OllamaUnavailableError):
            ai_assistant.generate_cover_letter("job", "resume")
        
        # Verify sleep was called with correct delays
        assert mock_sleep.call_count == 2  # Only 2 sleeps for 3 attempts (no sleep after last attempt)
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert calls == [2, 4]  # Exponential backoff: 2s, 4s (8s would be after 3rd failure)


class TestTemperatureConfiguration:
    """Test temperature configuration for different tasks."""
    
    def test_creative_temperature_for_cover_letters(self, ai_assistant, mock_requests):
        """Test cover letters use creative temperature (0.7)."""
        mock_response = Mock(status_code=200, json=lambda: {"response": "Letter"})
        mock_requests.post.return_value = mock_response
        
        ai_assistant.generate_cover_letter("job", "resume")
        
        payload = mock_requests.post.call_args[1]["json"]
        assert payload["temperature"] == 0.7
    
    def test_creative_temperature_for_motivational_messages(self, ai_assistant, mock_requests):
        """Test motivational messages use creative temperature (0.7)."""
        mock_response = Mock(status_code=200, json=lambda: {"response": "Message"})
        mock_requests.post.return_value = mock_response
        
        ai_assistant.generate_motivational_message("context")
        
        payload = mock_requests.post.call_args[1]["json"]
        assert payload["temperature"] == 0.7
    
    def test_analytical_temperature_for_prioritization(self, ai_assistant, mock_requests):
        """Test quest prioritization uses analytical temperature (0.3)."""
        mock_response = Mock(status_code=200, json=lambda: {"response": "[]"})
        mock_requests.post.return_value = mock_response
        
        ai_assistant.prioritize_quests([{"id": 1, "title": "Task", "quest_type": "daily", "xp_reward": 50, "difficulty": "easy"}])
        
        payload = mock_requests.post.call_args[1]["json"]
        assert payload["temperature"] == 0.3
    
    def test_analytical_temperature_for_skill_extraction(self, ai_assistant, mock_requests):
        """Test skill extraction uses analytical temperature (0.3)."""
        mock_response = Mock(status_code=200, json=lambda: {"response": "[]"})
        mock_requests.post.return_value = mock_response
        
        ai_assistant.extract_job_skills("job description")
        
        payload = mock_requests.post.call_args[1]["json"]
        assert payload["temperature"] == 0.3


class TestTokenLimits:
    """Test token limit configuration for different tasks."""
    
    def test_cover_letter_token_limit(self, ai_assistant, mock_requests):
        """Test cover letters use 500 token limit."""
        mock_response = Mock(status_code=200, json=lambda: {"response": "Letter"})
        mock_requests.post.return_value = mock_response
        
        ai_assistant.generate_cover_letter("job", "resume")
        
        payload = mock_requests.post.call_args[1]["json"]
        assert payload["num_predict"] == 500
    
    def test_prioritization_token_limit(self, ai_assistant, mock_requests):
        """Test prioritization uses 200 token limit."""
        mock_response = Mock(status_code=200, json=lambda: {"response": "[]"})
        mock_requests.post.return_value = mock_response
        
        ai_assistant.prioritize_quests([{"id": 1, "title": "Task", "quest_type": "daily", "xp_reward": 50, "difficulty": "easy"}])
        
        payload = mock_requests.post.call_args[1]["json"]
        assert payload["num_predict"] == 200
    
    def test_insights_token_limit(self, ai_assistant, mock_requests):
        """Test insights use 200 token limit."""
        mock_response = Mock(status_code=200, json=lambda: {"response": "- Insight"})
        mock_requests.post.return_value = mock_response
        
        stats = {"total_quests": 10, "xp_gained": 100, "daily_streak": 1, "top_categories": [], "completion_by_type": {}}
        ai_assistant.generate_insights(123, "7 days", stats)
        
        payload = mock_requests.post.call_args[1]["json"]
        assert payload["num_predict"] == 200


class TestTimeoutConfiguration:
    """Test timeout configuration."""
    
    def test_default_timeout(self, mock_requests):
        """Test default 30 second timeout is configured."""
        assistant = AIAssistant()
        assert assistant.timeout == 30
    
    def test_custom_timeout(self, mock_requests):
        """Test custom timeout can be configured."""
        assistant = AIAssistant(timeout=60)
        assert assistant.timeout == 60
    
    def test_timeout_passed_to_requests(self, ai_assistant, mock_requests):
        """Test timeout is passed to requests.post()."""
        mock_response = Mock(status_code=200, json=lambda: {"response": "Result"})
        mock_requests.post.return_value = mock_response
        
        ai_assistant.generate_motivational_message("context")
        
        call_kwargs = mock_requests.post.call_args[1]
        assert call_kwargs["timeout"] == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
