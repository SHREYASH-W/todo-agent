# Implementation Plan: LifeHunter Gamified Life Management System

## Overview

LifeHunter transforms real-life tasks into an immersive RPG experience with player progression, quest management, six specialized life modules, AI-powered assistance via Ollama, job scraping via MCP Fetch, and SQLite database access via MCP. This implementation follows a layered architecture: database schema → integration layer → application layer → module layer → presentation layer, with property-based testing for core business logic.

The implementation uses Python 3.10+ with Flask/FastAPI for the backend, vanilla HTML/CSS/JavaScript for the frontend, and external services (Ollama qwen2.5-coder:7b, MCP SQLite, MCP Fetch) for AI assistance, database operations, and web scraping.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure: `src/`, `tests/`, `static/`, `templates/`, `config/`
  - Create `requirements.txt` with dependencies: Flask/FastAPI, SQLAlchemy, requests, APScheduler, bcrypt, pytest, hypothesis, Chart.js
  - Create `README.md` with project overview and setup instructions
  - Initialize Git repository with `.gitignore` for Python projects
  - _Requirements: All system requirements_

- [x] 2. Database schema and initialization
  - [x] 2.1 Define SQLAlchemy ORM models for core entities
    - Create `src/models/player.py` with Player model (id, username, email, password_hash, level, xp, rank, stats, points, title)
    - Create `src/models/quest.py` with Quest model (id, player_id, quest_type, title, description, rewards, status, timestamps, parent_quest_id)
    - Create `src/models/skill.py` with Skill, PlayerSkill models
    - Create `src/models/achievement.py` with Achievement, PlayerAchievement models
    - Create `src/models/title.py` with Title, PlayerTitle models
    - Create `src/models/inventory.py` with InventoryItem model
    - Create `src/models/notification.py` with Notification model
    - _Requirements: 1.1-1.7, 2.1-2.8, 3.1-3.8, 4.1-4.7, 5.1-5.7, 8.1-8.7, 9.1-9.8, 10.1-10.7, 11.1-11.7, 12.1-12.7, 13.1-13.7_
  
  - [x] 2.2 Define SQLAlchemy ORM models for Career module entities
    - Create `src/models/job.py` with Job model (id, source, title, company, location, description, url, posted_date, scraped_at)
    - Create `src/models/job_match.py` with JobMatch model (id, player_id, job_id, match_score, matching_skills, calculated_at)
    - Create `src/models/application.py` with Application model (id, player_id, job_id, status, cover_letter, timestamps, interview_date, notes)
    - _Requirements: 15.1-15.7, 16.1-16.7, 17.1-17.7, 18.1-18.7_
  
  - [x] 2.3 Define SQLAlchemy ORM models for system entities
    - Create `src/models/performance_log.py` with PerformanceLog model
    - Create `src/models/database_backup.py` with DatabaseBackup model
    - _Requirements: System monitoring and backup_
  
  - [x] 2.4 Create database initialization script
    - Create `src/db/init_db.py` with schema creation functions
    - Implement `create_all_tables()` function using SQLAlchemy metadata
    - Create seed data functions for initial skills, achievements, titles
    - Add database connection validation
    - _Requirements: All entity requirements_

- [x] 3. Integration Layer - Database Manager
  - [x] 3.1 Implement Database Manager with MCP SQLite integration
    - Create `src/integrations/database_manager.py` with DatabaseManager class
    - Implement `execute_query(query, params)` method using MCP SQLite protocol
    - Implement `execute_transaction(queries)` method with rollback support
    - Implement connection pool management (max 10 connections, 30s timeout)
    - Implement `backup_database(backup_path)` method
    - Implement `validate_query(query)` method for SQL injection prevention
    - _Requirements: All database persistence requirements_
  
  - [ ]* 3.2 Write unit tests for Database Manager
    - Test query execution with parameterized queries
    - Test transaction rollback on errors
    - Test connection pool exhaustion handling
    - Test backup creation and verification
    - _Requirements: Database operations correctness_

- [x] 4. Integration Layer - AI Assistant
  - [x] 4.1 Implement AI Assistant with Ollama integration
    - Create `src/integrations/ai_assistant.py` with AIAssistant class
    - Implement `generate_cover_letter(job_description, resume)` method (temperature=0.7, max_tokens=500, 30s timeout)
    - Implement `prioritize_quests(quests)` method (temperature=0.3, max_tokens=200)
    - Implement `adjust_difficulty(player_id, performance_data)` method
    - Implement `generate_insights(player_id, period)` method
    - Implement `generate_motivational_message(context)` method
    - Implement `extract_job_skills(job_description)` method
    - Add retry logic with exponential backoff (3 attempts: 2s, 4s, 8s)
    - _Requirements: 28.1-28.7, 29.1-29.7, 30.1-30.7, 31.1-31.7_
  
  - [ ]* 4.2 Write unit tests for AI Assistant with Ollama mocks
    - Test cover letter generation with mocked Ollama responses
    - Test timeout handling and retry logic
    - Test error handling for unavailable Ollama service
    - Test all temperature and token configurations
    - _Requirements: 28.1-28.7_

- [x] 5. Integration Layer - Job Scraper
  - [x] 5.1 Implement Job Scraper with MCP Fetch integration
    - Create `src/integrations/job_scraper.py` with JobScraper class
    - Implement `scrape_linkedin(keywords, location)` method with rate limiting (1 req/2s)
    - Implement `scrape_indeed(keywords, location)` method with rate limiting (1 req/2s)
    - Implement `parse_job_html(html, source)` method for extracting job fields
    - Implement `deduplicate_jobs(jobs)` method using (title, company) combination
    - Implement `schedule_scraping(interval_hours)` method using APScheduler (6 hour interval)
    - Add retry logic with exponential backoff (3 attempts: 2s, 4s, 8s)
    - Add User-Agent rotation and robots.txt respect
    - _Requirements: 15.1-15.7_
  
  - [ ]* 5.2 Write property test for job deduplication
    - **Property 19: Job Deduplication**
    - **Validates: Requirements 15.5**
    - Use Hypothesis to generate lists of jobs with duplicate (title, company) pairs
    - Verify deduplication produces no duplicate (title, company) combinations
    - _Requirements: 15.5_
  
  - [ ]* 5.3 Write unit tests for Job Scraper
    - Test LinkedIn scraping with mocked HTTP responses
    - Test Indeed scraping with mocked HTTP responses
    - Test HTML parsing for various job posting formats
    - Test rate limiting enforcement
    - Test retry logic on failures
    - _Requirements: 15.1-15.7_

- [x] 6. Application Layer - Progression Engine
  - [x] 6.1 Implement Progression Engine core logic
    - Create `src/engine/progression_engine.py` with ProgressionEngine class
    - Implement `award_xp(player_id, xp_amount)` method with level-up detection using formula: xp_required = 100 * (level^1.5)
    - Implement `allocate_stat_point(player_id, stat_name)` method with validation (available_points >= 1)
    - Implement `allocate_skill_point(player_id, skill_id)` method with validation
    - Implement `get_player_stats(player_id)` method
    - Implement `check_rank_advancement(player_id)` method with thresholds: E(1), D(10), C(25), B(40), A(60), S(80), National(100)
    - Implement `calculate_xp_requirement(level)` method
    - Implement `calculate_derived_stats(stats)` method using: HP = 100 + (VIT * 10), MP = 50 + (INT * 5)
    - Add level boundary enforcement (1-999)
    - Add stat point granting (5 points per level up)
    - _Requirements: 1.1-1.7, 2.1-2.8, 3.1-3.8, 13.1-13.7_
  
  - [ ]* 6.2 Write property test for level progression through XP accumulation
    - **Property 1: Level Progression Through XP Accumulation**
    - **Validates: Requirements 1.1, 1.2, 1.4**
    - Use Hypothesis to generate player levels (1-999) and XP amounts
    - Verify level increments when XP >= threshold
    - Verify threshold recalculation for new level
    - _Requirements: 1.1, 1.2, 1.4_
  
  - [ ]* 6.3 Write property test for level boundary invariant
    - **Property 2: Level Boundary Invariant**
    - **Validates: Requirements 1.5**
    - Use Hypothesis to generate various XP award operations
    - Verify resulting level always stays within [1, 999]
    - _Requirements: 1.5_
  
  - [ ]* 6.4 Write property test for point allocation correctness
    - **Property 3: Point Allocation Correctness**
    - **Validates: Requirements 1.3, 1.7, 3.3, 9.3, 9.4**
    - Use Hypothesis to generate players with available points
    - Verify allocation decrements available points by 1
    - Verify allocation increments target stat/skill by 1
    - Verify available_points >= 0 invariant maintained
    - _Requirements: 1.3, 1.7, 3.3, 9.3, 9.4_
  
  - [ ]* 6.5 Write property test for derived stat calculation
    - **Property 4: Derived Stat Calculation**
    - **Validates: Requirements 3.5, 3.6, 3.7**
    - Use Hypothesis to generate VIT and INT values
    - Verify HP = 100 + (VIT * 10)
    - Verify MP = 50 + (INT * 5)
    - Verify recalculation triggers on VIT/INT changes
    - _Requirements: 3.5, 3.6, 3.7_
  
  - [ ]* 6.6 Write property test for gold balance non-negativity
    - **Property 17: Gold Balance Non-Negativity Invariant**
    - **Validates: Requirements 13.2, 13.3, 13.4**
    - Use Hypothesis to generate gold transactions (award, spend)
    - Verify resulting balance always >= 0
    - Verify operations that would cause negative balance are rejected
    - _Requirements: 13.2, 13.3, 13.4_
  
  - [ ]* 6.7 Write unit tests for Progression Engine
    - Test XP formula calculation for various levels
    - Test rank advancement at exact thresholds
    - Test stat allocation boundary cases
    - Test gold transactions and balance updates
    - _Requirements: 1.1-1.7, 2.1-2.8, 3.1-3.8, 13.1-13.7_

- [x] 7. Application Layer - Quest Manager
  - [x] 7.1 Implement Quest Manager core logic
    - Create `src/engine/quest_manager.py` with QuestManager class
    - Implement `create_daily_quests(player_id, date)` method generating 3-5 quests
    - Implement `create_main_quest(player_id, quest_data)` method with sub-quest support
    - Implement `start_instant_dungeon(player_id, dungeon_data)` method with timer (15 min - 4 hours)
    - Implement `create_emergency_quest(player_id, quest_data)` method with 2x XP multiplier
    - Implement `complete_quest(quest_id, player_id)` method with XP/gold rewards
    - Implement `check_daily_quest_failure(player_id, date)` method triggered at midnight
    - Implement `activate_penalty_zone(player_id)` method with -100 XP penalty on failure
    - Implement `get_active_quests(player_id)` method returning QuestCollection
    - Add quest limit enforcement: 10 main quests, 1 instant dungeon, 3 emergency quests
    - _Requirements: 4.1-4.7, 5.1-5.7, 6.1-6.7, 7.1-7.7, 8.1-8.7_
  
  - [ ]* 7.2 Write property test for daily quest count constraint
    - **Property 5: Daily Quest Count Constraint**
    - **Validates: Requirements 4.2**
    - Use Hypothesis to generate daily quest creation operations
    - Verify quest count always between 3 and 5 (inclusive)
    - _Requirements: 4.2_
  
  - [ ]* 7.3 Write property test for quest completion rewards
    - **Property 6: Quest Completion Rewards**
    - **Validates: Requirements 1.1, 4.3, 5.4**
    - Use Hypothesis to generate quests with various XP rewards
    - Verify player receives exact XP reward on completion
    - Verify quest status changes from "active" to "completed"
    - _Requirements: 1.1, 4.3, 5.4_
  
  - [ ]* 7.4 Write property test for daily quest completion percentage
    - **Property 7: Daily Quest Completion Percentage**
    - **Validates: Requirements 4.6**
    - Use Hypothesis to generate sets of daily quests with various completion states
    - Verify percentage = (completed / total) * 100
    - Verify percentage in range [0, 100]
    - _Requirements: 4.6_
  
  - [ ]* 7.5 Write property test for main quest sub-quest completion propagation
    - **Property 8: Main Quest Sub-quest Completion Propagation**
    - **Validates: Requirements 5.3**
    - Use Hypothesis to generate main quests with N sub-quests
    - Verify main quest status becomes "completed" when all N sub-quests completed
    - _Requirements: 5.3_
  
  - [ ]* 7.6 Write property test for main quest progress percentage
    - **Property 9: Main Quest Progress Percentage**
    - **Validates: Requirements 5.5**
    - Use Hypothesis to generate main quests with N sub-quests and K completed
    - Verify progress = (K / N) * 100
    - _Requirements: 5.5_
  
  - [ ]* 7.7 Write property test for concurrent main quest limit
    - **Property 10: Concurrent Main Quest Limit**
    - **Validates: Requirements 5.6**
    - Use Hypothesis to generate players with varying numbers of active main quests
    - Verify creation succeeds when N < 10
    - Verify creation fails when N = 10
    - _Requirements: 5.6_
  
  - [ ]* 7.8 Write property test for penalty zone state machine
    - **Property 11: Penalty Zone State Machine**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
    - Use Hypothesis to generate daily quest failure scenarios
    - Verify penalty zone activates on failed daily quests
    - Verify penalty zone deactivates on challenge completion
    - Verify -100 XP penalty applied on challenge failure
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [ ]* 7.9 Write unit tests for Quest Manager
    - Test instant dungeon timer expiration
    - Test emergency quest deadline enforcement
    - Test quest limit enforcement for all types
    - Test daily quest generation at midnight
    - _Requirements: 4.1-4.7, 5.1-5.7, 6.1-6.7, 7.1-7.7, 8.1-8.7_

- [x] 8. Application Layer - Skills and Abilities System
  - [x] 8.1 Implement skills and abilities logic
    - Create `src/engine/skill_system.py` with SkillSystem class
    - Implement `unlock_skill(player_id, skill_id)` method with level threshold validation
    - Implement `allocate_skill_point(player_id, skill_id)` method with max level limit (10)
    - Implement `apply_passive_bonuses(player_id)` method for automatic passive skill effects
    - Implement `activate_active_skill(player_id, skill_id)` method with cooldown timer
    - Implement skill point granting (1 point per level up)
    - _Requirements: 9.1-9.8_
  
  - [ ]* 8.2 Write property test for skill unlock based on level threshold
    - **Property 12: Skill Unlock Based on Level Threshold**
    - **Validates: Requirements 9.1**
    - Use Hypothesis to generate player levels and skill unlock levels
    - Verify skill unlocked if and only if player_level >= unlock_level
    - _Requirements: 9.1_
  
  - [ ]* 8.3 Write property test for passive skill bonus application
    - **Property 13: Passive Skill Bonus Application**
    - **Validates: Requirements 9.6**
    - Use Hypothesis to generate players with passive skills
    - Verify effective stats include passive bonuses automatically
    - _Requirements: 9.6_
  
  - [ ]* 8.4 Write unit tests for Skill System
    - Test active skill cooldown enforcement
    - Test skill prerequisite validation
    - Test skill max level limit (10)
    - _Requirements: 9.1-9.8_

- [x] 9. Application Layer - Achievement and Title Systems
  - [x] 9.1 Implement achievement and title logic
    - Create `src/engine/achievement_system.py` with AchievementSystem class
    - Implement `check_achievement_unlock(player_id, achievement_id)` method with condition evaluation
    - Implement `unlock_achievement(player_id, achievement_id)` method with stat bonus application
    - Implement `equip_title(player_id, title_id)` method with stat bonus application
    - Implement `unequip_title(player_id)` method with stat bonus removal
    - Implement achievement rarity categories: common, rare, epic, legendary
    - _Requirements: 10.1-10.7, 11.1-11.7_
  
  - [ ]* 9.2 Write property test for achievement unlock based on conditions
    - **Property 14: Achievement Unlock Based on Conditions**
    - **Validates: Requirements 10.1**
    - Use Hypothesis to generate player states and achievement conditions
    - Verify achievement unlocks when conditions satisfied
    - _Requirements: 10.1_
  
  - [ ]* 9.3 Write property test for title bonus application toggle
    - **Property 15: Title Bonus Application Toggle**
    - **Validates: Requirements 11.3, 11.4**
    - Use Hypothesis to generate titles with stat bonuses
    - Verify stats increase by B when equipped
    - Verify stats decrease by B when unequipped
    - Verify equip then unequip returns to original stats
    - _Requirements: 11.3, 11.4_
  
  - [ ]* 9.4 Write unit tests for Achievement and Title Systems
    - Test achievement condition evaluation for various types
    - Test achievement notification generation
    - Test title stat bonus percentage and flat value calculations
    - _Requirements: 10.1-10.7, 11.1-11.7_

- [x] 10. Application Layer - Inventory System
  - [x] 10.1 Implement inventory management logic
    - Create `src/engine/inventory_system.py` with InventorySystem class
    - Implement `add_item(player_id, item)` method with capacity check (100 per category)
    - Implement `remove_item(player_id, item_id)` method with existence validation
    - Implement `use_consumable(player_id, item_id)` method with removal after use
    - Implement `search_items(player_id, query)` method for name/category search
    - Implement item categories: templates, certificates, consumables
    - _Requirements: 12.1-12.7_
  
  - [ ]* 10.2 Write property test for inventory item addition and removal
    - **Property 16: Inventory Item Addition and Removal**
    - **Validates: Requirements 12.2, 12.4, 12.5**
    - Use Hypothesis to generate inventory states with varying item counts
    - Verify addition succeeds when I < C and increases count to I+1
    - Verify addition fails when I >= C
    - Verify removal succeeds for existing items and decreases count to I-1
    - Verify removal fails for non-existent items
    - _Requirements: 12.2, 12.4, 12.5_
  
  - [ ]* 10.3 Write unit tests for Inventory System
    - Test item search by name and category
    - Test consumable usage and removal
    - Test item organization by categories
    - _Requirements: 12.1-12.7_

- [x] 11. Application Layer - Module Manager
  - [x] 11.1 Implement module management and unlocking logic
    - Create `src/engine/module_manager.py` with ModuleManager class
    - Implement `get_available_modules(player_id)` method based on player rank
    - Implement `get_module(module_name)` method for module instance retrieval
    - Implement `check_module_unlock(player_id, module_name)` method
    - Implement `get_module_statistics(player_id)` method aggregating stats from all modules
    - Define module unlock requirements: E(Career), D(Skill), C(Fitness), B(Finance), A(Social), S(Habit)
    - _Requirements: 14.1-14.8_
  
  - [ ]* 11.2 Write property test for module unlock based on rank
    - **Property 18: Module Unlock Based on Rank**
    - **Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7**
    - Use Hypothesis to generate player ranks
    - Verify available modules equal union of all modules with unlock_rank <= player_rank
    - Verify progression: E(Career), D(+Skill), C(+Fitness), B(+Finance), A(+Social), S(+Habit)
    - _Requirements: 14.1-14.8_
  
  - [ ]* 11.3 Write unit tests for Module Manager
    - Test module instance retrieval
    - Test statistics aggregation from multiple modules
    - Test locked module access rejection
    - _Requirements: 14.1-14.8_

- [x] 12. Application Layer - Authentication Service
  - [x] 12.1 Implement authentication and session management
    - Create `src/engine/auth_service.py` with AuthService class
    - Implement `register(username, email, password)` method with bcrypt password hashing
    - Implement `login(username, password)` method with session creation
    - Implement `logout(session_id)` method with session cleanup
    - Implement `reset_password(email)` method with email verification
    - Implement account lockout after 5 failed login attempts
    - Implement session timeout (default 30 minutes)
    - _Requirements: Authentication requirements_
  
  - [ ]* 12.2 Write unit tests for Authentication Service
    - Test password hashing and verification
    - Test session creation and expiration
    - Test account lockout enforcement
    - Test unauthorized access prevention
    - _Requirements: Authentication security_

- [x] 13. Application Layer - Notification Service
  - [x] 13.1 Implement notification generation and delivery
    - Create `src/engine/notification_service.py` with NotificationService class
    - Implement `notify_level_up(player_id, new_level)` method
    - Implement `notify_quest_complete(player_id, quest_id)` method
    - Implement `notify_achievement_unlock(player_id, achievement_id)` method
    - Implement `notify_penalty_zone(player_id)` method
    - Implement `get_unread_notifications(player_id)` method
    - Implement `mark_as_read(notification_id)` method
    - Implement rate limiting: 1 notification per event type per minute
    - _Requirements: Notification requirements_
  
  - [ ]* 13.2 Write property test for notification rate limiting
    - **Property 24: Notification Rate Limiting**
    - **Validates: Notification rate limiting requirements**
    - Use Hypothesis to generate notification events within 1-minute windows
    - Verify no more than 1 notification per event type per minute
    - _Requirements: Rate limiting_
  
  - [ ]* 13.3 Write unit tests for Notification Service
    - Test notification creation for various event types
    - Test unread notification retrieval
    - Test mark as read functionality
    - _Requirements: Notification functionality_

- [~] 14. Checkpoint - Ensure all core components pass tests
  - Run pytest on all unit and property tests
  - Verify database schema creation and migration
  - Verify integration layer connections (Database Manager, AI Assistant, Job Scraper)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Module Layer - Career Hunter Module
  - [x] 15.1 Implement Career Hunter module core functionality
    - Create `src/modules/career_hunter.py` with CareerHunterModule class
    - Implement `scrape_jobs(sources, keywords)` method using JobScraper
    - Implement `match_jobs(player_id, jobs)` method using AI skill extraction and comparison
    - Implement `generate_cover_letter(player_id, job_id)` method using AIAssistant
    - Implement `create_application(player_id, job_id, cover_letter)` method with 50 XP reward
    - Implement `update_application_status(application_id, status)` method
    - Implement `generate_interview_prep(application_id)` method with 75 XP reward quest
    - Implement `create_followup_task(application_id, days)` method with 25 XP reward
    - Implement job match algorithm: extract skills → compare → calculate overlap → weight by required/preferred → return score (0-100)
    - _Requirements: 15.1-15.7, 16.1-16.7, 17.1-17.7, 18.1-18.7, 19.1-19.7, 20.1-20.7, 21.1-21.7_
  
  - [ ]* 15.2 Write property test for application state transition validity
    - **Property 20: Application State Transition Validity**
    - **Validates: Requirements 18.1, 18.2**
    - Use Hypothesis to generate application state transitions
    - Verify valid transitions: submitted → under_review → {interview_scheduled, rejected}, interview_scheduled → {offered, rejected}
    - Verify invalid transitions are rejected
    - _Requirements: 18.1, 18.2_
  
  - [ ]* 15.3 Write property test for follow-up task cancellation on terminal status
    - **Property 21: Follow-up Task Cancellation on Terminal Status**
    - **Validates: Requirements 20.7**
    - Use Hypothesis to generate applications reaching terminal status (rejected, offered)
    - Verify all associated pending follow-up tasks are cancelled
    - _Requirements: 20.7_
  
  - [ ]* 15.4 Write unit tests for Career Hunter module
    - Test job matching algorithm with various skill sets
    - Test cover letter generation with mocked AI responses
    - Test interview preparation quest creation
    - Test follow-up task scheduling
    - Test networking quest suggestions
    - _Requirements: 15.1-21.7_

- [x] 16. Module Layer - Skill Trainer Module (Placeholder)
  - [x] 16.1 Implement Skill Trainer module structure
    - Create `src/modules/skill_trainer.py` with SkillTrainerModule class
    - Implement placeholder methods for skill tracking and course recommendations
    - Integrate with module manager for D-Rank unlock
    - _Requirements: 14.2_

- [x] 17. Module Layer - Fitness Hunter Module (Placeholder)
  - [x] 17.1 Implement Fitness Hunter module structure
    - Create `src/modules/fitness_hunter.py` with FitnessHunterModule class
    - Implement placeholder methods for workout tracking and goals
    - Integrate with module manager for C-Rank unlock
    - _Requirements: 14.3_

- [x] 18. Module Layer - Finance Manager Module (Placeholder)
  - [x] 18.1 Implement Finance Manager module structure
    - Create `src/modules/finance_manager.py` with FinanceManagerModule class
    - Implement placeholder methods for budget tracking and financial goals
    - Integrate with module manager for B-Rank unlock
    - _Requirements: 14.4_

- [x] 19. Module Layer - Social Network Module (Placeholder)
  - [x] 19.1 Implement Social Network module structure
    - Create `src/modules/social_network.py` with SocialNetworkModule class
    - Implement placeholder methods for relationship tracking and social goals
    - Integrate with module manager for A-Rank unlock
    - _Requirements: 14.5_

- [x] 20. Module Layer - Habit Forge Module (Placeholder)
  - [x] 20.1 Implement Habit Forge module structure
    - Create `src/modules/habit_forge.py` with HabitForgeModule class
    - Implement placeholder methods for habit tracking and streaks
    - Integrate with module manager for S-Rank unlock
    - _Requirements: 14.6_

- [x] 21. REST API Layer - Player Endpoints
  - [x] 21.1 Implement player-related API endpoints
    - Create `src/api/routes/player.py` with Flask/FastAPI routes
    - Implement `GET /api/player/{id}` endpoint returning player profile
    - Implement `GET /api/player/{id}/stats` endpoint returning player statistics
    - Implement `POST /api/player/{id}/stats/allocate` endpoint for stat point allocation
    - Implement `GET /api/player/{id}/skills` endpoint returning skill tree
    - Implement `POST /api/player/{id}/skills/allocate` endpoint for skill point allocation
    - Add input validation and error handling (400 Bad Request, 404 Not Found)
    - _Requirements: 22.1-22.7_
  
  - [ ]* 21.2 Write integration tests for player endpoints
    - Test player profile retrieval
    - Test stat allocation with valid and invalid inputs
    - Test skill allocation with prerequisites
    - _Requirements: 22.1-22.7_

- [x] 22. REST API Layer - Quest Endpoints
  - [x] 22.1 Implement quest-related API endpoints
    - Create `src/api/routes/quest.py` with Flask/FastAPI routes
    - Implement `GET /api/quests` endpoint returning all active quests for player
    - Implement `POST /api/quests` endpoint for creating new quests
    - Implement `POST /api/quests/{id}/complete` endpoint for marking quests complete
    - Implement `DELETE /api/quests/{id}` endpoint for deleting quests
    - Implement `GET /api/quests/daily` endpoint returning today's daily quests
    - Add input validation and error handling (400 Bad Request, 404 Not Found, 409 Conflict)
    - _Requirements: 23.1-23.7_
  
  - [ ]* 22.2 Write integration tests for quest endpoints
    - Test quest retrieval organized by type
    - Test quest completion with XP rewards
    - Test quest creation with various types
    - Test daily quest retrieval
    - _Requirements: 23.1-23.7_

- [x] 23. REST API Layer - Career Module Endpoints
  - [x] 23.1 Implement career module API endpoints
    - Create `src/api/routes/career.py` with Flask/FastAPI routes
    - Implement `GET /api/career/jobs` endpoint returning matched jobs
    - Implement `POST /api/career/scrape` endpoint triggering job scraping
    - Implement `POST /api/career/applications` endpoint creating applications
    - Implement `GET /api/career/applications` endpoint returning application history
    - Implement `PUT /api/career/applications/{id}` endpoint updating application status
    - Implement `POST /api/career/cover-letter` endpoint generating cover letters
    - Add input validation and error handling (400 Bad Request, 503 Service Unavailable)
    - _Requirements: 15.1-21.7_
  
  - [ ]* 23.2 Write integration tests for career endpoints
    - Test job scraping trigger
    - Test job matching and ranking
    - Test cover letter generation
    - Test application creation and status updates
    - _Requirements: 15.1-21.7_

- [x] 24. REST API Layer - Module Endpoints
  - [x] 24.1 Implement module-related API endpoints
    - Create `src/api/routes/modules.py` with Flask/FastAPI routes
    - Implement `GET /api/modules` endpoint returning available modules based on rank
    - Implement `GET /api/modules/{name}/dashboard` endpoint returning module-specific dashboard data
    - Add module unlock status in response
    - _Requirements: 14.1-14.8, 26.1-26.7_
  
  - [ ]* 24.2 Write integration tests for module endpoints
    - Test module availability by rank
    - Test module dashboard data retrieval
    - Test locked module access rejection
    - _Requirements: 14.1-14.8, 26.1-26.7_

- [x] 25. REST API Layer - Authentication Endpoints
  - [x] 25.1 Implement authentication API endpoints
    - Create `src/api/routes/auth.py` with Flask/FastAPI routes
    - Implement `POST /api/auth/register` endpoint creating new accounts
    - Implement `POST /api/auth/login` endpoint creating sessions
    - Implement `POST /api/auth/logout` endpoint ending sessions
    - Implement `POST /api/auth/reset-password` endpoint for password reset
    - Add rate limiting for authentication endpoints
    - Add HTTPS enforcement for production
    - _Requirements: Authentication requirements_
  
  - [ ]* 25.2 Write integration tests for authentication endpoints
    - Test user registration with validation
    - Test login with valid and invalid credentials
    - Test session creation and expiration
    - Test account lockout after failed attempts
    - _Requirements: Authentication security_

- [~] 26. Checkpoint - Ensure all API endpoints pass tests
  - Run pytest on all API integration tests
  - Verify authentication and authorization enforcement
  - Test error handling for all endpoints
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 27. Web Interface - Main Dashboard
  - [~] 27.1 Create main dashboard HTML and CSS
    - Create `templates/dashboard.html` with dashboard layout
    - Create `static/css/dashboard.css` with responsive design (Flexbox/Grid)
    - Display player level, rank, HP, MP, XP bar with progress animation
    - Display all six stats (STR, INT, AGI, VIT, SEN, LUK) with visual bars
    - Display available stat points and skill points
    - Display equipped title below player name
    - Display current gold balance prominently
    - _Requirements: 22.1-22.7_
  
  - [~] 27.2 Implement dashboard JavaScript for real-time updates
    - Create `static/js/dashboard.js` with Fetch API calls
    - Implement XP bar dynamic update without page reload
    - Implement stat point allocation via AJAX
    - Implement auto-refresh every 10 seconds for notifications
    - Add loading indicators and error handling
    - _Requirements: 22.1-22.7_

- [ ] 28. Web Interface - Quest Log
  - [~] 28.1 Create quest log HTML and CSS
    - Create `templates/quest_log.html` with quest organization by type
    - Create `static/css/quest_log.css` with color coding (red for overdue)
    - Display separate sections: Daily Quests, Main Quests, Instant Dungeons, Emergency Quests
    - Display quest title, description, XP reward, completion status
    - Display progress bars for Main Quests
    - Display countdown timers for Instant Dungeons and Emergency Quests
    - _Requirements: 23.1-23.7_
  
  - [~] 28.2 Implement quest log JavaScript for interactions
    - Create `static/js/quest_log.js` with quest operations
    - Implement quest expansion to show full details and sub-quests
    - Implement single-click quest completion
    - Implement timer countdown with auto-refresh
    - Add quest completion animations
    - _Requirements: 23.1-23.7_

- [ ] 29. Web Interface - Skill Tree Visualization
  - [~] 29.1 Create skill tree HTML and CSS
    - Create `templates/skill_tree.html` with tree structure layout
    - Create `static/css/skill_tree.css` with locked/unlocked styling (grayscale/color)
    - Display skills in tree structure with prerequisite connections
    - Display available skill points at top
    - _Requirements: 24.1-24.7_
  
  - [~] 29.2 Implement skill tree JavaScript for interactions
    - Create `static/js/skill_tree.js` with skill operations
    - Implement skill hover tooltips showing details and requirements
    - Implement skill point allocation via click
    - Implement immediate UI update after allocation
    - Add skill unlock animations
    - _Requirements: 24.1-24.7_

- [ ] 30. Web Interface - Achievement Gallery
  - [~] 30.1 Create achievement gallery HTML and CSS
    - Create `templates/achievements.html` with grid layout
    - Create `static/css/achievements.css` with icon styling (color/grayscale)
    - Display achievements in grid with icons
    - Display achievement completion percentage
    - _Requirements: 25.1-25.7_
  
  - [~] 30.2 Implement achievement gallery JavaScript for interactions
    - Create `static/js/achievements.js` with achievement operations
    - Implement achievement click to show details and unlock requirements
    - Implement filter by rarity or category
    - Display unlock dates and stat bonuses
    - Add achievement unlock animations
    - _Requirements: 25.1-25.7_

- [ ] 31. Web Interface - Module Dashboards
  - [~] 31.1 Create Career Hunter module dashboard
    - Create `templates/modules/career_hunter.html` with module layout
    - Create `static/css/modules/career_hunter.css` for module styling
    - Display matched jobs with match scores
    - Display application history table (sortable by date, company, status)
    - Display application statistics: total submitted, response rate, interview rate, offer rate
    - Display job scraping trigger button
    - Display cover letter generation interface
    - _Requirements: 26.1-26.7, Career module requirements_
  
  - [~] 31.2 Implement Career Hunter JavaScript for interactions
    - Create `static/js/modules/career_hunter.js` with career operations
    - Implement job scraping trigger via AJAX
    - Implement cover letter generation with review interface
    - Implement application status updates
    - Implement application filtering by status or date range
    - _Requirements: Career module requirements_
  
  - [~] 31.3 Create placeholder module dashboards for other modules
    - Create `templates/modules/skill_trainer.html` with placeholder content and unlock message
    - Create `templates/modules/fitness_hunter.html` with placeholder content and unlock message
    - Create `templates/modules/finance_manager.html` with placeholder content and unlock message
    - Create `templates/modules/social_network.html` with placeholder content and unlock message
    - Create `templates/modules/habit_forge.html` with placeholder content and unlock message
    - Display unlock requirements for locked modules
    - _Requirements: 26.1-26.7_

- [ ] 32. Web Interface - Progress Analytics
  - [~] 32.1 Create analytics dashboard HTML and CSS
    - Create `templates/analytics.html` with chart layout
    - Create `static/css/analytics.css` for chart styling
    - Add time range selector: 7 days, 30 days, 90 days, all time
    - Display key performance indicators: daily quest streak, total quests completed, average XP per day
    - _Requirements: 27.1-27.7_
  
  - [~] 32.2 Implement analytics JavaScript with Chart.js
    - Create `static/js/analytics.js` with Chart.js integration
    - Implement XP gain over time line chart
    - Implement quest completion rates by type bar chart
    - Implement stat distribution radar chart
    - Implement time range change with chart refresh
    - Optimize chart rendering to complete within 3 seconds
    - _Requirements: 27.1-27.7_

- [ ] 33. Web Interface - Navigation and Layout
  - [~] 33.1 Create main layout and navigation
    - Create `templates/base.html` with common layout structure
    - Create `static/css/main.css` with global styles and navigation
    - Implement navigation menu with module links
    - Highlight active module in navigation
    - Add notification badge for unread notifications
    - Implement responsive design for mobile devices
    - _Requirements: 26.1-26.7_
  
  - [~] 33.2 Implement navigation JavaScript
    - Create `static/js/navigation.js` with navigation logic
    - Implement page transitions without full reload (SPA-style)
    - Implement notification polling every 30 seconds
    - Implement notification dropdown with mark as read
    - _Requirements: Notification requirements_

- [ ] 34. Background Jobs and Scheduled Tasks
  - [~] 34.1 Implement scheduled job system
    - Create `src/jobs/scheduler.py` with APScheduler configuration
    - Implement daily quest generation job triggered at midnight
    - Implement job scraping job every 6 hours
    - Implement database backup job daily at 2 AM
    - Implement penalty zone check job at midnight
    - Implement achievement check job on player actions
    - _Requirements: 4.1, 15.6, Backup requirements_
  
  - [ ]* 34.2 Write unit tests for scheduled jobs
    - Test daily quest generation timing
    - Test job scraping interval enforcement
    - Test database backup creation
    - _Requirements: Scheduled job correctness_

- [ ] 35. Configuration Management
  - [~] 35.1 Implement configuration system
    - Create `src/config/config.py` with Configuration class
    - Implement `load_config(file_path)` method parsing JSON/YAML config files
    - Implement `save_config(config, file_path)` method writing config to file
    - Define configuration schema: database_path, ollama_host, session_timeout, max_daily_quests, etc.
    - Add environment variable support for sensitive values
    - _Requirements: Configuration requirements_
  
  - [ ]* 35.2 Write property test for configuration parse-print round-trip
    - **Property 22: Configuration Parse-Print Round-Trip**
    - **Validates: Configuration requirements**
    - Use Hypothesis to generate configuration objects
    - Verify parse(print(C)) produces configuration equivalent to C
    - _Requirements: Configuration round-trip_

- [ ] 36. Data Export and Import
  - [~] 36.1 Implement data export and import functionality
    - Create `src/utils/data_export.py` with export functions
    - Implement `export_player_data(player_id, file_path)` method exporting to JSON
    - Implement `import_player_data(file_path)` method importing from JSON
    - Support exporting: player stats, quests, skills, achievements, titles, inventory, applications
    - Add data validation on import
    - _Requirements: Export/import requirements_
  
  - [ ]* 36.2 Write property test for player data export-import round-trip
    - **Property 23: Player Data Export-Import Round-Trip**
    - **Validates: Export/import requirements**
    - Use Hypothesis to generate player data objects
    - Verify import(export(P)) produces player data equivalent to P
    - _Requirements: Export/import round-trip_

- [ ] 37. Logging and Monitoring
  - [~] 37.1 Implement logging and performance monitoring
    - Create `src/utils/logger.py` with logging configuration
    - Implement application logging: info, warning, error levels
    - Implement performance logging for API endpoints
    - Implement database query logging
    - Implement external service call logging (Ollama, MCP)
    - Configure log rotation and retention (7 days)
    - _Requirements: Monitoring requirements_
  
  - [ ]* 37.2 Write unit tests for logging
    - Test log level filtering
    - Test log rotation
    - Test performance metric capture
    - _Requirements: Logging correctness_

- [ ] 38. Error Handling and Recovery
  - [~] 38.1 Implement centralized error handling
    - Create `src/utils/error_handler.py` with error handling utilities
    - Implement error response formatters for API (JSON with error codes)
    - Implement retry logic wrapper for transient failures
    - Implement database transaction rollback on errors
    - Implement graceful degradation for external service failures (fallback behavior)
    - Add user-friendly error messages (no internal details exposed)
    - _Requirements: Error handling requirements_
  
  - [ ]* 38.2 Write unit tests for error handling
    - Test retry logic with various failure scenarios
    - Test transaction rollback
    - Test fallback behavior for service unavailability
    - _Requirements: Error handling correctness_

- [ ] 39. Security Hardening
  - [~] 39.1 Implement security measures
    - Implement SQL injection prevention (parameterized queries only)
    - Implement XSS prevention (output escaping in templates)
    - Implement CSRF protection for POST endpoints
    - Implement rate limiting for all API endpoints (100 req/min per user)
    - Implement HTTPS enforcement in production
    - Implement secure session management (HTTPOnly, Secure, SameSite cookies)
    - Add security headers: Content-Security-Policy, X-Frame-Options, X-Content-Type-Options
    - _Requirements: Security requirements_
  
  - [ ]* 39.2 Write security tests
    - Test SQL injection prevention
    - Test XSS prevention
    - Test CSRF token validation
    - Test rate limiting enforcement
    - _Requirements: Security correctness_

- [ ] 40. Documentation and Deployment
  - [~] 40.1 Create comprehensive documentation
    - Create `docs/INSTALLATION.md` with setup instructions
    - Create `docs/API_REFERENCE.md` with all API endpoints documented
    - Create `docs/DATABASE_SCHEMA.md` with ER diagram and table descriptions
    - Create `docs/CONFIGURATION.md` with configuration options
    - Create `docs/ARCHITECTURE.md` with system architecture overview
    - Update `README.md` with quick start guide
    - _Requirements: Documentation requirements_
  
  - [~] 40.2 Create deployment scripts and configuration
    - Create `deploy/docker-compose.yml` for containerized deployment
    - Create `deploy/nginx.conf` for reverse proxy configuration
    - Create `deploy/systemd/lifehunter.service` for Linux service
    - Create `scripts/setup_database.sh` for database initialization
    - Create `scripts/backup_database.sh` for manual backups
    - _Requirements: Deployment requirements_

- [ ] 41. Final Integration and Testing
  - [~] 41.1 Run comprehensive test suite
    - Run all property-based tests with Hypothesis
    - Run all unit tests with pytest
    - Run all integration tests
    - Generate test coverage report (target: >80%)
    - Fix any failing tests
    - _Requirements: All requirements_
  
  - [~] 41.2 Perform end-to-end testing
    - Test complete user journey: registration → quest completion → level up → module unlock → career module usage
    - Test all API endpoints with Postman/curl
    - Test web interface in multiple browsers (Chrome, Firefox, Edge)
    - Test mobile responsiveness
    - Test error scenarios and recovery
    - _Requirements: All requirements_
  
  - [~] 41.3 Performance testing and optimization
    - Load test API endpoints with Apache Bench or Locust (target: 100 concurrent users)
    - Optimize slow database queries (add indexes where needed)
    - Optimize frontend bundle size (minify JS/CSS)
    - Test page load times (target: <2s for dashboard)
    - _Requirements: Performance requirements_

- [~] 42. Final Checkpoint - Complete System Validation
  - Ensure all 24 property-based tests pass
  - Ensure all unit and integration tests pass
  - Verify all modules unlock correctly at rank thresholds
  - Verify all external service integrations work (Ollama, MCP SQLite, MCP Fetch)
  - Verify web interface loads and updates correctly
  - Verify authentication and security measures are enforced
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing sub-tasks and can be skipped for faster MVP
- Each implementation task references specific requirements for traceability
- Property-based tests validate 24 universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests validate external service interactions
- Checkpoints ensure incremental validation at major milestones
- The task list focuses exclusively on implementation and testing tasks performable by a coding agent
- Modules beyond Career Hunter are implemented as placeholders (Skill Trainer, Fitness Hunter, Finance Manager, Social Network, Habit Forge) for future expansion
- The implementation follows a bottom-up approach: database → integration → application → module → presentation
- All code follows Python best practices: type hints, docstrings, PEP 8 style guide
- Security is enforced at every layer: input validation, parameterized queries, authentication, rate limiting, HTTPS

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2.1", "2.2", "2.3"] },
    { "id": 1, "tasks": ["2.4", "3.1", "4.1", "5.1"] },
    { "id": 2, "tasks": ["3.2", "4.2", "5.2", "5.3", "6.1"] },
    { "id": 3, "tasks": ["6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "7.1"] },
    { "id": 4, "tasks": ["7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8", "7.9", "8.1"] },
    { "id": 5, "tasks": ["8.2", "8.3", "8.4", "9.1", "10.1", "11.1", "12.1", "13.1"] },
    { "id": 6, "tasks": ["9.2", "9.3", "9.4", "10.2", "10.3", "11.2", "11.3", "12.2", "13.2", "13.3"] },
    { "id": 7, "tasks": ["15.1", "16.1", "17.1", "18.1", "19.1", "20.1"] },
    { "id": 8, "tasks": ["15.2", "15.3", "15.4", "21.1"] },
    { "id": 9, "tasks": ["21.2", "22.1", "23.1", "24.1", "25.1"] },
    { "id": 10, "tasks": ["22.2", "23.2", "24.2", "25.2", "27.1"] },
    { "id": 11, "tasks": ["27.2", "28.1", "29.1", "30.1", "31.1"] },
    { "id": 12, "tasks": ["28.2", "29.2", "30.2", "31.2", "31.3", "32.1", "33.1"] },
    { "id": 13, "tasks": ["32.2", "33.2", "34.1", "35.1", "36.1", "37.1", "38.1", "39.1"] },
    { "id": 14, "tasks": ["34.2", "35.2", "36.2", "37.2", "38.2", "39.2", "40.1"] },
    { "id": 15, "tasks": ["40.2", "41.1", "41.2", "41.3"] }
  ]
}
```
