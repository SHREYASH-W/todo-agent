"""
Integration tests for Database Manager with actual models

Tests Database Manager working with the LifeHunter system models
to ensure compatibility and correctness.
"""

import os
import tempfile
import pytest
from src.services.database_manager import DatabaseManager


@pytest.fixture
def integration_db():
    """Create a temporary database with LifeHunter schema."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create database with basic schema
    db_manager = DatabaseManager(path)
    
    # Create players table
    db_manager.execute_query("""
        CREATE TABLE players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            rank TEXT DEFAULT 'E',
            gold INTEGER DEFAULT 0,
            str_stat INTEGER DEFAULT 10,
            int_stat INTEGER DEFAULT 10,
            agi_stat INTEGER DEFAULT 10,
            vit_stat INTEGER DEFAULT 10,
            sen_stat INTEGER DEFAULT 10,
            luk_stat INTEGER DEFAULT 10,
            hp INTEGER DEFAULT 200,
            mp INTEGER DEFAULT 100,
            stat_points INTEGER DEFAULT 0,
            skill_points INTEGER DEFAULT 0,
            active_title_id INTEGER
        )
    """)
    
    # Create quests table
    db_manager.execute_query("""
        CREATE TABLE quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            quest_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            xp_reward INTEGER DEFAULT 0,
            gold_reward INTEGER DEFAULT 0,
            difficulty TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deadline TIMESTAMP,
            completed_at TIMESTAMP,
            parent_quest_id INTEGER,
            FOREIGN KEY (player_id) REFERENCES players(id)
        )
    """)
    
    # Create database_backups table
    db_manager.execute_query("""
        CREATE TABLE database_backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db_manager.close()
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def db_manager(integration_db):
    """Create DatabaseManager instance with integration database."""
    manager = DatabaseManager(integration_db)
    yield manager
    manager.close()


class TestPlayerOperations:
    """Test database operations for player management."""
    
    def test_create_player(self, db_manager):
        """Test creating a new player."""
        result = db_manager.execute_query("""
            INSERT INTO players (username, email, password_hash)
            VALUES (?, ?, ?)
        """, ("testuser", "test@example.com", "hashed_password"))
        
        assert result[0]["affected_rows"] == 1
        player_id = result[0]["lastrowid"]
        assert player_id > 0
    
    def test_update_player_stats(self, db_manager):
        """Test updating player stats."""
        # Create player
        result = db_manager.execute_query("""
            INSERT INTO players (username, email, password_hash)
            VALUES (?, ?, ?)
        """, ("player1", "player1@example.com", "hash"))
        player_id = result[0]["lastrowid"]
        
        # Update stats
        db_manager.execute_query("""
            UPDATE players SET xp = ?, level = ?, gold = ?
            WHERE id = ?
        """, (150, 2, 100, player_id))
        
        # Verify update
        player = db_manager.execute_query(
            "SELECT xp, level, gold FROM players WHERE id = ?",
            (player_id,)
        )
        
        assert player[0]["xp"] == 150
        assert player[0]["level"] == 2
        assert player[0]["gold"] == 100
    
    def test_allocate_stat_points(self, db_manager):
        """Test stat point allocation transaction."""
        # Create player with stat points
        result = db_manager.execute_query("""
            INSERT INTO players (username, email, password_hash, stat_points, str_stat)
            VALUES (?, ?, ?, ?, ?)
        """, ("player2", "player2@example.com", "hash", 5, 10))
        player_id = result[0]["lastrowid"]
        
        # Allocate 3 points to STR
        queries = [
            ("UPDATE players SET stat_points = stat_points - 3 WHERE id = ?", (player_id,)),
            ("UPDATE players SET str_stat = str_stat + 3 WHERE id = ?", (player_id,))
        ]
        
        success = db_manager.execute_transaction(queries)
        assert success is True
        
        # Verify allocation
        player = db_manager.execute_query(
            "SELECT stat_points, str_stat FROM players WHERE id = ?",
            (player_id,)
        )
        
        assert player[0]["stat_points"] == 2
        assert player[0]["str_stat"] == 13


class TestQuestOperations:
    """Test database operations for quest management."""
    
    def test_create_quest(self, db_manager):
        """Test creating a quest."""
        # Create player first
        result = db_manager.execute_query("""
            INSERT INTO players (username, email, password_hash)
            VALUES (?, ?, ?)
        """, ("questplayer", "quest@example.com", "hash"))
        player_id = result[0]["lastrowid"]
        
        # Create quest
        result = db_manager.execute_query("""
            INSERT INTO quests (player_id, quest_type, title, description, xp_reward)
            VALUES (?, ?, ?, ?, ?)
        """, (player_id, "daily", "Complete morning routine", "Wake up at 6 AM and exercise", 50))
        
        assert result[0]["affected_rows"] == 1
        quest_id = result[0]["lastrowid"]
        assert quest_id > 0
    
    def test_complete_quest_transaction(self, db_manager):
        """Test quest completion with XP award transaction."""
        # Create player
        result = db_manager.execute_query("""
            INSERT INTO players (username, email, password_hash, xp)
            VALUES (?, ?, ?, ?)
        """, ("questplayer2", "quest2@example.com", "hash", 100))
        player_id = result[0]["lastrowid"]
        
        # Create quest
        result = db_manager.execute_query("""
            INSERT INTO quests (player_id, quest_type, title, xp_reward, status)
            VALUES (?, ?, ?, ?, ?)
        """, (player_id, "daily", "Test Quest", 75, "active"))
        quest_id = result[0]["lastrowid"]
        
        # Complete quest: update quest status and award XP
        queries = [
            ("UPDATE quests SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?", ("completed", quest_id)),
            ("UPDATE players SET xp = xp + ? WHERE id = ?", (75, player_id))
        ]
        
        success = db_manager.execute_transaction(queries)
        assert success is True
        
        # Verify quest completion
        quest = db_manager.execute_query(
            "SELECT status, completed_at FROM quests WHERE id = ?",
            (quest_id,)
        )
        assert quest[0]["status"] == "completed"
        assert quest[0]["completed_at"] is not None
        
        # Verify XP award
        player = db_manager.execute_query(
            "SELECT xp FROM players WHERE id = ?",
            (player_id,)
        )
        assert player[0]["xp"] == 175


class TestBackupIntegration:
    """Test backup functionality with real data."""
    
    def test_backup_with_player_data(self, db_manager, integration_db):
        """Test database backup with player data."""
        # Insert test data
        db_manager.execute_query("""
            INSERT INTO players (username, email, password_hash, level, xp)
            VALUES (?, ?, ?, ?, ?)
        """, ("backupuser", "backup@example.com", "hash", 5, 500))
        
        # Create backup
        backup_path = integration_db + ".backup"
        
        try:
            success = db_manager.backup_database(backup_path)
            assert success is True
            
            # Verify backup contains data
            backup_manager = DatabaseManager(backup_path)
            players = backup_manager.execute_query(
                "SELECT * FROM players WHERE username = ?",
                ("backupuser",)
            )
            backup_manager.close()
            
            assert len(players) == 1
            assert players[0]["level"] == 5
            assert players[0]["xp"] == 500
        finally:
            if os.path.exists(backup_path):
                os.remove(backup_path)


class TestTransactionRollback:
    """Test transaction rollback scenarios."""
    
    def test_rollback_on_constraint_violation(self, db_manager):
        """Test rollback when unique constraint is violated."""
        # Create first player
        db_manager.execute_query("""
            INSERT INTO players (username, email, password_hash)
            VALUES (?, ?, ?)
        """, ("duplicate", "dup@example.com", "hash"))
        
        # Try to create second player with same username (should fail)
        queries = [
            ("INSERT INTO players (username, email, password_hash) VALUES (?, ?, ?)", 
             ("newuser", "new@example.com", "hash")),
            ("INSERT INTO players (username, email, password_hash) VALUES (?, ?, ?)", 
             ("duplicate", "another@example.com", "hash"))  # Duplicate username
        ]
        
        success = db_manager.execute_transaction(queries)
        assert success is False
        
        # Verify first insert was rolled back
        players = db_manager.execute_query(
            "SELECT * FROM players WHERE username = ?",
            ("newuser",)
        )
        assert len(players) == 0
    
    def test_rollback_preserves_original_data(self, db_manager):
        """Test that rollback preserves data before transaction."""
        # Create player
        result = db_manager.execute_query("""
            INSERT INTO players (username, email, password_hash, xp)
            VALUES (?, ?, ?, ?)
        """, ("rollbacktest", "rollback@example.com", "hash", 100))
        player_id = result[0]["lastrowid"]
        
        # Try transaction that will fail
        queries = [
            ("UPDATE players SET xp = xp + ? WHERE id = ?", (50, player_id)),
            ("INSERT INTO players (username, email, password_hash) VALUES (?, ?, ?)",
             ("rollbacktest", "dup@example.com", "hash"))  # Duplicate
        ]
        
        success = db_manager.execute_transaction(queries)
        assert success is False
        
        # Verify XP wasn't updated
        player = db_manager.execute_query(
            "SELECT xp FROM players WHERE id = ?",
            (player_id,)
        )
        assert player[0]["xp"] == 100  # Original value preserved


class TestConnectionPooling:
    """Test connection pooling with concurrent operations."""
    
    def test_multiple_concurrent_queries(self, db_manager):
        """Test multiple queries use connection pool efficiently."""
        # Create test players
        for i in range(5):
            db_manager.execute_query("""
                INSERT INTO players (username, email, password_hash)
                VALUES (?, ?, ?)
            """, (f"user{i}", f"user{i}@example.com", "hash"))
        
        # Execute multiple queries
        for i in range(5):
            players = db_manager.execute_query(
                "SELECT * FROM players WHERE username = ?",
                (f"user{i}",)
            )
            assert len(players) == 1
            assert players[0]["username"] == f"user{i}"
