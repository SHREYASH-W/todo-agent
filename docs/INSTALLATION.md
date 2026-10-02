# LifeHunter Installation Guide

## Prerequisites

- Python 3.10+
- SQLite 3.35+
- [Ollama](https://ollama.ai) with `qwen2.5-coder:7b` model (for AI features)
- Git

## Quick Start

### 1. Clone and Set Up

```bash
git clone <repository-url>
cd "mcp server"

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize the Database

```bash
python -m src.db.init_db
```

This creates all tables and seeds initial data (skills, achievements, titles, sample jobs).

### 3. Configure (Optional)

Copy and edit the default config:

```bash
copy config\.gitkeep config\lifehunter.json
```

Key settings in `config/lifehunter.json`:

```json
{
  "database_path": "database.db",
  "ollama_host": "http://localhost:11434",
  "session_timeout_minutes": 30,
  "log_level": "INFO"
}
```

Environment variable overrides use the `LH_` prefix:
```bash
set LH_DATABASE_PATH=data/production.db
set LH_OLLAMA_HOST=http://ollama-server:11434
```

### 4. Start Ollama (for AI features)

```bash
ollama pull qwen2.5-coder:7b
ollama serve
```

### 5. Run the Application

```bash
python -m src.app
# App starts at http://localhost:5000
```

Or with Flask CLI:
```bash
flask --app src.app run --debug
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Project Structure

```
mcp server/
├── src/
│   ├── api/routes/      # REST API endpoints
│   ├── config/          # Configuration system
│   ├── db/              # Database initialization
│   ├── engine/          # Core game logic
│   ├── jobs/            # Background scheduler
│   ├── models/          # SQLAlchemy ORM models
│   ├── modules/         # Life area modules
│   ├── services/        # External service integrations
│   └── utils/           # Utilities (logging, security, export)
├── static/              # CSS, JS, images
├── templates/           # HTML templates
├── tests/               # Test suite
├── docs/                # Documentation
└── scripts/             # Automation scripts
```
