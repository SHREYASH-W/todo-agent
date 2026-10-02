"""
Unit tests for Database Manager

Tests cover:
- Query execution with parameterized queries
- Transaction rollback on errors
- Connection pool exhaustion handling
- Backup creation and verification
- Query validation for security
"""

import os
import sqlite3
import tempfile
import pytest
from src.services.database_manager import DatabaseManager, ConnectionPool


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create a simple test table
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE test_players (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            xp INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE test_logs (
            id INTEGER PRIMARY KEY,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def db_manager(temp_db):
    """Create DatabaseManager instance with temp database."""
    manager = DatabaseManager(temp_db)
    yield manager
    manager.close()


class TestQueryExecution:
    """Test query execution functionality."""
    
    def test_execute_select_query(self, db_manager):
        """Test SELECT query execution."""
        # Insert test data
        db_manager.execute_query(
            "INSERT INTO test_players (name, xp) VALUES (?, ?)",
            ("TestPlayer", 100)
        )
        
        # Query data
        results = db_manager.execute_query(
            "SELECT * FROM test_players WHERE name = ?",
            ("TestPlayer",)
        )
        
        assert len(results) == 1
        assert results[0]["name"] == "TestPlayer"
        assert results[0]["xp"] == 100
    
    def test_execute_insert_query(self, db_manager):
        """Test INSERT query execution."""
        result = db_manager.execute_query(
            "INSERT INTO test_players (name, xp) VALUES (?, ?)",
            ("Player1", 50)
        )
        
        assert result[0]["affected_rows"] == 1
        assert result[0]["lastrowid"] > 0
    
    def test_execute_update_query(self, db_manager):
        """Test UPDATE query execution."""
        # Insert test data
        db_manager.execute_query(
            "INSERT INTO test_players (name, xp) VALUES (?, ?)",
            ("Player2", 100)
        )
        
        # Update data
        result = db_manager.execute_query(
            "UPDATE test_players SET xp = ? WHERE name = ?",
            (200, "Player2")
        )
        
        assert result[0]["affected_rows"] == 1
        
        # Verify update
        results = db_manager.execute_query(
            "SELECT xp FROM test_players WHERE name = ?",
            ("Player2",)
        )
        assert results[0]["xp"] == 200
    
    def test_execute_delete_query(self, db_manager):
        """Test DELETE query execution."""
        # Insert test data
        db_manager.execute_query(
            "INSERT INTO test_players (name, xp) VALUES (?, ?)",
            ("Player3", 75)
        )
        
        # Delete data
        result = db_manager.execute_query(
            "DELETE FROM test_players WHERE name = ?",
            ("Player3",)
        )
        
        assert result[0]["affected_rows"] == 1
        
        # Verify deletion
        results = db_manager.execute_query(
            "SELECT * FROM test_players WHERE name = ?",
            ("Player3",)
        )
        assert len(results) == 0
    
    def test_execute_query_with_no_params(self, db_manager):
        """Test query execution without parameters."""
        results = db_manager.execute_query("SELECT * FROM test_players")
        assert isinstance(results, list)
    
    def test_execute_query_with_empty_result(self, db_manager):
        """Test query that returns no results."""
        results = db_manager.execute_query(
            "SELECT * FROM test_players WHERE name = ?",
            ("NonExistent",)
        )
        assert len(results) == 0


class TestTransactionManagement:
    """Test transaction functionality."""
    
    def test_successful_transaction(self, db_manager):
        """Test successful transaction with multiple queries."""
        queries = [
            ("INSERT INTO test_players (name, xp) VALUES (?, ?)", ("Player1", 100)),
            ("INSERT INTO test_players (name, xp) VALUES (?, ?)", ("Player2", 200)),
            ("INSERT INTO test_logs (message) VALUES (?)", ("Transaction test",))
        ]
        
        success = db_manager.execute_transaction(queries)
        assert success is True
        
        # Verify all queries executed
        players = db_manager.execute_query("SELECT * FROM test_players")
        assert len(players) == 2
        
        logs = db_manager.execute_query("SELECT * FROM test_logs")
        assert len(logs) == 1
    
    def test_transaction_rollback_on_error(self, db_manager):
        """Test transaction rollback when a query fails."""
        # First query succeeds, second fails due to constraint
        queries = [
            ("INSERT INTO test_players (name, xp) VALUES (?, ?)", ("Player1", 100)),
            ("INSERT INTO test_players (id, name, xp) VALUES (?, ?, ?)", (1, "Player2", 200)),  # Duplicate ID
        ]
        
        success = db_manager.execute_transaction(queries)
        assert success is False
        
        # Verify rollback - no players should be inserted
        players = db_manager.execute_query("SELECT * FROM test_players")
        assert len(players) == 0
    
    def test_empty_transaction(self, db_manager):
        """Test transaction with empty query list."""
        success = db_manager.execute_transaction([])
        assert success is True
    
    def test_transaction_with_update_and_insert(self, db_manager):
        """Test transaction combining UPDATE and INSERT."""
        # Insert initial data
        db_manager.execute_query(
            "INSERT INTO test_players (name, xp) VALUES (?, ?)",
            ("Player1", 100)
        )
        
        # Transaction: update existing and insert new
        queries = [
            ("UPDATE test_players SET xp = xp + ? WHERE name = ?", (50, "Player1")),
            ("INSERT INTO test_logs (message) VALUES (?)", ("XP awarded",))
        ]
        
        success = db_manager.execute_transaction(queries)
        assert success is True
        
        # Verify results
        player = db_manager.execute_query(
            "SELECT xp FROM test_players WHERE name = ?",
            ("Player1",)
        )
        assert player[0]["xp"] == 150


class TestQueryValidation:
    """Test query validation for security."""
    
    def test_valid_select_query(self, db_manager):
        """Test validation of safe SELECT query."""
        assert db_manager.validate_query("SELECT * FROM test_players WHERE id = ?")
    
    def test_valid_insert_query(self, db_manager):
        """Test validation of safe INSERT query."""
        assert db_manager.validate_query("INSERT INTO test_players (name, xp) VALUES (?, ?)")
    
    def test_valid_update_query(self, db_manager):
        """Test validation of safe UPDATE query."""
        assert db_manager.validate_query("UPDATE test_players SET xp = ? WHERE id = ?")
    
    def test_invalid_drop_query(self, db_manager):
        """Test rejection of DROP query."""
        assert not db_manager.validate_query("SELECT * FROM players; DROP TABLE players")
    
    def test_invalid_delete_injection(self, db_manager):
        """Test rejection of DELETE injection."""
        assert not db_manager.validate_query("SELECT * FROM players; DELETE FROM players")
    
    def test_invalid_sql_injection_pattern(self, db_manager):
        """Test rejection of common SQL injection patterns."""
        assert not db_manager.validate_query("SELECT * FROM players WHERE name = '' OR '1'='1'")
        assert not db_manager.validate_query("SELECT * FROM players WHERE id = 1 OR 1=1")
    
    def test_invalid_comment_injection(self, db_manager):
        """Test rejection of comment-based injection."""
        assert not db_manager.validate_query("SELECT * FROM players WHERE id = 1 -- comment")
    
    def test_empty_query(self, db_manager):
        """Test rejection of empty query."""
        assert not db_manager.validate_query("")
        assert not db_manager.validate_query("   ")


class TestConnectionPool:
    """Test connection pool functionality."""
    
    def test_get_and_return_connection(self, temp_db):
        """Test getting and returning connection to pool."""
        pool = ConnectionPool(temp_db, max_connections=2)
        
        conn = pool.get_connection()
        assert conn is not None
        
        pool.return_connection(conn)
        pool.close_all()
    
    def test_connection_pool_reuse(self, temp_db):
        """Test connection reuse from pool."""
        pool = ConnectionPool(temp_db, max_connections=2)
        
        conn1 = pool.get_connection()
        pool.return_connection(conn1)
        
        conn2 = pool.get_connection()
        # Should reuse the same connection
        assert conn2 is conn1
        
        pool.return_connection(conn2)
        pool.close_all()
    
    def test_connection_pool_exhaustion(self, temp_db):
        """Test behavior when connection pool is exhausted."""
        pool = ConnectionPool(temp_db, max_connections=2, timeout=1)
        
        conn1 = pool.get_connection()
        conn2 = pool.get_connection()
        
        # Pool is exhausted, should timeout
        with pytest.raises(TimeoutError):
            pool.get_connection()
        
        pool.return_connection(conn1)
        pool.return_connection(conn2)
        pool.close_all()
    
    def test_stale_connection_replacement(self, temp_db):
        """Test replacement of stale connections."""
        pool = ConnectionPool(temp_db, max_connections=2)
        
        conn = pool.get_connection()
        # Simulate stale connection by closing it
        conn.close()
        
        pool.return_connection(conn)
        
        # Getting connection should create a new one
        new_conn = pool.get_connection()
        assert new_conn is not conn
        
        pool.return_connection(new_conn)
        pool.close_all()


class TestDatabaseBackup:
    """Test database backup functionality."""
    
    def test_backup_with_custom_path(self, db_manager, temp_db):
        """Test backup creation with custom path."""
        backup_path = temp_db + ".backup"
        
        try:
            success = db_manager.backup_database(backup_path)
            assert success is True
            assert os.path.exists(backup_path)
            
            # Verify backup is a valid database
            backup_conn = sqlite3.connect(backup_path)
            cursor = backup_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            backup_conn.close()
            
            assert len(tables) > 0
        finally:
            if os.path.exists(backup_path):
                os.remove(backup_path)
    
    def test_backup_with_auto_generated_name(self, db_manager):
        """Test backup creation with auto-generated filename."""
        success = db_manager.backup_database()
        assert success is True
        
        # Find and cleanup backup file
        for file in os.listdir('.'):
            if file.startswith('database_backup_') and file.endswith('.db'):
                os.remove(file)
                break
    
    def test_backup_creates_directory(self, db_manager, temp_db):
        """Test backup creates directory if it doesn't exist."""
        backup_dir = tempfile.mkdtemp()
        backup_path = os.path.join(backup_dir, "subdir", "backup.db")
        
        try:
            success = db_manager.backup_database(backup_path)
            assert success is True
            assert os.path.exists(backup_path)
        finally:
            if os.path.exists(backup_path):
                os.remove(backup_path)
            if os.path.exists(os.path.dirname(backup_path)):
                os.rmdir(os.path.dirname(backup_path))
            if os.path.exists(backup_dir):
                os.rmdir(backup_dir)
    
    def test_backup_with_data(self, db_manager):
        """Test backup preserves data."""
        # Insert test data
        db_manager.execute_query(
            "INSERT INTO test_players (name, xp) VALUES (?, ?)",
            ("BackupTest", 999)
        )
        
        backup_path = "test_backup.db"
        
        try:
            success = db_manager.backup_database(backup_path)
            assert success is True
            
            # Verify data in backup
            backup_conn = sqlite3.connect(backup_path)
            cursor = backup_conn.cursor()
            cursor.execute("SELECT * FROM test_players WHERE name = ?", ("BackupTest",))
            row = cursor.fetchone()
            backup_conn.close()
            
            assert row is not None
            assert row[1] == "BackupTest"
            assert row[2] == 999
        finally:
            if os.path.exists(backup_path):
                os.remove(backup_path)


class TestContextManager:
    """Test context manager functionality."""
    
    def test_context_manager_usage(self, temp_db):
        """Test DatabaseManager as context manager."""
        with DatabaseManager(temp_db) as db_manager:
            results = db_manager.execute_query("SELECT * FROM test_players")
            assert isinstance(results, list)
        
        # Manager should be closed after context exit
        # Connection pool should be closed


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_query_with_none_params(self, db_manager):
        """Test query execution with None params."""
        results = db_manager.execute_query(
            "SELECT * FROM test_players",
            None
        )
        assert isinstance(results, list)
    
    def test_invalid_query_raises_error(self, db_manager):
        """Test that invalid SQL raises error."""
        with pytest.raises(sqlite3.Error):
            db_manager.execute_query("INVALID SQL SYNTAX")
    
    def test_query_validation_failure_raises_error(self, db_manager):
        """Test that validation failure raises ValueError."""
        with pytest.raises(ValueError):
            db_manager.execute_query("SELECT * FROM players; DROP TABLE players")
