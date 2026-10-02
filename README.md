# LifeHunter System

A gamified life management system that transforms real-life tasks, goals, and personal development into an immersive RPG experience inspired by Solo Leveling mechanics.

## Overview

LifeHunter enables users to progress through ranks (E→D→C→B→A→S→National Level), gain experience points, level up their character, allocate stat points, complete quests, unlock abilities, and track progress across multiple life domains (career, skills, fitness, finance, social, habits).

## Features

### Core Systems
- **Player Progression**: XP-based leveling system (1-999 levels) with six character stats (STR, INT, AGI, VIT, SEN, LUK)
- **Rank System**: Seven rank tiers from E-Rank to National Level with progressive feature unlocking
- **Quest Management**: Multiple quest types including Daily Quests, Main Quests, Instant Dungeons, and Emergency Quests
- **Skills & Abilities**: Unlockable active and passive skills with skill point allocation
- **Achievement System**: Milestone tracking with rarity tiers and stat bonuses
- **Title System**: Earned designations providing permanent stat bonuses
- **Inventory**: Storage for templates, certificates, and consumable items
- **Gold Currency**: In-game currency earned through quest completion

### Life Area Modules
1. **Career Hunter** (E-Rank): Job scraping, AI-powered matching, auto-application system, interview prep
2. **Skill Trainer** (D-Rank): Skill development tracking and progression
3. **Fitness Hunter** (C-Rank): Physical health and exercise gamification
4. **Finance Manager** (B-Rank): Financial goal tracking and management
5. **Social Network** (A-Rank): Relationship and networking management
6. **Habit Forge** (S-Rank): Advanced habit formation and tracking

### AI Integration
- **Cover Letter Generation**: Customized cover letters via Ollama (qwen2.5-coder:7b)
- **Task Prioritization**: Intelligent quest prioritization based on urgency and impact
- **Difficulty Adjustment**: Dynamic difficulty scaling based on performance
- **Performance Insights**: AI-generated recommendations and motivational messages

## Technology Stack

**Backend:**
- Python 3.10+
- Flask (Web Framework)
- SQLAlchemy (ORM)
- APScheduler (Background Jobs)
- bcrypt (Password Security)

**Frontend:**
- HTML5 + CSS3 + Vanilla JavaScript
- Chart.js (Data Visualization)
- Responsive Design with Flexbox/Grid

**External Services:**
- SQLite 3.35+ (Database)
- MCP SQLite Server (Database Access Protocol)
- MCP Fetch Server (Web Scraping)
- Ollama with qwen2.5-coder:7b (AI Assistant)

**Testing:**
- pytest (Unit Testing)
- Hypothesis (Property-Based Testing)

## Installation

### Prerequisites
- Python 3.10 or higher
- Git
- Ollama (for AI features)
- MCP SQLite Server
- MCP Fetch Server

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lifehunter-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   FLASK_APP=src/app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///lifehunter.db
   OLLAMA_API_URL=http://localhost:11434
   MCP_SQLITE_URL=http://localhost:3000
   MCP_FETCH_URL=http://localhost:3001
   ```

6. **Initialize the database**
   ```bash
   python src/init_db.py
   ```

7. **Run the application**
   ```bash
   flask run
   ```

8. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
lifehunter-system/
├── src/                      # Source code
│   ├── app.py               # Main application entry point
│   ├── models/              # Database models
│   ├── controllers/         # API endpoints and business logic
│   ├── services/            # Core services (Progression, Quest, AI, etc.)
│   └── utils/               # Helper functions
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   └── property/           # Property-based tests
├── static/                  # Static assets (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/               # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   └── modules/
├── config/                  # Configuration files
│   ├── development.py
│   ├── production.py
│   └── testing.py
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in git)
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Usage

### Creating Your Character
1. Register a new account
2. Customize your initial character
3. Start with E-Rank and the Career Hunter module

### Completing Quests
1. Check your Daily Quests each day (refreshes at midnight)
2. Create Main Quests for long-term goals
3. Accept Instant Dungeons for time-limited challenges
4. Respond to Emergency Quests promptly

### Leveling Up
- Complete quests to earn XP
- Level up when you reach the XP threshold
- Allocate stat points to customize your build
- Unlock skills at specific level thresholds

### Career Hunter Module
1. Set your job search preferences
2. Review AI-matched jobs daily
3. Use auto-application for selected positions
4. Track application status and follow-ups
5. Complete interview preparation quests

### Penalty Zone
- Complete all Daily Quests before midnight to avoid penalties
- If triggered, complete the penalty challenge within 24 hours
- Failure results in -100 XP penalty

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_progression.py

# Run property-based tests
pytest tests/property/
```

### Database Migrations
```bash
# Create migration
python src/migrate.py create "description"

# Apply migrations
python src/migrate.py upgrade

# Rollback migration
python src/migrate.py downgrade
```

### Adding New Modules
1. Create module class in `src/services/modules/`
2. Define module-specific models in `src/models/`
3. Add module routes in `src/controllers/`
4. Update Module Manager with unlock requirements
5. Create module dashboard template

## Configuration

### Environment Variables
- `FLASK_APP`: Application entry point
- `FLASK_ENV`: Environment (development/production/testing)
- `SECRET_KEY`: Session encryption key
- `DATABASE_URL`: Database connection string
- `OLLAMA_API_URL`: Ollama service endpoint
- `MCP_SQLITE_URL`: MCP SQLite server URL
- `MCP_FETCH_URL`: MCP Fetch server URL

### Scheduled Jobs
- Daily Quest Generation: Every day at midnight
- Job Scraping: Every 6 hours
- Database Backup: Daily at 3 AM
- Penalty Zone Check: Daily at 11:59 PM

## API Documentation

Full API documentation is available at `/api/docs` when running in development mode.

### Key Endpoints
- `GET /api/player/{id}` - Get player profile
- `POST /api/quests/{id}/complete` - Complete quest
- `POST /api/player/{id}/stats/allocate` - Allocate stat point
- `GET /api/career/jobs` - Get matched jobs
- `POST /api/career/cover-letter` - Generate cover letter

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing Guidelines

- Write unit tests for all new functionality
- Use property-based tests for core logic
- Maintain test coverage above 80%
- Run tests before committing

## Troubleshooting

### Common Issues

**Ollama connection errors:**
- Verify Ollama service is running: `ollama serve`
- Check Ollama API URL in `.env`
- Ensure qwen2.5-coder:7b model is downloaded: `ollama pull qwen2.5-coder:7b`

**Database errors:**
- Delete `lifehunter.db` and run `python src/init_db.py` to recreate
- Check file permissions on database file
- Verify MCP SQLite server is running

**Job scraping failures:**
- Check MCP Fetch server status
- Verify internet connectivity
- Review rate limiting settings
- Check website HTML structure hasn't changed

## License

[Add your license here]

## Contact

[Add contact information]

## Acknowledgments

- Inspired by Solo Leveling manhwa/anime
- Built with Flask and SQLAlchemy
- AI powered by Ollama
- Property-based testing with Hypothesis
