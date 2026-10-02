# LifeHunter API Reference

Base URL: `http://localhost:5000/api`

All endpoints return JSON. Authentication via `session_token` in request body or `Authorization: Bearer <token>` header.

---

## Player Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/player/{id}` | Get player profile |
| GET | `/player/{id}/stats` | Get player statistics |
| POST | `/player/{id}/stats/allocate` | Allocate stat point |
| GET | `/player/{id}/skills` | Get skill tree |
| POST | `/player/{id}/skills/allocate` | Allocate skill point |

### POST `/player/{id}/stats/allocate`
```json
{ "stat_name": "str_stat" }
```
Valid stat names: `str_stat`, `int_stat`, `agi_stat`, `vit_stat`, `sen_stat`, `luk_stat`

---

## Quest Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/quests?player_id=1` | Get all active quests |
| GET | `/quests/daily?player_id=1` | Get today's daily quests |
| POST | `/quests` | Create new quest |
| POST | `/quests/{id}/complete` | Mark quest complete |
| DELETE | `/quests/{id}?player_id=1` | Delete quest |

### POST `/quests`
```json
{
  "player_id": 1,
  "quest_type": "main",
  "title": "Learn Python",
  "description": "Complete Python course",
  "xp_reward": 150,
  "gold_reward": 50,
  "difficulty": "medium"
}
```

---

## Career Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/career/jobs?player_id=1&min_score=70` | Get matched jobs |
| POST | `/career/scrape` | Trigger job scraping |
| POST | `/career/applications` | Create application |
| GET | `/career/applications?player_id=1` | Get applications |
| PUT | `/career/applications/{id}` | Update status |
| POST | `/career/cover-letter` | Generate cover letter |

### POST `/career/cover-letter`
```json
{
  "job_description": "We need a Python developer...",
  "resume": "Experienced developer with 5 years...",
  "job_title": "Senior Python Developer",
  "company": "TechCorp"
}
```

---

## Module Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/modules?player_id=1` | Get available modules |
| GET | `/modules/{name}/dashboard?player_id=1` | Module dashboard |

Module names: `career_hunter`, `skill_trainer`, `fitness_hunter`, `finance_manager`, `social_network`, `habit_forge`

---

## Authentication Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login |
| POST | `/auth/logout` | Logout |
| POST | `/auth/reset-password` | Reset password |

### POST `/auth/register`
```json
{ "username": "hunter", "email": "user@example.com", "password": "securepass123" }
```

### POST `/auth/login`
```json
{ "username": "hunter", "password": "securepass123" }
```
Response: `{ "session_token": "...", "player_id": 1 }`

---

## Error Responses

All errors return:
```json
{ "error": "Human-readable message", "type": "ErrorClassName" }
```

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 401 | Authentication required |
| 403 | Access denied / locked module |
| 404 | Resource not found |
| 409 | Conflict (duplicate, invalid state transition) |
| 503 | External service unavailable (Ollama, scraper) |
