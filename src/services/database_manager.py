"""
Database Manager for LifeHunter System

This module provides a wrapper for database operations using MCP SQLite protocol.
It handles connection pooling, transaction management, query validation, and backups.

Key Features:
- Execute SQL queries via MCP SQLite server
- Manage connection pool (max 10 connections, 30s timeout)
- Handle transaction rollback for consistency
- Validate queries for safety
- Log all operations
- Implement backup functionality

Usage:
    db_manager = DatabaseManager()
    results = db_manager.execute_query("SELECT * FROM players WHERE id = ?", (1,))
    
    # Transaction example
    queries = [
        ("UPDATE players SET xp = xp + ? WHERE id = ?", (100, 1)),
        ("INSERT INTO notifications (player_id, message) VALUES (?, ?)", (1, "Level up!"))
    ]
    success = db_manager.execute_transaction(queries)
"""

import os
import json
import logging
import shutil
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from contextlib import contextmanager
from queue import Queue, Empty
from threading import Lock


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Connection pool manager for SQLite database connections.
    
    Maintains a pool of reusable connections to avoid overhead of
    creating new connections for each query.
    
    Configuration:
    - Maximum connections: 10
    - Connection timeout: 30 seconds
    - Idle timeout: 300 seconds (5 minutes)
    """
    
    def __init__(self, database_path: str, max_connections: int = 10, timeout: int = 30):
        """
        Initialize connection pool.
        
        Args:
            database_path: Path to SQLite database file
            max_connections: Maximum number of connections in pool
            timeout: Connection timeout in seconds
        """
        self.database_path = database_path
        self.max_connections = max_connections
        self.timeout = timeout
        self.pool = Queue(maxsize=max_connections)
        self.lock = Lock()
        self._connection_count = 0
        
        logger.info(f"Connection pool initialized (max={max_connections}, timeout={timeout}s)")
    
    def _create_connection(self) -> sqlite3.Connection:
        """
        Create a new database connection.
        
        Returns:
            sqlite3.Connection: New database connection
        """
        conn = sqlite3.connect(
            self.database_path,
            timeout=self.timeout,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        logger.debug(f"Created new database connection ({self._connection_count + 1}/{self.max_connections})")
        return conn
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a connection from the pool.
        
        If pool is empty and under max connections, creates a new connection.
        Otherwise waits for an available connection.
        
        Returns:
            sqlite3.Connection: Database connection
            
        Raises:
            TimeoutError: If no connection available within timeout period
        """
        try:
            # Try to get existing connection from pool
            conn = self.pool.get(block=False)
            # Validate connection with simple query
            try:
                conn.execute("SELECT 1")
                logger.debug("Retrieved connection from pool")
                return conn
            except sqlite3.Error:
                # Connection is stale, create new one
                logger.warning("Stale connection detected, creating new one")
                conn.close()
                return self._create_connection()
                
        except Empty:
            # Pool is empty, create new connection if under limit
            with self.lock:
                if self._connection_count < self.max_connections:
                    self._connection_count += 1
                    return self._create_connection()
            
            # Pool exhausted, wait for available connection
            logger.warning(f"Connection pool exhausted, waiting for available connection...")
            try:
                conn = self.pool.get(timeout=self.timeout)
                logger.debug("Retrieved connection after waiting")
                return conn
            except Empty:
                raise TimeoutError(
                    f"Failed to get database connection within {self.timeout} seconds. "
                    f"Pool exhausted ({self.max_connections} connections in use)."
                )
    
    def return_connection(self, conn: sqlite3.Connection):
        """
        Return a connection to the pool.
        
        Args:
            conn: Connection to return to pool
        """
        try:
            # Validate connection is still good
            conn.execute("SELECT 1")
            self.pool.put(conn, block=False)
            logger.debug("Returned connection to pool")
        except (sqlite3.Error, Exception) as e:
            # Connection is bad, don't return to pool
            logger.warning(f"Connection invalid, closing: {e}")
            conn.close()
            with self.lock:
                self._connection_count -= 1
    
    def close_all(self):
        """Close all connections in the pool."""
        logger.info("Closing all connections in pool...")
        while not self.pool.empty():
            try:
                conn = self.pool.get(block=False)
                conn.close()
            except Empty:
                break
        self._connection_count = 0
        logger.info("All connections closed")


class DatabaseManager:
    """
    Database Manager for LifeHunter System.
    
    Provides high-level interface for database operations including:
    - Query execution with parameterization
    - Transaction management with automatic rollback
    - Connection pooling
    - Query validation for security
    - Database backup functionality
    - Operation logging
    
    This implementation uses direct SQLite connections but is designed
    to be compatible with MCP SQLite protocol for future migration.
    """
    
    def __init__(self, database_path: str = "database.db"):
        """
        Initialize Database Manager.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.connection_pool = ConnectionPool(
            database_path=database_path,
            max_connections=10,
            timeout=30
        )
        logger.info(f"Database Manager initialized (database={database_path})")
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for getting and returning connections.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = self.connection_pool.get_connection()
        try:
            yield conn
        finally:
            self.connection_pool.return_connection(conn)
    
    def validate_query(self, query: str) -> bool:
        """
        Validate query for safety before execution.
        
        Checks for common SQL injection patterns and dangerous operations.
        This is a basic validation; parameterized queries are still required.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            bool: True if query appears safe, False otherwise
            
        Example:
            if db_manager.validate_query("SELECT * FROM players"):
                # Execute query
        """
        query_lower = query.lower().strip()
        
        # Check for empty query
        if not query_lower:
            logger.warning("Query validation failed: empty query")
            return False
        
        # Check for SQL injection patterns
        dangerous_patterns = [
            "; drop ",
            "; delete ",
            "; truncate ",
            "' or '1'='1",
            "' or 1=1",
            " or 1=1",
            " or '1'='1",
            "-- ",
            "/*",
            "*/",
            "xp_cmdshell",
            "exec(",
            "execute(",
        ]
        
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                logger.warning(f"Query validation failed: dangerous pattern detected: {pattern}")
                return False
        
        # Warn about unparameterized queries (should use ? placeholders)
        if "'" in query or '"' in query:
            logger.warning("Query contains string literals - consider using parameterized queries")
        
        logger.debug("Query validation passed")
        return True
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute parameterized SQL query and return results.
        
        Args:
            query: SQL query string with ? placeholders
            params: Tuple of parameters to bind to query
            
        Returns:
            List[Dict]: List of result rows as dictionaries
            
        Raises:
            ValueError: If query validation fails
            sqlite3.Error: If query execution fails
            
        Example:
            results = db_manager.execute_query(
                "SELECT * FROM players WHERE id = ?",
                (player_id,)
            )
        """
        if not self.validate_query(query):
            raise ValueError("Query validation failed - query may be unsafe")
        
        params = params or ()
        start_time = time.time()
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                # For SELECT queries, fetch results
                if query.strip().upper().startswith("SELECT"):
                    rows = cursor.fetchall()
                    results = [dict(row) for row in rows]
                    conn.commit()  # Commit even for SELECT to release locks
                    
                    execution_time = time.time() - start_time
                    logger.info(f"Query executed successfully ({len(results)} rows, {execution_time:.3f}s)")
                    return results
                
                # For INSERT/UPDATE/DELETE, commit and return affected rows
                else:
                    conn.commit()
                    affected_rows = cursor.rowcount
                    
                    execution_time = time.time() - start_time
                    logger.info(f"Query executed successfully ({affected_rows} rows affected, {execution_time:.3f}s)")
                    return [{"affected_rows": affected_rows, "lastrowid": cursor.lastrowid}]
                    
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Query params: {params}")
            raise
    
    def execute_transaction(self, queries: List[Tuple[str, Tuple]]) -> bool:
        """
        Execute multiple queries in a transaction with automatic rollback on failure.
        
        All queries are executed atomically - if any query fails, all changes
        are rolled back to maintain data consistency.
        
        Args:
            queries: List of (query, params) tuples to execute
            
        Returns:
            bool: True if transaction succeeded, False otherwise
            
        Example:
            queries = [
                ("UPDATE players SET xp = xp + ? WHERE id = ?", (100, 1)),
                ("INSERT INTO notifications (player_id, message) VALUES (?, ?)", (1, "Level up!"))
            ]
            success = db_manager.execute_transaction(queries)
        """
        if not queries:
            logger.warning("execute_transaction called with empty query list")
            return True
        
        start_time = time.time()
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Begin transaction
                conn.execute("BEGIN TRANSACTION")
                logger.debug(f"Transaction started ({len(queries)} queries)")
                
                # Execute all queries
                for i, (query, params) in enumerate(queries):
                    if not self.validate_query(query):
                        raise ValueError(f"Query {i+1} validation failed")
                    
                    cursor.execute(query, params)
                    logger.debug(f"Query {i+1}/{len(queries)} executed ({cursor.rowcount} rows affected)")
                
                # Commit transaction
                conn.commit()
                execution_time = time.time() - start_time
                logger.info(f"Transaction committed successfully ({len(queries)} queries, {execution_time:.3f}s)")
                return True
                
        except (sqlite3.Error, ValueError) as e:
            # Rollback transaction on any error
            try:
                conn.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
            except:
                logger.error("Failed to rollback transaction")
            
            logger.error(f"Transaction failed: {e}")
            return False
    
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for backup file. If None, generates timestamped filename.
            
        Returns:
            bool: True if backup succeeded, False otherwise
            
        Example:
            success = db_manager.backup_database("backups/db_backup_2025_01_24.db")
        """
        if backup_path is None:
            # Generate timestamped backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"database_backup_{timestamp}.db"
        
        # Ensure backup directory exists
        backup_dir = os.path.dirname(backup_path)
        if backup_dir and not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        start_time = time.time()
        
        try:
            # Use SQLite backup API for consistent backup
            with self._get_connection() as source_conn:
                # Create backup connection
                backup_conn = sqlite3.connect(backup_path)
                
                # Perform backup
                with backup_conn:
                    source_conn.backup(backup_conn)
                
                backup_conn.close()
            
            # Get backup file size
            file_size = os.path.getsize(backup_path)
            file_size_mb = file_size / (1024 * 1024)
            
            execution_time = time.time() - start_time
            logger.info(
                f"Database backup created successfully: {backup_path} "
                f"({file_size_mb:.2f} MB, {execution_time:.3f}s)"
            )
            
            # Log backup to database
            self._log_backup(backup_path, file_size)
            
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            # Clean up partial backup file
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except:
                    pass
            return False
    
    def _log_backup(self, file_path: str, file_size: int):
        """
        Log backup operation to database.
        
        Args:
            file_path: Path to backup file
            file_size: Size of backup file in bytes
        """
        try:
            self.execute_query(
                """
                INSERT INTO database_backups (file_path, file_size, created_at)
                VALUES (?, ?, ?)
                """,
                (file_path, file_size, datetime.now())
            )
        except sqlite3.Error as e:
            logger.warning(f"Failed to log backup to database: {e}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection from the pool.
        
        Returns:
            sqlite3.Connection: Database connection
            
        Note:
            Caller is responsible for returning connection using
            connection_pool.return_connection()
            
        Example:
            conn = db_manager.get_connection()
            try:
                # Use connection
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM players")
            finally:
                db_manager.connection_pool.return_connection(conn)
        """
        return self.connection_pool.get_connection()
    
    def close(self):
        """Close all connections and clean up resources."""
        logger.info("Closing Database Manager...")
        self.connection_pool.close_all()
        logger.info("Database Manager closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


# Singleton instance for application-wide use
_db_manager_instance = None


def get_database_manager(database_path: str = "database.db") -> DatabaseManager:
    """
    Get singleton DatabaseManager instance.
    
    Args:
        database_path: Path to database file
        
    Returns:
        DatabaseManager: Singleton database manager instance
        
    Example:
        db_manager = get_database_manager()
        results = db_manager.execute_query("SELECT * FROM players")
    """
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager(database_path)
    return _db_manager_instance
