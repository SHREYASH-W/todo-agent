# Database Initialization Module

This module provides comprehensive database initialization and seeding functionality for the LifeHunter gamified life management system.

## Overview

The `init_db.py` script handles:
1. Database connection validation
2. Table creation for all entities
3. Seed data population for testing and development

## Usage

### Initialize Complete Database

```bash
# Run from project root
python -m src.db.init_db
```

This will:
- Validate database connection
- Create all tables
- Seed initial data (skills, achievements, titles, jobs, job matches, applications)

### Import as Module

```python
from src.db.init_db import initialize_database, seed_initial_data

# Full initialization
initialize_database()

# Or seed individual components
from src.db.init_db import seed_skills, seed_achievements, seed_titles
seed_skills()
seed_achievements()
seed_titles()
```

## Seed Data Summary

### Core Progression Data

#### Skills (17 total)
- **Early Game (Level 1-10)**: Task Focus, Quick Learner, Rush Hour, Stamina Boost
- **Mid Game (Level 10-40)**: Multi-Tasking, Career Momentum, Golden Touch, Second Wind, Strategic Mind, Interview Mastery
- **Late Game (Level 40-60)**: Overdrive, Perfect Execution, Network Effect
- **End Game (Level 60+)**: Unstoppable, Master of All, Limit Break, National Authority

Types:
- Active Skills: Special abilities with cooldowns
- Passive Skills: Automatic bonuses

#### Achievements (17 total)
- **Common (4)**: First Steps, Getting Started, Daily Grind, Quest Novice
- **Rare (5)**: Rising Star, Career Hunter, Dedicated, Quest Adept, Speed Runner
- **Epic (4)**: Elite Hunter, Network Master, Unstoppable Force, Quest Master
- **Legendary (4)**: National Level Authority, Legendary Hunter, Eternal Dedication, Perfect Score

#### Titles (16 total)
- **Early Game**: Novice Hunter, The Dedicated, Career Seeker
- **Mid Game**: Skilled Combatant, Quest Enthusiast, Network Builder, D-Rank Hunter, C-Rank Hunter
- **Late Game**: B-Rank Hunter, A-Rank Hunter, The Relentless, Fortune's Favorite
- **End Game**: S-Rank Hunter, National Level Hunter, The Immortal, Legend

### Career Module Data

#### Jobs (10 total)
Sample job listings from various sources for testing job matching and application tracking:

1. **Senior Python Developer** - TechCorp Inc (LinkedIn)
2. **Full Stack Developer** - StartupXYZ (Indeed)
3. **Backend Engineer** - CloudSolutions Ltd (LinkedIn)
4. **Junior Python Developer** - DevShop Agency (Indeed)
5. **AI/ML Engineer** - IntelliTech Systems (LinkedIn)
6. **Frontend Developer** - WebWorks Studio (Indeed)
7. **Web Developer** - DigitalCraft Solutions (LinkedIn)
8. **Data Engineer** - DataFlow Analytics (Indeed)
9. **Database Administrator** - SecureData Corp (LinkedIn)
10. **DevOps Engineer** - AutomateNow Inc (Indeed)

Each job includes:
- Source (LinkedIn/Indeed)
- Title, Company, Location
- Full job description
- Original posting URL
- Posted date and scraped timestamp

#### Job Matches (10 total)
Sample job matches linking Player ID 1 to all jobs with calculated match scores (65-92).

**Note**: Job matches are only seeded if Player ID 1 exists. Otherwise, matches are generated dynamically by the Career Hunter module.

Match scores are based on hypothetical player skills:
- High matches (85-92): Python-heavy roles
- Medium matches (70-84): Mixed stack or data roles
- Lower matches (65-75): Frontend-focused or specialized roles

#### Applications (5 total)
Sample applications in various states for testing the application tracking system:

1. **TechCorp Inc** - Status: `interview` (Interview scheduled for Jan 28)
2. **DigitalCraft** - Status: `under_review` (High match score, awaiting response)
3. **StartupXYZ** - Status: `submitted` (Just submitted)
4. **CloudSolutions** - Status: `rejected` (Learning opportunity noted)
5. **DataFlow** - Status: `submitted` (Emphasis on data pipeline experience)

**Note**: Applications are only seeded if Player ID 1 exists.

Each application includes:
- Status (submitted/under_review/interview/rejected/offered)
- AI-generated cover letter
- Submission and update timestamps
- Interview date (if scheduled)
- Player notes

## Database Schema

The initialization script creates tables for:

### Core Entities
- `players` - Player profiles with stats and progression
- `quests` - Quest tracking with types and rewards
- `skills` - Available skills with unlock requirements
- `player_skills` - Player skill progression
- `achievements` - Achievement definitions
- `player_achievements` - Unlocked achievements
- `titles` - Title definitions with bonuses
- `player_titles` - Unlocked titles
- `inventory_items` - Player inventory
- `notifications` - System notifications

### Career Module Entities
- `jobs` - Scraped job listings
- `job_matches` - AI-calculated job matches
- `applications` - Job application tracking

### System Entities
- `performance_logs` - System performance metrics
- `database_backups` - Backup records

## Idempotency

All seed functions are idempotent:
- Running seed functions multiple times will not create duplicates
- Existing records are detected and skipped
- Safe to run after partial failures

## Testing

Run unit tests:
```bash
pytest tests/unit/test_init_db.py -v
```

Test coverage:
- Database connection validation
- Table creation
- Seed data integrity
- Idempotency checks
- Data relationships

## Notes

- The script uses `datetime.utcnow()` which generates deprecation warnings in Python 3.12+. This is a known issue and does not affect functionality.
- Job matches and applications require a player to exist (Player ID 1). The script gracefully handles the case where no player exists.
- All timestamps are stored in UTC.
- Seed data is designed for development and testing purposes.

## Future Enhancements

- Add seed data for other modules (Fitness, Finance, Social, Habits)
- Add more diverse job listings across different industries
- Add sample quests for different types (Daily, Main, Instant Dungeon, Emergency)
- Add sample inventory items (templates, certificates, consumables)
