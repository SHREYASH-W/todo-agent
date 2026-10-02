"""
Database Manager Usage Examples

This file demonstrates how to use the DatabaseManager class
for various database operations in the LifeHunter system.
"""

from src.services.database_manager import DatabaseManager, get_database_manager


def example_basic_queries():
    """Example: Basic query execution."""
    print("=== Basic Query Execution ===")
    
    db_manager = get_database_manager()
    
    # SELECT query
    players = db_manager.execute_query(
        "SELECT * FROM players WHERE level >= ?",
        (10,)
    )
    print(f"Found {len(players)} players at level 10+")
    
    # INSERT query
    result = db_manager.execute_query(
        "INSERT INTO players (username, email, password_hash) VALUES (?, ?, ?)",
        ("newuser", "newuser@example.com", "hashed_password")
    )
    print(f"Created player with ID: {result[0]['lastrowid']}")
    
    # UPDATE query
    result = db_manager.execute_query(
        "UPDATE players SET xp = xp + ? WHERE id = ?",
        (100, 1)
    )
    print(f"Updated {result[0]['affected_rows']} player(s)")


def example_transactions():
    """Example: Transaction management."""
    print("\n=== Transaction Management ===")
    
    db_manager = get_database_manager()
    
    # Complete a quest and award XP in a single transaction
    queries = [
        ("UPDATE quests SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?", 
         ("completed", 5)),
        ("UPDATE players SET xp = xp + ? WHERE id = ?", 
         (75, 1)),
        ("INSERT INTO notifications (player_id, message) VALUES (?, ?)", 
         (1, "Quest completed! +75 XP"))
    ]
    
    success = db_manager.execute_transaction(queries)
    if success:
        print("Transaction completed successfully - quest marked complete and XP awarded")
    else:
        print("Transaction failed - all changes rolled back")


def example_stat_allocation():
    """Example: Stat point allocation with transaction."""
    print("\n=== Stat Point Allocation ===")
    
    db_manager = get_database_manager()
    
    player_id = 1
    stat_to_allocate = "str_stat"
    points = 5
    
    # Allocate stat points atomically
    queries = [
        (f"UPDATE players SET stat_points = stat_points - ? WHERE id = ? AND stat_points >= ?", 
         (points, player_id, points)),
        (f"UPDATE players SET {stat_to_allocate} = {stat_to_allocate} + ? WHERE id = ?", 
         (points, player_id))
    ]
    
    success = db_manager.execute_transaction(queries)
    if success:
        print(f"Allocated {points} points to {stat_to_allocate}")
    else:
        print("Failed to allocate stat points (insufficient points?)")


def example_backup():
    """Example: Database backup."""
    print("\n=== Database Backup ===")
    
    db_manager = get_database_manager()
    
    # Create backup with auto-generated filename
    success = db_manager.backup_database()
    if success:
        print("Backup created successfully with auto-generated filename")
    
    # Create backup with custom path
    success = db_manager.backup_database("backups/lifehunter_backup_20250124.db")
    if success:
        print("Backup created at custom path")


def example_query_validation():
    """Example: Query validation for security."""
    print("\n=== Query Validation ===")
    
    db_manager = get_database_manager()
    
    # Safe query
    safe_query = "SELECT * FROM players WHERE id = ?"
    if db_manager.validate_query(safe_query):
        print("✓ Safe query validated successfully")
    
    # Unsafe query (SQL injection attempt)
    unsafe_query = "SELECT * FROM players WHERE id = 1; DROP TABLE players"
    if not db_manager.validate_query(unsafe_query):
        print("✗ Unsafe query rejected")


def example_connection_pool():
    """Example: Using connection pool."""
    print("\n=== Connection Pool Usage ===")
    
    db_manager = get_database_manager()
    
    # Get connection from pool
    conn = db_manager.get_connection()
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM players")
        result = cursor.fetchone()
        print(f"Total players: {result['count']}")
    finally:
        # Always return connection to pool
        db_manager.connection_pool.return_connection(conn)


def example_context_manager():
    """Example: Using DatabaseManager as context manager."""
    print("\n=== Context Manager Usage ===")
    
    with DatabaseManager("database.db") as db_manager:
        # Database manager automatically closes when context exits
        players = db_manager.execute_query("SELECT COUNT(*) as count FROM players")
        print(f"Total players: {players[0]['count']}")
    
    print("DatabaseManager closed automatically")


def example_level_up_transaction():
    """Example: Complete level-up transaction."""
    print("\n=== Level Up Transaction ===")
    
    db_manager = get_database_manager()
    
    player_id = 1
    xp_to_add = 500
    new_level = 11
    stat_points_granted = 5
    skill_points_granted = 1
    
    # Level up transaction: add XP, update level, grant points, update rank
    queries = [
        ("UPDATE players SET xp = xp + ? WHERE id = ?", 
         (xp_to_add, player_id)),
        ("UPDATE players SET level = ? WHERE id = ?", 
         (new_level, player_id)),
        ("UPDATE players SET stat_points = stat_points + ? WHERE id = ?", 
         (stat_points_granted, player_id)),
        ("UPDATE players SET skill_points = skill_points + ? WHERE id = ?", 
         (skill_points_granted, player_id)),
        ("UPDATE players SET rank = ? WHERE id = ? AND level >= ?", 
         ("D", player_id, 10)),
        ("INSERT INTO notifications (player_id, message) VALUES (?, ?)", 
         (player_id, f"Level Up! Now level {new_level}. +{stat_points_granted} stat points, +{skill_points_granted} skill point"))
    ]
    
    success = db_manager.execute_transaction(queries)
    if success:
        print(f"Player leveled up to {new_level} successfully!")
    else:
        print("Level up failed - all changes rolled back")


def example_job_application_workflow():
    """Example: Job application workflow transaction."""
    print("\n=== Job Application Workflow ===")
    
    db_manager = get_database_manager()
    
    player_id = 1
    job_id = 42
    cover_letter = "AI-generated cover letter content..."
    
    # Create application, award XP, add to inventory
    queries = [
        ("INSERT INTO applications (player_id, job_id, status, cover_letter) VALUES (?, ?, ?, ?)", 
         (player_id, job_id, "submitted", cover_letter)),
        ("UPDATE players SET xp = xp + 50 WHERE id = ?", 
         (player_id,)),
        ("INSERT INTO inventory_items (player_id, item_type, name, content) VALUES (?, ?, ?, ?)", 
         (player_id, "template", "Cover Letter - Job #42", cover_letter)),
        ("INSERT INTO notifications (player_id, message) VALUES (?, ?)", 
         (player_id, "Application submitted! +50 XP"))
    ]
    
    success = db_manager.execute_transaction(queries)
    if success:
        print("Job application submitted successfully with XP reward and saved cover letter")
    else:
        print("Application submission failed - all changes rolled back")


if __name__ == "__main__":
    print("Database Manager Usage Examples")
    print("=" * 50)
    
    # Note: These examples assume the database exists and has the schema
    # Run src/db/init_db.py first to create tables
    
    try:
        example_basic_queries()
        example_transactions()
        example_stat_allocation()
        example_backup()
        example_query_validation()
        example_connection_pool()
        example_context_manager()
        example_level_up_transaction()
        example_job_application_workflow()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure to initialize the database first with src/db/init_db.py")
