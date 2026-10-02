# LifeHunter System Architecture

## Overview

LifeHunter is a gamified life management system built on a layered architecture:

```
Presentation Layer  →  REST API Layer  →  Application Layer
                                        →  Module Layer
                                        →  Integration Layer
                                        →  Data Layer (SQLite)
```

## Layers

### Presentation Layer
- `templates/` — Jinja2 HTML templates
- `static/css/` — Component-scoped CSS (BEM conventions)
- `static/js/`  — Vanilla ES6+ JavaScript with Fetch API

### REST API Layer (`src/api/routes/`)
- `player.py`  — Player profile, stats, skill tree
- `quest.py`   — Quest CRUD and completion
- `career.py`  — Career Hunter: jobs, applications, cover letters
- `modules.py` — Module availability and dashboards
- `auth.py`    — Registration, login, session management

### Application Layer (`src/engine/`)
- `progression_engine.py` — XP, levels, ranks, stats, gold
- `quest_manager.py`      — Quest creation, completion, penalty zone
- `skill_system.py`       — Skill unlocking, passives, active cooldowns
- `achievement_system.py` — Achievement and title management
- `inventory_system.py`   — Item categories and capacity
- `module_manager.py`     — Rank-based module unlocking
- `auth_service.py`       — bcrypt auth, session tokens, lockout
- `notification_service.py` — Event notifications with rate limiting

### Module Layer (`src/modules/`)
- `career_hunter.py`  — Full job search lifecycle (E-Rank)
- `skill_trainer.py`  — Learning tracking placeholder (D-Rank)
- `fitness_hunter.py` — Workout tracking placeholder (C-Rank)
- `finance_manager.py`— Finance tracking placeholder (B-Rank)
- `social_network.py` — Networking placeholder (A-Rank)
- `habit_forge.py`    — Habit tracking placeholder (S-Rank)

### Integration Layer (`src/services/`)
- `database_manager.py` — SQLite via connection pool
- `ai_assistant.py`     — Ollama API (qwen2.5-coder:7b)
- `job_scraper.py`      — LinkedIn/Indeed via MCP Fetch

### Data Layer (`src/models/`)
SQLAlchemy ORM models: Player, Quest, Skill, Achievement, Title, InventoryItem, Job, JobMatch, Application, Notification, PerformanceLog, DatabaseBackup

## Key Design Decisions

- **Stateless engine layer**: All engine methods take dicts as input, not ORM objects, enabling easy unit testing without a database.
- **Singleton services**: DatabaseManager, AIAssistant, and JobScraper are singletons accessed via `get_*()` functions.
- **Background scheduler**: APScheduler runs daily quest generation, job scraping, and DB backups as cron/interval jobs.
- **Progressive unlock**: Modules unlock at rank thresholds enforced by ModuleManager, not hardcoded in routes.

## External Services

| Service | Purpose | Default URL |
|---------|---------|------------|
| Ollama | AI generation | http://localhost:11434 |
| MCP Fetch | Web scraping | http://localhost:3000/fetch |
| SQLite | Database | database.db (local file) |
