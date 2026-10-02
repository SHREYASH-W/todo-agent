"""
Unit tests for database initialization script.

Tests the database initialization functions including:
- Connection validation
- Table creation
- Seed data functions
- Complete initialization workflow
"""

import pytest
from sqlalchemy import inspect

from src.db.init_db import (
    validate_connection,
    create_all_tables,
    seed_skills,
    seed_achievements,
    seed_titles,
    seed_initial_data,
    initialize_database,
)
from src.models import (
    engine,
    SessionLocal,
    Skill,
    Achievement,
    Title,
    Player,
    Quest,
)


class TestDatabaseConnection:
    """Test database connection validation."""
    
    def test_validate_connection_success(self):
        """Test that database connection validation succeeds."""
        result = validate_connection()
        assert result is True, "Database connection should be valid"


class TestTableCreation:
    """Test database table creation."""
    
    def test_create_all_tables_success(self):
        """Test that all tables are created successfully."""
        result = create_all_tables()
        assert result is True, "Table creation should succeed"
    
    def test_all_tables_exist(self):
        """Test that all required tables exist in the database."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            'players',
            'quests',
            'skills',
            'player_skills',
            'achievements',
            'player_achievements',
            'titles',
            'player_titles',
            'inventory_items',
            'notifications',
            'jobs',
            'job_matches',
            'applications',
            'performance_logs',
            'database_backups',
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table '{table}' should exist in database"
    
    def test_table_creation_idempotent(self):
        """Test that creating tables multiple times is safe."""
        result1 = create_all_tables()
        result2 = create_all_tables()
        assert result1 is True and result2 is True, "Multiple table creations should succeed"


class TestSeedSkills:
    """Test skills seeding functionality."""
    
    def test_seed_skills_success(self):
        """Test that skills are seeded successfully."""
        result = seed_skills()
        assert result is True, "Skills seeding should succeed"
    
    def test_skills_count(self):
        """Test that the correct number of skills are seeded."""
        db = SessionLocal()
        try:
            count = db.query(Skill).count()
            assert count == 17, f"Expected 17 skills, found {count}"
        finally:
            db.close()
    
    def test_skill_types(self):
        """Test that skills have correct types (active/passive)."""
        db = SessionLocal()
        try:
            skills = db.query(Skill).all()
            for skill in skills:
                assert skill.skill_type in ['active', 'passive'], \
                    f"Skill '{skill.name}' has invalid type: {skill.skill_type}"
        finally:
            db.close()
    
    def test_skill_level_requirements(self):
        """Test that skills have valid unlock level requirements."""
        db = SessionLocal()
        try:
            skills = db.query(Skill).all()
            for skill in skills:
                assert 1 <= skill.unlock_level <= 100, \
                    f"Skill '{skill.name}' has invalid unlock level: {skill.unlock_level}"
        finally:
            db.close()
    
    def test_seed_skills_idempotent(self):
        """Test that seeding skills multiple times doesn't create duplicates."""
        db = SessionLocal()
        try:
            count_before = db.query(Skill).count()
            seed_skills()
            count_after = db.query(Skill).count()
            assert count_before == count_after, "Duplicate seeding should not add more skills"
        finally:
            db.close()


class TestSeedAchievements:
    """Test achievements seeding functionality."""
    
    def test_seed_achievements_success(self):
        """Test that achievements are seeded successfully."""
        result = seed_achievements()
        assert result is True, "Achievements seeding should succeed"
    
    def test_achievements_count(self):
        """Test that the correct number of achievements are seeded."""
        db = SessionLocal()
        try:
            count = db.query(Achievement).count()
            assert count == 17, f"Expected 17 achievements, found {count}"
        finally:
            db.close()
    
    def test_achievement_rarities(self):
        """Test that achievements have valid rarity values."""
        db = SessionLocal()
        try:
            achievements = db.query(Achievement).all()
            valid_rarities = ['common', 'rare', 'epic', 'legendary']
            for achievement in achievements:
                assert achievement.rarity in valid_rarities, \
                    f"Achievement '{achievement.name}' has invalid rarity: {achievement.rarity}"
        finally:
            db.close()
    
    def test_achievement_rarity_distribution(self):
        """Test that achievements have appropriate rarity distribution."""
        db = SessionLocal()
        try:
            common_count = db.query(Achievement).filter_by(rarity='common').count()
            rare_count = db.query(Achievement).filter_by(rarity='rare').count()
            epic_count = db.query(Achievement).filter_by(rarity='epic').count()
            legendary_count = db.query(Achievement).filter_by(rarity='legendary').count()
            
            assert common_count > 0, "Should have at least one common achievement"
            assert rare_count > 0, "Should have at least one rare achievement"
            assert epic_count > 0, "Should have at least one epic achievement"
            assert legendary_count > 0, "Should have at least one legendary achievement"
        finally:
            db.close()
    
    def test_seed_achievements_idempotent(self):
        """Test that seeding achievements multiple times doesn't create duplicates."""
        db = SessionLocal()
        try:
            count_before = db.query(Achievement).count()
            seed_achievements()
            count_after = db.query(Achievement).count()
            assert count_before == count_after, "Duplicate seeding should not add more achievements"
        finally:
            db.close()


class TestSeedTitles:
    """Test titles seeding functionality."""
    
    def test_seed_titles_success(self):
        """Test that titles are seeded successfully."""
        result = seed_titles()
        assert result is True, "Titles seeding should succeed"
    
    def test_titles_count(self):
        """Test that the correct number of titles are seeded."""
        db = SessionLocal()
        try:
            count = db.query(Title).count()
            assert count == 16, f"Expected 16 titles, found {count}"
        finally:
            db.close()
    
    def test_titles_have_bonuses(self):
        """Test that all titles have stat bonuses defined."""
        db = SessionLocal()
        try:
            titles = db.query(Title).all()
            for title in titles:
                assert title.stat_bonuses is not None, \
                    f"Title '{title.name}' should have stat bonuses"
                assert len(title.stat_bonuses) > 0, \
                    f"Title '{title.name}' should have non-empty stat bonuses"
        finally:
            db.close()
    
    def test_rank_titles_exist(self):
        """Test that titles exist for each rank."""
        db = SessionLocal()
        try:
            rank_titles = [
                'D-Rank Hunter',
                'C-Rank Hunter',
                'B-Rank Hunter',
                'A-Rank Hunter',
                'S-Rank Hunter',
                'National Level Hunter'
            ]
            
            for rank_title_name in rank_titles:
                title = db.query(Title).filter_by(name=rank_title_name).first()
                assert title is not None, f"Rank title '{rank_title_name}' should exist"
        finally:
            db.close()
    
    def test_seed_titles_idempotent(self):
        """Test that seeding titles multiple times doesn't create duplicates."""
        db = SessionLocal()
        try:
            count_before = db.query(Title).count()
            seed_titles()
            count_after = db.query(Title).count()
            assert count_before == count_after, "Duplicate seeding should not add more titles"
        finally:
            db.close()


class TestSeedInitialData:
    """Test complete initial data seeding."""
    
    def test_seed_initial_data_success(self):
        """Test that all initial data is seeded successfully."""
        result = seed_initial_data()
        assert result is True, "Initial data seeding should succeed"
    
    def test_all_data_seeded(self):
        """Test that all data types are seeded."""
        db = SessionLocal()
        try:
            skills_count = db.query(Skill).count()
            achievements_count = db.query(Achievement).count()
            titles_count = db.query(Title).count()
            
            assert skills_count > 0, "Skills should be seeded"
            assert achievements_count > 0, "Achievements should be seeded"
            assert titles_count > 0, "Titles should be seeded"
        finally:
            db.close()


class TestInitializeDatabase:
    """Test complete database initialization workflow."""
    
    def test_initialize_database_success(self):
        """Test that complete database initialization succeeds."""
        result = initialize_database()
        assert result is True, "Database initialization should succeed"
    
    def test_database_ready_for_use(self):
        """Test that database is ready for use after initialization."""
        # Initialize database
        initialize_database()
        
        # Verify we can interact with all tables
        db = SessionLocal()
        try:
            # Test reading from seeded tables
            skills = db.query(Skill).first()
            achievements = db.query(Achievement).first()
            titles = db.query(Title).first()
            
            assert skills is not None, "Should be able to query skills"
            assert achievements is not None, "Should be able to query achievements"
            assert titles is not None, "Should be able to query titles"
            
            # Test we can query empty tables
            players_count = db.query(Player).count()
            quests_count = db.query(Quest).count()
            
            assert players_count >= 0, "Should be able to query players table"
            assert quests_count >= 0, "Should be able to query quests table"
        finally:
            db.close()


class TestDataIntegrity:
    """Test data integrity and relationships."""
    
    def test_skills_unique_names(self):
        """Test that all skills have unique names."""
        db = SessionLocal()
        try:
            skills = db.query(Skill).all()
            names = [skill.name for skill in skills]
            assert len(names) == len(set(names)), "All skill names should be unique"
        finally:
            db.close()
    
    def test_achievements_unique_names(self):
        """Test that all achievements have unique names."""
        db = SessionLocal()
        try:
            achievements = db.query(Achievement).all()
            names = [achievement.name for achievement in achievements]
            assert len(names) == len(set(names)), "All achievement names should be unique"
        finally:
            db.close()
    
    def test_titles_unique_names(self):
        """Test that all titles have unique names."""
        db = SessionLocal()
        try:
            titles = db.query(Title).all()
            names = [title.name for title in titles]
            assert len(names) == len(set(names)), "All title names should be unique"
        finally:
            db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
