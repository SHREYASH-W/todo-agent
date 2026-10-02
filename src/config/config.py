"""
Configuration System for LifeHunter System

Loads and saves JSON/YAML configuration with environment variable overrides.

Requirements: Configuration requirements
Property 22: Configuration Parse-Print Round-Trip
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default config file path
DEFAULT_CONFIG_PATH = "config/lifehunter.json"


@dataclass
class LifeHunterConfig:
    """Application configuration schema."""

    # Database
    database_path: str = "database.db"

    # Ollama / AI
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_timeout: int = 30

    # MCP servers
    mcp_sqlite_url: str = "http://localhost:3001"
    mcp_fetch_url: str  = "http://localhost:3000/fetch"

    # Session
    session_timeout_minutes: int = 30
    secret_key: str = "change-me-in-production"

    # Quest settings
    min_daily_quests: int = 3
    max_daily_quests: int = 5
    max_main_quests: int  = 10

    # Scheduler
    job_scrape_interval_hours: int = 6
    backup_hour: int = 2

    # Logging
    log_level: str = "INFO"
    log_file:  str = "logs/lifehunter.log"

    # Rate limiting
    api_rate_limit_per_minute: int = 100

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_config(file_path: str = DEFAULT_CONFIG_PATH) -> LifeHunterConfig:
    """
    Load configuration from a JSON file, then apply environment variable overrides.

    Environment variables use the prefix LH_ and uppercase key names.
    Example: LH_DATABASE_PATH overrides database_path.

    Args:
        file_path: Path to JSON config file

    Returns:
        LifeHunterConfig: Loaded configuration instance
    """
    config_dict: Dict[str, Any] = {}

    # Load from file if it exists
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
            logger.info(f"Configuration loaded from {file_path}")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load config from {file_path}: {e}")
    else:
        logger.info(f"Config file {file_path} not found, using defaults")

    # Apply environment variable overrides
    defaults = LifeHunterConfig()
    for key in asdict(defaults):
        env_key   = f"LH_{key.upper()}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            # Cast to the correct type
            default_val = getattr(defaults, key)
            try:
                if isinstance(default_val, int):
                    config_dict[key] = int(env_value)
                elif isinstance(default_val, bool):
                    config_dict[key] = env_value.lower() in ("1", "true", "yes")
                else:
                    config_dict[key] = env_value
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid env override {env_key}={env_value}: {e}")

    # Build config object, ignoring unknown keys
    known_keys = {f.name for f in defaults.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    filtered   = {k: v for k, v in config_dict.items() if k in known_keys}

    return LifeHunterConfig(**{**asdict(defaults), **filtered})


def save_config(config: LifeHunterConfig, file_path: str = DEFAULT_CONFIG_PATH) -> bool:
    """
    Save configuration to a JSON file.

    Args:
        config: Configuration to save
        file_path: Destination JSON file path

    Returns:
        bool: True if saved successfully
    """
    try:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info(f"Configuration saved to {file_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to save config to {file_path}: {e}")
        return False


# ── Singleton ────────────────────────────────────────────────
_config_instance: Optional[LifeHunterConfig] = None


def get_config() -> LifeHunterConfig:
    """Return the global configuration instance (lazy-loaded)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance
