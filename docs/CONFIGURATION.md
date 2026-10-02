# LifeHunter Configuration Guide

## Overview

LifeHunter loads configuration from a JSON file and applies environment variable overrides.
All environment variables use the `LH_` prefix followed by the uppercase field name.

## Default Config File

`config/lifehunter.json`

The file is created automatically on first run with defaults if it doesn't exist.

## Configuration Schema

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `database_path` | string | `database.db` | Path to the SQLite database file |
| `ollama_host` | string | `http://localhost:11434` | Ollama AI service URL |
| `ollama_model` | string | `qwen2.5-coder:7b` | Ollama model to use |
| `ollama_timeout` | int | `30` | Ollama request timeout in seconds |
| `mcp_sqlite_url` | string | `http://localhost:3001` | MCP SQLite server URL |
| `mcp_fetch_url` | string | `http://localhost:3000/fetch` | MCP Fetch server URL |
| `session_timeout_minutes` | int | `30` | Session timeout in minutes |
| `secret_key` | string | `change-me-in-production` | Flask secret key (change in production!) |
| `min_daily_quests` | int | `3` | Minimum daily quests generated per player |
| `max_daily_quests` | int | `5` | Maximum daily quests generated per player |
| `max_main_quests` | int | `10` | Maximum concurrent main quests per player |
| `job_scrape_interval_hours` | int | `6` | Job scraping interval in hours |
| `backup_hour` | int | `2` | Hour (UTC) for daily database backup |
| `log_level` | string | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `log_file` | string | `logs/lifehunter.log` | Log file path |
| `api_rate_limit_per_minute` | int | `100` | API rate limit per user per minute |

## Example Config File

```json
{
  "database_path": "database.db",
  "ollama_host": "http://localhost:11434",
  "ollama_model": "qwen2.5-coder:7b",
  "ollama_timeout": 30,
  "mcp_sqlite_url": "http://localhost:3001",
  "mcp_fetch_url": "http://localhost:3000/fetch",
  "session_timeout_minutes": 30,
  "secret_key": "your-secure-random-key-here",
  "min_daily_quests": 3,
  "max_daily_quests": 5,
  "max_main_quests": 10,
  "job_scrape_interval_hours": 6,
  "backup_hour": 2,
  "log_level": "INFO",
  "log_file": "logs/lifehunter.log",
  "api_rate_limit_per_minute": 100
}
```

## Environment Variable Overrides

Set `LH_<FIELDNAME_UPPERCASE>` to override any config field at runtime.

```bash
# Override database path
export LH_DATABASE_PATH=/data/lifehunter.db

# Override Ollama host
export LH_OLLAMA_HOST=http://ollama-server:11434

# Override secret key (recommended for production)
export LH_SECRET_KEY=your-very-secure-random-key

# Override log level
export LH_LOG_LEVEL=DEBUG

# Override session timeout
export LH_SESSION_TIMEOUT_MINUTES=60
```

## Production Checklist

- [ ] Set `LH_SECRET_KEY` to a cryptographically random value (e.g., `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Set `LH_DATABASE_PATH` to a persistent volume path
- [ ] Set `LH_LOG_LEVEL=WARNING` for production
- [ ] Configure `LH_OLLAMA_HOST` to point to your Ollama server
- [ ] Configure backup retention and storage
