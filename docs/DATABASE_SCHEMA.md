# LifeHunter Database Schema

## Overview

LifeHunter uses SQLite via SQLAlchemy ORM. All tables are created with `Base.metadata.create_all()`.

## Entity Relationship Summary

```
Player ──< Quest
       ──< PlayerSkill >── Skill
       ──< PlayerAchievement >── Achievement
       ──< PlayerTitle >── Title
       ──< InventoryItem
       ──< Notification
       ──< Application >── Job
       
Job ──< JobMatch >── Player
```

---

## Core Tables

### `players`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, autoincrement | Player unique ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Display name |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email address |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| level | INTEGER | DEFAULT 1 | Current level (1–999) |
| xp | INTEGER | DEFAULT 0 | Current XP within level |
| rank | VARCHAR(20) | DEFAULT 'E' | E/D/C/B/A/S/National |
| gold | INTEGER | DEFAULT 0 | Currency balance |
| str_stat | INTEGER | DEFAULT 10 | Strength stat |
| int_stat | INTEGER | DEFAULT 10 | Intelligence stat |
| agi_stat | INTEGER | DEFAULT 10 | Agility stat |
| vit_stat | INTEGER | DEFAULT 10 | Vitality stat |
| sen_stat | INTEGER | DEFAULT 10 | Sense stat |
| luk_stat | INTEGER | DEFAULT 10 | Luck stat |
| hp | INTEGER | DEFAULT 200 | Hit Points = 100 + (VIT×10) |
| mp | INTEGER | DEFAULT 100 | Mana Points = 50 + (INT×5) |
| stat_points | INTEGER | DEFAULT 0 | Unspent stat points |
| skill_points | INTEGER | DEFAULT 0 | Unspent skill points |
| active_title_id | INTEGER | FK → titles.id | Currently equipped title |
| created_at | DATETIME | DEFAULT NOW | Account creation time |
| last_login | DATETIME | | Last login time |

### `quests`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK | Quest ID |
| player_id | INTEGER | FK → players.id | Owner player |
| quest_type | VARCHAR(20) | NOT NULL | daily/main/instant/emergency |
| title | VARCHAR(200) | NOT NULL | Quest title |
| description | TEXT | | Quest description |
| xp_reward | INTEGER | DEFAULT 0 | XP awarded on completion |
| gold_reward | INTEGER | DEFAULT 0 | Gold awarded on completion |
| difficulty | VARCHAR(20) | | very_easy/easy/medium/hard |
| status | VARCHAR(20) | DEFAULT 'active' | active/completed/failed |
| deadline | DATETIME | | Optional deadline |
| completed_at | DATETIME | | Completion timestamp |
| parent_quest_id | INTEGER | FK → quests.id | Parent for sub-quests |
| created_at | DATETIME | DEFAULT NOW | Creation timestamp |

### `skills`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Skill ID |
| name | VARCHAR(100) | Skill name |
| description | TEXT | Skill description |
| skill_type | VARCHAR(20) | passive/active |
| max_level | INTEGER | Max skill level (default 10) |
| unlock_level | INTEGER | Player level required to unlock |
| prerequisite_skill_id | INTEGER FK | Required skill ID |
| effect_data | TEXT | JSON effect configuration |

### `player_skills`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Record ID |
| player_id | INTEGER FK | Player |
| skill_id | INTEGER FK | Skill |
| current_level | INTEGER | Current skill level (1–10) |
| unlocked_at | DATETIME | When skill was unlocked |

### `achievements`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Achievement ID |
| name | VARCHAR(100) | Achievement name |
| description | TEXT | Achievement description |
| rarity | VARCHAR(20) | common/rare/epic/legendary |
| condition_type | VARCHAR(50) | level/quest_count/stat/custom |
| condition_value | TEXT | JSON condition parameters |
| stat_bonus | TEXT | JSON stat bonuses applied on unlock |

### `player_achievements`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Record ID |
| player_id | INTEGER FK | Player |
| achievement_id | INTEGER FK | Achievement |
| unlocked_at | DATETIME | When achievement was unlocked |

### `titles`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Title ID |
| name | VARCHAR(100) | Title name |
| description | TEXT | Title description |
| unlock_condition | TEXT | How to unlock |
| stat_bonuses | TEXT | JSON stat bonuses when equipped |

### `player_titles`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Record ID |
| player_id | INTEGER FK | Player |
| title_id | INTEGER FK | Title |
| unlocked_at | DATETIME | When title was unlocked |

### `inventory_items`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Item ID |
| player_id | INTEGER FK | Owner player |
| item_type | VARCHAR(20) | template/certificate/consumable |
| name | VARCHAR(200) | Item name |
| content | TEXT | Item content (e.g., resume text) |
| acquired_at | DATETIME | When item was acquired |
| used_at | DATETIME | When consumable was used |

### `notifications`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Notification ID |
| player_id | INTEGER FK | Recipient player |
| notification_type | VARCHAR(50) | level_up/quest_complete/achievement_unlock/etc |
| title | VARCHAR(200) | Notification title |
| message | TEXT | Notification message |
| is_read | BOOLEAN | Whether notification has been read |
| created_at | DATETIME | Creation timestamp |

---

## Career Module Tables

### `jobs`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Job ID |
| source | VARCHAR(50) | linkedin/indeed |
| title | VARCHAR(200) | Job title |
| company | VARCHAR(200) | Company name |
| location | VARCHAR(200) | Job location |
| description | TEXT | Full job description |
| url | VARCHAR(500) UNIQUE | Job posting URL |
| posted_date | DATETIME | When job was posted |
| scraped_at | DATETIME | When job was scraped |

### `job_matches`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Match ID |
| player_id | INTEGER FK | Player |
| job_id | INTEGER FK | Job |
| match_score | FLOAT | Match score 0–100 |
| matching_skills | TEXT | JSON list of matching skills |
| calculated_at | DATETIME | When match was calculated |

### `applications`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Application ID |
| player_id | INTEGER FK | Applicant player |
| job_id | INTEGER FK | Applied job |
| status | VARCHAR(30) | submitted/under_review/interview_scheduled/offered/rejected |
| cover_letter | TEXT | Generated cover letter text |
| applied_at | DATETIME | Application submission time |
| updated_at | DATETIME | Last status update time |
| interview_date | DATETIME | Scheduled interview date |
| notes | TEXT | Player notes about application |

---

## System Tables

### `performance_logs`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Log ID |
| metric_name | VARCHAR(100) | Metric identifier |
| metric_value | FLOAT | Metric value |
| timestamp | DATETIME | When metric was recorded |

### `database_backups`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Backup ID |
| file_path | VARCHAR(500) | Path to backup file |
| file_size | INTEGER | Backup file size in bytes |
| created_at | DATETIME | When backup was created |

---

## Indexes

- `players.username` — unique index for login lookup
- `players.email` — unique index for registration check
- `quests.player_id` — for player quest queries
- `quests.status` — for active quest filtering
- `jobs.url` — unique index for deduplication
- `job_matches.player_id` — for player-specific matches
- `applications.player_id` — for application history
- `notifications.player_id` — for notification retrieval
- `performance_logs.metric_name` — for metric queries
- `performance_logs.timestamp` — for time-range queries

## XP Formula

```
xp_required(level) = 100 × level^1.5
```

## Derived Stats

```
HP = 100 + (VIT × 10)
MP = 50  + (INT × 5)
```

## Rank Thresholds

| Level | Rank |
|-------|------|
| 1 | E |
| 10 | D |
| 25 | C |
| 40 | B |
| 60 | A |
| 80 | S |
| 100 | National |
